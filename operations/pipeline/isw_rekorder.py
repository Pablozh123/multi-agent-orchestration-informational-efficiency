"""Rekorder für den Vorlauf ISW-Karte → Polymarket-Preis.

Misst, wie lange der Markt braucht, bis er eine Änderung der Auflösungsquelle
einpreist. Handelt nicht. Kein Order-Pfad, keine Keys, keine Wallet.

Warum überhaupt messen statt gleich handeln: Es gibt genau EINE saubere
Beobachtung (Krasnoiarske, 22.07.2026, Vorlauf 18 min 43 s, am 23.07. mit YES
aufgelöst). Ein historischer Backtest ist ausgeschlossen, weil ISW die
Polygone periodisch löscht und neu zeichnet — `CreationDate` ist kein
Ereignisprotokoll. Belastbar ist nur Vorwärtsmessung.

Messdesign (nach dem Logik-Review vom 24.07.):

1. Stolperdraht — `editingInfo.lastEditDate` der vier qualifizierenden Layer.
   Der Layer-Stand wird erst NACH erfolgreicher Auswertung fortgeschrieben:
   scheitert der Flächenabruf, versucht es der nächste Poll erneut, statt das
   Ereignis endgültig zu verlieren. `None` überschreibt nie einen bekannten
   Stand.
2. Übergänge — der beobachtete Deckungszustand je Siedlung und Layer wird mit
   dem aktuellen Flächenschnitt verglichen. Jeder Übergang erzeugt einen
   KANDIDATEN (`kandidat_treffer` / `kandidat_verlust`) mit sofortiger
   T+0-Messung: Preis, Orderbuch-Tiefe, Vorlauf.
3. Beruhigungsfenster — ein Kandidat wird erst nach BERUHIGUNG_S Bestand
   bestätigt (`*_bestaetigt`) oder verworfen (`*_verworfen`). Kehrt der alte
   Zustand vorher zurück, heben sich Kandidat und Gegenereignis auf (Flap).
   Das nettet die Lösch-/Neuzeichnen-Zyklen der ISW-Rebuilds zu null und
   spiegelt zugleich die Persistenzklausel der Marktregel.
4. Vorlauf — `vorlauf_s` rechnet gegen die JÜNGSTE Änderung
   (max(CreationDate, EditDate)) der jüngsten schneidenden Fläche, mit einer
   je Layer FRISCH genommenen Erkennungszeit. Beides Review-Befunde: die alte
   Fassung mass bei erweiterten Polygonen die Anlagezeit (Tage statt
   Sekunden) und fror `jetzt` vor dem Backoff ein (negative Vorläufe
   möglich).

Die Auswertung nutzt nur `*_bestaetigt`-Ereignisse; die T+0-Messung stammt
aus dem Kandidaten-Eintrag. Bekannte Restlücke: stürzt der Prozess zwischen
Protokoll-Zeile und Zustands-Schreiben ab, kann ein Kandidat nach Neustart
doppelt protokolliert werden — bei der Auswertung über (slug, layer,
erste_sichtung) deduplizieren.

Die Marktliste wird alle MARKT_REFRESH_S neu gezogen (ein Gamma-Aufruf);
nur die Siedlungsgeometrien sind dauerhaft gecacht — sie sind
Verwaltungsgrenzen, ändern sich nie und waren als wiederholte Abfrage der
Auslöser der ArcGIS-Drosselung.

Aufruf:

    python -m operations.pipeline.isw_rekorder --einmal
    python -m operations.pipeline.isw_rekorder --takt-s 20
"""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import httpx

from operations.pipeline.isw_karten_watch import (
    QUALIFIZIERENDE_LAYER,
    ISWFehler,
    ISWFlaeche,
    ISWKarte,
    koordinate_aus_beschreibung,
    markt_kriterium,
    markt_polaritaet,
    polygone_beruehren,
)

GAMMA_BASIS = "https://gamma-api.polymarket.com"
CLOB_BASIS = "https://clob.polymarket.com"
UKRAINE_TAG = "ukraine-map"

# ISW arbeitet im US-Ostküsten-Arbeitstag; beobachtete Einzel-Edits am 22.07.
# lagen bei 15:20, 18:47, 19:48, 20:14 und 20:39 UTC.
AKTIV_VON_UTC = 14
AKTIV_BIS_UTC = 23
TAKT_AKTIV_S = 20
TAKT_RUHE_S = 120

