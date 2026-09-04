"""Fed-Text-Drop-Rekorder: Redetext gegen Polymarket-"Say"-Maerkte messen.

Misst, ob und wie schnell die Wortmaerkte einer Fed-Rede (Polymarket-Event
"What will Kevin Warsh say during ...") den PUBLIZIERTEN Redetext
einpreisen. Handelt nicht. Kein Order-Pfad, keine Keys, keine Wallet.

Befund, der das Modul begruendet (Retro 04.09.2026, Jackson-Hole-Rede
Warsh 28.08., Event 870938, CLOB-Minutenhistorie):

- Die Fed stellt den Redetext zum Redebeginn online: Feed-Eintrag
  "8/28/2026 10:00:00 AM", Seite `Last-Modified: 14:00:11 GMT` — elf
  Sekunden nach dem angesetzten Start.
- Eine Prognose allein aus dem Text traf 20 von 22 Wortmaerkten. Die zwei
  Abweichungen: "Good Morning" (Begruessung, nicht im Manuskript) und
  "Bitcoin/Crypto" (im Text, aber nicht gesprochen — Fussnote oder
  ausgelassene Passage).
- Der Markt preiste trotzdem WORT FUER WORT beim Sprechen: CapEx stand
  20 Minuten bei 0.49, obwohl das Wort im Text stand; Bank/Asset 10+
  sprang erst nach 28 Minuten; "Framework" (0.74, im Text nicht
  vorhanden) zerfiel erst ab Minute 26. Sieben mittelpreisige Woerter
  resolvten NO — alle bei 14:00:11 aus dem Text erkennbar.

Das ist die Gegenlage zu Earnings-Calls und Trump-Reden, wo der Markt
gehoerte Woerter in 1-4 s einpreist (Uebergabe 28.07.): Hier existiert
eine TEXTQUELLE mit Minuten Vorlauf, die die Crowd nicht liest. Ob das
wiederkehrend gilt (naechste Gelegenheiten: FOMC-Statement 14:00 ET und
Eroeffnungs-Statement der Pressekonferenz 14:30 ET am 16.09., jede
Warsh-Rede mit Polymarket-Event), misst dieser Rekorder.

Messdesign:

1. Quelle: entweder eine feste URL (Redeseite oder PDF) oder der
   Fed-JSON-Feed `ne-speeches.json` (neuer Eintrag zu Sprecher + Datum
   liefert den Link). Die Quelle wird im Takt TAKT_S gepollt, bis sie
   200 liefert und der extrahierte Text laenger als MIN_TEXTLAENGE ist.
2. `text_da`: Erkennungszeit, `Last-Modified`, Textlaenge, Anzahl Polls.
   Fussnoten/Referenzen werden abgeschnitten (Fussnoten zaehlen nicht als
   gesprochen; Abweichung Bitcoin/Crypto).
3. Prognose je Markt aus dem Text mit denselben Regeln wie die Bots
   (`market_rules.build_rules`, `counter_engine.compile_patterns`):
   Anzahl, Schwelle, YES/NO.
4. Buch-Nachlauf: best bid/ask je Markt (CLOB /book) vor dem Warten
   (Baseline), bei Erkennung und danach alle BUCH_TAKT_S fuer
   NACHLAUF_MIN Minuten.
5. `--auswerte`: je Markt Vor-Mid, Prognose, Minuten bis zum ersten
   Sprung um SPRUNG — die Vorlauf-Verteilung wie bei ISW/DeepState.

Aufruf:

    python -m operations.pipeline.fed_text_rekorder --event 870938 \
        --quelle https://www.federalreserve.gov/newsevents/speech/warsh20260828a.htm \
        --ab 2026-08-28T13:55:00Z --nachlauf-min 45
    python -m operations.pipeline.fed_text_rekorder --event <id> \
        --feed-sprecher Warsh --feed-datum 9/16/2026 --ab 2026-09-16T18:25:00Z
    python -m operations.pipeline.fed_text_rekorder --auswerte \
        data/live/fed_text_rekorder/870938/ereignisse.jsonl
"""

