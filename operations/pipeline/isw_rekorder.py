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

Quellseitige Sperre (Betriebsvorfall 01.09.2026): Der ArcGIS-Origin
antwortete 20:00–21:01 UTC exakt eine Stunde lang mit HTTP 403 auf allen
vier Layern. 403 steht bewusst nicht im Wiederhol-Backoff des Clients
(dauerhafter Fehler), also lief der 1-s-Takt ungebremst durch die Sperre
und schrieb 1674 Fehlerzeilen. Seither gilt: ein Status aus SPERR_STATUS
schaltet den Rekorder in eine Abkühlpause (SPERRE_START_S, verdoppelt bis
SPERRE_MAX_S), protokolliert EIN `sperre`-Ereignis beim Beginn und ein
`sperre_ende` beim ersten Erfolg; Herzschläge laufen während der Pause
weiter, damit der Watchdog nicht neu startet. Zyklen während der Sperre
schreiben `letzter_zyklus_ts` nicht fort — das erste Ereignis nach der
Sperre trägt dadurch `nach_ausfall_s` wie nach jedem anderen Ausfall
(Messprotokoll, Amendment A3).

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
# Schnell-Polling seit 27.08. (vorher 20 s): Die Stinky-Forensik vom 11.08.
# zeigt Konkurrenz-Bots, die 5 s nach der Karten-Publikation kaufen und das
# Buch binnen 6 s leerfegen — mit 20-s-Takt (gemessene Latenz 45 s) ist das
# Rennen verloren. Ein Zyklus kostet vier Metadaten-GETs mit Cache-Buster
# (je ~200 ms, siehe isw_karten_watch.layer_stand); mit Takt 1 s liegt die
# effektive Erkennungslatenz bei ~2 s. Lasttest 27.08.: 4 min Dauerlast mit
# ~4 req/s ohne eine einzige Drosselung (429 erst bei Volldaten-Dauerlast,
# Befund 23.07.). INSTRUMENT-WECHSEL fuer die Vorlauf-Messreihe: vorlauf_s
# vor/nach dem 27.08. nicht mischen (Nachtrag im Messprotokoll).
TAKT_AKTIV_S = 1
TAKT_RUHE_S = 120

# Herzschlag-Events entkoppelt vom Poll-Takt: bei 1-s-Zyklen wuerde je Zyklus
# eine Zeile nach bot_events.jsonl geschrieben (~40k/Tag). Der Watchdog
# toleriert 1800 s (wachposten.json) — 60 s ist dicht genug.
HERZSCHLAG_MIN_ABSTAND_S = 60.0

# Beruhigungsfenster: der Rebuild vom 21.07. brauchte 48 Minuten vom ersten
# bis zum letzten Feature. 60 Minuten decken Löschen-und-Neuzeichnen ab.
BERUHIGUNG_S = 3600

# Marktliste neu ziehen (ein Gamma-Aufruf): 10 von 52 Märkten waren nach dem
# ersten 19-h-Fenster bereits geschlossen — eine Startliste veraltet schnell.
MARKT_REFRESH_S = 900

# HTTP-Budget je Zyklus für Preis-/Buchabrufe: ein Massenübergang (Rebuild)
# darf nicht Dutzende CLOB-Aufrufe in einem Durchlauf auslösen.
PREISABRUFE_JE_ZYKLUS = 12

# Ab wann gilt eine Lücke zwischen zwei Zyklen als Ausfall? Der Watchdog
# erklärt einen Bot erst nach 600 s für tot und tickt alle 5 Minuten —
# ein Absturz bleibt also bis zu ~15 Minuten unbemerkt. Ereignisse, die
# direkt nach einer solchen Lücke erkannt werden, tragen einen
# unbrauchbaren T+0-Preis: der Markt kann sich während des Ausfalls längst
# bewegt haben, und eine Überraschung sähe dann wie ein antizipierter Fall
# aus. Genau die Richtung, die die Go-Entscheidung verzerrt. Solche
# Ereignisse werden markiert, nicht stillschweigend mitgezählt.
AUSFALL_SCHWELLE_S = 300.0

