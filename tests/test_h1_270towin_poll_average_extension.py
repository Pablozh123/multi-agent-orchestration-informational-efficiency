from __future__ import annotations

import json
from pathlib import Path

import httpx
import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_270towin_poll_average_extension import (
    TWO_SEVENTY_POLL_AVERAGE_ENDPOINT,
    build_270towin_poll_average_cases,
    generate_h1_270towin_poll_average_outputs,
    mock_two_seventy_poll_average_rows,
    parse_two_seventy_poll_average_rows,
    read_polymarket_state_cases,
    transformed_margin_probability,
    validate_270towin_poll_average_cases,
)
from operations.analysis.h1_state_poll_snapshot_extension import ALL_US_STATES


def test_parse_two_seventy_poll_average_rows_excludes_national_and_district_rows() -> None:
    frame = parse_two_seventy_poll_average_rows(mock_two_seventy_poll_average_rows())

    assert len(frame) == 43
    assert set(frame["state"]).issubset(set(ALL_US_STATES))
    assert "0" not in set(frame["state"])
    assert "Maine Dist. 1" not in set(frame["state"])
    assert "Nebraska Dist. 2" not in set(frame["state"])
    assert sorted(set(ALL_US_STATES) - set(frame["state"])) == [
        "Alabama",
        "Hawaii",
        "Idaho",
        "Illinois",
        "Kentucky",
        "Louisiana",
        "Mississippi",
    ]


def test_build_270towin_poll_average_cases_uses_documented_probability_transform(
    tmp_path: Path,
) -> None:
    pm_cases = read_polymarket_state_cases(_write_polymarket_cases(tmp_path))
    poll_frame = parse_two_seventy_poll_average_rows(mock_two_seventy_poll_average_rows())

    cases = validate_270towin_poll_average_cases(
        build_270towin_poll_average_cases(
            poll_frame=poll_frame,
            polymarket_cases=pm_cases,
        )
    )

    arizona = cases.loc[cases["state"] == "Arizona"].iloc[0]
    expected_probability = transformed_margin_probability(48.47 - 46.82)
    assert len(cases) == 3
    assert arizona["poll_derived_probability"] == pytest.approx(expected_probability)
    assert arizona["polymarket_brier"] == pytest.approx((0.80 - 1.0) ** 2)
    assert arizona["poll_derived_brier"] == pytest.approx(
        (expected_probability - 1.0) ** 2
    )
    assert arizona["loss_advantage"] == pytest.approx(
        arizona["poll_derived_brier"] - arizona["polymarket_brier"]
    )


def test_generate_h1_270towin_poll_average_outputs_mock(tmp_path: Path) -> None:
    result = generate_h1_270towin_poll_average_outputs(
        source="mock",
        polymarket_cases_input=_write_polymarket_cases(tmp_path),
        cases_output=tmp_path / "cases.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        metadata_output=tmp_path / "metadata.json",
    )

    cases = pd.read_csv(tmp_path / "cases.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "figure.png")

    assert result.case_count == 3
    assert result.poll_average_state_rows == 43
    assert len(cases) == 3
    assert float(_summary_value(summary, "poll_average_endpoint_row_count")) == 49.0
    assert float(_summary_value(summary, "poll_average_missing_state_count")) == 7.0
    assert metadata["method"]["uses_raw_poll_shares_directly"] is False
    assert metadata["method"]["collects_polymarket_live_data"] is False
    assert metadata["method"]["does_not_use_llms"] is True
    assert metadata["outputs"]["contains_wallet_addresses"] is False
    assert metadata["outputs"]["broad_many_cases_claim_supported_now"] is False
    assert metadata["limitations"]["not_raw_poll_comparison"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0


def test_live_generation_fetches_only_public_poll_endpoint(tmp_path: Path) -> None:
    requested_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url).startswith(TWO_SEVENTY_POLL_AVERAGE_ENDPOINT):
            return httpx.Response(200, json={"results": _mock_results_payload()})
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = generate_h1_270towin_poll_average_outputs(
            source="live",
            polymarket_cases_input=_write_polymarket_cases(tmp_path),
            cases_output=tmp_path / "cases.csv",
            summary_output=tmp_path / "summary.csv",
            figure_output=tmp_path / "figure.png",
            metadata_output=tmp_path / "metadata.json",
            client=client,
        )

    assert result.case_count == 3
    assert len(requested_urls) == 1
    assert requested_urls[0].startswith(TWO_SEVENTY_POLL_AVERAGE_ENDPOINT)
    assert not any("orders" in url.lower() for url in requested_urls)
    assert not any("wallet" in url.lower() for url in requested_urls)


def test_validate_270towin_poll_average_cases_rejects_forbidden_columns(
    tmp_path: Path,
) -> None:
    pm_cases = read_polymarket_state_cases(_write_polymarket_cases(tmp_path))
    poll_frame = parse_two_seventy_poll_average_rows(mock_two_seventy_poll_average_rows())
    cases = build_270towin_poll_average_cases(
        poll_frame=poll_frame,
        polymarket_cases=pm_cases,
    )
    cases["wallet_address"] = "0xabc"

    with pytest.raises(ValueError, match="forbidden columns"):
        validate_270towin_poll_average_cases(cases)


def _write_polymarket_cases(tmp_path: Path) -> Path:
    path = tmp_path / "polymarket_cases.csv"
    rows = [
        _pm_row("Arizona", 1.0, 0.80),
        _pm_row("California", 0.0, 0.08),
        _pm_row("Pennsylvania", 1.0, 0.55),
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _pm_row(state: str, outcome: float, probability: float) -> dict[str, object]:
    slug = state.lower().replace(" ", "-")
    return {
        "state": state,
        "forecast_timestamp_utc": "2024-11-05T13:22:58Z",
        "polymarket_observed_at_utc": "2024-11-05T13:00:02Z",
        "polymarket_market_slug": f"will-a-republican-win-{slug}",
        "polymarket_market_id": f"market-{slug}",
        "polymarket_condition_id": f"condition-{slug}",
        "target_outcome": "Republican wins state",
        "target_token_id": f"token-{slug}",
        "outcome_value": outcome,
        "polymarket_probability": probability,
        "polymarket_source_url": f"https://polymarket.com/market/{slug}",
    }


def _mock_results_payload() -> dict[str, dict[str, object]]:
    return {
        str(row["state"]): {
            key: value for key, value in row.items() if key != "state"
        }
        for row in mock_two_seventy_poll_average_rows()
    }


def _summary_value(summary: pd.DataFrame, summary_id: str) -> str:
    row = summary.loc[summary["summary_id"] == summary_id, "value"]
    assert len(row) == 1
    return str(row.iloc[0])
