from __future__ import annotations

import json
from pathlib import Path

import httpx
import pandas as pd

from operations.collectors.swiss_referendum_polymarket import (
    EVENT_SLUG,
    GAMMA_BASE_URL,
    TEN_MILLION_MARKET_SLUG,
    build_snapshot_row,
    collect_swiss_referendum_polymarket_snapshot,
    main,
    mock_gamma_event,
    validate_snapshot_frame,
)


COLLECTED_AT = "2026-06-08T14:00:00Z"


def test_build_snapshot_row_extracts_ten_million_market() -> None:
    row = build_snapshot_row(
        mock_gamma_event(),
        collected_at=pd.Timestamp(COLLECTED_AT).to_pydatetime(),
    )

    assert row["event_slug"] == EVENT_SLUG
    assert row["market_slug"] == TEN_MILLION_MARKET_SLUG
    assert row["yes_probability"] == 0.225
    assert row["no_probability"] == 0.775
    assert row["yes_token_id"] == "111"
    assert row["no_token_id"] == "222"


def test_validate_snapshot_rejects_wallet_columns() -> None:
    row = build_snapshot_row(
        mock_gamma_event(),
        collected_at=pd.Timestamp(COLLECTED_AT).to_pydatetime(),
    )
    frame = pd.DataFrame([row])
    frame["wallet_address"] = "0x" + "a" * 40

    try:
        validate_snapshot_frame(frame)
    except ValueError as exc:
        assert "wallet columns" in str(exc)
    else:
        raise AssertionError("wallet column was not rejected")


def test_collect_live_uses_public_gamma_event_endpoint(tmp_path: Path) -> None:
    snapshots_path = tmp_path / "snapshots.csv"
    metadata_path = tmp_path / "metadata.json"
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(f"{GAMMA_BASE_URL}/events"):
            return httpx.Response(200, json=mock_gamma_event())
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect_swiss_referendum_polymarket_snapshot(
            source="live",
            snapshots_path=snapshots_path,
            metadata_path=metadata_path,
            collected_at_utc=COLLECTED_AT,
            append=True,
            client=client,
        )

    snapshots = pd.read_csv(snapshots_path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert result.row_count == 1
    assert result.latest_yes_probability == 0.225
    assert len(snapshots) == 1
    assert metadata["method"]["uses_public_gamma_event_metadata"] is True
    assert metadata["limitations"]["does_not_use_order_endpoints"] is True
    assert not any("orders" in url for url in requested_urls)
    assert any(url.startswith(f"{GAMMA_BASE_URL}/events") for url in requested_urls)


def test_collect_append_deduplicates_same_snapshot_bucket(tmp_path: Path) -> None:
    snapshots_path = tmp_path / "snapshots.csv"
    metadata_path = tmp_path / "metadata.json"

    collect_swiss_referendum_polymarket_snapshot(
        source="mock",
        snapshots_path=snapshots_path,
        metadata_path=metadata_path,
        collected_at_utc=COLLECTED_AT,
        append=True,
    )
    result = collect_swiss_referendum_polymarket_snapshot(
        source="mock",
        snapshots_path=snapshots_path,
        metadata_path=metadata_path,
        collected_at_utc=COLLECTED_AT,
        append=True,
    )

    snapshots = pd.read_csv(snapshots_path)
    assert result.row_count == 1
    assert len(snapshots) == 1


def test_cli_mock_source_writes_outputs(tmp_path: Path, capsys) -> None:
    snapshots_path = tmp_path / "snapshots.csv"
    metadata_path = tmp_path / "metadata.json"

    exit_code = main(
        [
            "--source",
            "mock",
            "--snapshots-output",
            str(snapshots_path),
            "--metadata-output",
            str(metadata_path),
            "--collected-at-utc",
            COLLECTED_AT,
            "--append",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "latest_yes_probability" in captured.out
    assert snapshots_path.exists()
    assert metadata_path.exists()
