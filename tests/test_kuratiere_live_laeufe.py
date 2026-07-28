"""Tests fuer die kuratierten Kopien der Live-Laeufe."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from operations.pipeline import daily_review_run as drr
from operations.pipeline import kuratiere_live_laeufe as kll

ROH_ENTSCHEIDUNG = {
    "wall_ts_utc": "2026-07-18T00:48:20Z",
    "decision": {
        "market_id": "2915475",
        "action": "YES",
        "token_id": "47900998634893562413140228299940745842076639687768198084780422581015272074160",
        "outcome": "Yes",
        "limit_price": 0.68,
        "reason": "count 4 >= ziel 1, ask 0.68 <= 0.9",
    },
    "result": {
        "market_id": "2915475",
        "action": "YES",
        "token_id": "479009986348935624131402282999407458420766396877681980847804",
        "limit_price": 0.68,
        "size_usd": 132.36,
        "size_shares": 147.06,
        "status": "live_fill",
        "detail": "Sweep: 2 Clips, ['0x4d335c329a5b:73.52941@<= 0.9']",
    },
    "book_snapshot": {
        "asks": [{"price": "0.99", "size": "205"}, {"price": "0.68", "size": "229.81"}],
        "bids": [{"price": "0.01", "size": "5"}, {"price": "0.63", "size": "129.83"}],
        "timestamp": "1784335630241",
        "min_order_size": "5",
        "neg_risk": False,
    },
}

ROH_EREIGNISSE = [
    {"wall_ts_utc": "t0", "art": "start", "profil": "allin_july17"},
    {"wall_ts_utc": "t1", "art": "buchlog", "ask": 0.68, "bid": 0.63},
    {"wall_ts_utc": "t2", "art": "chunk", "index": 1, "staende": {"tariff": 2}},
    {"wall_ts_utc": "t3", "art": "fertig", "endstaende": {"tariff": 3, "ai": 7}},
]


def _schreibe_rohlauf(root: Path, profil: str = "allin_july17") -> Path:
    quell_dir = root / profil
    quell_dir.mkdir(parents=True)
    (quell_dir / "decisions_log.jsonl").write_text(
        json.dumps(ROH_ENTSCHEIDUNG) + "\n", encoding="utf-8"
    )
    (quell_dir / "bot_events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in ROH_EREIGNISSE) + "\n", encoding="utf-8"
    )
    # Dateien, die nie ins Repo duerfen.
    (quell_dir / "deposit_wallet.json").write_text("{}", encoding="utf-8")
    (quell_dir / "episode.mp3").write_bytes(b"ID3")
    (quell_dir / "orderbook_log.csv").write_text("ts,ask\n", encoding="utf-8")
    return quell_dir


def test_kuration_behaelt_nur_publish_felder(tmp_path: Path) -> None:
    kuratiert = kll.kuratiere_entscheidung(ROH_ENTSCHEIDUNG)

    assert set(kuratiert) == {"wall_ts_utc", "decision", "result", "book_snapshot"}
    # outcome bleibt als Seiten-Fallback fuer den Extraktions-Deckel.
    assert set(kuratiert["decision"]) == {"action", "reason", "limit_price", "outcome"}
    assert set(kuratiert["result"]) == {"size_usd"}

    text = json.dumps(kuratiert)
    for verboten in (
        "token_id", "market_id", "size_shares", "status", "detail",
        "0x4d335c329a5b", "timestamp", "min_order_size", "neg_risk",
    ):
        assert verboten not in text
    # Preis UND Groesse bleiben stehen (die Extraktionsquote braucht die
    # Ebenen-Tiefe); alle anderen Buchfelder fliegen raus.
    for seite in ("asks", "bids"):
        for eintrag in kuratiert["book_snapshot"][seite]:
            assert set(eintrag) <= {"price", "size"}
            assert "price" in eintrag


def test_kuration_behaelt_nur_wortzaehler_ereignisse() -> None:
    kuratiert = [kll.kuratiere_ereignis(e) for e in ROH_EREIGNISSE]

    assert kuratiert[0] is None  # start
    assert kuratiert[1] is None  # buchlog
    assert kuratiert[2] == {"art": "chunk", "staende": {"tariff": 2}}
    assert kuratiert[3] == {"art": "fertig", "endstaende": {"tariff": 3, "ai": 7}}


def test_kuratierter_lauf_kopiert_keine_wallet_oder_audiodateien(tmp_path: Path) -> None:
    quelle = tmp_path / "live"
    ziel = tmp_path / "curated"
    _schreibe_rohlauf(quelle)

    ergebnisse = kll.kuratiere_alle(quelle, ziel)

    assert [e.profil for e in ergebnisse] == ["allin_july17"]
    assert ergebnisse[0].n_entscheidungen == 1
    assert ergebnisse[0].n_zaehler_ereignisse == 2
    geschrieben = {p.name for p in (ziel / "allin_july17").iterdir()}
    assert geschrieben == {"decisions_log.jsonl", "bot_events.jsonl"}


def test_kuratierter_lauf_ergibt_dasselbe_artefakt_wie_die_rohquelle(
    tmp_path: Path,
) -> None:
    """Der Publish-Schritt darf die Kuration nicht bemerken."""

    quelle = tmp_path / "live"
    ziel = tmp_path / "curated"
    quell_dir = _schreibe_rohlauf(quelle)
    kll.kuratiere_alle(quelle, ziel)

    aus_roh = drr.build_pipeline_forward(
        live_dir=quell_dir, profil="allin_july17", now_utc="2026-07-22T00:00:00+00:00"
    )
    aus_kuratiert = drr.build_pipeline_forward(
        live_dir=ziel / "allin_july17",
        profil="allin_july17",
        now_utc="2026-07-22T00:00:00+00:00",
    )

    assert aus_kuratiert.model_dump() == aus_roh.model_dump()
    assert aus_kuratiert.eintraege[0].bestes_angebot == 0.68
    assert aus_kuratiert.eintraege[0].bestes_gebot == 0.63
    assert aus_kuratiert.wortzaehler_endstaende == {"tariff": 3, "ai": 7}


def test_kuration_bricht_bei_redaktions_fund_ab(tmp_path: Path) -> None:
    quelle = tmp_path / "live"
    ziel = tmp_path / "curated"
    quell_dir = quelle / "leak"
    quell_dir.mkdir(parents=True)
    leck = dict(ROH_ENTSCHEIDUNG)
    leck["decision"] = dict(ROH_ENTSCHEIDUNG["decision"])
    leck["decision"]["reason"] = "0x" + "a" * 40
    (quell_dir / "decisions_log.jsonl").write_text(
        json.dumps(leck) + "\n", encoding="utf-8"
    )

    with pytest.raises(drr.RedactionGateError):
        kll.kuratiere_alle(quelle, ziel)
