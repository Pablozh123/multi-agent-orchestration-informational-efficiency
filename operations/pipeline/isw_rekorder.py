"""Rekorder für den Vorlauf ISW-Karte → Polymarket-Preis.

Misst, wie lange der Markt braucht, bis er eine Änderung der Auflösungsquelle
einpreist. Handelt nicht. Kein Order-Pfad, keine Keys, keine Wallet.

Warum überhaupt messen statt gleich handeln: Es gibt genau EINE saubere
Beobachtung (Krasnoiarske, 22.07.2026, Vorlauf 18 min 43 s). Ein historischer
Backtest ist ausgeschlossen, weil ISW die Polygone periodisch löscht und neu
zeichnet — `CreationDate` ist kein Ereignisprotokoll (am 21.07. entstanden 115
Features in 48 Minuten). Belastbar ist nur Vorwärtsmessung. Der Rekorder
sammelt die Verteilung, aus der sich die Frage "gibt es hier eine Kante"
beantworten lässt, statt sie aus N=1 zu behaupten.

Ablauf je Durchlauf:

1. Stolperdraht — `editingInfo.lastEditDate` der vier qualifizierenden Layer
   vergleichen (gemessen 104 ms je Layer). Ohne Änderung endet der Durchlauf.
2. Delta — nur bei Änderung die Flächen des betroffenen Layers holen.
3. Geometrie — lokal gegen die gecachten Siedlungsflächen schneiden.
   Server-seitig wäre je Siedlung eine Anfrage nötig (52 × ~600 ms); lokal
   ist der Test praktisch gratis.
4. Bei neuem Treffer: Ereignis schreiben und Preis-Nachfassungen einplanen
   (T+0, T+1, T+5, T+30 Minuten).

Schutz vor Falsch-Positiven, jeder Punkt aus einem beobachteten Fehlermodus:
- Bulk-Rebuild-Bremse (siehe `ist_bulk_rebuild`).
- Marktpolarität: `will-ukraine-re-enter-…` invertiert das Signal.
- Kriterium: "capture all of" verlangt Vollüberdeckung; der Rekorder
  protokolliert dort die Berührung, bewertet aber die Auflösung NICHT.
- Persistenz: eine Berührung ist ein Kandidat, keine Auflösung. Der Zustand
  je Treffer wird getrennt geführt.

Aufruf:

    python -m operations.pipeline.isw_rekorder --einmal
    python -m operations.pipeline.isw_rekorder --takt-s 20
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import httpx

from operations.pipeline.isw_karten_watch import (
    QUALIFIZIERENDE_LAYER,
    ISWFehler,
    ISWFlaeche,
    ISWKarte,
    Siedlung,
    ist_bulk_rebuild,
    koordinate_aus_beschreibung,
    markt_kriterium,
    markt_polaritaet,
    neue_zeitstempel,
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

NACHFASS_MINUTEN = (0, 1, 5, 30)

STANDARD_ZUSTAND = Path("data/live/isw_rekorder/zustand.json")
STANDARD_PROTOKOLL = Path("data/live/isw_rekorder/ereignisse.jsonl")


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


@dataclass
class Kartenereignis:
    """Eine neu erkannte Überdeckung einer beobachteten Siedlung."""

    erkannt_utc: str
    layer: str
    objectid: int
    feature_zeit_utc: str | None
    slug: str
    siedlung: str
    polaritaet: str
    kriterium: str
    auswertbar: bool
    preis_yes_bei_erkennung: float | None
    vorlauf_s: float | None       # Erkennung minus Feature-Zeit
    nachfassungen: dict[str, float | None] = field(default_factory=dict)


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
    """Read-only Polymarket-Zugriff: Marktliste und Preise."""

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

    def schliessen(self) -> None:
        self._client.close()


def baue_watchlist(leser: PolymarktLeser, karte: ISWKarte,
                   pause_s: float = 0.3) -> list[Marktziel]:
    """Märkte mit Koordinate auf Siedlungsflächen abbilden.

    Die Zuordnung läuft ausschliesslich über die Koordinate — Namen weichen
    zwischen Markt und ISW-Layer ab.

    `pause_s` entzerrt die Siedlungsabfragen. Ohne Pause laufen rund 50
    Abfragen in Folge gegen den FeatureServer und lösen die Drosselung aus
    (HTTP 429, beobachtet 23.07.). Die Watchlist wird nur beim Start gebaut,
    die Pause kostet also einmalig gut 15 Sekunden.
    """
    ziele: list[Marktziel] = []
    siedlungs_cache: dict[tuple[float, float], Siedlung | None] = {}
    for markt in leser.maerkte():
        koordinate = koordinate_aus_beschreibung(markt.get("description"))
        if koordinate is None:
            continue
        lat, lon = koordinate
        schluessel = (round(lat, 5), round(lon, 5))
        if schluessel not in siedlungs_cache:
            siedlungs_cache[schluessel] = karte.siedlung_an_punkt(lat, lon)
            if pause_s:
                time.sleep(pause_s)
        siedlung = siedlungs_cache[schluessel]
        if siedlung is None or not siedlung.ringe:
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
            siedlung_name=siedlung.name,
            siedlung_objectid=siedlung.objectid,
            ringe=siedlung.ringe,
        ))
    return ziele


# ------------------------------------------------------------ Kernauswertung

def neue_treffer(flaechen: list[ISWFlaeche],
                 ziele: list[Marktziel],
                 bereits_gedeckt: dict[str, list[str]]) -> list[tuple[Marktziel, ISWFlaeche]]:
    """Welche Siedlungen sind neu von diesem Layer gedeckt?

    `bereits_gedeckt` bildet slug -> Liste bereits bekannter Layernamen ab und
    verhindert, dass derselbe Zustand bei jedem Durchlauf erneut feuert.
    """
    treffer: list[tuple[Marktziel, ISWFlaeche]] = []
    for ziel in ziele:
        for flaeche in flaechen:
            if not flaeche.ringe:
                continue
            if not polygone_beruehren(flaeche.ringe, ziel.ringe):
                continue
            if flaeche.layer in bereits_gedeckt.get(ziel.slug, []):
                break
            treffer.append((ziel, flaeche))
            break
    return treffer


def _lade_zustand(pfad: Path) -> dict:
    if not pfad.exists():
        return {"layer_stand": {}, "gedeckt": {}, "offene_nachfassungen": []}
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"layer_stand": {}, "gedeckt": {}, "offene_nachfassungen": []}


def _schreibe_zustand(pfad: Path, zustand: dict) -> None:
    """Atomar schreiben — der Ordner wird parallel gelesen (Torn-Write-Lehre)."""
    pfad.parent.mkdir(parents=True, exist_ok=True)
    temp = pfad.with_suffix(pfad.suffix + ".tmp")
    temp.write_text(json.dumps(zustand, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    temp.replace(pfad)


def _protokolliere(pfad: Path, eintrag: dict) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with pfad.open("a", encoding="utf-8") as datei:
        datei.write(json.dumps(eintrag, ensure_ascii=False) + "\n")


def durchlauf(karte: ISWKarte,
              leser: PolymarktLeser,
              ziele: list[Marktziel],
              zustand: dict,
              protokoll: Path) -> list[Kartenereignis]:
    """Ein Poll-Zyklus über alle vier Layer."""
    ereignisse: list[Kartenereignis] = []
    jetzt = _jetzt_utc()

    for layer in QUALIFIZIERENDE_LAYER:
        try:
            stand = karte.layer_stand(layer)
        except ISWFehler as fehler:
            _protokolliere(protokoll, {
                "art": "fehler", "zeit_utc": _iso(jetzt),
                "layer": layer.name, "status": fehler.status,
            })
            continue

        vorher = zustand["layer_stand"].get(layer.name)
        if stand is not None and vorher == stand:
            continue
        zustand["layer_stand"][layer.name] = stand

        # Erster Lauf: nur grundieren, nicht signalisieren.
        grundierung = vorher is None

        try:
            flaechen = karte.flaechen(layer)
        except ISWFehler as fehler:
            _protokolliere(protokoll, {
                "art": "fehler", "zeit_utc": _iso(jetzt),
                "layer": layer.name, "status": fehler.status,
            })
            continue

        # Nur was seit dem letzten Stand dazukam, zaehlt fuer die Bremse.
        frisch = neue_zeitstempel([f.zeitstempel_ms for f in flaechen], vorher)
        if ist_bulk_rebuild(frisch):
            _protokolliere(protokoll, {
                "art": "rebuild", "zeit_utc": _iso(jetzt),
                "layer": layer.name, "n_flaechen": len(flaechen),
                "n_neu": len(frisch),
                "hinweis": "Bulk-Rebuild erkannt, neu grundiert statt signalisiert",
            })
            grundierung = True

        for ziel, flaeche in neue_treffer(flaechen, ziele, zustand["gedeckt"]):
            zustand["gedeckt"].setdefault(ziel.slug, [])
            if flaeche.layer not in zustand["gedeckt"][ziel.slug]:
                zustand["gedeckt"][ziel.slug].append(flaeche.layer)
            if grundierung:
                continue

            preis = leser.preis_yes(ziel.token_yes)
            feature_zeit = _ms_nach_iso(flaeche.zeitstempel_ms)
            vorlauf = None
            if flaeche.zeitstempel_ms:
                vorlauf = (jetzt.timestamp()
                           - flaeche.zeitstempel_ms / 1000)
            ereignis = Kartenereignis(
                erkannt_utc=_iso(jetzt),
                layer=flaeche.layer,
                objectid=flaeche.objectid,
                feature_zeit_utc=feature_zeit,
                slug=ziel.slug,
                siedlung=ziel.siedlung_name,
                polaritaet=ziel.polaritaet,
                kriterium=ziel.kriterium,
                auswertbar=ziel.auswertbar,
                preis_yes_bei_erkennung=preis,
                vorlauf_s=vorlauf,
                nachfassungen={"0": preis},
            )
            ereignisse.append(ereignis)
            _protokolliere(protokoll, {"art": "treffer", **asdict(ereignis)})
            for minute in NACHFASS_MINUTEN[1:]:
                zustand["offene_nachfassungen"].append({
                    "slug": ziel.slug,
                    "token": ziel.token_yes,
                    "layer": flaeche.layer,
                    "faellig_ts": jetzt.timestamp() + minute * 60,
                    "minute": minute,
                })

    _faellige_nachfassungen(leser, zustand, protokoll)
    return ereignisse


def _faellige_nachfassungen(leser: PolymarktLeser, zustand: dict,
                            protokoll: Path) -> None:
    """Preis-Nachfassungen einsammeln, deren Zeitpunkt erreicht ist."""
    jetzt_ts = _jetzt_utc().timestamp()
    offen = []
    for auftrag in zustand.get("offene_nachfassungen", []):
        if auftrag["faellig_ts"] > jetzt_ts:
            offen.append(auftrag)
            continue
        _protokolliere(protokoll, {
            "art": "nachfassung",
            "zeit_utc": _iso(_jetzt_utc()),
            "slug": auftrag["slug"],
            "layer": auftrag["layer"],
            "minute": auftrag["minute"],
            "preis_yes": leser.preis_yes(auftrag["token"]),
        })
    zustand["offene_nachfassungen"] = offen


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        description="Rekorder ISW-Karte -> Polymarket-Preis (read-only)")
    zerleger.add_argument("--einmal", action="store_true",
                          help="nur ein Durchlauf, dann beenden")
    zerleger.add_argument("--takt-s", type=int, default=None,
                          help="fester Poll-Abstand statt Tageszeit-Automatik")
    zerleger.add_argument("--zustand", type=Path, default=STANDARD_ZUSTAND)
    zerleger.add_argument("--protokoll", type=Path, default=STANDARD_PROTOKOLL)
    argumente = zerleger.parse_args(argv)

    karte = ISWKarte()
    leser = PolymarktLeser()
    zustand = _lade_zustand(argumente.zustand)

    print("Watchlist wird gebaut ...")
    ziele = baue_watchlist(leser, karte)
    auswertbar = [z for z in ziele if z.auswertbar]
    print(f"{len(ziele)} Maerkte mit Siedlungsflaeche, "
          f"davon {len(auswertbar)} auswertbar "
          f"(russisch + Beruehrungskriterium)")

    try:
        while True:
            ereignisse = durchlauf(karte, leser, ziele, zustand,
                                   argumente.protokoll)
            _schreibe_zustand(argumente.zustand, zustand)
            for ereignis in ereignisse:
                marke = "" if ereignis.auswertbar else "  [nicht auswertbar]"
                print(f"TREFFER {ereignis.erkannt_utc} {ereignis.layer} "
                      f"-> {ereignis.slug} ({ereignis.siedlung}) "
                      f"YES={ereignis.preis_yes_bei_erkennung}{marke}")
            if argumente.einmal:
                return 0
            time.sleep(argumente.takt_s or takt_fuer(_jetzt_utc()))
    except KeyboardInterrupt:
        return 0
    finally:
        karte.schliessen()
        leser.schliessen()


if __name__ == "__main__":
    raise SystemExit(main())
