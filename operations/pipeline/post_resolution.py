"""Auswertung nach Aufloesung: Pipeline-Wissen vs. Markt vs. eigene Fills.

Je gehandeltem/entscheidbarem Markt:
- Zeitstempel, zu dem die Pipeline den Zielstand kannte (Chunk-Event-Log),
- Markt-Konvergenz (CLOB-Minutenreihe, dauerhaft richtige Seite 0.9/0.1),
- eigene Fills (decisions_log.jsonl),
- Brutto-PnL: Fill-Shares * (Payout - Preis), ohne Gebuehren/Slippage-
  Modellierung. Dry-Run-Fills sind simulierte Fills (Annahme dokumentiert).

Aufruf nach Marktaufloesung:
  python -m operations.pipeline.post_resolution
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone

from operations.pipeline import config
from operations.pipeline.market_rules import lade_snapshot_rules


def _lade_jsonl(pfad) -> list[dict]:
    if not pfad.exists():
        return []
    with open(pfad, encoding="utf-8") as f:
        return [json.loads(z) for z in f if z.strip()]


def _konvergenz_ts(token_id: str, start_epoch: int, end_epoch: int,
                   outcome_yes_gewann: bool) -> str | None:
    """Konvergenz der YES-Reihe wie in mentions_latency (Suffix-Regel)."""
    import httpx

    r = httpx.get(
        "https://clob.polymarket.com/prices-history",
        params={"market": token_id, "startTs": start_epoch,
                "endTs": end_epoch, "fidelity": 1},
        headers=config.HTTP_HEADERS, timeout=30,
    )
    r.raise_for_status()
    punkte = sorted((int(h["t"]), float(h["p"])) for h in r.json().get("history", []))
    if not punkte:
        return None

    def korrekt(p: float) -> bool:
        return p >= 0.9 if outcome_yes_gewann else p <= 0.1

    start = None
    for t, p in reversed(punkte):
        if korrekt(p):
            start = t
        else:
            break
    if start is None:
        return None
    return datetime.fromtimestamp(start, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    import httpx

    r = httpx.get(config.GAMMA_EVENT_URL, headers=config.HTTP_HEADERS, timeout=60)
    r.raise_for_status()
    maerkte = {str(m["id"]): m for m in r.json().get("markets", [])}

    rules = {r_.market_id: r_ for r_ in lade_snapshot_rules()}
    events = _lade_jsonl(config.LIVE_DIR / "bot_events.jsonl")
    decisions = _lade_jsonl(config.LIVE_DIR / "decisions_log.jsonl")

    drop = next((e for e in events if e["art"] == "drop_erkannt"), None)
    drop_epoch = None
    if drop:
        drop_epoch = int(datetime.fromisoformat(
            drop["wall_ts_utc"].replace("Z", "+00:00")).timestamp())

    # Pipeline-Wissen: erster Chunk-Zeitstempel, an dem der Stand das Ziel
    # (YES) erreichte bzw. der letzte Chunk (NO-Wissen = Transkript-Ende).
    wissen: dict[str, dict] = {}
    for e in events:
        if e["art"] != "chunk":
            continue
        for slug, stand in e.get("staende", {}).items():
            w = wissen.setdefault(slug, {"final": 0, "ziel_ts": None})
            w["final"] = stand
            w["letzter_chunk_ts"] = e["wall_ts_utc"]
            rule = next((x for x in rules.values() if x.slug == slug), None)
            if rule is not None and w["ziel_ts"] is None:
                ziel = 1 if rule.schwelle <= 1 else rule.schwelle + config.YES_SCHWELLE_PUFFER
                if stand >= ziel:
                    w["ziel_ts"] = e["wall_ts_utc"]

    zeilen = []
    pnl_summe = 0.0
    for d in decisions:
        res = d["result"]
        if res["status"] not in ("dry_run_fill", "live_fill", "live_partial"):
            continue
        mid = res["market_id"]
        markt = maerkte.get(mid, {})
        rule = rules.get(mid)
        op = markt.get("outcomePrices")
        op = json.loads(op) if isinstance(op, str) else (op or [])
        yes_gewann = bool(op) and float(op[0]) > 0.99
        if not markt.get("closed"):
            payout = None
        else:
            gewonnen = (res["action"] == "YES") == yes_gewann
            payout = 1.0 if gewonnen else 0.0
        preis = float(res["limit_price"])
        shares = float(res["size_shares"])
        pnl = round(shares * (payout - preis), 2) if payout is not None else None
        if pnl is not None:
            pnl_summe += pnl

        konv = None
        if drop_epoch and rule is not None and markt.get("closed"):
            ende = drop_epoch + 6 * 86400
            try:
                konv = _konvergenz_ts(rule.yes_token_id, drop_epoch - 3600,
                                      ende, yes_gewann)
            except Exception:  # noqa: BLE001
                konv = None

        w = wissen.get(rule.slug if rule else "", {})
        zeilen.append({
            "market_id": mid,
            "slug": rule.slug if rule else "",
            "action": res["action"],
            "fill_status": res["status"],
            "fill_preis": preis,
            "fill_shares": shares,
            "fill_usd": res["size_usd"],
            "fill_ts_utc": d["wall_ts_utc"],
            "pipeline_wissen_ts_utc": (w.get("ziel_ts") if res["action"] == "YES"
                                       else w.get("letzter_chunk_ts")),
            "markt_konvergenz_ts_utc": konv,
            "aufgeloest": bool(markt.get("closed")),
            "yes_gewann": yes_gewann if markt.get("closed") else None,
            "pnl_brutto_usd": pnl,
        })

    pfad = config.LIVE_DIR / "post_resolution_auswertung.csv"
    if zeilen:
        with open(pfad, "w", newline="", encoding="utf-8") as f:
            w_ = csv.DictWriter(f, fieldnames=list(zeilen[0].keys()))
            w_.writeheader()
            w_.writerows(zeilen)
        print(f"Geschrieben: {pfad}")
    else:
        print("Keine Fills im Log — nichts auszuwerten.")
    offen = [z for z in zeilen if not z["aufgeloest"]]
    print(f"Fills: {len(zeilen)}, davon unaufgeloest: {len(offen)}")
    print(f"Brutto-PnL (aufgeloeste): {round(pnl_summe, 2)} USD "
          f"(Dry-Run-Fills sind simuliert)")


if __name__ == "__main__":
    main()
