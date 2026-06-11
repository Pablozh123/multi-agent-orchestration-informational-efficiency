from __future__ import annotations

import json
from pathlib import Path

import httpx
import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_270towin_state_forecast_extension import (
    CASE_COLUMNS,
    TWO_SEVENTY_STATE_PROBABILITIES,
    build_270towin_state_case_row,
    generate_h1_270towin_state_forecast_outputs,
    mock_gamma_market,
    validate_270towin_state_cases,
    validate_two_seventy_probability_specs,
)
from operations.analysis.h1_state_poll_snapshot_extension import (
    ALL_US_STATES,
    CLOB_BASE_URL,
    GAMMA_BASE_URL,
    POLYMARKET_STATE_MARKET_SLUGS,
    REPUBLICAN_WON_2024_STATES,
)


FORECAST_TS = pd.Timestamp("2024-11-05T13:00:00Z")


def test_generate_h1_270towin_state_forecast_outputs_mock(tmp_path: Path) -> None:
    result = generate_h1_270towin_state_forecast_outputs(
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
    assert result.exact_probability_case_count == 22
    assert result.censored_boundary_case_count == 28
    assert result.polymarket_lower_loss_count == 7
    assert result.two_seventy_lower_loss_count == 43
    assert result.mean_polymarket_brier == pytest.approx(0.0196)
    assert result.mean_two_seventy_brier == pytest.approx(0.03059892)
    assert len(cases) == 50
    assert len(summary) >= 12
    assert metadata["method"]["uses_raw_poll_shares_directly"] is False
    assert metadata["method"]["rcp_included"] is False
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["broad_many_cases_claim_supported_now"] is False
    assert metadata["outputs"]["exact_probability_case_count"] == 22
    assert metadata["outputs"]["censored_boundary_case_count"] == 28
    assert metadata["limitations"]["mean_loss_advantage_not_same_as_majority_of_states"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_probability_specs_cover_50_states_and_mark_censored_values() -> None:
    specs = validate_two_seventy_probability_specs(TWO_SEVENTY_STATE_PROBABILITIES)

    assert len(specs) == 50
    assert {spec.state for spec in specs} == set(ALL_US_STATES)
    assert sum(spec.probability_precision == "exact_percent" for spec in specs) == 22
    assert (
        sum(spec.probability_precision == "censored_boundary_>99.9" for spec in specs)
        == 28
    )
    assert all(0.0 <= spec.trump_probability <= 1.0 for spec in specs)


def test_build_270towin_state_case_row_live_style_uses_public_read_endpoints() -> None:
    requested_urls: list[str] = []
    spec = next(item for item in TWO_SEVENTY_STATE_PROBABILITIES if item.state == "Arizona")

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(f"{GAMMA_BASE_URL}/markets"):
            return httpx.Response(200, json=[mock_gamma_market(spec.state)])
        if str(request.url).startswith(f"{CLOB_BASE_URL}/prices-history"):
            return httpx.Response(
                200,
                json={"history": [{"t": int(FORECAST_TS.timestamp()) + 2, "p": 0.86}]},
            )
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        row = build_270towin_state_case_row(
            spec=spec,
            source="live",
            forecast_ts=FORECAST_TS,
            client=client,
        )

    assert row["polymarket_probability"] == 0.86
    assert row["two_seventy_trump_win_probability"] == pytest.approx(0.693)
    assert row["lower_loss_source"] == "polymarket"
    assert any(url.startswith(f"{GAMMA_BASE_URL}/markets") for url in requested_urls)
    assert any(url.startswith(f"{CLOB_BASE_URL}/prices-history") for url in requested_urls)
    assert not any("orders" in url for url in requested_urls)


def test_live_generation_reads_public_market_data_without_order_paths(
    tmp_path: Path,
) -> None:
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
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
        result = generate_h1_270towin_state_forecast_outputs(
            source="live",
            cases_output=tmp_path / "cases.csv",
            summary_output=tmp_path / "summary.csv",
            figure_output=tmp_path / "figure.png",
            metadata_output=tmp_path / "metadata.json",
            client=client,
        )

    assert result.case_count == 50
    assert sum(url.startswith(f"{GAMMA_BASE_URL}/markets") for url in requested_urls) == 50
    assert sum(url.startswith(f"{CLOB_BASE_URL}/prices-history") for url in requested_urls) == 50
    assert not any("orders" in url for url in requested_urls)


def test_validate_270towin_state_cases_rejects_missing_state_row() -> None:
    rows = []
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500))) as client:
        for spec in validate_two_seventy_probability_specs(TWO_SEVENTY_STATE_PROBABILITIES):
            rows.append(
                build_270towin_state_case_row(
                    spec=spec,
                    source="mock",
                    forecast_ts=FORECAST_TS,
                    client=client,
                )
            )
    frame = pd.DataFrame(rows, columns=CASE_COLUMNS).iloc[:-1]

    with pytest.raises(ValueError, match="50 state rows"):
        validate_270towin_state_cases(frame)
