"""ISW-Karten-Watcher: ArcGIS-FeatureServer des Institute for the Study of War.

Auflösungsquelle der Polymarket-Serie `ukraine-map`. Die Karte ist kein Bild,
sondern ein FeatureServer — Polygone sind direkt abfragbar, kein OCR nötig.

Regel-Abbildung (Auflösungstext, verbatim aus der Gamma-API für
`will-russia-enter-krasnoiarske-by-july-31`):
- Qualifizierend ist "any continuous shading" aus GENAU VIER Layern:
  Assessed Russian Infiltration Areas / Assessed Russian Control /
  Assessed Russian Advance In Ukraine / Assessed Russian Gains in the
  Past 24 Hours. Der Kontroll-Layer allein genügt NICHT als Beobachtung.
- "enter" heisst Berührung: "any part of the specified territory".
  "capture all of" verlangt Vollüberdeckung — anderes Kriterium.
- Persistenz: die Schattierung muss "through the next full ISW daily
  update cycle" Bestand haben. Eine Berührung ist also ein Kandidat,
  keine Auflösung.

Vier Befunde aus der Sondierung vom 23.07., die die Auslegung bestimmen
(Details in docs/project/UKRAINE_ISW_LATENZ_SONDIERUNG.md):

1. Feature-Zeit ≠ Layer-Zeit. Beim Krasnoiarske-Ereignis stand die
   `editingInfo.lastEditDate` des Layers auf 22:44 UTC, das auslösende
   Polygon trug `CreationDate` 20:39 UTC. Wer die Layer-Zeit als
   Ereigniszeit nimmt, misst den Vorlauf mit falschem Vorzeichen.
   Layer-Zeit ist der Stolperdraht, Feature-Zeit der Zeitstempel.
2. Der Infiltrations-Layer hat die niedrigste ISW-Beweisschwelle
   ("begrenzte Präsenz, aber ohne Kontrolle") und schaltet deshalb
   zuerst. Im gemessenen Fall hat der Kontroll-Layer bis heute nicht
   reagiert.
3. Namen tragen nicht. Der Markt schreibt "Krasnoiarske", der
   Siedlungs-Layer führt "Krasnoyarske"; eine Namenssuche liefert null
   Treffer. Zuordnung ausschliesslich über die Koordinate.
4. Bulk-Rebuilds. Am 21.07. entstanden 115 Infiltrations-Features in
   48 Minuten — ISW löscht und zeichnet periodisch neu. Ein naiver
   "neues Feature"-Trigger feuert dann für Dutzende Siedlungen auf
   einmal, und `CreationDate` taugt nicht als historisches Protokoll.

Feldverfügbarkeit je Layer (bestimmt die Delta-Strategie):

    Layer          CreationDate  EditDate  Delta-Abfrage
    infiltration   ja            ja        ja
    advance        ja            ja        ja
    control        nein          ja        nur über EditDate
    gains24h       nein          nein      nein -> Geometrie-Diff

Read-only. Kein Order-Pfad, keine Schreibzugriffe auf ISW.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

import httpx

ARCGIS_BASIS = (
    "https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/"
)
SIEDLUNGS_LAYER = "Ukrainian_Settlements_Updated_view/FeatureServer/0"

# Gemessen 23.07.: Layer-Metadaten 104 ms, Volldatenabruf 1494 ms,
# 15 Polls in Folge ohne Rate-Limit (Median 543 ms).
STANDARD_TIMEOUT = 30.0

_KOORDINATE = re.compile(r"\(\s*([0-9]+(?:\.[0-9]+)?)\s*[^0-9]*?N\s*[,;]?\s*"
                         r"([0-9]+(?:\.[0-9]+)?)\s*[^0-9]*?E\s*\)")


@dataclass(frozen=True)
class ISWLayer:
    """Ein qualifizierender Kartenlayer samt seiner Abfrage-Fähigkeiten.

    `id_feld` ist nicht überall `OBJECTID`: der Gains24h-View führt `FID`.
    Eine feste Annahme quittiert ArcGIS mit HTTP 400 (Probelauf 23.07.).
    """

    name: str
    pfad: str
    hat_creation_date: bool
    hat_edit_date: bool
    id_feld: str = "OBJECTID"

    @property
    def delta_faehig(self) -> bool:
        """Ob gezielt nach Änderungen gefragt werden kann."""
        return self.hat_creation_date or self.hat_edit_date


# Reihenfolge = erwartete Schaltreihenfolge (niedrigste Beweisschwelle zuerst).
QUALIFIZIERENDE_LAYER: tuple[ISWLayer, ...] = (
    ISWLayer(
        "infiltration",
        "View_AssessedRussianInfiltrationAreasinUkraine_V4/FeatureServer/0",
        hat_creation_date=True,
        hat_edit_date=True,
    ),
    ISWLayer(
        "gains24h",
        "Assessed_Russian_Gains_in_the_Past_24_Hours_view/FeatureServer/0",
        hat_creation_date=False,
        hat_edit_date=False,
        id_feld="FID",
    ),
    ISWLayer(
        "advance",
        "AssessedRussianAdvanceInUkraine_V2_view/FeatureServer/0",
        hat_creation_date=True,
        hat_edit_date=True,
    ),
    ISWLayer(
        "control",
        "VIEW_RussiaCoTinUkraine_V3/FeatureServer/49",
        hat_creation_date=False,
        hat_edit_date=True,
    ),
)

LAYER_NACH_NAME = {layer.name: layer for layer in QUALIFIZIERENDE_LAYER}


@dataclass
class Siedlung:
    """Verwaltungsfläche aus dem ISW-Siedlungslayer."""

    objectid: int
    name: str            # ADM4_EN, Schreibweise des Layers (nicht des Markts)
    ringe: list[list[list[float]]] = field(default_factory=list)


@dataclass
class ISWFlaeche:
    """Ein Polygon eines qualifizierenden Layers."""

    layer: str
    objectid: int
    ringe: list[list[list[float]]]
    creation_ms: int | None = None
    edit_ms: int | None = None

    @property
    def zeitstempel_ms(self) -> int | None:
        """Beste verfügbare Ereigniszeit: Anlage vor Änderung."""
        return self.creation_ms if self.creation_ms is not None else self.edit_ms


class ISWFehler(RuntimeError):
    """HTTP- oder API-Fehler des FeatureServers; status für Backoff."""

    def __init__(self, status: int, body: str = "") -> None:
        super().__init__(f"isw_arcgis HTTP {status}: {body[:160]}")
        self.status = status


# ------------------------------------------------------------------ Parsing

def koordinate_aus_beschreibung(text: str | None) -> tuple[float, float] | None:
    """Zieht "(48.419117° N, 37.125165° E)" aus dem Marktbeschreibungstext.

    Gibt (lat, lon) zurück oder None. Die Koordinate ist die einzige
    belastbare Ortszuordnung — Namen weichen zwischen Markt und ISW-Layer ab
    (Befund 3 im Modul-Docstring).
    """
    if not text:
        return None
    treffer = _KOORDINATE.search(text)
    if not treffer:
        return None
    return float(treffer.group(1)), float(treffer.group(2))


def markt_polaritaet(slug: str | None) -> str:
    """Wessen Vorrücken der Markt bejaht.

    "russisch"   -> russische Schattierung ist das YES-Signal
    "ukrainisch" -> russische Schattierung ist das GEGEN-Signal
                    (`will-ukraine-re-enter-…`, `…-recapture-…`)
    "unklar"     -> nicht automatisch entscheidbar, nie handeln

    Eigener Fehlerfall aus der Sondierung: ein Filter auf "enter" im Slug
    fängt "re-enter" mit und dreht damit das Vorzeichen um.
    """
    if not slug:
        return "unklar"
    s = slug.lower()
    if "ukraine-re-enter" in s or "ukraine-recapture" in s:
        return "ukrainisch"
    if s.startswith("will-ukraine") or "-recapture-" in s:
        return "ukrainisch"
    if s.startswith("will-russia"):
        return "russisch"
    return "unklar"


def markt_kriterium(slug: str | None) -> str:
    """Welcher Geometrietest den Markt auflöst.

    "beruehrung"   -> "enter": jede Berührung genügt (auswertbar)
    "vollstaendig" -> "capture all of": Vollüberdeckung nötig
                      (der Rekorder protokolliert nur die Berührung und
                       bewertet die Auflösung ausdrücklich NICHT)
    """
    if not slug:
        return "unklar"
    s = slug.lower()
    if "-capture-all-of-" in s:
        return "vollstaendig"
    if "-enter-" in s or "-capture-" in s:
        return "beruehrung" if "-enter-" in s else "vollstaendig"
    return "unklar"


# ---------------------------------------------------------------- Geometrie
# Bewusst ohne shapely: der Test ist klein, deterministisch und
# testabgedeckt, und das Repo bekommt keine neue Abhaengigkeit.

def bounding_box(ringe: list[list[list[float]]]) -> tuple[float, float, float, float]:
    """(xmin, ymin, xmax, ymax) über alle Ringe."""
    xs = [p[0] for ring in ringe for p in ring]
    ys = [p[1] for ring in ringe for p in ring]
    if not xs:
        raise ValueError("leere Geometrie")
    return min(xs), min(ys), max(xs), max(ys)


def _boxen_ueberlappen(a: tuple[float, float, float, float],
                       b: tuple[float, float, float, float]) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def punkt_in_polygon(x: float, y: float,
                     ringe: list[list[list[float]]]) -> bool:
    """Even-odd-Test über alle Ringe (ArcGIS: äusserer Ring plus Löcher)."""
    innen = False
    for ring in ringe:
        n = len(ring)
        for i in range(n):
            x1, y1 = ring[i][0], ring[i][1]
            x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
            if (y1 > y) != (y2 > y):
                schnitt_x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if x < schnitt_x:
                    innen = not innen
    return innen


def _orientierung(a: list[float], b: list[float], c: list[float]) -> int:
    wert = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if wert > 0:
        return 1
    if wert < 0:
        return -1
    return 0


def _auf_strecke(a: list[float], b: list[float], p: list[float]) -> bool:
    return (min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def strecken_schneiden(a: list[float], b: list[float],
                       c: list[float], d: list[float]) -> bool:
    """Schneiden sich die Strecken ab und cd (inkl. kollinearer Berührung)?"""
    o1, o2 = _orientierung(a, b, c), _orientierung(a, b, d)
    o3, o4 = _orientierung(c, d, a), _orientierung(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and _auf_strecke(a, b, c):
        return True
    if o2 == 0 and _auf_strecke(a, b, d):
        return True
    if o3 == 0 and _auf_strecke(c, d, a):
        return True
    if o4 == 0 and _auf_strecke(c, d, b):
        return True
    return False


def _kanten(ringe: list[list[list[float]]]):
    for ring in ringe:
        n = len(ring)
        for i in range(n):
            yield ring[i], ring[(i + 1) % n]


def polygone_beruehren(a: list[list[list[float]]],
                       b: list[list[list[float]]]) -> bool:
    """Teilen sich zwei Polygone irgendeinen Punkt?

    Vollständig für einfache Polygone: Boxen-Vorfilter, dann Ecke-in-Fläche
    in beide Richtungen (deckt vollständige Enthaltung ab), dann
    Kantenschnitt (deckt echte Überlappung ohne enthaltene Ecke ab).
    """
    if not a or not b:
        return False
    if not _boxen_ueberlappen(bounding_box(a), bounding_box(b)):
        return False
    for ring in a:
        for punkt in ring:
            if punkt_in_polygon(punkt[0], punkt[1], b):
                return True
    for ring in b:
        for punkt in ring:
            if punkt_in_polygon(punkt[0], punkt[1], a):
                return True
    for p1, p2 in _kanten(a):
        for p3, p4 in _kanten(b):
            if strecken_schneiden(p1, p2, p3, p4):
                return True
    return False


def neue_zeitstempel(zeitstempel_ms: list[int | None],
                     seit_ms: int | None) -> list[int]:
    """Nur die Stempel, die nach dem letzten bekannten Layer-Stand liegen.

    Ohne diese Einschränkung bewertet die Rebuild-Bremse bei jedem Poll die
    gesamte Layer-Historie. Die ist naturgemäss geclustert (ISW baut den
    Layer periodisch neu auf), die Bremse würde dauerhaft greifen und der
    Rekorder nie ein Signal liefern — ein stiller Totalausfall des
    Instruments. Gefunden im Probelauf vom 23.07.
    """
    stempel = [t for t in zeitstempel_ms if t is not None]
    if seit_ms is None:
        return stempel
    return [t for t in stempel if t > seit_ms]


def ist_bulk_rebuild(zeitstempel_ms: list[int],
                     schwelle: int = 10,
                     fenster_s: int = 300) -> bool:
    """Erkennt einen Neuaufbau des Layers statt einer echten Änderung.

    Muster vom 21.07.: 115 Features in 48 Minuten. Ohne diese Bremse feuert
    der Rekorder nach jedem Rebuild für Dutzende Siedlungen gleichzeitig.

    Erwartet die per `neue_zeitstempel` gefilterten Stempel, nicht den
    gesamten Layer-Inhalt.
    """
    stempel = sorted(t for t in zeitstempel_ms if t is not None)
    if len(stempel) < schwelle:
        return False
    fenster_ms = fenster_s * 1000
    for i in range(len(stempel) - schwelle + 1):
        if stempel[i + schwelle - 1] - stempel[i] <= fenster_ms:
            return True
    return False


# ------------------------------------------------------------------- Client

class ISWKarte:
    """Read-only Zugriff auf den ISW-FeatureServer."""

    def __init__(self, basis: str = ARCGIS_BASIS,
                 timeout: float = STANDARD_TIMEOUT,
                 client: httpx.Client | None = None) -> None:
        self.basis = basis
        self.timeout = timeout
        self._client = client

    def _sess(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": "thesis-isw-rekorder/1.0 (read-only)"},
            )
        return self._client

    def _json(self, url: str, daten: dict | None = None) -> dict:
        sess = self._sess()
        if daten is None:
            antwort = sess.get(url)
        else:
            antwort = sess.post(url, data=daten)
        if antwort.status_code != 200:
            raise ISWFehler(antwort.status_code, antwort.text)
        nutz = antwort.json()
        # ArcGIS meldet Fehler mit HTTP 200 und einem error-Objekt.
        if isinstance(nutz, dict) and "error" in nutz:
            fehler = nutz["error"]
            raise ISWFehler(int(fehler.get("code", 200)),
                            str(fehler.get("message", "")))
        return nutz

    def layer_stand(self, layer: ISWLayer) -> int | None:
        """`editingInfo.lastEditDate` in ms — der Stolperdraht.

        Billigster Poll (gemessen 104 ms). Erkennt auch Löschungen, die eine
        reine CreationDate-Abfrage übersieht. Als Ereigniszeit ungeeignet,
        siehe Befund 1 im Modul-Docstring.
        """
        nutz = self._json(f"{self.basis}{layer.pfad}?f=json")
        stand = (nutz.get("editingInfo") or {}).get("lastEditDate")
        return int(stand) if stand is not None else None

    def flaechen(self, layer: ISWLayer, where: str = "1=1",
                 mit_geometrie: bool = True) -> list[ISWFlaeche]:
        """Polygone eines Layers, in WGS84."""
        felder = [layer.id_feld]
        if layer.hat_creation_date:
            felder.append("CreationDate")
        if layer.hat_edit_date:
            felder.append("EditDate")
        daten = {
            "f": "json",
            "where": where,
            "outFields": ",".join(felder),
            "returnGeometry": "true" if mit_geometrie else "false",
            "outSR": "4326",
        }
        nutz = self._json(f"{self.basis}{layer.pfad}/query", daten)
        heraus: list[ISWFlaeche] = []
        for eintrag in nutz.get("features") or []:
            attribute = eintrag.get("attributes") or {}
            geometrie = eintrag.get("geometry") or {}
            heraus.append(ISWFlaeche(
                layer=layer.name,
                objectid=int(attribute.get(layer.id_feld) or 0),
                ringe=geometrie.get("rings") or [],
                creation_ms=attribute.get("CreationDate"),
                edit_ms=attribute.get("EditDate"),
            ))
        return heraus

    def siedlung_an_punkt(self, lat: float, lon: float) -> Siedlung | None:
        """Verwaltungsfläche, in der die Marktkoordinate liegt."""
        daten = {
            "f": "json",
            "where": "1=1",
            "geometry": json.dumps(
                {"x": lon, "y": lat, "spatialReference": {"wkid": 4326}}
            ),
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "OBJECTID,ADM4_EN",
            "returnGeometry": "true",
            "outSR": "4326",
        }
        nutz = self._json(f"{self.basis}{SIEDLUNGS_LAYER}/query", daten)
        eintraege = nutz.get("features") or []
        if not eintraege:
            return None
        erster = eintraege[0]
        attribute = erster.get("attributes") or {}
        return Siedlung(
            objectid=int(attribute.get("OBJECTID", 0)),
            name=str(attribute.get("ADM4_EN") or ""),
            ringe=(erster.get("geometry") or {}).get("rings") or [],
        )

    def schliessen(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
