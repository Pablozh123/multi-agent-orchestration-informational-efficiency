from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.collectors.polymarket_watchlist import (
    CURATED_WATCHLIST_COLUMNS,
    build_watchlist_report,
    main,
    validate_curated_watchlist,
    validate_curated_watchlist_file,
)


def test_validate_curated_watchlist_accepts_candidate_rows() -> None:
    frame = validate_curated_watchlist(
        pd.DataFrame([_row(review_status="candidate")], columns=CURATED_WATCHLIST_COLUMNS)
    )
    report = build_watchlist_report(frame, input_path=Path("watchlist.csv"))

    assert len(frame) == 1
    assert report["candidate_count"] == 1
    assert report["accepted_count"] == 0
    assert report["auto_discovered_rows_are_monitor_ready"] is False
    assert report["contains_wallet_addresses"] is False


def test_validate_curated_watchlist_accepts_reviewed_market() -> None:
    frame = validate_curated_watchlist(
        pd.DataFrame(
            [
                _row(
                    review_status="accepted",
                    source_url="https://polymarket.com/event/example-election-market",
                    inclusion_reason="reviewed election market with clear political scope",
                    reviewed_by="chole",
                    reviewed_at_utc="2026-05-22T12:00:00Z",
                )
            ],
            columns=CURATED_WATCHLIST_COLUMNS,
        )
    )

    assert len(frame) == 1
    assert frame.iloc[0]["review_status"] == "accepted"


def test_accepted_watchlist_row_requires_review_metadata() -> None:
    with pytest.raises(ValueError, match="missing review fields"):
        validate_curated_watchlist(
            pd.DataFrame([_row(review_status="accepted")], columns=CURATED_WATCHLIST_COLUMNS)
        )


def test_accepted_watchlist_row_rejects_noise_terms() -> None:
    with pytest.raises(ValueError, match="excluded market terms"):
        validate_curated_watchlist(
            pd.DataFrame(
                [
                    _row(
                        question="Will the Colorado Avalanche win the NHL Stanley Cup?",
                        review_status="accepted",
                        source_url="https://polymarket.com/event/example-sports-market",
                        inclusion_reason="bad accepted fixture",
                        reviewed_by="chole",
                        reviewed_at_utc="2026-05-22T12:00:00Z",
                    )
                ],
                columns=CURATED_WATCHLIST_COLUMNS,
            )
        )


def test_rejected_watchlist_row_requires_exclusion_reason() -> None:
    with pytest.raises(ValueError, match="requires exclusion_reason"):
        validate_curated_watchlist(
            pd.DataFrame([_row(review_status="rejected")], columns=CURATED_WATCHLIST_COLUMNS)
        )


def test_curated_watchlist_file_cli_writes_report(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "watchlist.csv"
    report_path = tmp_path / "report.json"
    pd.DataFrame([_row(review_status="candidate")], columns=CURATED_WATCHLIST_COLUMNS).to_csv(
        input_path,
        index=False,
    )

    exit_code = main(["--input", str(input_path), "--report-output", str(report_path)])

    captured = capsys.readouterr()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert "candidate_count" in captured.out
    assert report["status"] == "pass"
    assert report["row_count"] == 1


def test_validate_curated_watchlist_file_missing_input_returns_clear_error(
    tmp_path: Path,
) -> None:
    with pytest.raises(FileNotFoundError, match="Curated watchlist CSV not found"):
        validate_curated_watchlist_file(
            input_path=tmp_path / "missing.csv",
            report_path=tmp_path / "report.json",
        )


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "watch_id": "watch_001",
        "market_id": "0x" + "a" * 64,
        "condition_id": "0x" + "a" * 64,
        "token_ids": "111,222",
        "question": "Will a candidate win the next presidential nomination?",
        "category": "politics",
        "subcategory": "example-election-market",
        "monitoring_scope": "election",
        "review_status": "candidate",
        "source_url": "",
        "inclusion_reason": "",
        "exclusion_reason": "",
        "reviewed_by": "",
        "reviewed_at_utc": "",
        "notes": "",
    }
    row.update(overrides)
    return row
