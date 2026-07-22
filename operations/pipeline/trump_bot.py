"""Trump-Post-Bot: Truth-Social-Feed -> Wort-Matching -> YES-Kaeufe.

Woechentliche Serie trump-post-weekly (z.B. Event 690224, 13.-19.07. ET).
NUR YES, wie beim Elon-Bot: die NO-Seite konvergiert die ganze Woche
gegen 1, der Edge liegt im Fenster zwischen Trumps Post und der
Markt-Einpreisung. Marktregeln sind wortgleich zur Elon-Serie ->
ElonMatcher und baue_elon_rules werden wiederverwendet (strikt =
Auto-Kauf; Compound-Substring = nur verdacht-Event; Bild-Posts = nur
medien_hinweis, kein OCR).

Quelle: oeffentliche Truth-API via curl_cffi-Chrome-Impersonation
(truth_watch.py) — kein Login, keine Cookies. Startscan holt beim
Start die Historie seit Periodenstart (faengt vom Markt uebersehene
Woerter, Birth-Tourism-Muster), danach since_id-Polling.

Aufruf:
  BOT_PROFIL=trump_july13 python -m operations.pipeline.trump_bot [--live]
"""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone

from operations.pipeline import config, startwache
from operations.pipeline.decision import entscheide_yes, nach_edge_sortiert
from operations.pipeline.elon_bot import ElonMatcher, baue_elon_rules
from operations.pipeline.orderbook import (
    best_ask,
    fetch_book,
    log_snapshots,
    now_utc_iso,
)
from operations.pipeline.truth_watch import TruthFehler, TruthPost, TruthWatcher

_GEFUELLT = ("dry_run_fill", "live_fill", "live_partial")


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


def hole_startscan(watcher, start_dt: datetime, max_seiten: int = 40,
                   seiten_pause_s: float = 5.0) -> list[TruthPost]:
    """Alle Posts seit Periodenstart (rueckwaerts paginiert, testbar).

    Die API liefert neueste zuerst; wir blaettern mit max_id, bis ein
    Post VOR dem Periodenstart auftaucht oder eine Seite leer ist.
    Zwischen den Seiten wird pausiert: Cloudflare drosselt schnelle
    Request-Folgen mit 429 (Befund 18.07. beim Smoke-Test).
    """
    posts: list[TruthPost] = []
    max_id: int | None = None
    for _ in range(max_seiten):
        seite = watcher.hole_posts(max_id=max_id)
        if not seite:
            break
        fertig = False
        for p in seite:
            if _utc(p.created_utc) < start_dt:
                fertig = True
                break
            posts.append(p)
        if fertig:
            break
        max_id = min(p.post_id for p in seite)
        if seiten_pause_s > 0:
            time.sleep(seiten_pause_s)
    return posts


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
    verdacht_gemeldet: set[str] = set()
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
                        and e.get("status") in _GEFUELLT):
                    getradet.add(str(e.get("market_id")))

    _schreibe_event("start", {
        "modus": modus, "aktive_maerkte": len(rules),
        "bereits_getradet": sorted(getradet),
        "periode": [config.PERIODE_START_UTC, config.PERIODE_ENDE_UTC],
    })
    print(f"[{modus}] Trump-Bot: {len(rules)} Maerkte, "
          f"Periode bis {config.PERIODE_ENDE_UTC}.")

    def verarbeite(p: TruthPost, quelle: str) -> None:
        wann = _utc(p.created_utc)
        if wann < start or wann > ende or p.ist_repost:
            return
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
        for k in nach_edge_sortiert(treffer):
            r, book = k["rule"], k["book"]
            try:
                d = entscheide_yes(r, 1, k["best_ask"])
                res = executor.place(d, book)
                if res.status in _GEFUELLT:
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

    watcher = TruthWatcher(config.TRUTH_USER_ID)
    gesehen: set[int] = set()
    seit_id: int | None = None
    startscan_fertig = False
    letzter_buchlog = 0.0
    backoff_s = 0.0

    while True:
        if _stop():
            _schreibe_event("stop", {"grund": "STOP-Datei"})
            print("Kill-Switch aktiv, beende.")
            return
        if datetime.now(timezone.utc) > ende:
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
                _schreibe_event("fehler", {"wo": "buchlog",
                                           "fehler": str(ex)})
            letzter_buchlog = jetzt

        try:
            if not startscan_fertig:
                posts = hole_startscan(watcher, start)
                quelle = "startscan"
                _schreibe_event("startscan", {"posts": len(posts)})
                startscan_fertig = True
            else:
                posts = watcher.hole_posts(since_id=seit_id)
                quelle = "poll"
            backoff_s = 0.0
        except TruthFehler as ex:
            # 403/429: Cloudflare drosselt -> exponentiell strecken,
            # nie blacken (Ratelimit-Lehre vom Elon-Texas-Fall).
            backoff_s = min(300.0, max(30.0, backoff_s * 2))
            _schreibe_event("warnung", {
                "wo": "truth_poll", "status": ex.status,
                "backoff_s": backoff_s})
            time.sleep(backoff_s)
            continue
        except Exception as ex:  # noqa: BLE001
            backoff_s = min(300.0, max(15.0, backoff_s * 2))
            _schreibe_event("fehler", {"wo": "truth_poll",
                                       "fehler": str(ex),
                                       "backoff_s": backoff_s})
            time.sleep(backoff_s)
            continue

        for p in posts:
            if p.post_id in gesehen:
                continue
            gesehen.add(p.post_id)
            verarbeite(p, quelle)
        if posts:
            seit_id = max(seit_id or 0, max(p.post_id for p in posts))

        time.sleep(config.TRUTH_POLL_S)


def refresh_snapshot() -> None:
    """Aktualisiert den Gamma-Snapshot des konfigurierten Events."""
    import httpx

    r = httpx.get(config.GAMMA_EVENT_URL, headers=config.HTTP_HEADERS,
                  timeout=60)
    r.raise_for_status()
    e = r.json()
    felder = ["id", "slug", "question", "conditionId", "description",
              "outcomes", "outcomePrices", "clobTokenIds", "bestAsk",
              "bestBid", "closed", "umaResolutionStatus"]
    snap = {
        "event_id": str(e.get("id") or config.EVENT_ID),
        "slug": e.get("slug"),
        "abgerufen_am_utc": now_utc_iso(),
        "markets": [{k: m.get(k) for k in felder}
                    for m in e.get("markets", [])],
    }
    config.GAMMA_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with open(config.GAMMA_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--live", action="store_true",
                   help="echte Orders (Standard: Dry-Run)")
    p.add_argument("--refresh-rules", action="store_true",
                   help="Gamma-Snapshot vor dem Start aktualisieren")
    argv = p.parse_args()
    if argv.refresh_rules:
        refresh_snapshot()
    lauf(live=argv.live)


if __name__ == "__main__":
    main()
