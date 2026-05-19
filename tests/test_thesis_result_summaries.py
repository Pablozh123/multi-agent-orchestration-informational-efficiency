from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from operations.analysis.thesis_result_summaries import (
    SUMMARY_COLUMNS,
    build_h1_summary,
    generate_thesis_result_summaries,
    main,
)


def test_generate_thesis_result_summaries_writes_traceable_outputs(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path)

    result = generate_thesis_result_summaries(results_dir=tmp_path, output_dir=tmp_path)

    h1 = pd.read_csv(result.h1_path)
    h2 = pd.read_csv(result.h2_path)
    h3 = pd.read_csv(result.h3_path)
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert tuple(h1.columns) == SUMMARY_COLUMNS
    assert tuple(h2.columns) == SUMMARY_COLUMNS
    assert tuple(h3.columns) == SUMMARY_COLUMNS
    assert h1["source_artifact"].str.len().gt(0).all()
    assert h2["limitation"].str.len().gt(0).all()
    assert h3["allowed_interpretation"].str.len().gt(0).all()
    assert metadata["method"]["does_not_use_llms"] is True


def test_missing_source_artifact_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Required thesis summary source artifact"):
        generate_thesis_result_summaries(results_dir=tmp_path, output_dir=tmp_path)


def test_h3_summary_contains_no_wallet_addresses(tmp_path: Path) -> None:
    _write_source_artifacts(tmp_path)

    result = generate_thesis_result_summaries(results_dir=tmp_path, output_dir=tmp_path)

    h3_text = result.h3_path.read_text(encoding="utf-8")
    h3 = pd.read_csv(result.h3_path)
    assert "wallet_address" not in h3.columns
    assert "0x" not in h3_text


def test_h1_summary_excludes_rcp_even_if_source_artifact_contains_rcp(
    tmp_path: Path,
) -> None:
    _write_source_artifacts(tmp_path, include_rcp=True)

    h1 = build_h1_summary(tmp_path)

    joined = "\n".join(
        h1[["summary_id", "label", "metric"]].astype(str).agg(" ".join, axis=1).tolist()
    ).lower()
    assert "rcp" not in joined


def test_cli_returns_clear_error_for_missing_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["--results-dir", str(tmp_path), "--output-dir", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "ERROR: Required thesis summary source artifact" in captured.err


def _write_source_artifacts(path: Path, *, include_rcp: bool = False) -> None:
    brier = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "bs_polymarket": [0.10, 0.20],
            "bs_fivethirtyeight": [0.30, 0.40],
            "bs_always_50": [0.25, 0.25],
            "bs_prior_day": [0.12, 0.22],
        }
    )
    if include_rcp:
        brier["bs_rcp"] = [0.50, 0.45]
    brier.to_csv(path / "h1_brier_scores.csv", index=False)
    dm_results = [
        {
            "source_1": "Polymarket",
            "source_2": "FiveThirtyEight",
            "dm_statistic": -1.0,
            "p_value": 0.01,
            "n_obs": 2,
            "interpretation": "toy",
        },
        {
            "source_1": "Polymarket",
            "source_2": "RCP",
            "dm_statistic": -1.0,
            "p_value": 0.02,
            "n_obs": 2,
            "interpretation": "toy",
        },
    ]
    (path / "h1_diebold_mariano.json").write_text(
        json.dumps(dm_results),
        encoding="utf-8",
    )
    pd.DataFrame(
        {
            "event_id": ["evt_1"],
            "title": ["Toy event"],
            "window_label": ["primary_0d_to_1d"],
            "observed_days": [2],
            "final_cumulative_abnormal_change": [0.12],
            "estimation_observations": [13],
        }
    ).to_csv(path / "h2_event_window_summary.csv", index=False)
    (path / "h3_wallet_distribution_inventory.json").write_text(
        json.dumps(
            {
                "tier_counts": {
                    "tier_1_top_1pct": 1,
                    "tier_2_top_5pct": 2,
                    "tier_3_top_10pct": 3,
                    "tier_4_observed_baseline": 4,
                }
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame(
        {
            "tier": ["tier_1_top_1pct", "tier_2_top_5pct"],
            "lag_days": [1, 2],
            "correlation": [0.5, -0.2],
            "status": ["ok", "ok"],
        }
    ).to_csv(path / "h3_lead_lag_correlations.csv", index=False)
    pd.DataFrame(
        {
            "tier": ["tier_1_top_1pct", "tier_2_top_5pct"],
            "lag_days": [1, 2],
            "p_value": [0.03, 0.20],
            "status": ["ok", "ok"],
        }
    ).to_csv(path / "h3_granger_results.csv", index=False)
    (path / "h3_granger_metadata.json").write_text(
        json.dumps({"input": {"model_row_count": 20}}),
        encoding="utf-8",
    )