NACHFASS_MINUTEN = (0, 1, 5, 30)

# Quellseitige Sperre: 403 ist kein transienter Fehler, sondern eine
# Abweisung — weiterpollen verlängert sie nur. 60 s -> 120 -> 240 -> 480
# -> 600 s Deckel; die Stunde vom 01.09. hätte so ~8 Versuche statt 1674
# Fehlerzeilen gekostet.
SPERR_STATUS = frozenset({403})
SPERRE_START_S = 60.0
SPERRE_MAX_S = 600.0

STANDARD_ZUSTAND = Path("data/live/isw_rekorder/zustand.json")
STANDARD_PROTOKOLL = Path("data/live/isw_rekorder/ereignisse.jsonl")
STANDARD_GEOMETRIE = Path("data/live/isw_rekorder/geometrie_cache.json")
STANDARD_FEUERBEFEHLE = Path("data/live/isw_rekorder/feuerbefehle.jsonl")

ZUSTAND_SCHEMA = 2


def _leerer_zustand() -> dict:
    return {
        "schema": ZUSTAND_SCHEMA,
        "layer_stand": {},
        "beobachtet": {},        # slug -> [layernamen mit beobachteter Deckung]
        "kandidaten": [],        # offene Übergänge im Beruhigungsfenster
        "qualifiziert": {},      # slug -> [layer], bestätigte Treffer (absorbierend)
        "offene_nachfassungen": [],
        "letzter_zyklus_ts": None,   # für die Ausfallerkennung
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
    # Gamma `endDate`. Ein Siedlungsereignis trifft mehrere Laufzeiten
    # gleichzeitig (Krasnoiarske 3, Oleksiyevo 2); die Feuerkette wählt
    # daraus den kurzdatiertesten Markt.
    ende_utc: str | None = None

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


@dataclass
class Sperre:
    """Abkühlpause nach einer quellseitigen Abweisung (HTTP 403).

    Lebt nur im Prozess: nach einem Neustart beginnt die Eskalation neu
    bei SPERRE_START_S — ein Neustart unter Sperre ist selten und die
    Folge (ein Versuch zu früh) harmlos.
    """

    seit_ts: float | None = None
    status: int | None = None
    wartezeit_s: float = SPERRE_START_S
    versuche: int = 0

    @property
    def aktiv(self) -> bool:
        return self.seit_ts is not None

    def treffer(self, status: int, jetzt_ts: float) -> bool:
        """Abweisung verbuchen. True, wenn die Sperre damit BEGINNT."""
        if not self.aktiv:
            self.seit_ts = jetzt_ts
            self.status = status
            self.wartezeit_s = SPERRE_START_S
            self.versuche = 1
            return True
        self.versuche += 1
        self.wartezeit_s = min(self.wartezeit_s * 2, SPERRE_MAX_S)
        return False

    def ende(self, jetzt_ts: float) -> dict:
        """Sperre aufheben; liefert die Kennzahlen für das Protokoll."""
        info = {
            "status": self.status,
            "dauer_s": round(jetzt_ts - (self.seit_ts or jetzt_ts), 1),
            "versuche": self.versuche,
        }
        self.seit_ts = None
        self.status = None
        self.wartezeit_s = SPERRE_START_S
        self.versuche = 0
        return info


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
            ende_utc=markt.get("endDate"),
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


def uebertrage_deckung(zustand: dict, alte: list[Marktziel],
                       neue: list[Marktziel]) -> list[str]:
    """Deckungszustand auf neu geslugte Märkte derselben Siedlung übertragen.

    Polymarket vergibt für dieselbe Frage gelegentlich neue Slugs (beobachtet
    31.07.: `…-kostyantynivka-by-september-30-2026` wurde zu
    `…-2026-715`). Der Zustand ist slug-geführt, der neue Slug startet also
    ohne Deckung — beim nächsten Layer-Edit meldete der Rekorder dann eine
    "neue" Schattierung, die in Wahrheit seit Tagen besteht. Solche
    Phantom-Ereignisse verschmutzen die Vorlauf-Verteilung (sie sähen wie
    antizipierte Fälle aus).

    Die physische Tatsache "Siedlung ist geschattet" hängt an der Siedlung,
    nicht am Markt. Neue Slugs erben deshalb den Zustand jedes bekannten
    Markts derselben Siedlung (`siedlung_objectid`, stabil).
    """
    siedlung_von: dict[str, int] = {z.slug: z.siedlung_objectid
                                    for z in list(alte) + list(neue)}
    deckung_je_siedlung: dict[int, list[str]] = {}
    qualifiziert_je_siedlung: dict[int, list[str]] = {}
    for slug, layers in zustand["beobachtet"].items():
        objectid = siedlung_von.get(slug)
        if objectid is not None and layers:
            deckung_je_siedlung.setdefault(objectid, list(layers))
    for slug, layers in zustand["qualifiziert"].items():
        objectid = siedlung_von.get(slug)
        if objectid is not None and layers:
            qualifiziert_je_siedlung.setdefault(objectid, list(layers))

    uebertragen: list[str] = []
    for ziel in neue:
        if ziel.slug in zustand["beobachtet"]:
            continue
        geerbt = deckung_je_siedlung.get(ziel.siedlung_objectid)
        if geerbt:
            zustand["beobachtet"][ziel.slug] = list(geerbt)
            uebertragen.append(ziel.slug)
        geerbt_q = qualifiziert_je_siedlung.get(ziel.siedlung_objectid)
        if geerbt_q and ziel.slug not in zustand["qualifiziert"]:
            zustand["qualifiziert"][ziel.slug] = list(geerbt_q)
    return uebertragen


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

def _pruefe_ausfall(zustand: dict, protokoll: Path,
                    hinweis: str = "") -> float:
    """Lücke seit dem letzten beobachtenden Zyklus; 0.0 wenn keine.

    Nach einer Lücke ist der gleich gemessene T+0-Preis nicht der Preis
    zum Zeitpunkt der ISW-Änderung — das Ereignis wird markiert.
    """
    vorheriger_zyklus = zustand.get("letzter_zyklus_ts")
    if not vorheriger_zyklus:
        return 0.0
    luecke = _jetzt_utc().timestamp() - vorheriger_zyklus
    if luecke <= AUSFALL_SCHWELLE_S:
        return 0.0
    ausfall_s = round(luecke, 1)
    _protokolliere(protokoll, {
        "art": "ausfall_erkannt",
        "zeit_utc": _iso(_jetzt_utc()),
        "luecke_s": ausfall_s,
        "hinweis": (hinweis + " " if hinweis else "")
        + "Ereignisse dieses Zyklus tragen einen unsicheren T+0-Preis",
    })
    return ausfall_s


def durchlauf(karte: ISWKarte,
              leser: PolymarktLeser,
              ziele: list[Marktziel],
              zustand: dict,
              protokoll: Path,
              sperre: Sperre | None = None) -> list[dict]:
    """Ein Poll-Zyklus über alle vier Layer. Liefert neue Kandidaten-Einträge.

    `sperre` (optional) macht aus einer quellseitigen Abweisung eine
    Abkühlpause statt eines Fehlers je Zyklus; siehe Modul-Docstring.
    """
    meldungen: list[dict] = []
    budget = {"rest": PREISABRUFE_JE_ZYKLUS}
    slugs_aktiv = {z.slug for z in ziele}
    ziel_nach_slug = {z.slug: z for z in ziele}

    # Während einer Sperre beobachtet der Zyklus nichts — die Lücke wird
    # erst beim ersten Erfolg nach der Sperre gemessen und gemeldet.
    ausfall_s = 0.0
    if sperre is None or not sperre.aktiv:
        ausfall_s = _pruefe_ausfall(zustand, protokoll)
    gesperrt = False

    def _abgewiesen(fehler: ISWFehler, layer_name: str) -> bool:
        """Sperre verbuchen; True wenn der Zyklus abzubrechen ist."""
        nonlocal gesperrt
        if sperre is None or fehler.status not in SPERR_STATUS:
            _protokolliere(protokoll, {
                "art": "fehler", "zeit_utc": _iso(_jetzt_utc()),
                "layer": layer_name, "status": fehler.status,
            })
            return False
        jetzt_ts = _jetzt_utc().timestamp()
        if sperre.treffer(fehler.status, jetzt_ts):
            _protokolliere(protokoll, {
                "art": "sperre",
                "zeit_utc": _iso(_jetzt_utc()),
                "layer": layer_name,
                "status": fehler.status,
                "wartezeit_s": sperre.wartezeit_s,
                "hinweis": "Quelle weist ab; Abkuehlpause statt Dauerpoll",
            })
        gesperrt = True
        return True

    def _preis(token: str) -> tuple[float | None, bool]:
        if budget["rest"] <= 0:
            return None, True
        budget["rest"] -= 1
        return leser.preis_yes(token), False

    for layer in QUALIFIZIERENDE_LAYER:
        try:
            stand = karte.layer_stand(layer)
        except ISWFehler as fehler:
            if _abgewiesen(fehler, layer.name):
                # Die Sperre trifft alle Layer — nicht weiterhämmern.
                break
            continue
        if sperre is not None and sperre.aktiv:
            info = sperre.ende(_jetzt_utc().timestamp())
            _protokolliere(protokoll, {
                "art": "sperre_ende",
                "zeit_utc": _iso(_jetzt_utc()),
                "layer": layer.name,
                **info,
            })
            ausfall_s = _pruefe_ausfall(zustand, protokoll,
                                        hinweis="Nach Sperre:")
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
            if _abgewiesen(fehler, layer.name):
                break
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
                "nach_ausfall_s": ausfall_s,
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
    if not gesperrt:
        # Ein gesperrter Zyklus hat die Karte nicht gesehen; die Lücke
        # läuft weiter bis zum ersten Erfolg (siehe _pruefe_ausfall).
        zustand["letzter_zyklus_ts"] = _jetzt_utc().timestamp()
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


def _herzschlag_faellig(letzter: float | None, jetzt: float) -> bool:
    """Ob wieder ein Herzschlag geschrieben werden soll (entkoppelt vom
    Poll-Takt, sonst eine Event-Zeile je 1-s-Zyklus)."""
    return letzter is None or jetzt - letzter >= HERZSCHLAG_MIN_ABSTAND_S


def _schlafe(sekunden: float, herzschlag=None,
             scheibe_s: float = HERZSCHLAG_MIN_ABSTAND_S) -> None:
    """Pause in Scheiben, zwischen denen ein Herzschlag geschrieben wird.

    Die Abkühlpause reicht bis SPERRE_MAX_S (600 s) — genau die Grenze,
    ab der der Watchdog einen Bot für tot erklärt (STALE_S). Ohne
    Zwischen-Herzschläge würde er den wartenden Rekorder neu starten,
    und der Neustart pollte sofort wieder in die Sperre hinein.
    """
    rest = float(sekunden)
    while rest > 0:
        stueck = min(rest, scheibe_s)
        time.sleep(stueck)
        rest -= stueck
        if rest > 0 and herzschlag is not None:
            herzschlag()


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


def _feuern(meldungen: list[dict], ziele: list[Marktziel],
            befehle_pfad: Path) -> None:
    """Sofort-Trigger: Kandidaten → Order-Spezifikation, ohne Verzug.

    Getrennt vom Messpfad. Das Beruhigungsfenster (3600 s) bleibt für die
    Statistik unangetastet — es ist länger als das gesamte
    Krasnoiarske-Fenster und als Handelsauslöser deshalb unbrauchbar.

    Schluckt jeden eigenen Fehler: Die Messreihe ist das Fundament und
    darf nie an der Feuerkette sterben.
    """
    try:
        from operations.pipeline import isw_feuerkette as feuerkette

        jetzt = _jetzt_utc()
        verbraucht = feuerkette.wochenverbrauch(befehle_pfad, jetzt)
        befehle, ablehnungen = feuerkette.pruefe(
            meldungen, {z.slug: z for z in ziele},
            verbraucht_usdc=verbraucht, jetzt=jetzt)
        feuerkette.schreibe(befehle_pfad, befehle + ablehnungen)
        for befehl in befehle:
            print(f"FEUERBEFEHL {befehl.markt_slug} ask={befehl.best_ask} "
                  f"max={befehl.max_preis} {befehl.einsatz_usdc:.0f} USDC "
                  f"gueltig bis {befehl.gueltig_bis_utc}")
        for ablehnung in ablehnungen:
            print(f"  kein Feuer {ablehnung.markt_slug}: {ablehnung.grund}")
    except Exception as fehler:  # noqa: BLE001 - Messung geht vor
        print(f"WARNUNG Feuerkette uebersprungen ({fehler})")


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
    zerleger.add_argument("--feuerbefehle", type=Path,
                          default=STANDARD_FEUERBEFEHLE,
                          help="Spur der Order-Spezifikationen")
    zerleger.add_argument("--keine-feuerkette", dest="feuerkette",
                          action="store_false",
                          help="nur messen, keine Order-Spezifikationen "
                               "ausgeben")
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
        argumente.feuerbefehle = live_dir / "feuerbefehle.jsonl"
        _herzschlag(live_dir, art="start",
                    takt_aktiv_s=TAKT_AKTIV_S, takt_ruhe_s=TAKT_RUHE_S)

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
    letzter_herzschlag: float | None = None  # None -> erster Zyklus schreibt
    sperre = Sperre()
    try:
        while True:
            try:
                meldungen = durchlauf(karte, leser, ziele, zustand,
                                      argumente.protokoll, sperre=sperre)
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
            if _herzschlag_faellig(letzter_herzschlag, time.monotonic()):
                _herzschlag(live_dir, kandidaten=len(zustand["kandidaten"]))
                letzter_herzschlag = time.monotonic()
            for m in meldungen:
                marke = "" if m.get("auswertbar") else "  [nicht auswertbar]"
                print(f"KANDIDAT {m['zeit_utc']} {m['layer']} -> {m['slug']} "
                      f"({m['siedlung']}) YES={m.get('preis_yes')}{marke}")
            if meldungen and argumente.feuerkette:
                _feuern(meldungen, ziele, argumente.feuerbefehle)
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
                        # Erst erben, dann bereinigen: der Zustand des alten
                        # Slugs ist die Quelle fuer den neu geslugten Markt.
                        geerbt = uebertrage_deckung(zustand, ziele, neue)
                        geschlossen = _bereinige_zustand(
                            zustand, neu_slugs, argumente.protokoll)
                        _protokolliere(argumente.protokoll, {
                            "art": "watchlist_refresh",
                            "zeit_utc": _iso(_jetzt_utc()),
                            "n_maerkte": len(neue),
                            "neu": sorted(neu_slugs - alt_slugs),
                            "entfernt": sorted(alt_slugs - neu_slugs),
                            "kandidaten_geschlossen": geschlossen,
                            "deckung_geerbt": sorted(geerbt),
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
            if sperre.aktiv:
                print(f"SPERRE HTTP {sperre.status} seit "
                      f"{sperre.versuche} Versuch(en), warte "
                      f"{sperre.wartezeit_s:.0f} s")
                _schlafe(sperre.wartezeit_s, herzschlag=lambda: _herzschlag(
                    live_dir, kandidaten=len(zustand["kandidaten"]),
                    sperre_s=sperre.wartezeit_s))
                letzter_herzschlag = time.monotonic()
            else:
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
