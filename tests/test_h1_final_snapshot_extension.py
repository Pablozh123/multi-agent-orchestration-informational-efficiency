from __future__ import annotations

import json
from pathlib import Path

import httpx
import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_final_snapshot_extension import (
    CLOB_BASE_URL,
    FINAL_SNAPSHOT_CASES,
    GAMMA_BASE_URL,
    build_case_row,
    generate_h1_final_snapshot_outputs,
    mock_gamma_event,
    validate_cases,
)


FORECAST_TS = pd.Timestamp("2024-11-05T11:00:00Z")


def test_generate_h1_final_snapshot_outputs_mock(tmp_path: Path) -> None:
    result = generate_h1_final_snapshot_outputs(
        source="mock",
        cases_output=tmp_path / "cases.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    cases = pd.read_csv(tmp_path / "cases.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.case_count == 8
    assert result.polymarket_lower_loss_count == 5
    assert result.traditional_lower_loss_count == 3
    assert len(cases) == 8
    assert len(summary) >= 6
    assert metadata["outputs"]["independent_resolved_outcome_count"] == 8
    assert metadata["outputs"]["broad_many_cases_claim_supported_now"] is False
    assert "us_2024_senate_texas_republican" in metadata["case_ids"]
    assert metadata["limitations"]["not_raw_poll_comparison"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_build_case_row_live_style_uses_public_endpoints() -> None:
    spec = FINAL_SNAPSHOT_CASES[0]
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(f"{GAMMA_BASE_URL}/events"):
            return httpx.Response(200, json=[mock_gamma_event(spec)])
        if str(request.url).startswith(f"{CLOB_BASE_URL}/prices-history"):
            return httpx.Response(
                200,
                json={
                    "history": [
                        {"t": int(FORECAST_TS.timestamp()) - 3600, "p": 0.61},
                        {"t": int(FORECAST_TS.timestamp()) + 2, "p": 0.63},
                    ]
                },
            )
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        row = build_case_row(
            spec,
            source="live",
            forecast_ts=FORECAST_TS,
            client=client,
        )

    assert row["polymarket_probability"] == 0.63
    assert row["polymarket_time_distance_seconds"] == 2
    assert row["lower_loss_source"] == "polymarket"
    assert any(url.startswith(f"{GAMMA_BASE_URL}/events") for url in requested_urls)
    assert any(url.startswith(f"{CLOB_BASE_URL}/prices-history") for url in requested_urls)
    assert not any("orders" in url for url in requested_urls)


def test_validate_cases_rejects_invalid_probabilities() -> None:
    valid = []
    for spec in FINAL_SNAPSHOT_CASES:
        row = build_case_row(
            spec,
            source="mock",
            forecast_ts=FORECAST_TS,
            client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500))),
        )
        valid.append(row)
    frame = pd.DataFrame(valid)
    frame.loc[0, "traditional_probability"] = 1.2

    with pytest.raises(ValueError, match="traditional_probability"):
        validate_cases(frame)
