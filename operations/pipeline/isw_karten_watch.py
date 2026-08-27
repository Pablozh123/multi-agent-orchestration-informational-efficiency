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
import time
from dataclasses import dataclass, field

import httpx

ARCGIS_BASIS = (
    "https://services5.arcgis.com/SaBe5HMtmnbqSWlu/arcgis/rest/services/"
)
SIEDLUNGS_LAYER = "Ukrainian_Settlements_Updated_view/FeatureServer/0"

# Gemessen 23.07.: Layer-Metadaten 104 ms (Cache-Treffer, s. layer_stand),
# Volldatenabruf 1494 ms. Neu gemessen 27.08. mit Cache-Buster: Metadaten
# ~200 ms ab Origin. Unter Dauerlast drosselt der Server (HTTP 429; am
# 23.07. bei Volldaten-Dauerlast beobachtet), und einzelne Abrufe laufen
# in Read-Timeouts -- beides muss der Client abfangen.
STANDARD_TIMEOUT = 30.0

# Eigener Status fuer Transportfehler ohne HTTP-Antwort (Timeout, DNS,
# Verbindungsabbruch). Kein echter HTTP-Code.
TRANSPORT_STATUS = 599

WIEDERHOLBAR = frozenset({429, 500, 502, 503, 504, TRANSPORT_STATUS})

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
    def juengste_aenderung_ms(self) -> int | None:
        """Zeit der letzten Änderung: Maximum aus Anlage und Edit.

        Neue Überdeckung entsteht auch dadurch, dass ISW ein BESTEHENDES
        Polygon per Edit erweitert. Wer dann die Anlagezeit als Ereigniszeit
        nimmt, misst Tage statt Sekunden (Review-Befund 24.07.; der
        Krasnoiarske-Fall trug einen Edit 21:02 auf einem 20:39 angelegten
        Polygon).
        """
        stempel = [s for s in (self.creation_ms, self.edit_ms) if s is not None]
        return max(stempel) if stempel else None


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
    "unklar"     -> nicht automatisch entscheidbar, nie handeln

    Entschieden wird ausschliesslich über das Subjekt am Slug-Anfang.
    Verb-Substrings sind doppelt verbrannt: "enter" fängt "re-enter", und
    ein "-recapture-"-Filter hätte `will-russia-recapture-…` fälschlich
    ukrainisch eingefärbt (russische Rückeroberung = russische Schattierung
    = YES; Review-Befund 24.07.).
    """
    if not slug:
        return "unklar"
    s = slug.lower()
    if s.startswith("will-russia"):
        return "russisch"
    if s.startswith("will-ukraine"):
        return "ukrainisch"
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


def _segment_box_ueberlappt(p1: list[float], p2: list[float],
                            box: tuple[float, float, float, float]) -> bool:
    """Kommt die Strecke p1p2 überhaupt in die Nähe der Box?"""
    if max(p1[0], p2[0]) < box[0] or min(p1[0], p2[0]) > box[2]:
        return False
    if max(p1[1], p2[1]) < box[1] or min(p1[1], p2[1]) > box[3]:
        return False
    return True


def polygone_beruehren(a: list[list[list[float]]],
                       b: list[list[list[float]]]) -> bool:
    """Teilen sich zwei Polygone irgendeinen Punkt?

    Drei Stufen, absteigend nach Kosten:

    1. Boxen-Vorfilter.
    2. Kantenschnitt, aber NUR gegen die Kanten von `a`, die in die Box von
       `b` hineinreichen.
    3. Fehlt jede Randberührung, ist JEDER Ring entweder vollständig im
       anderen Polygon oder vollständig draussen (die Grenze zu kreuzen
       bräuchte einen Kantenschnitt). Darum genügt der erste Punkt — aber
       je Ring, nicht je Polygon: ArcGIS-Features dürfen mehrere
       Aussenringe tragen (Multipart), und ein Teilpolygon kann ganz im
       anderen liegen, während der erste Ring weit entfernt ist
       (Review-Befund 24.07., mit Gegenbeispiel am echten Code belegt).

    Warum Stufe 2 den Kantenfilter braucht: Das grösste Kontroll-Polygon der
    ISW-Karte trägt 51'901 Stützpunkte in einem Ring. Der naive Test — alle
    Ecken beider Polygone gegeneinander plus alle Kantenpaare — kostete dafür
    gemessene 5.6 s je Siedlung, hochgerechnet 48 Minuten je Durchlauf. Der
    Rekorder blieb im ersten Durchlauf hängen (Befund 23.07.). Mit Filter
    bleibt es bei zwei linearen Durchläufen über `a`.

    Löcher bleiben korrekt behandelt: `punkt_in_polygon` zählt even-odd über
    alle Ringe. Ein Loch-Ring-Punkt ist ein Randpunkt des Polygons; liegt er
    im anderen Polygon, berühren sie sich wirklich. Liegt das andere Polygon
    ganz IM Loch, sind alle Punkttests negativ — korrekt disjunkt.
    """
    a = [ring for ring in a if ring]
    b = [ring for ring in b if ring]
    if not a or not b:
        return False
    box_a, box_b = bounding_box(a), bounding_box(b)
    if not _boxen_ueberlappen(box_a, box_b):
        return False

    kanten_b = list(_kanten(b))
    for p1, p2 in _kanten(a):
        if not _segment_box_ueberlappt(p1, p2, box_b):
            continue
        for p3, p4 in kanten_b:
            if strecken_schneiden(p1, p2, p3, p4):
                return True

    for ring in a:
        if punkt_in_polygon(ring[0][0], ring[0][1], b):
            return True
    for ring in b:
        if punkt_in_polygon(ring[0][0], ring[0][1], a):
            return True
    return False


# Anmerkung: Die fruehere Rebuild-Bremse (ist_bulk_rebuild/neue_zeitstempel)
# ist entfernt. Der Review vom 24.07. hat gezeigt, dass sie im Live-Takt nie
# greift (beim 21.07.-Muster sieht ein 20-s-Poll ~1 neues Feature je Delta,
# Schwelle war 10) und die Loesch-Phase eines Rebuilds gar nicht abdeckt.
# Den Schutz uebernimmt das Beruhigungsfenster im Rekorder: Ereignisse werden
# als Kandidaten gefuehrt und erst nach Bestand ueber das Fenster bestaetigt —
# ein Loeschen-und-Neuzeichnen-Zyklus nettet sich damit zu null Ereignissen.

# ------------------------------------------------------------------- Client

class ISWKarte:
    """Read-only Zugriff auf den ISW-FeatureServer."""

    def __init__(self, basis: str = ARCGIS_BASIS,
                 timeout: float = STANDARD_TIMEOUT,
                 client: httpx.Client | None = None,
                 max_versuche: int = 5,
                 backoff_start_s: float = 10.0) -> None:
        # 10/20/40/80 s -> rund 150 s Geduld. Vier Versuche ab 5 s (35 s)
        # reichten am 23.07. nicht aus, um eine anhaltende Drosselung
        # auszusitzen.
        self.basis = basis
        self.timeout = timeout
        self.max_versuche = max_versuche
        self.backoff_start_s = backoff_start_s
        self._client = client

    def _sess(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                headers={"User-Agent": "thesis-isw-rekorder/1.0 (read-only)"},
            )
        return self._client

    def _einmal(self, url: str, daten: dict | None) -> dict:
        sess = self._sess()
        try:
            if daten is None:
                antwort = sess.get(url)
            else:
                antwort = sess.post(url, data=daten)
        except httpx.HTTPError as fehler:
            # Transportfehler (Timeout, Verbindungsabbruch, DNS) als
            # wiederholbaren ISWFehler durchreichen. Ohne das reisst ein
            # einzelner Netz-Schluckauf den ganzen Rekorder ab -- genau so
            # ist er am 23.07. nach dem ersten Durchlauf gestorben.
            raise ISWFehler(TRANSPORT_STATUS, str(fehler)) from fehler
        if antwort.status_code != 200:
            raise ISWFehler(antwort.status_code, antwort.text)
        try:
            nutz = antwort.json()
        except ValueError as fehler:
            # 200-Antwort ohne JSON (z. B. Cloudflare-Fehlerseite) ist ein
            # transienter Fall und gehoert in den Backoff, nicht als
            # ungefangene Exception in den Durchlauf (Review-Befund 24.07.).
            raise ISWFehler(TRANSPORT_STATUS,
                            "keine JSON-Antwort") from fehler
        # ArcGIS meldet Fehler auch mit HTTP 200 und einem error-Objekt —
        # unter anderem 429 "Unable to perform query. Too many requests."
        if isinstance(nutz, dict) and "error" in nutz:
            fehler = nutz["error"]
            raise ISWFehler(int(fehler.get("code", 200)),
                            str(fehler.get("message", "")))
        return nutz

    def _json(self, url: str, daten: dict | None = None) -> dict:
        """Abruf mit Backoff bei Drosselung.

        Der FeatureServer drosselt unter Dauerlast (beobachtet 23.07.: HTTP
        429 "Too many requests" im error-Objekt einer 200-Antwort). Ohne
        Backoff verschärft der Rekorder die Drosselung, statt sie abzuwarten.
        """
        wartezeit = self.backoff_start_s
        letzter: ISWFehler | None = None
        for versuch in range(self.max_versuche):
            try:
                return self._einmal(url, daten)
            except ISWFehler as fehler:
                if fehler.status not in WIEDERHOLBAR:
                    raise
                letzter = fehler
                if versuch < self.max_versuche - 1:
                    time.sleep(wartezeit)
                    wartezeit *= 2
        raise letzter if letzter else ISWFehler(500, "unbekannt")

    def layer_stand(self, layer: ISWLayer) -> int | None:
        """`editingInfo.lastEditDate` in ms — der Stolperdraht.

        Erkennt auch Löschungen, die eine reine CreationDate-Abfrage
        übersieht. Als Ereigniszeit ungeeignet, siehe Befund 1 im
        Modul-Docstring.

        Cache-Buster (Messung 27.08.): Der CDN cached die Layer-Metadaten
        300 s (`cache-control: max-age=300`, `X-Cache: TCP_HIT`, ~10 ms) —
        ohne eindeutigen Parameter ist jedes Polling unter 5 Minuten
        wirkungslos, der Poll liest nur den Cache. Mit `_cb` antwortet der
        Origin (TCP_MISS, ~200 ms) mit dem echten Stand. Die 104-ms-Messung
        vom 23.07. war ein Cache-Treffer.
        """
        nutz = self._json(f"{self.basis}{layer.pfad}?f=json"
                          f"&_cb={int(time.time() * 1000)}")
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
