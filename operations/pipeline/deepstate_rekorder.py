"""DeepState-Rekorder: Vorlauf DeepStateMap -> ISW-Karte -> Polymarket-Preis.

Misst, ob die DeepStateMap-Karte (deepstatemap.live) die ISW-Schattierung
und damit die Marktbewegung der `ukraine-map`-Serie VORWEGNIMMT — und um
wie viel. Handelt nicht. Kein Order-Pfad, keine Keys, keine Wallet.

Warum eine zweite Quelle (Recherche 27.08.2026, N1, und Hannivka 01.09.):

- Die grossen "Will Russia capture [Stadt] by ..."-Leitern loesen ueber die
  ISW-Karte auf und nennen DeepStateMap als offiziellen Fallback. DeepState
  aktualisiert mehrmals taeglich, in der Regel Stunden vor dem
  ISW-Tagesupdate.
- Das Rennen an der ISW-Quelle ist verloren: Bei Hannivka (01.09.) erkannte
  der ISW-Rekorder die Aenderung 0,8 s nach dem Feature-Zeitstempel — und
  die Ask-Seite war trotzdem schon weg (bid 0.79 / ask 0.98 bei +1 s,
  Prints bei +3 s). Bei Stinky (11.08.) lag der Markt 90 min flach und
  sprang exakt in der ISW-Publikationsminute. Den DeepState-Vorlauf
  handelt bisher niemand sichtbar (n=1-Beleg) — ob er existiert und wie
  oft er in ISW-Schattierung muendet, ist die Messfrage.

Messdesign:

1. Stolperdraht — `GET /api/history/last` mit ETag (`If-None-Match`): der
   Server antwortet 304, solange sich die Karte nicht geaendert hat; ein
   Cache-Buster erzwingt Origin-Antworten (der CDN cached 300 s, derselbe
   Befund wie bei ISW, Amendment A1). Ein Poll kostet damit im Normalfall
   0 Byte Nutzlast.
2. Zwei Klassen aus den Polygonnamen der Karte: `besetzt`
   (geoJSON.status.occupied) und `grauzone` (geoJSON.status.unknown). Die
   Grauzone ist das DeepState-Gegenstueck zum ISW-Infiltrationslayer
   (niedrigste Beweisschwelle, schaltet zuerst).
3. Uebergaenge — je Markt und Klasse wird der Beruehrungszustand der
   Siedlungsflaeche (dieselbe ISW-Verwaltungsgrenze wie im ISW-Rekorder,
   derselbe Geometrie-Cache) mit der neuen Karte verglichen. Jeder
   Uebergang erzeugt `ds_treffer` / `ds_verlust` mit sofortiger
   T+0-Messung (Preis, Buchtiefe) und Nachfassungen bei +1/+5/+30 min.
   Kein Beruhigungsfenster: DeepState loescht und zeichnet nicht in
   Rebuilds neu; Korrekturen erscheinen als `nachbearbeitung` (gleiche
   Karten-ID, neuer ETag).
4. Erwaehnungen — der Beschreibungstext jedes Updates nennt Orte mit
   Koordinaten-Links ("The enemy has advanced near <a ...>Rodynske</a>").
   Sie werden extrahiert und Maerkten im Umkreis NAEHE_KM zugeordnet —
   ein zweiter, textbasierter Signalkanal, der auch dort greift, wo das
   Polygon die Verwaltungsgrenze (noch) nicht schneidet.
5. Vorlauf gegen ISW entsteht NICHT hier, sondern in der Auswertung
   (`operations.analysis.deepstate_vorlauf_auswertung`), die dieses
   Protokoll mit dem des ISW-Rekorders je Siedlung verknuepft.

Betrieb: Watchdog-Profil `deepstate_ukraine` (`--live`, read-only).
Quellseitige Abweisungen (4xx/5xx) gehen in dieselbe Abkuehlpause wie beim
ISW-Rekorder (Sperre, Amendment A3) — DeepState ist eine kleine Seite,
Dauerpoll gegen einen Fehler waere unhoeflich und riskant.

Aufruf:

    python -m operations.pipeline.deepstate_rekorder --einmal
    python -m operations.pipeline.deepstate_rekorder --takt-s 60
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import httpx

from operations.pipeline.isw_karten_watch import ISWKarte, polygone_beruehren
from operations.pipeline.isw_rekorder import (
    NACHFASS_MINUTEN,
    PREISABRUFE_JE_ZYKLUS,
    Marktziel,
    PolymarktLeser,
    Sperre,
    _faellige_nachfassungen,
    _herzschlag,
    _herzschlag_faellig,
    _iso,
    _jetzt_utc,
    _protokolliere,
    _pruefe_ausfall,
    _schlafe,
    _schreibe_zustand,
    lade_geometrie_cache,
    lade_marktziele,
)

DEEPSTATE_BASIS = "https://deepstatemap.live/api/history"

# DeepState aktualisiert wenige Male am Tag; mit ETag kostet ein Poll im
# Normalfall eine 304-Antwort ohne Nutzlast. 60 s ist dicht genug fuer
# einen Vorlauf, der in Stunden gemessen wird, und haelt den Herzschlag
# ohne Sonderbehandlung unter STALE_S des Watchdogs.
TAKT_S = 60
MARKT_REFRESH_S = 900

# Umkreis, in dem eine erwaehnte Koordinate einem Markt zugeordnet wird.
# Siedlungsflaechen im Donbas haben typisch 2-6 km Durchmesser; 5 km
# faengt "near <Ort>" ein, ohne die Nachbarsiedlung mitzunehmen.
NAEHE_KM = 5.0

KLASSEN = ("besetzt", "grauzone")
_KLASSE_MARKER = {
    "geojson.status.occupied": "besetzt",
    "geojson.status.unknown": "grauzone",
}

# "<a href="https://deepstatemap.live/en#13/48.3585352/37.1725898">Rodynske</a>"
_LINK = re.compile(
    r"#\d+/(-?\d+(?:\.\d+)?)/(-?\d+(?:\.\d+)?)\"[^>]*>([^<]+)</a>")

STANDARD_ZUSTAND = Path("data/live/deepstate_rekorder/zustand.json")
STANDARD_PROTOKOLL = Path("data/live/deepstate_rekorder/ereignisse.jsonl")
STANDARD_GEOMETRIE = Path("data/live/deepstate_rekorder/geometrie_cache.json")

ZUSTAND_SCHEMA = 1


def _leerer_zustand() -> dict:
    return {
        "schema": ZUSTAND_SCHEMA,
        "karte_id": None,
        "etag": None,
        "karte_created_at": None,
        "beobachtet": {},            # slug -> [klassen mit Beruehrung]
        "offene_nachfassungen": [],
        "letzter_zyklus_ts": None,
    }


# ------------------------------------------------------------------ Parsing

def klasse_aus_name(name: str | None) -> str | None:
    """Polygon-Klasse aus dem dreisprachigen Feature-Namen.

    DeepState schreibt "Окуповано /// Occupied /// geoJSON.status.occupied";
    der letzte Teil ist der stabile Schluessel, die Uebersetzungen nicht.
    """
    if not name:
        return None
    kurz = name.lower()
    for marker, klasse in _KLASSE_MARKER.items():
        if marker in kurz:
            return klasse
    return None


def erwaehnungen(beschreibung: str | None) -> list[dict]:
    """Orte mit Koordinaten aus dem Beschreibungs-HTML eines Updates."""
    heraus: list[dict] = []
    for lat, lon, name in _LINK.findall(beschreibung or ""):
        try:
            heraus.append({"name": name.strip(), "lat": float(lat),
                           "lon": float(lon)})
        except ValueError:
            continue
    return heraus


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def maerkte_nahe(punkte: list[dict], ziele: list[Marktziel],
                 radius_km: float = NAEHE_KM) -> list[dict]:
    """Erwaehnte Orte um die Maerkte im Umkreis ergaenzen."""
    heraus: list[dict] = []
    for punkt in punkte:
        nahe = []
        for ziel in ziele:
            km = haversine_km(punkt["lat"], punkt["lon"], ziel.lat, ziel.lon)
            if km <= radius_km:
                nahe.append({"slug": ziel.slug, "km": round(km, 2)})
        nahe.sort(key=lambda n: n["km"])
        heraus.append({**punkt, "maerkte_nahe": nahe})
    return heraus


@dataclass
class DSKarte:
    """Eine geparste DeepState-Karte: nur die klassifizierten Polygone."""

    id: int
    datetime: str | None
    etag: str | None
    polygone: list[tuple[str, list[list[list[float]]]]] = field(
        default_factory=list)
    n_features: int = 0


def _ringe_2d(koordinaten: list) -> list[list[list[float]]]:
    """GeoJSON-Ringe [lon, lat, alt] -> [lon, lat] wie die ArcGIS-Ringe."""
    return [[[float(p[0]), float(p[1])] for p in ring] for ring in koordinaten]


def parse_karte(nutz: dict, etag: str | None = None) -> DSKarte:
    """`/api/history/last` -> DSKarte. Erwartet {id, map: {features}, datetime}."""
    karte_id = int(nutz.get("id") or 0)
    geo = nutz.get("map") if isinstance(nutz.get("map"), dict) else nutz
    features = geo.get("features") or []
    polygone: list[tuple[str, list[list[list[float]]]]] = []
    for feature in features:
        klasse = klasse_aus_name((feature.get("properties") or {}).get("name"))
        if klasse is None:
            continue
        geometrie = feature.get("geometry") or {}
        typ = geometrie.get("type")
        if typ == "Polygon":
            polygone.append((klasse, _ringe_2d(geometrie.get("coordinates") or [])))
        elif typ == "MultiPolygon":
            for teil in geometrie.get("coordinates") or []:
                polygone.append((klasse, _ringe_2d(teil)))
    return DSKarte(id=karte_id, datetime=nutz.get("datetime"), etag=etag,
                   polygone=polygone, n_features=len(features))


class DSFehler(RuntimeError):
    """HTTP-Fehler der DeepState-API; status fuer die Sperre."""

    def __init__(self, status: int, body: str = "") -> None:
        super().__init__(f"deepstate HTTP {status}: {body[:160]}")
        self.status = status


# ------------------------------------------------------------------- Client

class DeepStateLeser:
    """Read-only Zugriff auf die DeepState-Historie."""

    def __init__(self, basis: str = DEEPSTATE_BASIS, timeout: float = 60.0,
                 client: httpx.Client | None = None) -> None:
        self.basis = basis
        self._client = client or httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "thesis-deepstate-rekorder/1.0 (read-only)",
                     "Accept": "application/json"},
        )

    def _get(self, pfad: str, kopf: dict | None = None) -> httpx.Response:
        try:
            return self._client.get(
                f"{self.basis}{pfad}",
                params={"_cb": int(time.time() * 1000)},
                headers=kopf or {},
            )
        except httpx.HTTPError as fehler:
            raise DSFehler(599, str(fehler)) from fehler

    def letzte_karte(self, etag: str | None) -> DSKarte | None:
        """Neueste Karte, oder None wenn unveraendert (304)."""
        kopf = {"If-None-Match": etag} if etag else {}
        antwort = self._get("/last", kopf)
        if antwort.status_code == 304:
            return None
        if antwort.status_code != 200:
            raise DSFehler(antwort.status_code, antwort.text)
        try:
            nutz = antwort.json()
        except ValueError as fehler:
            raise DSFehler(599, "keine JSON-Antwort") from fehler
        return parse_karte(nutz, antwort.headers.get("etag"))

    def eintrag(self, karte_id: int) -> dict | None:
        """Historien-Eintrag (createdAt, Beschreibung) zu einer Karten-ID.

        Die oeffentliche Liste ist ~1,3 MB; sie wird nur bei einer NEUEN
        Karte gelesen, nie im Poll-Takt.
        """
        antwort = self._get("/public")
        if antwort.status_code != 200:
            raise DSFehler(antwort.status_code, antwort.text)
        try:
            liste = antwort.json()
        except ValueError as fehler:
            raise DSFehler(599, "keine JSON-Antwort") from fehler
        for eintrag in liste if isinstance(liste, list) else []:
            if int(eintrag.get("id") or 0) == karte_id:
                return eintrag
        return None

    def schliessen(self) -> None:
        self._client.close()


# ------------------------------------------------------------ Kernauswertung

def deckung(polygone: list[tuple[str, list[list[list[float]]]]],
            ziele: list[Marktziel]) -> dict[str, set[str]]:
    """Welche Klassen beruehren welche Siedlung? slug -> {klassen}."""
    heraus: dict[str, set[str]] = {}
    for ziel in ziele:
        for klasse, ringe in polygone:
            if not ringe or klasse in heraus.get(ziel.slug, set()):
                continue
            if polygone_beruehren(ringe, ziel.ringe):
                heraus.setdefault(ziel.slug, set()).add(klasse)
    return heraus


def _epoch(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def durchlauf(leser_ds: DeepStateLeser,
              leser_pm: PolymarktLeser,
              ziele: list[Marktziel],
              zustand: dict,
              protokoll: Path,
              sperre: Sperre | None = None,
              letzte_polygone: list | None = None) -> list[dict]:
    """Ein Poll-Zyklus. Liefert neue Uebergangs-Eintraege.

    `letzte_polygone` (optional, Liste) wird mit den Polygonen der zuletzt
    gelesenen Karte gefuellt — der Marktlisten-Refresh grundiert damit
    neue Slugs, ohne die Karte erneut zu holen.
    """
    meldungen: list[dict] = []
    ausfall_s = 0.0
    if sperre is None or not sperre.aktiv:
        ausfall_s = _pruefe_ausfall(zustand, protokoll)

    try:
        karte = leser_ds.letzte_karte(zustand.get("etag"))
    except DSFehler as fehler:
        if sperre is None:
            _protokolliere(protokoll, {
                "art": "fehler", "zeit_utc": _iso(_jetzt_utc()),
                "status": fehler.status,
            })
            return meldungen
        if sperre.treffer(fehler.status, _jetzt_utc().timestamp()):
            _protokolliere(protokoll, {
                "art": "sperre", "zeit_utc": _iso(_jetzt_utc()),
                "status": fehler.status, "wartezeit_s": sperre.wartezeit_s,
                "hinweis": "Quelle weist ab; Abkuehlpause statt Dauerpoll",
            })
        # Polymarket ist erreichbar: Nachfassungen laufen weiter. Der
        # Zyklus-Zeitstempel friert ein (Karte nicht gesehen).
        _faellige_nachfassungen(leser_pm, zustand, protokoll)
        return meldungen

    if sperre is not None and sperre.aktiv:
        info = sperre.ende(_jetzt_utc().timestamp())
        _protokolliere(protokoll, {
            "art": "sperre_ende", "zeit_utc": _iso(_jetzt_utc()), **info})
        ausfall_s = _pruefe_ausfall(zustand, protokoll, hinweis="Nach Sperre:")

    if karte is not None:
        meldungen = _verarbeite_karte(karte, leser_ds, leser_pm, ziele,
                                      zustand, protokoll, ausfall_s)
        if letzte_polygone is not None:
            letzte_polygone[:] = karte.polygone

    _faellige_nachfassungen(leser_pm, zustand, protokoll)
    zustand["letzter_zyklus_ts"] = _jetzt_utc().timestamp()
    return meldungen


def _verarbeite_karte(karte: DSKarte, leser_ds: DeepStateLeser,
                      leser_pm: PolymarktLeser, ziele: list[Marktziel],
                      zustand: dict, protokoll: Path,
                      ausfall_s: float) -> list[dict]:
    jetzt = _jetzt_utc()
    grundierung = zustand.get("karte_id") is None
    neu = karte.id != zustand.get("karte_id")
    budget = {"rest": PREISABRUFE_JE_ZYKLUS}

    eintrag: dict | None = None
    if neu and not grundierung:
        try:
            eintrag = leser_ds.eintrag(karte.id)
        except DSFehler as fehler:
            _protokolliere(protokoll, {
                "art": "fehler", "zeit_utc": _iso(jetzt),
                "wo": "eintrag", "status": fehler.status,
            })
    created_at = (eintrag or {}).get("createdAt")
    created_ts = _epoch(created_at)
    vorlauf = (round(jetzt.timestamp() - created_ts, 1)
               if created_ts is not None else None)
    erwaehnt = maerkte_nahe(
        erwaehnungen((eintrag or {}).get("descriptionEn")
                     or (eintrag or {}).get("description")),
        ziele)

    _protokolliere(protokoll, {
        "art": "karte_neu" if neu else "nachbearbeitung",
        "zeit_utc": _iso(jetzt),
        "karte_id": karte.id,
        "karte_datetime": karte.datetime,
        "created_at": created_at,
        "updated_at": (eintrag or {}).get("updatedAt"),
        "vorlauf_s": vorlauf,
        "n_features": karte.n_features,
        "n_polygone": len(karte.polygone),
        "erwaehnt": erwaehnt,
        "grundierung": grundierung,
        "nach_ausfall_s": ausfall_s,
    })

    aktuelle = deckung(karte.polygone, ziele)
    meldungen: list[dict] = []

    def _preis(token: str) -> tuple[float | None, bool]:
        if budget["rest"] <= 0:
            return None, True
        budget["rest"] -= 1
        return leser_pm.preis_yes(token), False

    for ziel in ziele:
        vorher = set(zustand["beobachtet"].get(ziel.slug, []))
        nachher = aktuelle.get(ziel.slug, set())
        zustand["beobachtet"][ziel.slug] = sorted(nachher)
        if grundierung:
            continue
        for klasse in sorted(nachher - vorher):
            preis, uebersprungen = _preis(ziel.token_yes)
            buch = None
            if ziel.auswertbar and budget["rest"] > 0:
                budget["rest"] -= 1
                buch = leser_pm.buch_tiefe(ziel.token_yes)
            meldung = {
                "art": "ds_treffer",
                "zeit_utc": _iso(jetzt),
                "slug": ziel.slug,
                "klasse": klasse,
                "siedlung": ziel.siedlung_name,
                "objectid": ziel.siedlung_objectid,
                "karte_id": karte.id,
                "created_at": created_at,
                "vorlauf_s": vorlauf,
                "polaritaet": ziel.polaritaet,
                "kriterium": ziel.kriterium,
                "auswertbar": ziel.auswertbar,
                "preis_yes": preis,
                "preis_uebersprungen": uebersprungen,
                "buch": buch,
                "nach_ausfall_s": ausfall_s,
                "erwaehnt": any(n["slug"] == ziel.slug
                                for e in erwaehnt for n in e["maerkte_nahe"]),
            }
            _protokolliere(protokoll, meldung)
            meldungen.append(meldung)
            for minute in NACHFASS_MINUTEN[1:]:
                zustand["offene_nachfassungen"].append({
                    "slug": ziel.slug,
                    "token": ziel.token_yes,
                    "layer": klasse,
                    "minute": minute,
                    "erste_sichtung_ts": jetzt.timestamp(),
                    "faellig_ts": jetzt.timestamp() + minute * 60,
                })
        for klasse in sorted(vorher - nachher):
            preis = None
            if ziel.auswertbar:
                preis, _ = _preis(ziel.token_yes)
            _protokolliere(protokoll, {
                "art": "ds_verlust",
                "zeit_utc": _iso(jetzt),
                "slug": ziel.slug,
                "klasse": klasse,
                "siedlung": ziel.siedlung_name,
                "objectid": ziel.siedlung_objectid,
                "karte_id": karte.id,
                "auswertbar": ziel.auswertbar,
                "preis_yes": preis,
                "restliche_klassen": sorted(nachher),
            })

    if grundierung:
        _protokolliere(protokoll, {
            "art": "grundierung",
            "zeit_utc": _iso(jetzt),
            "karte_id": karte.id,
            "n_polygone": len(karte.polygone),
            "n_gedeckt": len(aktuelle),
        })

    zustand["karte_id"] = karte.id
    zustand["etag"] = karte.etag
    if created_at:
        zustand["karte_created_at"] = created_at
    return meldungen


def _lade_zustand(pfad: Path) -> dict:
    if not pfad.exists():
        return _leerer_zustand()
    try:
        roh = json.loads(pfad.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _leerer_zustand()
    if not isinstance(roh, dict) or roh.get("schema") != ZUSTAND_SCHEMA:
        return _leerer_zustand()
    zustand = _leerer_zustand()
    zustand.update(roh)
    return zustand


def grundiere_neue_ziele(zustand: dict, ziele: list[Marktziel],
                         polygone: list) -> list[str]:
    """Neue Slugs mit der zuletzt gesehenen Karte grundieren.

    Ohne das meldete die naechste Karte fuer einen neu gelisteten Markt
    eine "neue" Beruehrung, die in Wahrheit seit Tagen besteht — dasselbe
    Phantom, das der ISW-Rekorder ueber die Slug-Vererbung abfaengt.
    """
    neue = [z for z in ziele if z.slug not in zustand["beobachtet"]]
    if not neue:
        return []
    aktuelle = deckung(polygone, neue)
    for ziel in neue:
        zustand["beobachtet"][ziel.slug] = sorted(aktuelle.get(ziel.slug, set()))
    return [z.slug for z in neue]


def _bereinige_zustand(zustand: dict, slugs_aktiv: set[str]) -> None:
    for slug in [s for s in zustand["beobachtet"] if s not in slugs_aktiv]:
        del zustand["beobachtet"][slug]
    zustand["offene_nachfassungen"] = [
        a for a in zustand["offene_nachfassungen"] if a["slug"] in slugs_aktiv
    ]


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(
        description="Rekorder DeepStateMap -> Polymarket-Preis (read-only)")
    zerleger.add_argument("--einmal", action="store_true",
                          help="nur ein Durchlauf, dann beenden")
    zerleger.add_argument("--takt-s", type=int, default=TAKT_S)
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
        profil = os.environ.get("BOT_PROFIL", "deepstate_ukraine")
        wurzel = Path(os.environ.get("THESIS_LIVE_ROOT", "data/live"))
        live_dir = wurzel / profil
        from operations.pipeline.startwache import wache_nehmen
        if not wache_nehmen(live_dir):
            print(f"{profil}: andere Instanz haelt start.lock - Ende.")
            return 0
        argumente.zustand = live_dir / "zustand.json"
        argumente.protokoll = live_dir / "ereignisse.jsonl"
        argumente.geometrie_cache = live_dir / "geometrie_cache.json"
        _herzschlag(live_dir, art="start", takt_s=argumente.takt_s)

    karte_isw = ISWKarte()          # nur fuer Siedlungsflaechen (gecacht)
    leser_pm = PolymarktLeser()
    leser_ds = DeepStateLeser()
    zustand = _lade_zustand(argumente.zustand)
    cache = lade_geometrie_cache(argumente.geometrie_cache)

    print("Marktliste wird aufgebaut ...")
    try:
        ziele = lade_marktziele(leser_pm, karte_isw, cache,
                                argumente.geometrie_cache)
    except Exception as fehler:  # noqa: BLE001 - ohne Ziele kein Betrieb
        print(f"FATAL Marktliste nicht ladbar: {fehler}")
        return 1
    print(f"{len(ziele)} Maerkte mit Siedlungsflaeche, "
          f"davon {sum(1 for z in ziele if z.auswertbar)} auswertbar")

    letzter_refresh = time.monotonic()
    letzter_herzschlag: float | None = None
    letzte_polygone: list = []
    sperre = Sperre()
    try:
        while True:
            try:
                meldungen = durchlauf(leser_ds, leser_pm, ziele, zustand,
                                      argumente.protokoll, sperre=sperre,
                                      letzte_polygone=letzte_polygone)
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
                _herzschlag(live_dir, karte_id=zustand.get("karte_id"))
                letzter_herzschlag = time.monotonic()
            for m in meldungen:
                marke = "" if m.get("auswertbar") else "  [nicht auswertbar]"
                print(f"DS-{m['art'][3:].upper()} {m['zeit_utc']} {m['klasse']} "
                      f"-> {m['slug']} ({m['siedlung']}) "
                      f"YES={m.get('preis_yes')}{marke}")
            if argumente.einmal:
                return 0

            if time.monotonic() - letzter_refresh >= argumente.markt_refresh_s:
                letzter_refresh = time.monotonic()
                try:
                    neue = lade_marktziele(leser_pm, karte_isw, cache,
                                           argumente.geometrie_cache)
                    alt_slugs = {z.slug for z in ziele}
                    neu_slugs = {z.slug for z in neue}
                    if alt_slugs != neu_slugs:
                        grundiert = grundiere_neue_ziele(
                            zustand, neue, letzte_polygone)
                        _bereinige_zustand(zustand, neu_slugs)
                        _protokolliere(argumente.protokoll, {
                            "art": "watchlist_refresh",
                            "zeit_utc": _iso(_jetzt_utc()),
                            "n_maerkte": len(neue),
                            "neu": sorted(neu_slugs - alt_slugs),
                            "entfernt": sorted(alt_slugs - neu_slugs),
                            "grundiert": sorted(grundiert),
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
                print(f"SPERRE HTTP {sperre.status}, warte "
                      f"{sperre.wartezeit_s:.0f} s")
                _schlafe(sperre.wartezeit_s, herzschlag=lambda: _herzschlag(
                    live_dir, karte_id=zustand.get("karte_id"),
                    sperre_s=sperre.wartezeit_s))
                letzter_herzschlag = time.monotonic()
            else:
                time.sleep(argumente.takt_s)
    except KeyboardInterrupt:
        _herzschlag(live_dir, art="stop")
        return 0
    finally:
        karte_isw.schliessen()
        leser_pm.schliessen()
        leser_ds.schliessen()


if __name__ == "__main__":
    raise SystemExit(main())
