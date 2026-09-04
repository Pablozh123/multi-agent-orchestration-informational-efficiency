"""Quellen-Wache: Aenderungs-Rekorder fuer Aufloesungsquellen ausserhalb der Karten.

Verallgemeinert das ISW-/DeepState-Muster (Quelle pollen, Aenderung mit
Zeitstempel protokollieren, Markt-Reaktion nachfassen) auf beliebige
Webquellen, die Polymarket-Maerkte aufloesen oder ihnen vorauslaufen
(Recherche 27./28.08.2026 §8, Nicht-Mention-Klassen). Handelt nicht. Kein
Order-Pfad, keine Keys, keine Wallet.

Warum messen statt bauen: Fuer keine dieser Quellen ist bekannt, WIE OFT
und WANN sie sich aendern und ob der Markt darauf verzoegert reagiert. Der
Rekorder liefert genau diese Basisdaten — dieselbe Vorwaertsmessung, die
bei ISW den 18-min-Fall Krasnoiarske und bei der Fed-Rede den 4-40-min-
Vorlauf sichtbar machte.

Standard-Quellen (STANDARD_QUELLEN; per --quellen JSON ueberschreibbar):

    opm_status         OPM Operating Status — Aufloesungsuhr der Shutdown-
                       Ende-Leitern (Nov 2025: Bill 12.11. 21:45 ET, OPM-Seite
                       13.11. -> 97-c-Sprosse auf 1 c). Naechste Klippe
                       04./11.12.2026.
    doj_clemency       DOJ-Liste der Begnadigungen — Aufloesungsquelle der
                       Pardon-Leitern (Truth-Post ist schneller; hier wird
                       gemessen, wie viel spaeter die amtliche Liste folgt).
    scotus_opinions    Slip-Opinions der laufenden Term, scotus_orders die
                       Orders-Liste — 10:00-ET-Drops ab Oktober.
    fed_speeches_feed  JSON-Feed der Fed-Reden (Text erscheint zum Redebeginn,
                       Befund 28.08.: Last-Modified 14:00:11 GMT).
    fed_press_feed     JSON-Feed der Pressemitteilungen (FOMC-Statement 14:00 ET).
    nhc_atlantic       NHC-Advisory-RSS Atlantik (Advisory-Takt, Specials).
    apple_top_free_us  Apple-RSS Top-Free-Apps US — Quelle der taeglichen
                       "#1 Free App"-Maerkte.

Messdesign:

1. Poll je Quelle im eigenen Takt; Conditional GET (ETag/If-Modified-Since)
   wo der Server es anbietet, 304 = keine Aenderung ohne Nutzlast.
2. Normalisierung vor dem Hash: HTML -> sichtbarer Text ohne Script/Style/
   Kommentare; JSON -> kanonisch sortiert; XML/Text -> Whitespace-normiert.
   Ein Hash-Wechsel ist eine `aenderung` mit Erst-/Letztsichtung, Groessen,
   Last-Modified und einem kurzen Diff-Ausschnitt (erste abweichenden
   Zeilen), damit die Auswertung sieht, WAS sich geaendert hat.
3. Markt-Hook: traegt eine Quelle `markt_event_id`, wird bei jeder
   Aenderung das Gamma-Event gelesen (best bid/ask je Markt) und bei
   +1/+5/+30 min nachgefasst (`nachfassung`) — Vorlauf-Messung wie bei ISW.
4. Fehler: HTTP-Fehler oder Timeouts schalten die Quelle in eine Abkuehl-
   pause (SPERRE_START_S, verdoppelt bis SPERRE_MAX_S) mit EINEM `sperre`-
   Ereignis und `sperre_ende` beim ersten Erfolg (Amendment-A3-Muster).
5. Betrieb als Watchdog-Profil (`--live`, BOT_PROFIL, Herzschlag in
   bot_events.jsonl alle HERZSCHLAG_S, STALE_S des Watchdogs ist 600 s).

Aufruf:

    python -m operations.pipeline.quellen_wache --einmal
    python -m operations.pipeline.quellen_wache --takt-s 60
    python -m operations.pipeline.quellen_wache --live      # Watchdog
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

GAMMA = "https://gamma-api.polymarket.com"
UA = {"User-Agent": "ba-thesis quellen_wache (read-only, ETag-aware)"}

TAKT_S = 60
SCHLEIFE_MIN_S = 5
HERZSCHLAG_S = 120
SPERRE_START_S = 60
SPERRE_MAX_S = 900
NACHFASS_MINUTEN = (1, 5, 30)
DIFF_MAX_ZEILEN = 6
DIFF_MAX_ZEICHEN = 400

STANDARD_WURZEL = Path("data/live/quellen_wache")
ZUSTAND_SCHEMA = 1

# markt_event_id: Gamma-Event, dessen Quotes bei einer Aenderung der Quelle
# sofort und bei +1/+5/+30 min festgehalten werden (Stand 04.09.2026:
# Shutdown-by-Oct-1 580520, Pardon-Leiter 674973, Fed Decision September
# 481717, Cat-4-Landfall 131388). Laufen die Events aus, Hook im Override
# nachziehen — der Rekorder misst dann weiter, nur ohne Buch.
STANDARD_QUELLEN: dict[str, dict] = {
    "opm_status": {
        "url": "https://www.opm.gov/policy-data-oversight/snow-dismissal-procedures/current-status/",
        "art": "html", "takt_s": 60, "markt_event_id": "580520"},
    "doj_clemency": {
        "url": "https://www.justice.gov/pardon/clemency-grants-president-donald-j-trump-2025-present",
        "art": "html", "takt_s": 300, "markt_event_id": "674973"},
    "scotus_opinions": {
        "url": "https://www.supremecourt.gov/opinions/slipopinion/25", "art": "html", "takt_s": 60},
    "scotus_orders": {
        "url": "https://www.supremecourt.gov/orders/ordersofthecourt/25", "art": "html", "takt_s": 60},
    "fed_speeches_feed": {
        "url": "https://www.federalreserve.gov/json/ne-speeches.json", "art": "json", "takt_s": 60},
    "fed_press_feed": {
        "url": "https://www.federalreserve.gov/json/ne-press.json", "art": "json", "takt_s": 60,
        "markt_event_id": "481717"},
    "nhc_atlantic": {
        "url": "https://www.nhc.noaa.gov/index-at.xml", "art": "text", "takt_s": 120,
        "markt_event_id": "131388",
        # Feed-Zeitstempel bewegen sich ohne Inhalt (Befund 04.09. 18:05Z).
        "ignoriere": [r"<pubDate>.*?</pubDate>", r"<lastBuildDate>.*?</lastBuildDate>",
                      r"\bas of \w{3}, \d{1,2} \w{3} \d{4} [\d:]+ GMT"]},
    "apple_top_free_us": {
        "url": "https://rss.marketingtools.apple.com/api/v2/us/apps/top-free/10/apps.json",
        "art": "json", "takt_s": 300,
        "ignoriere": [r'"updated":"[^"]*",?']},
}


@dataclass
class Antwort:
    status: int
    headers: dict
    body: bytes


Holer = Callable[[str, dict], Antwort]
JsonHoler = Callable[[str], object]


def _jetzt() -> datetime:
    return datetime.now(timezone.utc)


def _iso(zeit: datetime) -> str:
    return zeit.isoformat(timespec="seconds").replace("+00:00", "Z")


# ------------------------------------------------------------------- HTTP

def hole(url: str, headers: dict) -> Antwort:
    req = urllib.request.Request(url, headers={**UA, **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return Antwort(r.status, dict(r.headers), r.read())
    except urllib.error.HTTPError as ex:
        return Antwort(ex.code, dict(ex.headers or {}), b"")
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        return Antwort(0, {"fehler": str(ex)}, b"")


def hole_json(url: str):
    a = hole(url, {})
    if a.status != 200:
        raise RuntimeError(f"HTTP {a.status} fuer {url}")
    return json.loads(a.body.decode("utf-8"))


# --------------------------------------------------------- Normalisierung

_SCRIPT = re.compile(r"<(script|style|noscript)\b.*?</\1>", re.S | re.I)
_KOMMENTAR = re.compile(r"<!--.*?-->", re.S)
_TAG = re.compile(r"<[^>]+>")


def normalisiere(body: bytes, art: str, ignoriere: tuple[str, ...] | list[str] = ()) -> str:
    """Vergleichbare Textform je Quellenart (siehe Messdesign 2).

    `ignoriere`: Regex-Muster, die vor dem Hash entfernt werden — fuer
    Zeitstempel und Zaehler, die sich ohne inhaltliche Aenderung bewegen
    (Live-Befund 04.09. 18:05Z: der NHC-RSS traegt `pubDate` und "No
    tropical cyclones as of <Zeit>" und aenderte sich damit alle zwei
    Minuten). Bei JSON wirken die Muster auf der kanonischen Form.
    """
    text = body.decode("utf-8", errors="replace")
    if art == "json":
        try:
            text = json.dumps(json.loads(text.lstrip("﻿")), sort_keys=True,
                              ensure_ascii=False, separators=(",", ":"))
            for muster in ignoriere:
                text = re.sub(muster, "", text)
            return text
        except json.JSONDecodeError:
            pass
    for muster in ignoriere:
        text = re.sub(muster, "", text, flags=re.S)
    if art == "html":
        text = _KOMMENTAR.sub(" ", _SCRIPT.sub(" ", text))
        text = _TAG.sub("\n", text)
    zeilen = [re.sub(r"\s+", " ", z).strip() for z in text.splitlines()]
    return "\n".join(z for z in zeilen if z)


def hash_von(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def diff_ausschnitt(alt: str, neu: str) -> str:
    """Erste abweichende Zeilen (+/-), gekuerzt — zeigt, WAS sich aenderte."""
    zeilen = []
    for z in difflib.unified_diff(alt.splitlines(), neu.splitlines(), lineterm="", n=0):
        if z.startswith(("+++", "---", "@@")):
            continue
        zeilen.append(z[:120])
        if len(zeilen) >= DIFF_MAX_ZEILEN:
            break
    return "\n".join(zeilen)[:DIFF_MAX_ZEICHEN]


# ---------------------------------------------------------------- Zustand

def leerer_zustand() -> dict:
    return {"schema": ZUSTAND_SCHEMA, "quellen": {}, "offene_nachfassungen": []}


def lade_zustand(pfad: Path) -> dict:
    if pfad.exists():
        try:
            daten = json.loads(pfad.read_text(encoding="utf-8"))
            if isinstance(daten, dict) and "quellen" in daten:
                daten.setdefault("offene_nachfassungen", [])
                return daten
        except json.JSONDecodeError:
            pass
    return leerer_zustand()


def schreibe_zustand(pfad: Path, zustand: dict) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_suffix(".tmp")
    tmp.write_text(json.dumps(zustand, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, pfad)


def protokolliere(pfad: Path, eintrag: dict, jetzt: datetime | None = None) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    zeile = {"zeit_utc": _iso(jetzt or _jetzt()), **eintrag}
    with open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps(zeile, ensure_ascii=False) + "\n")


def lade_quellen(pfad: Path | None) -> dict[str, dict]:
    if pfad is None:
        return dict(STANDARD_QUELLEN)
    daten = json.loads(Path(pfad).read_text(encoding="utf-8"))
    quellen = daten.get("quellen", daten) if isinstance(daten, dict) else {}
    out = {}
    for name, cfg in quellen.items():
        if not isinstance(cfg, dict) or not cfg.get("url"):
            continue
        out[name] = {"art": "html", "takt_s": TAKT_S, **cfg}
    return out


# ------------------------------------------------------------------ Markt

def markt_quotes(event_id: str, hole_json_fn: JsonHoler = hole_json) -> dict:
    """best bid/ask je Markt eines Gamma-Events (Fehler werden zur Notiz)."""
    try:
        ev = hole_json_fn(f"{GAMMA}/events/{event_id}")
    except Exception as ex:  # Messung darf am Markt-Hook nicht scheitern
        return {"fehler": str(ex)}
    out = {}
    for m in (ev.get("markets") or []) if isinstance(ev, dict) else []:
        out[str(m.get("id"))] = {"frage": (m.get("question") or "")[:80],
                                 "bid": m.get("bestBid"), "ask": m.get("bestAsk")}
    return out


# ------------------------------------------------------------------- Kern

def pruefe_quelle(name: str, cfg: dict, zustand: dict, protokoll: Path, holer: Holer,
                  hole_json_fn: JsonHoler = hole_json, jetzt: datetime | None = None) -> str:
    """Ein Poll einer Quelle. Liefert 'unveraendert' | 'erstsichtung' | 'aenderung' |
    'gesperrt' | 'fehler' | 'nicht_faellig'."""
    jetzt = jetzt or _jetzt()
    q = zustand["quellen"].setdefault(name, {"hash": None, "etag": None, "last_modified": None,
                                             "letzte_pruefung_utc": None,
                                             "letzte_aenderung_utc": None,
                                             "sperre_bis_utc": None, "sperre_s": 0,
                                             "text": None})
    if q.get("sperre_bis_utc") and jetzt < datetime.fromisoformat(
            q["sperre_bis_utc"].replace("Z", "+00:00")):
        return "gesperrt"
    if q.get("letzte_pruefung_utc"):
        letzte = datetime.fromisoformat(q["letzte_pruefung_utc"].replace("Z", "+00:00"))
        if (jetzt - letzte).total_seconds() < cfg.get("takt_s", TAKT_S) - 0.5:
            return "nicht_faellig"

    headers = {}
    if q.get("etag"):
        headers["If-None-Match"] = q["etag"]
    if q.get("last_modified"):
        headers["If-Modified-Since"] = q["last_modified"]
    a = holer(cfg["url"], headers)
    q["letzte_pruefung_utc"] = _iso(jetzt)

    if a.status == 304:
        _sperre_ende(name, q, protokoll, jetzt)
        return "unveraendert"
    if a.status != 200 or not a.body:
        q["sperre_s"] = min(max(q.get("sperre_s", 0) * 2, SPERRE_START_S), SPERRE_MAX_S)
        if not q.get("sperre_bis_utc"):
            protokolliere(protokoll, {"art": "sperre", "quelle": name, "status": a.status,
                                      "pause_s": q["sperre_s"],
                                      "hinweis": str(a.headers.get("fehler", ""))[:120]}, jetzt)
        q["sperre_bis_utc"] = _iso(jetzt + timedelta(seconds=q["sperre_s"]))
        return "fehler"

    _sperre_ende(name, q, protokoll, jetzt)
    q["etag"] = a.headers.get("ETag") or q.get("etag")
    q["last_modified"] = a.headers.get("Last-Modified") or q.get("last_modified")
    text = normalisiere(a.body, cfg.get("art", "html"), tuple(cfg.get("ignoriere") or ()))
    h = hash_von(text)
    if q.get("hash") is None:
        q.update({"hash": h, "text": text[:20000], "letzte_aenderung_utc": _iso(jetzt)})
        protokolliere(protokoll, {"art": "erstsichtung", "quelle": name, "hash": h[:16],
                                  "groesse": len(a.body),
                                  "last_modified": q["last_modified"]}, jetzt)
        return "erstsichtung"
    if h == q["hash"]:
        return "unveraendert"

    eintrag = {"art": "aenderung", "quelle": name, "hash_alt": q["hash"][:16], "hash_neu": h[:16],
               "groesse": len(a.body), "last_modified": q["last_modified"],
               "vorherige_aenderung_utc": q.get("letzte_aenderung_utc"),
               "diff": diff_ausschnitt(q.get("text") or "", text)}
    if cfg.get("markt_event_id"):
        eintrag["markt_event_id"] = str(cfg["markt_event_id"])
        eintrag["buch_t0"] = markt_quotes(str(cfg["markt_event_id"]), hole_json_fn)
        for minute in NACHFASS_MINUTEN:
            zustand["offene_nachfassungen"].append({
                "quelle": name, "markt_event_id": str(cfg["markt_event_id"]),
                "aenderung_utc": _iso(jetzt), "minute": minute,
                "faellig_utc": _iso(jetzt + timedelta(minutes=minute))})
    protokolliere(protokoll, eintrag, jetzt)
    q.update({"hash": h, "text": text[:20000], "letzte_aenderung_utc": _iso(jetzt)})
    return "aenderung"


def _sperre_ende(name: str, q: dict, protokoll: Path, jetzt: datetime) -> None:
    if q.get("sperre_bis_utc"):
        protokolliere(protokoll, {"art": "sperre_ende", "quelle": name,
                                  "pause_s": q.get("sperre_s", 0)}, jetzt)
    q["sperre_bis_utc"] = None
    q["sperre_s"] = 0


def nachfassungen(zustand: dict, protokoll: Path, hole_json_fn: JsonHoler = hole_json,
                  jetzt: datetime | None = None) -> int:
    """Faellige Markt-Nachfassungen ausfuehren; liefert deren Anzahl."""
    jetzt = jetzt or _jetzt()
    offen, erledigt = [], 0
    for nf in zustand.get("offene_nachfassungen", []):
        if datetime.fromisoformat(nf["faellig_utc"].replace("Z", "+00:00")) <= jetzt:
            protokolliere(protokoll, {"art": "nachfassung", **nf,
                                      "buch": markt_quotes(nf["markt_event_id"], hole_json_fn)},
                          jetzt)
            erledigt += 1
        else:
            offen.append(nf)
    zustand["offene_nachfassungen"] = offen
    return erledigt


def ein_zyklus(quellen: dict[str, dict], zustand: dict, protokoll: Path, holer: Holer = hole,
               hole_json_fn: JsonHoler = hole_json, jetzt: datetime | None = None) -> dict:
    jetzt = jetzt or _jetzt()
    ergebnis = {}
    for name, cfg in quellen.items():
        ergebnis[name] = pruefe_quelle(name, cfg, zustand, protokoll, holer, hole_json_fn, jetzt)
    ergebnis["_nachfassungen"] = nachfassungen(zustand, protokoll, hole_json_fn, jetzt)
    return ergebnis


# ------------------------------------------------------------- Herzschlag

def herzschlag(live_dir: Path | None, art: str = "herzschlag", **extra) -> None:
    """Watchdog-Lebenszeichen nach data/live/<profil>/bot_events.jsonl."""
    if live_dir is None:
        return
    live_dir.mkdir(parents=True, exist_ok=True)
    zeile = {"wall_ts_utc": _iso(_jetzt()), "art": art, **extra}
    with (live_dir / "bot_events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(zeile, ensure_ascii=False) + "\n")


# -------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None, holer: Holer = hole, hole_json_fn: JsonHoler = hole_json,
         schlaf: Callable[[float], None] = time.sleep) -> int:
    ap = argparse.ArgumentParser(description="Quellen-Wache (read-only Aenderungs-Rekorder)")
    ap.add_argument("--einmal", action="store_true", help="ein Zyklus ueber alle Quellen")
    ap.add_argument("--takt-s", type=float, default=SCHLEIFE_MIN_S,
                    help="Schleifen-Pause; je Quelle gilt zusaetzlich ihr eigener takt_s")
    ap.add_argument("--live", action="store_true",
                    help="Watchdog-Modus: BOT_PROFIL, start.lock, bot.pid, Herzschlag")
    ap.add_argument("--quellen", type=Path, help="JSON mit {name: {url, art, takt_s, markt_event_id}}")
    ap.add_argument("--wurzel", type=Path, default=STANDARD_WURZEL)
    ap.add_argument("--max-zyklen", type=int, default=0, help="0 = endlos (Tests: begrenzen)")
    args = ap.parse_args(argv)

    live_dir: Path | None = None
    wurzel = args.wurzel
    if args.live:
        profil = os.environ.get("BOT_PROFIL", "quellen_wache")
        wurzel = Path(os.environ.get("THESIS_LIVE_ROOT", "data/live")) / profil
        live_dir = wurzel
        from operations.pipeline.startwache import wache_nehmen
        if not wache_nehmen(live_dir):
            print(f"{profil}: andere Instanz haelt start.lock - Ende.")
            return 0
        herzschlag(live_dir, art="start", takt_s=args.takt_s)

    quellen = lade_quellen(args.quellen)
    zustand_pfad = wurzel / "zustand.json"
    protokoll = wurzel / "ereignisse.jsonl"
    zustand = lade_zustand(zustand_pfad)
    letzter_herzschlag = time.time()
    zyklen = 0
    while True:
        ergebnis = ein_zyklus(quellen, zustand, protokoll, holer, hole_json_fn)
        schreibe_zustand(zustand_pfad, zustand)
        zyklen += 1
        interessant = {k: v for k, v in ergebnis.items()
                       if v not in ("unveraendert", "nicht_faellig") and not k.startswith("_")}
        if interessant or args.einmal:
            print(f"[{_iso(_jetzt())}] Zyklus {zyklen}: "
                  + (", ".join(f"{k}={v}" for k, v in interessant.items()) or "keine Aenderung")
                  + (f", {ergebnis['_nachfassungen']} Nachfassungen"
                     if ergebnis.get("_nachfassungen") else ""))
        if args.einmal or (args.max_zyklen and zyklen >= args.max_zyklen):
            break
        if live_dir is not None and time.time() - letzter_herzschlag >= HERZSCHLAG_S:
            herzschlag(live_dir, quellen=len(quellen), zyklen=zyklen)
            letzter_herzschlag = time.time()
        schlaf(max(args.takt_s, 1.0))
    if live_dir is not None:
        herzschlag(live_dir, art="fertig", zyklen=zyklen)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