from __future__ import annotations

import argparse
import html as htmlmod
import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from operations.pipeline.counter_engine import compile_patterns, count_in_text
from operations.pipeline.market_rules import MarketRule, build_rules

GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
FED_FEED = "https://www.federalreserve.gov/json/ne-speeches.json"
UA = {"User-Agent": "ba-thesis fed_text_rekorder (read-only)"}

TAKT_S = 1.0            # Polltakt auf die Quelle, bis der Text erscheint
BUCH_TAKT_S = 5.0       # Buch-Snapshots im Nachlauf
NACHLAUF_MIN = 45
MIN_TEXTLAENGE = 2000   # Redeseiten unter 2000 Zeichen sind Platzhalter
SPRUNG = 0.25           # |Mid - Vor-Mid| fuer die Vorlauf-Auswertung
FEED_TAKT_S = 5.0
WARTE_MELDUNG_ALLE = 60  # Polls zwischen zwei "quelle_wartet"-Zeilen

STANDARD_WURZEL = Path("data/live/fed_text_rekorder")

# Fed-Redeseiten: Artikelspalte, dahinter Fussnoten/Referenzen.
_ARTIKEL = re.compile(r'<div[^>]+class="col-xs-12 col-sm-8 col-md-8"[^>]*>(.*)', re.S)
_FUSSNOTEN = re.compile(
    r'<div[^>]+class="[^"]*footnotes?[^"]*"|<h\d[^>]*>\s*(?:References|Footnotes|Notes)\s*</h\d>'
    r'|<p[^>]*>\s*<strong>\s*(?:References|Footnotes)\s*</strong>',
    re.I)


@dataclass
class Antwort:
    status: int
    headers: dict
    body: bytes
    zeit_utc: str


@dataclass
class Prognose:
    market_id: str
    frage: str
    varianten: list[str]
    schwelle: int
    anzahl: int
    yes: bool
    status: str
    grund: str = ""


Holer = Callable[[str], Antwort]
JsonHoler = Callable[[str], object]


def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


# ------------------------------------------------------------------- HTTP

def hole(url: str) -> Antwort:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return Antwort(r.status, dict(r.headers), r.read(), _jetzt())
    except urllib.error.HTTPError as ex:
        return Antwort(ex.code, dict(ex.headers or {}), b"", _jetzt())
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        return Antwort(0, {"fehler": str(ex)}, b"", _jetzt())


def hole_json(url: str):
    a = hole(url)
    if a.status != 200:
        raise RuntimeError(f"HTTP {a.status} fuer {url}")
    return json.loads(a.body.decode("utf-8").lstrip("﻿"))


# ------------------------------------------------------------------- Text

def _pdf_text(body: bytes) -> str:
    try:
        from pypdf import PdfReader  # optional
    except ImportError:  # pragma: no cover - Umgebung ohne pypdf
        return ""
    import io
    reader = PdfReader(io.BytesIO(body))
    return " ".join((p.extract_text() or "") for p in reader.pages)


def extrahiere_text(body: bytes, content_type: str = "") -> str:
    """Gesprochener Text einer Redeseite/eines PDFs, ohne Fussnoten/Referenzen."""
    if body[:4] == b"%PDF" or "pdf" in (content_type or "").lower():
        roh = _pdf_text(body)
        cut = re.search(r"\n\s*(?:References|Footnotes)\s*\n", roh)
        if cut:
            roh = roh[:cut.start()]
        return re.sub(r"\s+", " ", roh).strip()
    seite = body.decode("utf-8", errors="replace")
    seite = re.sub(r"<script.*?</script>|<style.*?</style>", " ", seite, flags=re.S | re.I)
    m = _ARTIKEL.search(seite)
    if m:
        seite = m.group(1)
    cut = _FUSSNOTEN.search(seite)
    if cut:
        seite = seite[:cut.start()]
    text = htmlmod.unescape(re.sub(r"<[^>]+>", " ", seite))
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------- Prognose

