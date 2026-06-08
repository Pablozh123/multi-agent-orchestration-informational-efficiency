from __future__ import annotations

import json
from pathlib import Path

import httpx
import pandas as pd
import pytest

from operations.collectors.swiss_referendum_history import (
    CLOB_BASE_URL,
    collect_swiss_referendum_price_history,
    main,
    validate_history_frame,
)


def test_collect_history_mock_writes_bounded_rows(tmp_path: Path) -> None:
    paths = _paths(tmp_path)

    result = collect_swiss_referendum_price_history(
        source="mock",
        poll_input_path=paths["poll_input_path"],
        snapshots_path=paths["snapshots_path"],
        history_path=paths["history_path"],
        metadata_path=paths["metadata_path"],
    )

    history = pd.read_csv(paths["history_path"])
    metadata = json.loads(paths["metadata_path"].read_text(encoding="utf-8"))
    assert result.poll_count == 2
    assert result.row_count == 8
    assert result.token_id == "111"
    assert len(history) == 8
    assert metadata["method"]["bounded_poll_windows_only"] is True
    assert metadata["outputs"]["contains_order_instructions"] is False


def test_collect_history_live_uses_public_clob_history_endpoint(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(f"{CLOB_BASE_URL}/prices-history"):
            return httpx.Response(
                200,
                json={"history": [{"t": 1780458900, "p": 0.44}, {"t": 1780462500, "p": 0.41}]},
            )
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = collect_swiss_referendum_price_history(
            source="live",
            poll_input_path=paths["poll_input_path"],
            snapshots_path=paths["snapshots_path"],
            history_path=paths["history_path"],
            metadata_path=paths["metadata_path"],
            client=client,
        )

    assert result.row_count >= 2
    assert any(url.startswith(f"{CLOB_BASE_URL}/prices-history") for url in requested_urls)
    assert not any("orders" in url for url in requested_urls)


def test_history_validation_rejects_wallet_columns(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    collect_swiss_referendum_price_history(
        source="mock",
        poll_input_path=paths["poll_input_path"],
        snapshots_path=paths["snapshots_path"],
        history_path=paths["history_path"],
        metadata_path=paths["metadata_path"],
    )
    history = pd.read_csv(paths["history_path"])
    history["wallet_address"] = "0x" + "a" * 40

    with pytest.raises(ValueError, match="wallet columns"):
        validate_history_frame(history)


def test_history_cli_writes_outputs(tmp_path: Path, capsys) -> None:
    paths = _paths(tmp_path)

    exit_code = main(
        [
            "--source",
            "mock",
            "--poll-input",
            str(paths["poll_input_path"]),
            "--snapshots",
            str(paths["snapshots_path"]),
            "--history-output",
            str(paths["history_path"]),
            "--metadata-output",
            str(paths["metadata_path"]),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "row_count" in captured.out
    assert paths["history_path"].exists()


def _paths(root: Path) -> dict[str, Path]:
    poll_input_path = root / "polls.csv"
    snapshots_path = root / "snapshots.csv"
    pd.DataFrame(
        [
            {
                "poll_id": "poll_001",
                "published_at_utc": "2026-06-03T03:55:00Z",
                "yes_share": 0.45,
                "source_url": "https://www.srf.ch/news/schweiz/2-srg-umfrage-keine-10-mio-schweiz-kippt-ins-nein-52-prozent-dagegen",
            },
            {
                "poll_id": "poll_002",
                "published_at_utc": "2026-06-07T00:00:00Z",
                "yes_share": 0.44,
                "source_url": "https://example.invalid/poll",
            },
        ]
    ).to_csv(poll_input_path, index=False)
    pd.DataFrame(
        [
            {
                "collected_at_utc": "2026-06-08T12:00:00Z",
                "yes_token_id": "111",
            }
        ]
    ).to_csv(snapshots_path, index=False)
    return {
        "poll_input_path": poll_input_path,
        "snapshots_path": snapshots_path,
        "history_path": root / "history.csv",
        "metadata_path": root / "metadata.json",
    }