# Beruhigungsfenster: der Rebuild vom 21.07. brauchte 48 Minuten vom ersten
# bis zum letzten Feature. 60 Minuten decken Löschen-und-Neuzeichnen ab.
BERUHIGUNG_S = 3600

# Marktliste neu ziehen (ein Gamma-Aufruf): 10 von 52 Märkten waren nach dem
# ersten 19-h-Fenster bereits geschlossen — eine Startliste veraltet schnell.
MARKT_REFRESH_S = 900

# HTTP-Budget je Zyklus für Preis-/Buchabrufe: ein Massenübergang (Rebuild)
# darf nicht Dutzende CLOB-Aufrufe in einem Durchlauf auslösen.
PREISABRUFE_JE_ZYKLUS = 12

NACHFASS_MINUTEN = (0, 1, 5, 30)

STANDARD_ZUSTAND = Path("data/live/isw_rekorder/zustand.json")
STANDARD_PROTOKOLL = Path("data/live/isw_rekorder/ereignisse.jsonl")
STANDARD_GEOMETRIE = Path("data/live/isw_rekorder/geometrie_cache.json")

ZUSTAND_SCHEMA = 2


def _leerer_zustand() -> dict:
    return {
        "schema": ZUSTAND_SCHEMA,
        "layer_stand": {},
        "beobachtet": {},        # slug -> [layernamen mit beobachteter Deckung]
        "kandidaten": [],        # offene Übergänge im Beruhigungsfenster
        "qualifiziert": {},      # slug -> [layer], bestätigte Treffer (absorbierend)
        "offene_nachfassungen": [],
    }


@dataclass
class Marktziel:
    """Ein beobachteter Markt samt aufgelöster Siedlungsfläche."""

    slug: str
    frage: str
    lat: float
    lon: float
    token_yes: str
    polaritaet: str
    kriterium: str
    siedlung_name: str
    siedlung_objectid: int
    ringe: list[list[list[float]]] = field(default_factory=list)

    @property
    def auswertbar(self) -> bool:
        """Ob ein Treffer überhaupt als Signal taugt."""
        return self.polaritaet == "russisch" and self.kriterium == "beruehrung"


def _jetzt_utc() -> datetime:
    return datetime.now(UTC)


def _iso(zeit: datetime) -> str:
    return zeit.strftime("%Y-%m-%dT%H:%M:%SZ")


def _ms_nach_iso(ms: int | None) -> str | None:
    if ms is None:
        return None
    return _iso(datetime.fromtimestamp(ms / 1000, UTC))


def takt_fuer(zeit: datetime) -> int:
    """Poll-Abstand: dicht im ISW-Arbeitsfenster, sonst sparsam."""
    return TAKT_AKTIV_S if AKTIV_VON_UTC <= zeit.hour < AKTIV_BIS_UTC else TAKT_RUHE_S


# ------------------------------------------------------------- Polymarket

class PolymarktLeser:
    """Read-only Polymarket-Zugriff: Marktliste, Preise, Orderbuch."""

    def __init__(self, timeout: float = 30.0,
                 client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "thesis-isw-rekorder/1.0 (read-only)"},
        )

    def maerkte(self, tag: str = UKRAINE_TAG) -> list[dict]:
        """Alle offenen Märkte des Tags, über die Event-Liste eingesammelt."""
        gesehen: dict[str, dict] = {}
        for offset in range(0, 500, 100):
            antwort = self._client.get(
                f"{GAMMA_BASIS}/events",
                params={"limit": 100, "offset": offset,
                        "closed": "false", "tag_slug": tag},
            )
            antwort.raise_for_status()
            stapel = antwort.json()
            if not stapel:
                break
            for ereignis in stapel:
                for markt in ereignis.get("markets") or []:
                    if markt.get("closed") or not markt.get("acceptingOrders"):
                        continue
                    gesehen[str(markt.get("id"))] = markt
        return list(gesehen.values())

    def preis_yes(self, token_id: str) -> float | None:
        """Mittelpreis der YES-Seite; None wenn kein Buch vorhanden."""
        try:
            antwort = self._client.get(
                f"{CLOB_BASIS}/midpoint", params={"token_id": token_id}
            )
            antwort.raise_for_status()
            wert = antwort.json().get("mid")
            return float(wert) if wert is not None else None
        except (httpx.HTTPError, ValueError, TypeError):
            return None

    def buch_tiefe(self, token_id: str) -> dict | None:
        """Ask-Tiefe der YES-Seite — beantwortet 'war das Buch füllbar?'.

        Der Midpoint allein kann das nicht (Review-Befund 24.07.): im
        Krasnoiarske-Sweep lag der billigste Fill bei 0.395, obwohl der
        Midpoint davor 0.046 zeigte.
        """
        try:
            antwort = self._client.get(
                f"{CLOB_BASIS}/book", params={"token_id": token_id}
            )
            antwort.raise_for_status()
            buch = antwort.json()
            asks = sorted(
                (float(a["price"]), float(a["size"]))
                for a in buch.get("asks") or []
            )
            bids = [float(b["price"]) for b in buch.get("bids") or []]

            def usd_bis(grenze: float) -> float:
                return round(sum(p * s for p, s in asks if p <= grenze), 2)

            return {
                "best_bid": max(bids) if bids else None,
                "best_ask": asks[0][0] if asks else None,
                "usd_bis_030": usd_bis(0.30),
                "usd_bis_050": usd_bis(0.50),
            }
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return None

    def schliessen(self) -> None:
        self._client.close()


