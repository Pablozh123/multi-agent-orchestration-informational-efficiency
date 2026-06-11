from __future__ import annotations

import json
from pathlib import Path

import httpx
import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_rieke_state_forecast_extension import (
    CASE_COLUMNS,
    RIEKE_MODEL_LOG_URL,
    RIEKE_WIN_STATE_URL,
    build_rieke_state_case_row,
    generate_h1_rieke_state_forecast_outputs,
    mock_gamma_market,
    mock_rieke_model_log_rows,
    mock_rieke_win_state_rows,
    parse_rieke_model_log,
    parse_rieke_win_state,
    rieke_forecast_timestamp,
    validate_rieke_state_cases,
)
from operations.analysis.h1_state_poll_snapshot_extension import (
    ALL_US_STATES,
    CLOB_BASE_URL,
    GAMMA_BASE_URL,
    POLYMARKET_STATE_MARKET_SLUGS,
    REPUBLICAN_WON_2024_STATES,
)


FORECAST_TS = pd.Timestamp("2024-11-05T13:22:58Z")


def test_generate_h1_rieke_state_forecast_outputs_mock(tmp_path: Path) -> None:
    result = generate_h1_rieke_state_forecast_outputs(
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

    assert result.case_count == 50
    assert result.polymarket_lower_loss_count == 50
    assert result.rieke_lower_loss_count == 0
    assert result.mean_polymarket_brier == pytest.approx(0.0196)
    assert result.mean_rieke_brier == pytest.approx(0.04)
    assert len(cases) == 50
    assert len(summary) >= 8
    assert metadata["method"]["uses_raw_poll_shares_directly"] is False
    assert metadata["method"]["rcp_included"] is False
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["limitations"]["mean_loss_advantage_not_same_as_majority_of_states"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_build_rieke_state_case_row_live_style_uses_public_read_endpoints() -> None:
    requested_urls: list[str] = []
    win_state = parse_rieke_win_state(mock_rieke_win_state_rows())
    model_log = parse_rieke_model_log(mock_rieke_model_log_rows())
    forecast_ts = rieke_forecast_timestamp(model_log, "2024-11-05")
    state = "Arizona"

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(f"{GAMMA_BASE_URL}/markets"):
            return httpx.Response(200, json=[mock_gamma_market(state)])
        if str(request.url).startswith(f"{CLOB_BASE_URL}/prices-history"):
            return httpx.Response(
                200,
                json={"history": [{"t": int(FORECAST_TS.timestamp()) + 2, "p": 0.86}]},
            )
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        row = build_rieke_state_case_row(
            state=state,
            source="live",
            win_state=win_state,
            run_date="2024-11-05",
            forecast_ts=forecast_ts,
            client=client,
        )

    assert row["polymarket_probability"] == 0.86
    assert row["rieke_republican_win_probability"] == pytest.approx(0.8)
    assert row["lower_loss_source"] == "polymarket"
    assert any(url.startswith(f"{GAMMA_BASE_URL}/markets") for url in requested_urls)
    assert any(url.startswith(f"{CLOB_BASE_URL}/prices-history") for url in requested_urls)
    assert not any("orders" in url for url in requested_urls)


def test_live_generation_downloads_rieke_sources_and_reads_public_market_data(
    tmp_path: Path,
) -> None:
    requested_urls: list[str] = []
    win_csv = pd.DataFrame(mock_rieke_win_state_rows()).to_csv(index=False)
    log_csv = pd.DataFrame(mock_rieke_model_log_rows()).to_csv(index=False)

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url) == RIEKE_WIN_STATE_URL:
            return httpx.Response(200, text=win_csv)
        if str(request.url) == RIEKE_MODEL_LOG_URL:
            return httpx.Response(200, text=log_csv)
        if str(request.url).startswith(f"{GAMMA_BASE_URL}/markets"):
            slug = str(request.url.params["slug"])
            state = next(
                item
                for item, market_slug in POLYMARKET_STATE_MARKET_SLUGS.items()
                if market_slug == slug
            )
            return httpx.Response(200, json=[mock_gamma_market(state)])
        if str(request.url).startswith(f"{CLOB_BASE_URL}/prices-history"):
            token = str(request.url.params["market"])
            state_slug = token.removeprefix("token-").removesuffix("-yes")
            state = state_slug.replace("_", " ").title()
            outcome = 1.0 if state in REPUBLICAN_WON_2024_STATES else 0.0
            price = 0.86 if outcome == 1.0 else 0.14
            return httpx.Response(
                200,
                json={"history": [{"t": int(FORECAST_TS.timestamp()) + 2, "p": price}]},
            )
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = generate_h1_rieke_state_forecast_outputs(
            source="live",
            cases_output=tmp_path / "cases.csv",
            summary_output=tmp_path / "summary.csv",
            figure_output=tmp_path / "figure.png",
            metadata_output=tmp_path / "metadata.json",
            client=client,
        )

    assert result.case_count == 50
    assert RIEKE_WIN_STATE_URL in requested_urls
    assert RIEKE_MODEL_LOG_URL in requested_urls
    assert sum(url.startswith(f"{GAMMA_BASE_URL}/markets") for url in requested_urls) == 50
    assert sum(url.startswith(f"{CLOB_BASE_URL}/prices-history") for url in requested_urls) == 50


def test_validate_rieke_state_cases_rejects_missing_state_row() -> None:
    rows = []
    win_state = parse_rieke_win_state(mock_rieke_win_state_rows())
    model_log = parse_rieke_model_log(mock_rieke_model_log_rows())
    forecast_ts = rieke_forecast_timestamp(model_log, "2024-11-05")
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500))) as client:
        for state in ALL_US_STATES:
            rows.append(
                build_rieke_state_case_row(
                    state=state,
                    source="mock",
                    win_state=win_state,
                    run_date="2024-11-05",
                    forecast_ts=forecast_ts,
                    client=client,
                )
            )
    frame = pd.DataFrame(rows, columns=CASE_COLUMNS).iloc[:-1]

    with pytest.raises(ValueError, match="50 state rows"):
        validate_rieke_state_cases(frame)