def regeln_aus_event(event: dict) -> list[MarketRule]:
    return build_rules(event.get("markets") or [])


def prognosen(text: str, rules: list[MarketRule]) -> list[Prognose]:
    out = []
    for r in rules:
        if r.status != "active":
            out.append(Prognose(r.market_id, r.question, [], 0, 0, False, "skip", r.skip_grund))
            continue
        n = count_in_text(text, compile_patterns(r.varianten))
        out.append(Prognose(r.market_id, r.question, list(r.varianten), r.schwelle, n,
                            n >= r.schwelle, "active"))
    return out


# ------------------------------------------------------------------- Buch

def bestes_niveau(book: dict) -> tuple[float | None, float | None]:
    """Best bid / best ask aus einer CLOB-/book-Antwort."""
    def preise(seite):
        out = []
        for eintrag in book.get(seite) or []:
            try:
                out.append(float(eintrag.get("price")))
            except (TypeError, ValueError, AttributeError):
                continue
        return out
    bids, asks = preise("bids"), preise("asks")
    return (max(bids) if bids else None), (min(asks) if asks else None)


def buch_snapshot(rules: list[MarketRule], hole_json_fn: JsonHoler = hole_json) -> dict:
    buecher = {}
    for r in rules:
        if r.status != "active" or not r.yes_token_id:
            continue
        try:
            book = hole_json_fn(f"{CLOB}/book?token_id={r.yes_token_id}")
            bid, ask = bestes_niveau(book if isinstance(book, dict) else {})
        except Exception as ex:  # Buchfehler duerfen die Messung nicht stoppen
            bid, ask, book = None, None, {"fehler": str(ex)}
        buecher[r.market_id] = {"bid": bid, "ask": ask}
    return buecher


# -------------------------------------------------------------- Protokoll

def protokolliere(pfad: Path, eintrag: dict) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    eintrag = {"zeit_utc": _jetzt(), **eintrag}
    with open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------- Feed

def finde_im_feed(feed: list, sprecher: str, datum: str) -> str | None:
    """Link des Feed-Eintrags zu Sprecher + Datum ('9/16/2026'), sonst None.

    Der Fed-Feed traegt 'd' als 'M/D/YYYY h:mm:ss AM', 't' als Titel und
    'l' als Pfad; der Sprecher steht je nach Eintrag in 's' oder im Titel.
    """
    for e in feed or []:
        d = str(e.get("d") or "")
        beschreibung = " ".join(str(e.get(k) or "") for k in ("s", "t", "l")).lower()
        if d.startswith(datum) and sprecher.lower() in beschreibung:
            return e.get("l")
    return None


def _absolut(link: str) -> str:
    return "https://www.federalreserve.gov" + link if link.startswith("/") else link


# ----------------------------------------------------------------- Ablauf