# ------------------------------------------------ Geometrie-Cache & Maerkte

def _cache_key(lat: float, lon: float) -> str:
    return f"{lat:.5f},{lon:.5f}"


def lade_geometrie_cache(pfad: Path,
                         alt_watchlist: Path | None = None) -> dict:
    """Siedlungsgeometrien aus dem Cache; einmalige Migration vom alten
    watchlist.json (das Geometrie und Marktliste vermischte)."""
    if pfad.exists():
        try:
            roh = json.loads(pfad.read_text(encoding="utf-8"))
            if isinstance(roh, dict):
                return roh
        except (json.JSONDecodeError, OSError):
            pass
    cache: dict = {}
    if alt_watchlist is not None and alt_watchlist.exists():
        try:
            alt = json.loads(alt_watchlist.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            alt = []
        if isinstance(alt, list):
            for eintrag in alt:
                try:
                    cache.setdefault(
                        _cache_key(eintrag["lat"], eintrag["lon"]),
                        {
                            "objectid": eintrag["siedlung_objectid"],
                            "name": eintrag["siedlung_name"],
                            "ringe": eintrag["ringe"],
                        },
                    )
                except (KeyError, TypeError):
                    continue
    return cache


def speichere_geometrie_cache(pfad: Path, cache: dict) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    temp = pfad.with_suffix(pfad.suffix + ".tmp")
    temp.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    temp.replace(pfad)


def lade_marktziele(leser: PolymarktLeser, karte: ISWKarte, cache: dict,
                    cache_pfad: Path | None,
                    pause_s: float = 0.3) -> list[Marktziel]:
    """Offene Märkte auf Siedlungsflächen abbilden.

    Zuordnung ausschliesslich über die Koordinate (Namen weichen zwischen
    Markt und ISW-Layer ab). Der Siedlungslayer wird nur für Koordinaten
    befragt, die noch nicht im Cache liegen — auch negative Ergebnisse
    werden gemerkt, sonst fragt jeder Refresh dieselben Lücken erneut ab.
    """
    ziele: list[Marktziel] = []
    gewachsen = False
    for markt in leser.maerkte():
        koordinate = koordinate_aus_beschreibung(markt.get("description"))
        if koordinate is None:
            continue
        lat, lon = koordinate
        schluessel = _cache_key(lat, lon)
        if schluessel not in cache:
            siedlung = karte.siedlung_an_punkt(lat, lon)
            if siedlung is None or not siedlung.ringe:
                cache[schluessel] = {"leer": True}
            else:
                cache[schluessel] = {
                    "objectid": siedlung.objectid,
                    "name": siedlung.name,
                    "ringe": siedlung.ringe,
                }
            gewachsen = True
            if pause_s:
                time.sleep(pause_s)
        eintrag = cache[schluessel]
        if eintrag.get("leer"):
            continue
        try:
            token = json.loads(markt.get("clobTokenIds") or "[]")[0]
        except (json.JSONDecodeError, IndexError, TypeError):
            continue
        slug = markt.get("slug") or ""
        ziele.append(Marktziel(
            slug=slug,
            frage=markt.get("question") or "",
            lat=lat,
            lon=lon,
            token_yes=str(token),
            polaritaet=markt_polaritaet(slug),
            kriterium=markt_kriterium(slug),
            siedlung_name=eintrag["name"],
            siedlung_objectid=eintrag["objectid"],
            ringe=eintrag["ringe"],
        ))
    if gewachsen and cache_pfad is not None:
        speichere_geometrie_cache(cache_pfad, cache)
    return ziele


# ------------------------------------------------------------ Kernauswertung

def deckung(flaechen: list[ISWFlaeche],
            ziele: list[Marktziel]) -> dict[str, ISWFlaeche]:
    """Welche Siedlungen deckt dieser Layer gerade? slug -> jüngste Fläche.

    Bewusst die JÜNGSTE schneidende Fläche, nicht die erste in
    Server-Reihenfolge: der Ereignis-Zeitstempel soll von der auslösenden
    Änderung stammen, nicht von einem Alt-Polygon mit Randberührung
    (Review-Befund 24.07.).
    """
    heraus: dict[str, ISWFlaeche] = {}
    for ziel in ziele:
        beste: ISWFlaeche | None = None
        for flaeche in flaechen:
            if not flaeche.ringe:
                continue
            if not polygone_beruehren(flaeche.ringe, ziel.ringe):
                continue
            if beste is None or ((flaeche.juengste_aenderung_ms or -1)
                                 > (beste.juengste_aenderung_ms or -1)):
                beste = flaeche
        if beste is not None:
            heraus[ziel.slug] = beste
    return heraus


# ------------------------------------------------------- Zustand & Protokoll

def _lade_zustand(pfad: Path) -> dict:
    if not pfad.exists():
        return _leerer_zustand()
    try:
        roh = json.loads(pfad.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _leerer_zustand()
    if not isinstance(roh, dict) or roh.get("schema") != ZUSTAND_SCHEMA:
        # Schema-Wechsel: bewusst neu grundieren (der Multipart-Fix vom
        # 24.07. kann den Deckungszustand ändern).
        return _leerer_zustand()
    zustand = _leerer_zustand()
    zustand.update(roh)
    return zustand


def _schreibe_zustand(pfad: Path, zustand: dict) -> None:
    """Atomar, mit einem Wiederholungsversuch (Windows-Datei-Locks)."""
    for versuch in (0, 1):
        try:
            pfad.parent.mkdir(parents=True, exist_ok=True)
            temp = pfad.with_suffix(pfad.suffix + ".tmp")
            temp.write_text(
                json.dumps(zustand, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temp.replace(pfad)
            return
        except OSError:
            if versuch:
                break
            time.sleep(0.5)
    print("WARNUNG Zustand nicht geschrieben, naechster Zyklus versucht erneut")


def _protokolliere(pfad: Path, eintrag: dict) -> None:
    """Zeile anhängen, mit einem Wiederholungsversuch; nie den Lauf abreissen."""
    zeile = json.dumps(eintrag, ensure_ascii=False)
    for versuch in (0, 1):
        try:
            pfad.parent.mkdir(parents=True, exist_ok=True)
            with pfad.open("a", encoding="utf-8") as datei:
                datei.write(zeile + "\n")
            return
        except OSError:
            if versuch:
                break
            time.sleep(0.5)
    print(f"WARNUNG Protokoll nicht schreibbar: {zeile[:200]}")


# ---------------------------------------------------------------- Kandidaten

def _entferne_kandidat(zustand: dict, slug: str, layer: str,
                       art: str) -> dict | None:
    """Offenen Kandidaten (slug, layer, art) aus dem Zustand nehmen."""
    for i, k in enumerate(zustand["kandidaten"]):
        if k["slug"] == slug and k["layer"] == layer and k["art"] == art:
            return zustand["kandidaten"].pop(i)
    return None


def _reife_kandidaten(zustand: dict, leser: PolymarktLeser,
                      protokoll: Path) -> None:
    """Kandidaten nach Ablauf des Beruhigungsfensters entscheiden."""
    jetzt = _jetzt_utc()
    ts = jetzt.timestamp()
    offen: list[dict] = []
    for k in zustand["kandidaten"]:
        if ts - k["erste_sichtung_ts"] < BERUHIGUNG_S:
            offen.append(k)
            continue
        gedeckt = k["layer"] in zustand["beobachtet"].get(k["slug"], [])
        haelt = gedeckt if k["art"] == "treffer" else not gedeckt
        status = "bestaetigt" if haelt else "verworfen"
        eintrag = {
            "art": f"{k['art']}_{status}",
            "zeit_utc": _iso(jetzt),
            "slug": k["slug"],
            "layer": k["layer"],
            "siedlung": k.get("siedlung"),
            "auswertbar": k.get("auswertbar"),
            "erste_sichtung_utc": k.get("erste_sichtung_utc"),
            "dauer_s": round(ts - k["erste_sichtung_ts"], 1),
        }
        if k.get("auswertbar"):
            eintrag["preis_yes_jetzt"] = leser.preis_yes(k["token"])
        _protokolliere(protokoll, eintrag)
        if k["art"] == "treffer" and status == "bestaetigt":
            q = zustand["qualifiziert"].setdefault(k["slug"], [])
            if k["layer"] not in q:
                q.append(k["layer"])
    zustand["kandidaten"] = offen


def _bereinige_zustand(zustand: dict, slugs_aktiv: set[str],
                       protokoll: Path) -> int:
    """Zustand auf die aktuelle Marktliste einschränken.

    Kandidaten geschlossener Märkte werden mit eigenem Status protokolliert:
    ein Markt, der vor Ablauf des Beruhigungsfensters schliesst, ist oft
    genau der interessante Fall (aufgelöst wegen des Ereignisses).
    """
    jetzt = _jetzt_utc()
    behalten: list[dict] = []
    geschlossen = 0
    for k in zustand["kandidaten"]:
        if k["slug"] in slugs_aktiv:
            behalten.append(k)
            continue
        geschlossen += 1
        _protokolliere(protokoll, {
            "art": k["art"] + "_markt_geschlossen",
            "zeit_utc": _iso(jetzt),
            "slug": k["slug"],
            "layer": k["layer"],
            "erste_sichtung_utc": k.get("erste_sichtung_utc"),
            "hinweis": "Markt vor Fensterende geschlossen (oft: aufgeloest)",
        })
    zustand["kandidaten"] = behalten
    for slug in [s for s in zustand["beobachtet"] if s not in slugs_aktiv]:
        del zustand["beobachtet"][slug]
    zustand["offene_nachfassungen"] = [
        a for a in zustand["offene_nachfassungen"] if a["slug"] in slugs_aktiv
    ]
    return geschlossen


# -------------------------------------------------------------- Durchlauf

def durchlauf(karte: ISWKarte,
              leser: PolymarktLeser,
              ziele: list[Marktziel],
              zustand: dict,
              protokoll: Path) -> list[dict]:
    """Ein Poll-Zyklus über alle vier Layer. Liefert neue Kandidaten-Einträge."""
    meldungen: list[dict] = []
    budget = {"rest": PREISABRUFE_JE_ZYKLUS}
    slugs_aktiv = {z.slug for z in ziele}
    ziel_nach_slug = {z.slug: z for z in ziele}

    def _preis(token: str) -> tuple[float | None, bool]:
        if budget["rest"] <= 0:
            return None, True
        budget["rest"] -= 1
        return leser.preis_yes(token), False

    for layer in QUALIFIZIERENDE_LAYER:
        try:
            stand = karte.layer_stand(layer)
        except ISWFehler as fehler:
            _protokolliere(protokoll, {
                "art": "fehler", "zeit_utc": _iso(_jetzt_utc()),
                "layer": layer.name, "status": fehler.status,
            })
            continue
        if stand is None:
            # Metadaten ohne lastEditDate: bekannten Stand NIE mit None
            # ueberschreiben, sonst grundiert der Folgelauf still
            # (Review-Befund 24.07.).
            continue
        vorher = zustand["layer_stand"].get(layer.name)
        if vorher == stand:
            continue

        try:
            flaechen = karte.flaechen(layer)
        except ISWFehler as fehler:
            # layer_stand bewusst NICHT fortschreiben: der naechste Poll
            # sieht die Aenderung erneut, statt sie endgueltig zu verlieren.
            _protokolliere(protokoll, {
                "art": "fehler", "zeit_utc": _iso(_jetzt_utc()),
                "layer": layer.name, "status": fehler.status,
            })
            continue

        # Erkennungszeit FRISCH nach dem Abruf — ein eingefrorenes 'jetzt'
        # macht vorlauf_s unter Backoff minutenweise falsch.
        jetzt = _jetzt_utc()
        aktuelle = deckung(flaechen, ziele)
        vorher_gedeckt = {
            s for s, layers in zustand["beobachtet"].items()
            if layer.name in layers and s in slugs_aktiv
        }
        grundierung = vorher is None

        for slug in [s for s in aktuelle if s not in vorher_gedeckt]:
            zustand["beobachtet"].setdefault(slug, [])
            if layer.name not in zustand["beobachtet"][slug]:
                zustand["beobachtet"][slug].append(layer.name)
            if grundierung:
                continue
            flap = _entferne_kandidat(zustand, slug, layer.name, "verlust")
            if flap is not None:
                _protokolliere(protokoll, {
                    "art": "verlust_verworfen",
                    "zeit_utc": _iso(jetzt),
                    "slug": slug,
                    "layer": layer.name,
                    "dauer_s": round(jetzt.timestamp()
                                     - flap["erste_sichtung_ts"], 1),
                    "hinweis": "Deckung binnen Fenster zurueck (Flap/Rebuild)",
                })
                continue
            ziel = ziel_nach_slug[slug]
            flaeche = aktuelle[slug]
            preis, uebersprungen = _preis(ziel.token_yes)
            buch = None
            if ziel.auswertbar and budget["rest"] > 0:
                budget["rest"] -= 1
                buch = leser.buch_tiefe(ziel.token_yes)
            vorlauf = None
            if flaeche.juengste_aenderung_ms:
                vorlauf = round(
                    jetzt.timestamp() - flaeche.juengste_aenderung_ms / 1000, 1
                )
            kandidat = {
                "art": "treffer",
                "slug": slug,
                "layer": layer.name,
                "siedlung": ziel.siedlung_name,
                "token": ziel.token_yes,
                "auswertbar": ziel.auswertbar,
                "objectid": flaeche.objectid,
                "erste_sichtung_ts": jetzt.timestamp(),
                "erste_sichtung_utc": _iso(jetzt),
                "vorlauf_s": vorlauf,
            }
            zustand["kandidaten"].append(kandidat)
            eintrag = {
                "art": "kandidat_treffer",
                "zeit_utc": _iso(jetzt),
                "slug": slug,
                "layer": layer.name,
                "siedlung": ziel.siedlung_name,
                "objectid": flaeche.objectid,
                "feature_zeit_utc": _ms_nach_iso(flaeche.juengste_aenderung_ms),
                "vorlauf_s": vorlauf,
                "polaritaet": ziel.polaritaet,
                "kriterium": ziel.kriterium,
                "auswertbar": ziel.auswertbar,
                "markt_bereits_qualifiziert":
                    bool(zustand["qualifiziert"].get(slug)),
                "preis_yes": preis,
                "preis_uebersprungen": uebersprungen,
                "buch": buch,
            }
            _protokolliere(protokoll, eintrag)
            meldungen.append(eintrag)
            for minute in NACHFASS_MINUTEN[1:]:
                zustand["offene_nachfassungen"].append({
                    "slug": slug,
                    "token": ziel.token_yes,
                    "layer": layer.name,
                    "minute": minute,
                    "erste_sichtung_ts": jetzt.timestamp(),
                    "faellig_ts": jetzt.timestamp() + minute * 60,
                })

        for slug in [s for s in vorher_gedeckt if s not in aktuelle]:
            zustand["beobachtet"][slug] = [
                name for name in zustand["beobachtet"].get(slug, [])
                if name != layer.name
            ]
            if grundierung:
                continue
            flap = _entferne_kandidat(zustand, slug, layer.name, "treffer")
            if flap is not None:
                _protokolliere(protokoll, {
                    "art": "treffer_verworfen",
                    "zeit_utc": _iso(jetzt),
                    "slug": slug,
                    "layer": layer.name,
                    "dauer_s": round(jetzt.timestamp()
                                     - flap["erste_sichtung_ts"], 1),
                    "hinweis": "Deckung binnen Fenster verschwunden (Flap)",
                })
                continue
            ziel = ziel_nach_slug[slug]
            preis = None
            if ziel.auswertbar:
                preis, _ = _preis(ziel.token_yes)
            kandidat = {
                "art": "verlust",
                "slug": slug,
                "layer": layer.name,
                "siedlung": ziel.siedlung_name,
                "token": ziel.token_yes,
                "auswertbar": ziel.auswertbar,
                "erste_sichtung_ts": jetzt.timestamp(),
                "erste_sichtung_utc": _iso(jetzt),
            }
            zustand["kandidaten"].append(kandidat)
            _protokolliere(protokoll, {
                "art": "kandidat_verlust",
                "zeit_utc": _iso(jetzt),
                "slug": slug,
                "layer": layer.name,
                "siedlung": ziel.siedlung_name,
                "auswertbar": ziel.auswertbar,
                "preis_yes": preis,
                "restliche_layer": zustand["beobachtet"].get(slug, []),
            })

        if grundierung:
            # Bereits gedeckte Siedlungen gelten als qualifiziert: der Markt
            # preist sie laengst (Divergenz-Scan 23.07.: alle bei 0.91+).
            for slug in aktuelle:
                q = zustand["qualifiziert"].setdefault(slug, [])
                if layer.name not in q:
                    q.append(layer.name)
            _protokolliere(protokoll, {
                "art": "grundierung",
                "zeit_utc": _iso(jetzt),
                "layer": layer.name,
                "n_flaechen": len(flaechen),
                "n_gedeckt": len(aktuelle),
            })

        # Erst NACH erfolgreicher Auswertung fortschreiben.
        zustand["layer_stand"][layer.name] = stand

    _reife_kandidaten(zustand, leser, protokoll)
    _faellige_nachfassungen(leser, zustand, protokoll)
    return meldungen


def _faellige_nachfassungen(leser: PolymarktLeser, zustand: dict,
                            protokoll: Path) -> None:
    """Preis-Nachfassungen einsammeln, deren Zeitpunkt erreicht ist.

    Protokolliert neben der geplanten Minute den realen Abstand zur ersten
    Sichtung — unter Backoff können die auseinanderlaufen, und die
    Auswertung braucht den echten Abstand.
    """
    jetzt = _jetzt_utc()
    ts = jetzt.timestamp()
    offen = []
    for auftrag in zustand.get("offene_nachfassungen", []):
        if auftrag["faellig_ts"] > ts:
            offen.append(auftrag)
            continue
        real_s = None
        if auftrag.get("erste_sichtung_ts"):
            real_s = round(ts - auftrag["erste_sichtung_ts"], 1)
        _protokolliere(protokoll, {
            "art": "nachfassung",
            "zeit_utc": _iso(jetzt),
            "slug": auftrag["slug"],
            "layer": auftrag["layer"],
            "geplante_minute": auftrag["minute"],
            "real_s": real_s,
            "preis_yes": leser.preis_yes(auftrag["token"]),
        })
    zustand["offene_nachfassungen"] = offen


def _herzschlag(live_dir: Path | None, art: str = "herzschlag",
                **extra) -> None:
    """Watchdog-Lebenszeichen nach `data/live/<profil>/bot_events.jsonl`.

    Der Watchdog erklärt einen Bot für tot, wenn das letzte Event älter als
    600 s ist (`STALE_S`); `art` "stop"/"fertig" heisst absichtlich beendet.
    Der Ruhe-Takt von 120 s hält den Abstand komfortabel darunter.
    """
    if live_dir is None:
        return
    zeile = json.dumps(
        {"wall_ts_utc": _iso(_jetzt_utc()), "art": art, **extra},
        ensure_ascii=False,
    )
    for versuch in (0, 1):
        try:
            live_dir.mkdir(parents=True, exist_ok=True)
            with (live_dir / "bot_events.jsonl").open(
                    "a", encoding="utf-8") as datei:
                datei.write(zeile + "\n")
            return
        except OSError:
            if versuch:
                break
            time.sleep(0.5)
    print("WARNUNG bot_events.jsonl nicht schreibbar")


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        description="Rekorder ISW-Karte -> Polymarket-Preis (read-only)")
    zerleger.add_argument("--einmal", action="store_true",
                          help="nur ein Durchlauf, dann beenden")
    zerleger.add_argument("--takt-s", type=int, default=None,
                          help="fester Poll-Abstand statt Tageszeit-Automatik")
    zerleger.add_argument("--live", action="store_true",
                          help="Watchdog-Modus: Profil aus BOT_PROFIL, "
                               "Startwache-Lock, bot.pid, Herzschlag-Events; "
                               "alle Pfade unter data/live/<profil>/")
    zerleger.add_argument("--zustand", type=Path, default=STANDARD_ZUSTAND)
    zerleger.add_argument("--protokoll", type=Path, default=STANDARD_PROTOKOLL)
    zerleger.add_argument("--geometrie-cache", type=Path,
                          default=STANDARD_GEOMETRIE)
    zerleger.add_argument("--markt-refresh-s", type=int,
                          default=MARKT_REFRESH_S)
    argumente = zerleger.parse_args(argv)

    live_dir: Path | None = None
    if argumente.live:
        # Watchdog-Vertrag (siehe operations/pipeline/watchdog.py): Start
        # als `-m ... --live` mit BOT_PROFIL in der Umgebung; genau eine
        # Instanz je Profil via start.lock; bot.pid sofort nach Lock-Gewinn
        # (uebernimmt wache_nehmen); Lebenszeichen in bot_events.jsonl.
        profil = os.environ.get("BOT_PROFIL", "isw_ukraine")
        wurzel = Path(os.environ.get("THESIS_LIVE_ROOT", "data/live"))
        live_dir = wurzel / profil
        from operations.pipeline.startwache import wache_nehmen
        if not wache_nehmen(live_dir):
            print(f"{profil}: andere Instanz haelt start.lock - Ende.")
            return 0
        argumente.zustand = live_dir / "zustand.json"
        argumente.protokoll = live_dir / "ereignisse.jsonl"
        argumente.geometrie_cache = live_dir / "geometrie_cache.json"
        _herzschlag(live_dir, art="start")

    karte = ISWKarte()
    leser = PolymarktLeser()
    zustand = _lade_zustand(argumente.zustand)
    cache = lade_geometrie_cache(
        argumente.geometrie_cache,
        alt_watchlist=argumente.geometrie_cache.parent / "watchlist.json",
    )

    print("Marktliste wird aufgebaut ...")
    try:
        ziele = lade_marktziele(leser, karte, cache, argumente.geometrie_cache)
    except Exception as fehler:  # noqa: BLE001 - ohne Ziele kein Betrieb
        # Bewusst KEIN stop-Event: transiente Gamma-Ausfaelle soll der
        # Watchdog per Neustart ueberbruecken.
        print(f"FATAL Marktliste nicht ladbar: {fehler}")
        return 1
    auswertbar = [z for z in ziele if z.auswertbar]
    print(f"{len(ziele)} Maerkte mit Siedlungsflaeche, "
          f"davon {len(auswertbar)} auswertbar "
          f"(russisch + Beruehrungskriterium)")

    letzter_refresh = time.monotonic()
    try:
        while True:
            try:
                meldungen = durchlauf(karte, leser, ziele, zustand,
                                      argumente.protokoll)
            except Exception as fehler:  # noqa: BLE001 - Messlauf nie abreissen
                _protokolliere(argumente.protokoll, {
                    "art": "lauf_fehler",
                    "zeit_utc": _iso(_jetzt_utc()),
                    "typ": type(fehler).__name__,
                    "text": str(fehler)[:300],
                })
                print(f"Durchlauf-Fehler ({type(fehler).__name__}), weiter: "
                      f"{str(fehler)[:120]}")
                meldungen = []
            _schreibe_zustand(argumente.zustand, zustand)
            _herzschlag(live_dir, kandidaten=len(zustand["kandidaten"]))
            for m in meldungen:
                marke = "" if m.get("auswertbar") else "  [nicht auswertbar]"
                print(f"KANDIDAT {m['zeit_utc']} {m['layer']} -> {m['slug']} "
                      f"({m['siedlung']}) YES={m.get('preis_yes')}{marke}")
            if argumente.einmal:
                return 0

            if time.monotonic() - letzter_refresh >= argumente.markt_refresh_s:
                letzter_refresh = time.monotonic()
                try:
                    neue = lade_marktziele(leser, karte, cache,
                                           argumente.geometrie_cache)
                    alt_slugs = {z.slug for z in ziele}
                    neu_slugs = {z.slug for z in neue}
                    if alt_slugs != neu_slugs:
                        geschlossen = _bereinige_zustand(
                            zustand, neu_slugs, argumente.protokoll)
                        _protokolliere(argumente.protokoll, {
                            "art": "watchlist_refresh",
                            "zeit_utc": _iso(_jetzt_utc()),
                            "n_maerkte": len(neue),
                            "neu": sorted(neu_slugs - alt_slugs),
                            "entfernt": sorted(alt_slugs - neu_slugs),
                            "kandidaten_geschlossen": geschlossen,
                        })
                    ziele = neue
                except Exception as fehler:  # noqa: BLE001 - alte Liste weiter
                    _protokolliere(argumente.protokoll, {
                        "art": "lauf_fehler",
                        "zeit_utc": _iso(_jetzt_utc()),
                        "wo": "markt_refresh",
                        "typ": type(fehler).__name__,
                        "text": str(fehler)[:300],
                    })
            time.sleep(argumente.takt_s or takt_fuer(_jetzt_utc()))
    except KeyboardInterrupt:
        # Manuelles Ende: der Watchdog resurrectet stop-beendete Bots nicht.
        _herzschlag(live_dir, art="stop")
        return 0
    finally:
        karte.schliessen()
        leser.schliessen()


if __name__ == "__main__":
    raise SystemExit(main())
