"""Elon-Post-Bot: X-Feed -> Wort-Matching -> YES-Kaeufe (Event 690237).

NUR YES (User-Vorgabe 13.7.): die NO-Seite konvergiert die ganze Woche
gegen 1 — dort gibt es keinen Geschwindigkeits-Edge. Der Edge liegt im
Fenster zwischen Elons Post und der Markt-Einpreisung.

Matching nach Marktregeln (siehe config-Profile elon_*, aktuell
elon_july20 fuer Event 715491):
- STRIKT (loest Auto-Kauf aus): exaktes Wort, Plural/Possessiv, jede
  Gross-/Kleinschreibung, Sigil davor (#/@/$). Angrenzende Buchstaben,
  Ziffern oder Unterstriche blocken (deckt "Misspellings zaehlen nicht"
  und "Symbole im Wort disqualifizieren" ab).
- VERDACHT (nur Event, kein Auto-Kauf): Begriff steckt als Substring in
  einem groesseren Wort (Compounds zaehlen laut Regel, Ableitungen
  nicht — per Regex nicht trennbar -> manuell entscheiden).
- Bild-Posts: Text in Bildern zaehlt laut Regel, wird hier aber nicht
  ausgewertet (kein OCR) — Medien-Posts werden als Hinweis geloggt.

Cookies: X_AUTH_TOKEN und X_CT0 in .env. Fehlen sie, wartet der Bot und
laedt .env jede Minute neu (Handel startet dann automatisch).

Aufruf:
  BOT_PROFIL=elon_july20 python -m operations.pipeline.elon_bot [--live]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone

from operations.pipeline import config, startwache
from operations.pipeline.decision import (
    entscheide_yes,
    nach_edge_sortiert,
)
from operations.pipeline.market_rules import (
    MarketRule,
    _token_ids,
    parse_zitierte_begriffe,
)
from operations.pipeline.orderbook import best_ask, fetch_book, log_snapshots, now_utc_iso
from operations.pipeline.x_watch import (
    ApifyReplyFetcher,
    AuthFehler,
    RateLimit,
    XPost,
    XWatcher,
)


def _schreibe_event(art: str, daten: dict) -> None:
    pfad = config.LIVE_DIR / "bot_events.jsonl"
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps(
            {"wall_ts_utc": now_utc_iso(), "art": art, **daten},
            ensure_ascii=False,
        ) + "\n")


def _stop() -> bool:
    return config.STOP_FILE.exists()


def _utc(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc)


def baue_elon_rules() -> list[MarketRule]:
    """Regeln fuer die Elon-Post-Maerkte direkt aus dem Snapshot.

    Bewusst NICHT market_rules.build_rule: dessen Ausnahme-Skip ("only
    if" in der Beschreibung) wuerde hier jeden Markt verwerfen — die
    "only if"-Klausel ist Standard-Boilerplate der Elon-Serie (Bildtext-
    Regel) und wurde manuell geprueft (13.7.). Geschlossene Maerkte
    (z.B. "Claude", bereits 1.00) werden uebersprungen.
    """
    with open(config.GAMMA_SNAPSHOT, encoding="utf-8") as f:
        snap = json.load(f)
    rules = []
    for m in snap["markets"]:
        frage = m.get("question") or ""
        begriffe = parse_zitierte_begriffe(frage)
        yes_id, no_id = _token_ids(m)
        if m.get("closed") or not begriffe or not yes_id:
            continue
        rules.append(MarketRule(
            market_id=str(m.get("id")), slug=m.get("slug", ""),
            question=frage, varianten=begriffe, schwelle=1,
            yes_token_id=yes_id, no_token_id=no_id,
            homophon_sensitiv=False,  # Text-Matching, kein ASR
            status="active",
            resolution_hinweis=(m.get("description") or "")[:400],
        ))
    return rules


def _strikt_pattern(begriff: str) -> re.Pattern:
    """Wort mit Plural/Possessiv, Sigils davor ok, sonst harte Grenzen."""
    kern = re.escape(begriff.strip())
    kern = kern.replace(r"\ ", r"[\s\-]+")  # "Video game" / "video-game"
    suffix = r"(?:['’]s|s['’]|es|s)?"
    return re.compile(
        rf"(?<![A-Za-z0-9_]){kern}{suffix}(?![A-Za-z0-9_])", re.IGNORECASE)


def _verdacht_pattern(begriff: str) -> re.Pattern | None:
    """Substring-Pattern fuer Compound-Kandidaten (Ein-Wort, >=3)."""
    v = begriff.strip()
    if len(v) < 3 or not v.isalpha():
        return None
    return re.compile(re.escape(v), re.IGNORECASE)


class ElonMatcher:
    def __init__(self, rule: MarketRule) -> None:
        self.rule = rule
        self.strikt = [_strikt_pattern(b) for b in rule.varianten]
        self.verdacht = [p for p in
                         (_verdacht_pattern(b) for b in rule.varianten) if p]

    def pruefe(self, text: str) -> tuple[bool, bool]:
        """(strikter Treffer, Verdachts-Treffer-ohne-Strikt)."""
        strikt = any(p.search(text) for p in self.strikt)
        if strikt:
            return True, False
        return False, any(p.search(text) for p in self.verdacht)


def lauf(live: bool) -> None:
    # Startwache VOR allem Setup (Vorfall 22.7., lemonade_july22):
    # zweite Instanz desselben Profils beendet sich sofort; der Gewinner
    # schreibt bot.pid atomar, bevor das Setup beginnt.
    if not startwache.wache_nehmen(config.LIVE_DIR):
        _schreibe_event("doppelstart_abgebrochen", {
            "grund": "start.lock belegt — andere Instanz laeuft/startet",
            "verlierer_pid": os.getpid(),
        })
        print("Startwache belegt (andere Instanz laeuft) — beende.")
        return
    from operations.pipeline.execution import DryRunExecutor, LiveExecutor

    executor = LiveExecutor() if live else DryRunExecutor()
    modus = "LIVE" if live else "DRY_RUN"
    rules = baue_elon_rules()
    matcher = {r.market_id: ElonMatcher(r) for r in rules}
    getradet: set[str] = set()
    verdacht_gemeldet: set[str] = set()  # f"{market_id}:{post_id}"
    start = _utc(config.PERIODE_START_UTC)
    ende = _utc(config.PERIODE_ENDE_UTC)

    # Neustart-Schutz: bereits gekaufte Maerkte aus dem Event-Log.
    ev_pfad = config.LIVE_DIR / "bot_events.jsonl"
    if ev_pfad.exists():
        with open(ev_pfad, encoding="utf-8") as f:
            for zeile in f:
                try:
                    e = json.loads(zeile)
                except json.JSONDecodeError:
                    continue
                if (e.get("art") == "yes_entscheidung"
                        and e.get("action") == "YES"
                        and e.get("status") in ("dry_run_fill", "live_fill",
                                                "live_partial")):
                    getradet.add(str(e.get("market_id")))

    _schreibe_event("start", {
        "modus": modus, "aktive_maerkte": len(rules),
        "bereits_getradet": sorted(getradet),
        "periode": [config.PERIODE_START_UTC, config.PERIODE_ENDE_UTC],
    })
    print(f"[{modus}] Elon-Bot: {len(rules)} Maerkte, "
          f"Periode bis {config.PERIODE_ENDE_UTC}.")

    watcher: XWatcher | None = None
    gesehen: set[int] = set()
    startscan_fertig = False
    letzte_abdeckung: bool | None = None
    letzter_buchlog = 0.0
    letzte_cookie_meldung = 0.0
    backoff_bis = 0.0
    # Optionaler Apify-Reply-Kanal: schliesst die Fremd-Reply-Luecke des
    # nativen Feeds. Nur aktiv, wenn APIFY_TOKEN in .env steht (sonst
    # keine externen Kosten). Laeuft alle APIFY_INTERVALL_S.
    apify: ApifyReplyFetcher | None = None
    apify_intervall_s = 300.0
    letzter_apify = 0.0

    def cookies_laden() -> tuple[str | None, str | None]:
        from dotenv import load_dotenv

        load_dotenv(config.REPO_ROOT / ".env", override=True)
        return os.environ.get("X_AUTH_TOKEN"), os.environ.get("X_CT0")

    def verarbeite(p: XPost, quelle: str) -> None:
        if p.post_id in gesehen:
            return
        gesehen.add(p.post_id)
        wann = _utc(p.created_utc)
        if wann < start or wann > ende or p.ist_repost:
            return
        # Phase 1: alle strikten Treffer sammeln (Buch/Ask), Verdacht loggen.
        treffer = []
        for r in rules:
            if r.market_id in getradet:
                continue
            strikt, verdacht = matcher[r.market_id].pruefe(p.text)
            if strikt:
                try:
                    book = fetch_book(r.yes_token_id)
                    treffer.append({"rule": r, "book": book,
                                    "best_ask": best_ask(book)})
                except Exception as ex:  # noqa: BLE001
                    _schreibe_event("fehler", {"wo": f"yes_fetch:{r.slug}",
                                               "fehler": str(ex)})
            elif verdacht:
                schluessel = f"{r.market_id}:{p.post_id}"
                if schluessel not in verdacht_gemeldet:
                    verdacht_gemeldet.add(schluessel)
                    _schreibe_event("verdacht", {
                        "markt": r.slug, "post_id": str(p.post_id),
                        "post_utc": p.created_utc,
                        "text_auszug": p.text[:180],
                        "hinweis": ("Substring-Treffer (Compound zaehlt, "
                                    "Ableitung nicht) — manuell pruefen"),
                    })
        # Phase 2: bei mehreren Treffern in EINEM Post (z.B. "Tesla Bitcoin")
        # edge-sortiert kaufen — billigster Ask zuerst aus dem geteilten Pool.
        for k in nach_edge_sortiert(treffer):
            r, book = k["rule"], k["book"]
            try:
                d = entscheide_yes(r, 1, k["best_ask"])
                res = executor.place(d, book)
                if res.status in ("dry_run_fill", "live_fill",
                                  "live_partial"):
                    getradet.add(r.market_id)
                _schreibe_event("yes_entscheidung", {
                    "market_id": r.market_id, "markt": r.slug,
                    "post_id": str(p.post_id),
                    "post_utc": p.created_utc, "quelle": quelle,
                    "text_auszug": p.text[:180], "best_ask": k["best_ask"],
                    "action": d.action, "status": res.status,
                    "grund": d.reason,
                })
                print(f"TREFFER {r.slug[:40]}: {d.action}/{res.status} "
                      f"| {p.text[:60]!r}")
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": f"yes:{r.slug}",
                                           "fehler": str(ex)})
        if p.hat_medien:
            _schreibe_event("medien_hinweis", {
                "post_id": str(p.post_id), "post_utc": p.created_utc,
                "text_auszug": p.text[:120],
            })

    while True:
        if _stop():
            _schreibe_event("stop", {"grund": "STOP-Datei"})
            print("Kill-Switch aktiv, beende.")
            return
        jetzt_dt = datetime.now(timezone.utc)
        if jetzt_dt > ende:
            _schreibe_event("fertig", {
                "grund": "periodenende", "getradet": sorted(getradet)})
            print("Marktperiode vorbei, beende.")
            return

        jetzt = time.time()
        if jetzt - letzter_buchlog >= 300:
            try:
                zeilen = log_snapshots(rules, now_utc_iso())
                _schreibe_event("buchlog", {"n_zeilen": len(zeilen)})
            except Exception as ex:  # noqa: BLE001
                _schreibe_event("fehler", {"wo": "buchlog", "fehler": str(ex)})
            letzter_buchlog = jetzt

        if watcher is None:
            auth, ct0 = cookies_laden()
            if not auth or not ct0:
                if jetzt - letzte_cookie_meldung > 1800:
                    _schreibe_event("warte_auf_cookies", {
                        "hinweis": "X_AUTH_TOKEN/X_CT0 fehlen in .env"})
                    print("Warte auf X_AUTH_TOKEN/X_CT0 in .env ...")
                    letzte_cookie_meldung = jetzt
                time.sleep(60)
                continue
            watcher = XWatcher(auth, ct0, config.X_USER_ID)
            # Apify nur noch als Tiefen-Fallback: der native Feed liefert
            # ueber UserTweetsAndReplies+transaction-id bereits Fremd-
            # Replies. Apify nur zuschalten, wenn Token da UND explizit
            # gewuenscht (APIFY_REPLY_FALLBACK=1) — sonst keine Kosten.
            apify_token = os.environ.get("APIFY_TOKEN")
            if apify_token and os.environ.get("APIFY_REPLY_FALLBACK") == "1":
                apify = ApifyReplyFetcher(apify_token, config.X_USER_ID)
                _schreibe_event("apify_kanal_aktiv", {
                    "intervall_s": apify_intervall_s,
                    "hinweis": "Reply-Tiefen-Fallback via Apify"})
            _schreibe_event("x_watcher_bereit", {
                "apify_reply_kanal": apify is not None})

        if jetzt < backoff_bis:
            time.sleep(min(10.0, backoff_bis - jetzt))
            continue

        try:
            posts, cursor = watcher.hole_posts()
            # Reply-Abdeckung ueberwachen: faellt die Query auf UserTweets
            # zurueck (transaction-id nicht baubar / Algo gedreht), fehlen
            # Fremd-Replies — einmalig warnen.
            if not startscan_fertig:
                _schreibe_event("feed_modus", {
                    "query": watcher._query[0] if watcher._query else None,
                    "reply_abdeckung": watcher.reply_abdeckung,
                })
                if not watcher.reply_abdeckung:
                    _schreibe_event("warnung", {
                        "wo": "reply_abdeckung",
                        "txn_fehler": watcher._txn._fehler,
                        "letzter_fehler": watcher.letzter_fehler,
                        "hinweis": ("nur UserTweets aktiv — Fremd-Replies "
                                    "fehlen. transaction-id pruefen oder "
                                    "APIFY_REPLY_FALLBACK=1 setzen."),
                    })
                letzte_abdeckung = watcher.reply_abdeckung
            else:
                # Query-Wechsel sichtbar machen (Selbstheilung UserTweets
                # -> UserTweetsAndReplies, sobald die transaction-id wieder
                # baut). feed_modus loggt nur beim Start.
                if watcher.reply_abdeckung != letzte_abdeckung:
                    _schreibe_event("feed_wechsel", {
                        "query": (watcher._query[0]
                                  if watcher._query else None),
                        "reply_abdeckung": watcher.reply_abdeckung,
                    })
                    letzte_abdeckung = watcher.reply_abdeckung
            if not startscan_fertig:
                # Historie seit Periodenstart nachziehen. Seitenzahl je
                # Profil (config.X_STARTSCAN_SEITEN): ein Start mitten in
                # der Marktperiode muss weiter zurueckblaettern als ein
                # Start am Periodenanfang.
                seiten = 0
                alle = list(posts)
                while (cursor and seiten < config.X_STARTSCAN_SEITEN and alle
                       and _utc(alle[-1].created_utc) > start):
                    mehr, cursor = watcher.hole_posts(cursor)
                    if not mehr:
                        break
                    alle += mehr
                    seiten += 1
                _schreibe_event("startscan", {
                    "posts_geladen": len(alle),
                    "aeltester": alle[-1].created_utc if alle else None,
                    # Belegt beim Armieren mitten in der Periode, ob der
                    # Scan bis zum Periodenstart zurueckkam.
                    "seiten_geblaettert": seiten,
                    "seiten_max": config.X_STARTSCAN_SEITEN,
                    "erreicht_periodenstart": bool(
                        alle and _utc(alle[-1].created_utc) <= start),
                })
                startscan_fertig = True
                posts = alle
            for p in posts:
                verarbeite(p, "poll")

            # Apify-Reply-Kanal (nur mit Token): Fremd-Replies seit dem
            # letzten Lauf nachziehen.
            if apify is not None and jetzt - letzter_apify >= apify_intervall_s:
                try:
                    von = max(int(start.timestamp()),
                              int(jetzt - apify_intervall_s - 60))
                    bis = int(datetime.now(timezone.utc).timestamp())
                    reply_posts = apify.hole(von, bis, max_items=100)
                    neu = sum(1 for p in reply_posts if p.post_id not in gesehen)
                    for p in reply_posts:
                        verarbeite(p, "apify_reply")
                    _schreibe_event("apify_lauf", {
                        "geladen": len(reply_posts), "neu": neu})
                except Exception as ex:  # noqa: BLE001
                    _schreibe_event("fehler", {"wo": "apify",
                                               "fehler": str(ex)[:200]})
                letzter_apify = jetzt
        except RateLimit:
            _schreibe_event("ratelimit", {"backoff_s": 120})
            backoff_bis = time.time() + 120
        except AuthFehler as ex:
            _schreibe_event("auth_fehler", {
                "fehler": str(ex)[:200],
                "hinweis": "X-Cookies abgelaufen? .env aktualisieren.",
            })
            print("AUTH-FEHLER — Cookies pruefen. Neuer Versuch in 5 Min.")
            watcher = None  # .env neu laden, ggf. frische Cookies
            time.sleep(300)
        except Exception as ex:  # noqa: BLE001
            msg = str(ex)
            # Read-Timeout ist die transienteste Fehlerart (X-Endpoint
            # gelegentlich langsam, Befund 13.7.: ~1/5min). Kurzer Retry
            # statt 45s Pause -> Blindfenster von ~65s auf ~20s.
            ist_timeout = ("timed out" in msg.lower()
                           or "timeout" in type(ex).__name__.lower())
            _schreibe_event("fehler", {"wo": "x_poll", "fehler": msg[:200],
                                       "timeout": ist_timeout})
            backoff_bis = time.time() + (8 if ist_timeout else 45)

        # Adaptives Pacing (Fix 15.7.): X deckelt UserTweetsAndReplies je
        # 15-min-Fenster; der 5s-Poll erschoepft es regelmaessig. Der alte
        # "bis Reset schlafen"-Guard verursachte 10-Min-Blackouts (Texas-
        # Post 15.7. dadurch 9 Min zu spaet erkannt -> Ask weg). Statt am
        # Fensterende voll zu schlafen, die VERBLEIBENDEN Requests
        # gleichmaessig ueber das Restfenster strecken: bei gesundem Budget
        # 5s-Takt, bei knappem Budget graduell langsamer (aber NIE Blackout,
        # NIE 429). Self-correcting — nutzt das echte remaining/reset.
        pause = config.X_POLL_S
        if (watcher is not None and watcher.rate_remaining is not None
                and watcher.rate_reset):
            rest_s = max(0.0, watcher.rate_reset - time.time())
            nutzbar = watcher.rate_remaining - 2  # 2 Puffer gegen 429
            if nutzbar <= 0:
                # Budget erschoepft (durch Spreading praktisch nie): bis
                # Reset warten, aber in <=60s-Haeppchen, damit ein frueher
                # Reset schnell erkannt wird (nicht 10 Min blind).
                pause = min(max(rest_s + 2, config.X_POLL_S), 60.0)
            else:
                pause = max(config.X_POLL_S, rest_s / nutzbar)
            if pause > config.X_POLL_S + 1:
                _schreibe_event("rate_pace", {
                    "pause_s": round(pause, 1),
                    "remaining": watcher.rate_remaining,
                    "rest_s": round(rest_s)})
        time.sleep(pause)


def refresh_snapshot() -> None:
    import httpx

    r = httpx.get(config.GAMMA_EVENT_URL, headers=config.HTTP_HEADERS,
                  timeout=60)
    r.raise_for_status()
    e = r.json()
    felder = ["id", "slug", "question", "conditionId", "description",
              "outcomes", "outcomePrices", "clobTokenIds", "bestAsk",
              "bestBid", "closed", "umaResolutionStatus"]
    snap = {
        "event_id": str(e.get("id")),
        "slug": e.get("slug"),
        "abgerufen_am_utc": now_utc_iso(),
        "markets": [{k: m.get(k) for k in felder} for m in e.get("markets", [])],
    }
    config.GAMMA_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with open(config.GAMMA_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)


def main() -> None:
    import sys

    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--live", action="store_true",
                        help="ECHTE Orders (sonst Dry-Run)")
    parser.add_argument("--refresh-rules", action="store_true")
    argv = parser.parse_args()

    if argv.refresh_rules or not config.GAMMA_SNAPSHOT.exists():
        refresh_snapshot()
    lauf(live=argv.live)


if __name__ == "__main__":
    main()