def warte_auf_text(url: str, holer: Holer, takt_s: float, deadline: datetime | None,
                   protokoll: Path, schlaf: Callable[[float], None] = time.sleep,
                   uhr: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
    """Pollt die Quelle, bis Text da ist. Liefert (text, meta) oder None."""
    polls = 0
    while True:
        a = holer(url)
        polls += 1
        if a.status == 200 and a.body:
            text = extrahiere_text(a.body, a.headers.get("Content-Type", ""))
            if len(text) >= MIN_TEXTLAENGE:
                meta = {"art": "text_da", "url": url, "erkannt_utc": a.zeit_utc,
                        "last_modified": a.headers.get("Last-Modified"),
                        "textlaenge": len(text), "polls": polls}
                protokolliere(protokoll, meta)
                return text, meta
        if polls % WARTE_MELDUNG_ALLE == 0:
            protokolliere(protokoll, {"art": "quelle_wartet", "url": url,
                                      "status": a.status, "polls": polls})
        if deadline is not None and uhr() >= deadline:
            protokolliere(protokoll, {"art": "abbruch_deadline", "url": url, "polls": polls})
            return None
        schlaf(takt_s)


def nachlauf(rules: list[MarketRule], dauer_min: float, takt_s: float, protokoll: Path,
             hole_json_fn: JsonHoler = hole_json, schlaf: Callable[[float], None] = time.sleep,
             uhr: Callable[[], float] = time.time) -> int:
    start = uhr()
    n = 0
    while uhr() - start < dauer_min * 60:
        protokolliere(protokoll, {"art": "buch", "phase": "nachlauf",
                                  "buecher": buch_snapshot(rules, hole_json_fn)})
        n += 1
        schlaf(takt_s)
    return n


def _mid(b: dict) -> float | None:
    if b.get("bid") is None or b.get("ask") is None:
        return None
    return (float(b["bid"]) + float(b["ask"])) / 2


def _parse_zeit(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def auswerte(protokoll: Path) -> list[dict]:
    """Je Markt: Vor-Mid, Prognose, Minuten bis zum ersten Sprung um SPRUNG."""
    zeilen = [json.loads(z) for z in protokoll.read_text(encoding="utf-8").splitlines() if z.strip()]
    text_da = next((z for z in zeilen if z.get("art") == "text_da"), None)
    prog = next((z for z in zeilen if z.get("art") == "prognose"), None)
    buecher = [z for z in zeilen if z.get("art") == "buch"]
    if text_da is None or prog is None:
        return []
    t0 = _parse_zeit(text_da["zeit_utc"])
    vorher = [b for b in buecher if _parse_zeit(b["zeit_utc"]) <= t0]
    nachher = [b for b in buecher if _parse_zeit(b["zeit_utc"]) > t0]
    basis = vorher[-1] if vorher else (nachher[0] if nachher else None)
    out = []
    for p in prog.get("prognosen") or []:
        mid0 = _mid((basis or {}).get("buecher", {}).get(p["market_id"], {})) if basis else None
        minuten = None
        if mid0 is not None:
            for b in nachher:
                m = _mid(b.get("buecher", {}).get(p["market_id"], {}))
                if m is not None and abs(m - mid0) >= SPRUNG:
                    minuten = round((_parse_zeit(b["zeit_utc"]) - t0).total_seconds() / 60, 1)
                    break
        out.append({"frage": p["frage"], "prognose_yes": p["yes"], "anzahl": p["anzahl"],
                    "schwelle": p["schwelle"], "mid_vor_text": mid0,
                    "minuten_bis_sprung": minuten, "status": p["status"]})
    return out


def _tabelle(zeilen: list[dict]) -> str:
    out = [f"{'Frage':<58} {'Progn.':>6} {'n':>3} {'S':>2} {'Mid vor':>8} {'min->Sprung':>12}"]
    for z in zeilen[:50]:
        mid = f"{z['mid_vor_text']:.3f}" if z["mid_vor_text"] is not None else "-"
        mins = z["minuten_bis_sprung"] if z["minuten_bis_sprung"] is not None else "-"
        out.append(f"{z['frage'][:58]:<58} {'YES' if z['prognose_yes'] else 'NO':>6} "
                   f"{z['anzahl']:>3} {z['schwelle']:>2} {mid:>8} {str(mins):>12}")
    return "\n".join(out)


def _schlafe_bis(ab: datetime, schlaf: Callable[[float], None], uhr) -> None:
    while True:
        rest = (ab - uhr()).total_seconds()
        if rest <= 0:
            return
        schlaf(min(rest, 30.0))


def main(argv: list[str] | None = None, holer: Holer = hole, hole_json_fn: JsonHoler = hole_json,
         schlaf: Callable[[float], None] = time.sleep,
         uhr: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--event", help="Gamma-Event-ID des Say-Markts")
    ap.add_argument("--quelle", help="URL der Redeseite / des PDFs")
    ap.add_argument("--feed-sprecher", help="Sprecher fuer die Feed-Suche (z. B. Warsh)")
    ap.add_argument("--feed-datum", help="Datum im Feed-Format M/D/YYYY (z. B. 9/16/2026)")
    ap.add_argument("--ab", help="fruehester Pollbeginn, ISO-UTC (z. B. 2026-09-16T18:25:00Z)")
    ap.add_argument("--deadline", help="Abbruch, wenn bis dahin kein Text (ISO-UTC)")
    ap.add_argument("--takt-s", type=float, default=TAKT_S)
    ap.add_argument("--buch-takt-s", type=float, default=BUCH_TAKT_S)
    ap.add_argument("--nachlauf-min", type=float, default=NACHLAUF_MIN)
    ap.add_argument("--wurzel", type=Path, default=STANDARD_WURZEL)
    ap.add_argument("--einmal", action="store_true", help="kein Nachlauf (Smoke-Test)")
    ap.add_argument("--auswerte", type=Path, help="Protokoll auswerten statt aufzeichnen")
    args = ap.parse_args(argv)

    if args.auswerte:
        zeilen = auswerte(args.auswerte)
        print(_tabelle(zeilen) if zeilen else "Protokoll ohne text_da/prognose.")
        return 0

    if not args.event or not (args.quelle or (args.feed_sprecher and args.feed_datum)):
        ap.error("--event und (--quelle oder --feed-sprecher + --feed-datum) sind noetig")

    event = hole_json_fn(f"{GAMMA}/events/{args.event}")
    rules = regeln_aus_event(event if isinstance(event, dict) else {})
    protokoll = args.wurzel / str(args.event) / "ereignisse.jsonl"
    protokolliere(protokoll, {"art": "start", "event": str(args.event), "titel": event.get("title"),
                              "n_regeln": sum(1 for r in rules if r.status == "active"),
                              "quelle": args.quelle, "feed_sprecher": args.feed_sprecher,
                              "feed_datum": args.feed_datum})
    protokolliere(protokoll, {"art": "buch", "phase": "vor_text",
                              "buecher": buch_snapshot(rules, hole_json_fn)})

    if args.ab:
        _schlafe_bis(_parse_zeit(args.ab), schlaf, uhr)
    deadline = _parse_zeit(args.deadline) if args.deadline else None

    url = args.quelle
    if not url:
        while True:
            try:
                link = finde_im_feed(hole_json_fn(FED_FEED), args.feed_sprecher, args.feed_datum)
            except Exception as ex:
                link = None
                protokolliere(protokoll, {"art": "feed_fehler", "fehler": str(ex)})
            if link:
                url = _absolut(link)
                protokolliere(protokoll, {"art": "feed_treffer", "url": url})
                break
            if deadline is not None and uhr() >= deadline:
                protokolliere(protokoll, {"art": "abbruch_deadline", "quelle": "feed"})
                return 1
            schlaf(FEED_TAKT_S)

    ergebnis = warte_auf_text(url, holer, args.takt_s, deadline, protokoll, schlaf, uhr)
    if ergebnis is None:
        return 1
    text, _meta = ergebnis
    prog = prognosen(text, rules)
    protokolliere(protokoll, {"art": "prognose", "prognosen": [asdict(p) for p in prog]})
    protokolliere(protokoll, {"art": "buch", "phase": "bei_text",
                              "buecher": buch_snapshot(rules, hole_json_fn)})
    print(f"Text da ({len(text)} Zeichen). Prognosen:")
    for p in prog[:50]:
        print(f"  {p.frage[:60]:<60} {p.anzahl:>3}/{p.schwelle:<3} -> {'YES' if p.yes else 'NO'}"
              f"{'' if p.status == 'active' else '  [skip: ' + p.grund + ']'}")
    if not args.einmal:
        nachlauf(rules, args.nachlauf_min, args.buch_takt_s, protokoll, hole_json_fn, schlaf)
        protokolliere(protokoll, {"art": "fertig"})
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
