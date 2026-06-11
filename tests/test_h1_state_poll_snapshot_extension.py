from __future__ import annotations

import json
from pathlib import Path

import httpx
import matplotlib.image as mpimg
import pandas as pd
import pytest

from operations.analysis.h1_state_poll_snapshot_extension import (
    CLOB_BASE_URL,
    FIVETHIRTYEIGHT_POLL_AVERAGES_URL,
    GAMMA_BASE_URL,
    STATE_POLL_SNAPSHOT_CASES,
    build_state_case_row,
    build_state_coverage_audit,
    build_poll_transform_sensitivity,
    generate_h1_state_poll_snapshot_outputs,
    mock_gamma_event,
    mock_poll_average_rows,
    normal_cdf,
    parse_poll_average_snapshot,
    poll_error_sigma_points,
    validate_state_cases,
    validate_state_coverage,
)


SNAPSHOT_TS = pd.Timestamp("2024-09-12T12:00:00Z")


def test_generate_h1_state_poll_snapshot_outputs_mock(tmp_path: Path) -> None:
    result = generate_h1_state_poll_snapshot_outputs(
        source="mock",
        cases_output=tmp_path / "cases.csv",
        summary_output=tmp_path / "summary.csv",
        figure_output=tmp_path / "figure.png",
        sensitivity_output=tmp_path / "sensitivity.csv",
        sensitivity_figure_output=tmp_path / "sensitivity.png",
        coverage_output=tmp_path / "coverage.csv",
        coverage_figure_output=tmp_path / "coverage.png",
        metadata_output=tmp_path / "metadata.json",
    )

    cases = pd.read_csv(tmp_path / "cases.csv")
    summary = pd.read_csv(tmp_path / "summary.csv")
    sensitivity = pd.read_csv(tmp_path / "sensitivity.csv")
    coverage = pd.read_csv(tmp_path / "coverage.csv")
    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    image = mpimg.imread(tmp_path / "figure.png")
    sensitivity_image = mpimg.imread(tmp_path / "sensitivity.png")
    coverage_image = mpimg.imread(tmp_path / "coverage.png")

    assert result.case_count == 13
    assert result.polymarket_lower_loss_count == 8
    assert result.poll_derived_lower_loss_count == 5
    assert result.mean_polymarket_brier == pytest.approx(0.13355132692307695)
    assert result.mean_poll_derived_brier == pytest.approx(0.17635906875132107)
    assert len(cases) == 13
    assert len(summary) >= 6
    assert len(sensitivity) == 12
    assert len(coverage) == 50
    assert int(coverage["polymarket_market_available"].sum()) == 50
    assert int(coverage["poll_snapshot_has_rep_dem"].sum()) == 13
    assert int(coverage["included_in_brier_comparison"].sum()) == 13
    assert (
        coverage["coverage_status"]
        .value_counts()
        .to_dict()["excluded_missing_538_poll_snapshot"]
        == 37
    )
    assert int(sensitivity["polymarket_lower_loss_count"].min()) == 7
    assert int(sensitivity["polymarket_lower_loss_count"].max()) == 12
    assert (sensitivity["mean_loss_advantage"] > 0).all()
    assert metadata["outputs"]["independent_resolved_outcome_count"] == 13
    assert metadata["outputs"]["sensitivity_row_count"] == 12
    assert metadata["outputs"]["sensitivity_min_polymarket_lower_loss_count"] == 7
    assert metadata["outputs"]["sensitivity_max_polymarket_lower_loss_count"] == 12
    assert metadata["outputs"]["coverage_state_universe_count"] == 50
    assert metadata["outputs"]["coverage_polymarket_market_count"] == 50
    assert metadata["outputs"]["coverage_valid_brier_pair_count"] == 13
    assert metadata["limitations"]["coverage_audit_is_not_additional_brier_evidence"] is True
    assert metadata["outputs"]["broad_many_cases_claim_supported_now"] is False
    assert metadata["method"]["raw_poll_average_used_directly_as_probability"] is False
    assert metadata["method"]["rcp_included"] is False
    assert metadata["limitations"]["not_official_538_state_win_forecast"] is True
    assert image.size > 0
    assert float(image.std()) > 0.0
    assert sensitivity_image.size > 0
    assert float(sensitivity_image.std()) > 0.0
    assert coverage_image.size > 0
    assert float(coverage_image.std()) > 0.0


def test_poll_margin_transform_uses_documented_error_scale() -> None:
    sigma = poll_error_sigma_points()
    assert sigma == pytest.approx(3.8 / (2.0 / 3.141592653589793) ** 0.5)
    assert normal_cdf(0.0) == pytest.approx(0.5)
    assert normal_cdf(1.0 / sigma) > 0.5
    assert normal_cdf(-1.0 / sigma) < 0.5


def test_poll_transform_sensitivity_keeps_parameter_grid_explicit() -> None:
    poll_frame = parse_poll_average_snapshot(mock_poll_average_rows())
    rows = []
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500))) as client:
        for spec in STATE_POLL_SNAPSHOT_CASES:
            rows.append(
                build_state_case_row(
                    spec,
                    source="mock",
                    poll_frame=poll_frame,
                    snapshot_ts=SNAPSHOT_TS,
                    client=client,
                )
            )
    sensitivity = build_poll_transform_sensitivity(pd.DataFrame(rows))

    assert sensitivity["poll_error_mae_points"].tolist() == [
        2.0,
        2.5,
        3.0,
        3.5,
        3.8,
        4.0,
        4.5,
        5.0,
        6.0,
        7.0,
        8.0,
        10.0,
    ]
    row_38 = sensitivity.loc[sensitivity["poll_error_mae_points"] == 3.8].iloc[0]
    assert int(row_38["polymarket_lower_loss_count"]) == 8
    assert row_38["mean_loss_advantage"] == pytest.approx(0.04280774182824412)


def test_state_coverage_audit_documents_why_pairs_stop_at_13() -> None:
    poll_frame = parse_poll_average_snapshot(mock_poll_average_rows())
    coverage = build_state_coverage_audit(poll_frame=poll_frame)

    assert len(coverage) == 50
    assert int(coverage["polymarket_market_available"].sum()) == 50
    assert int(coverage["poll_snapshot_has_rep_dem"].sum()) == 13
    assert int(coverage["included_in_brier_comparison"].sum()) == 13
    status_counts = coverage["coverage_status"].value_counts().to_dict()
    assert status_counts["included_brier_pair"] == 13
    assert status_counts["excluded_missing_538_poll_snapshot"] == 37
    assert "excluded_missing_both_sources" not in status_counts
    assert set(
        coverage.loc[coverage["included_in_brier_comparison"], "state"]
    ) == {spec.state for spec in STATE_POLL_SNAPSHOT_CASES}


def test_build_state_case_row_live_style_uses_public_read_endpoints() -> None:
    spec = STATE_POLL_SNAPSHOT_CASES[0]
    poll_frame = parse_poll_average_snapshot(mock_poll_average_rows())
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
                        {"t": int(SNAPSHOT_TS.timestamp()) - 3600, "p": 0.61},
                        {"t": int(SNAPSHOT_TS.timestamp()) + 2, "p": 0.605},
                    ]
                },
            )
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        row = build_state_case_row(
            spec,
            source="live",
            poll_frame=poll_frame,
            snapshot_ts=SNAPSHOT_TS,
            client=client,
        )

    assert row["polymarket_probability"] == 0.605
    assert row["polymarket_time_distance_seconds"] == 2
    assert row["lower_loss_source"] == "polymarket"
    assert any(url.startswith(f"{GAMMA_BASE_URL}/events") for url in requested_urls)
    assert any(url.startswith(f"{CLOB_BASE_URL}/prices-history") for url in requested_urls)
    assert not any("orders" in url for url in requested_urls)


def test_live_generation_downloads_538_poll_average_csv(tmp_path: Path) -> None:
    requested_urls: list[str] = []
    poll_csv = pd.DataFrame(mock_poll_average_rows()).to_csv(index=False)

    def handler(request: httpx.Request) -> httpx.Response:
        requested_urls.append(str(request.url))
        if str(request.url) == FIVETHIRTYEIGHT_POLL_AVERAGES_URL:
            return httpx.Response(200, text=poll_csv)
        if str(request.url).startswith(f"{GAMMA_BASE_URL}/events"):
            slug = str(request.url.params["slug"])
            spec = next(item for item in STATE_POLL_SNAPSHOT_CASES if item.event_slug == slug)
            return httpx.Response(200, json=[mock_gamma_event(spec)])
        if str(request.url).startswith(f"{CLOB_BASE_URL}/prices-history"):
            return httpx.Response(
                200,
                json={"history": [{"t": int(SNAPSHOT_TS.timestamp()) + 2, "p": 0.605}]},
            )
        return httpx.Response(404, json={"error": "unexpected"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = generate_h1_state_poll_snapshot_outputs(
            source="live",
            cases_output=tmp_path / "cases.csv",
            summary_output=tmp_path / "summary.csv",
            figure_output=tmp_path / "figure.png",
            sensitivity_output=tmp_path / "sensitivity.csv",
            sensitivity_figure_output=tmp_path / "sensitivity.png",
            coverage_output=tmp_path / "coverage.csv",
            coverage_figure_output=tmp_path / "coverage.png",
            metadata_output=tmp_path / "metadata.json",
            client=client,
        )

    metadata = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert result.case_count == 13
    assert metadata["method"]["read_only_public_endpoints"] is True
    assert FIVETHIRTYEIGHT_POLL_AVERAGES_URL in requested_urls
    assert any(url.startswith(f"{GAMMA_BASE_URL}/events") for url in requested_urls)
    assert any(url.startswith(f"{CLOB_BASE_URL}/prices-history") for url in requested_urls)


def test_validate_state_cases_rejects_invalid_probabilities() -> None:
    result_rows = []
    poll_frame = parse_poll_average_snapshot(mock_poll_average_rows())
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500))) as client:
        for spec in STATE_POLL_SNAPSHOT_CASES:
            result_rows.append(
                build_state_case_row(
                    spec,
                    source="mock",
                    poll_frame=poll_frame,
                    snapshot_ts=SNAPSHOT_TS,
                    client=client,
                )
            )
    frame = pd.DataFrame(result_rows)
    frame.loc[0, "poll_derived_probability"] = -0.1

    with pytest.raises(ValueError, match="poll_derived_probability"):
        validate_state_cases(frame)


def test_validate_state_coverage_rejects_missing_state_row() -> None:
    poll_frame = parse_poll_average_snapshot(mock_poll_average_rows())
    coverage = build_state_coverage_audit(poll_frame=poll_frame).iloc[:-1]

    with pytest.raises(ValueError, match="50 state rows"):
        validate_state_coverage(coverage)
