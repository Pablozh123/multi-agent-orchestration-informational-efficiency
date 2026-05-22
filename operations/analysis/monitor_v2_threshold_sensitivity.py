"""Generate deterministic monitor v2 threshold-sensitivity reports.

The report reads existing bounded monitor snapshot files and compares the
current Rule C configuration with clearly labelled diagnostic alternatives.
It writes aggregate file-based outputs only and does not collect data, write to
the database, call LLMs, activate agents or MCP tools, or send orders.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from operations.analysis.monitor_v2_snapshot import (
    SEVERITY_RANK,
    build_monitor_v2_alert_rows,
    load_snapshot_frame,
)
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_rolling_history import (
    ROLLING_SCORING_SNAPSHOTS_OUTPUT,
)


THRESHOLD_SENSITIVITY_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_threshold_sensitivity.csv"
)
THRESHOLD_SENSITIVITY_BY_FAMILY_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_threshold_sensitivity_by_family.csv"
)
THRESHOLD_SENSITIVITY_FIGURE_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_threshold_sensitivity.png"
)
THRESHOLD_SENSITIVITY_METADATA_OUTPUT = (
    RESULTS_DIR / "monitor_v2_polymarket_threshold_sensitivity_metadata.json"
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "scenario_id",
    "scenario_type",
    "baseline_observations",
    "min_baseline_observations",
    "rule_label",
    "row_count",
    "alert_count",
    "info_count",
    "watch_count",
    "high_count",
    "critical_count",
    "ok_count",
    "zero_mad_count",
    "insufficient_baseline_count",
    "shadow_percentile_ge_90_count",
    "shadow_percentile_ge_95_count",
    "max_robust_z",
    "max_percentile_rank",
    "likely_driver",
    "interpretation",
    "limitation",
    "claim_scope",
)

BY_FAMILY_COLUMNS: tuple[str, ...] = (
    "scenario_id",
    "anomaly_family",
    "metric_name",
    "tier",
    "row_count",
    "alert_count",
    "ok_count",
    "zero_mad_count",
    "insufficient_baseline_count",
    "shadow_percentile_ge_95_count",
    "max_robust_z",
    "max_percentile_rank",
)


@dataclass(frozen=True)
class SensitivityScenario:
    """A labelled scoring configuration for threshold sensitivity."""

    scenario_id: str
    scenario_type: str
    baseline_observations: int
    min_baseline_observations: int
    rule_label: str


@dataclass(frozen=True)
class ThresholdSensitivityResult:
    """Summary of generated threshold-sensitivity artifacts."""

    summary_path: Path
    by_family_path: Path
    figure_path: Path
    metadata_path: Path
    scenario_count: int
    default_alert_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly summary."""

        return {
            "summary_path": str(self.summary_path),
            "by_family_path": str(self.by_family_path),
            "figure_path": str(self.figure_path),
            "metadata_path": str(self.metadata_path),
            "scenario_count": self.scenario_count,
            "default_alert_count": self.default_alert_count,
        }


DEFAULT_SCENARIOS: tuple[SensitivityScenario, ...] = (
    SensitivityScenario(
        scenario_id="default_rule_c_30_20",
        scenario_type="default",
        baseline_observations=30,
        min_baseline_observations=20,
        rule_label="Rule C default; production-like 30/20 baseline",
    ),
    SensitivityScenario(
        scenario_id="diagnostic_rule_c_30_10",
        scenario_type="diagnostic_sensitivity",
        baseline_observations=30,
        min_baseline_observations=10,
        rule_label="Rule C with lower minimum baseline; diagnostic only",
    ),
    SensitivityScenario(
        scenario_id="diagnostic_rule_c_10_5",
        scenario_type="diagnostic_sensitivity",
        baseline_observations=10,
        min_baseline_observations=5,
        rule_label="Rule C with shorter baseline; diagnostic only",
    ),
    SensitivityScenario(
        scenario_id="diagnostic_rule_c_5_3",
        scenario_type="diagnostic_sensitivity",
        baseline_observations=5,
        min_baseline_observations=3,
        rule_label="Rule C with very short baseline; diagnostic only",
    ),
)


def generate_threshold_sensitivity_report(
    *,
    snapshots_path: Path = ROLLING_SCORING_SNAPSHOTS_OUTPUT,
    summary_path: Path = THRESHOLD_SENSITIVITY_OUTPUT,
    by_family_path: Path = THRESHOLD_SENSITIVITY_BY_FAMILY_OUTPUT,
    figure_path: Path = THRESHOLD_SENSITIVITY_FIGURE_OUTPUT,
    metadata_path: Path = THRESHOLD_SENSITIVITY_METADATA_OUTPUT,
    scenarios: Sequence[SensitivityScenario] = DEFAULT_SCENARIOS,
) -> ThresholdSensitivityResult:
    """Write aggregate sensitivity reports from an existing snapshot file."""

    if not scenarios:
        raise ValueError("at least one threshold-sensitivity scenario is required")
    snapshots = load_snapshot_frame(snapshots_path)
    summary_rows: list[dict[str, object]] = []
    family_rows: list[dict[str, object]] = []
    for scenario in scenarios:
        scored = build_monitor_v2_alert_rows(
            snapshots,
            baseline_observations=scenario.baseline_observations,
            min_baseline_observations=scenario.min_baseline_observations,
        )
        summary_rows.append(_summarize_scenario(scored, scenario))
        family_rows.extend(_summarize_by_family(scored, scenario))

    summary = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)
    by_family = pd.DataFrame(family_rows, columns=BY_FAMILY_COLUMNS)
    for path, frame in ((summary_path, summary), (by_family_path, by_family)):
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)

    _write_sensitivity_figure(summary, figure_path)
    metadata = _build_metadata(
        snapshots=snapshots,
        summary=summary,
        by_family=by_family,
        snapshots_path=snapshots_path,
        summary_path=summary_path,
        by_family_path=by_family_path,
        figure_path=figure_path,
        scenarios=scenarios,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    default_alert_count = int(
        summary.loc[summary["scenario_type"] == "default", "alert_count"].sum()
    )
    return ThresholdSensitivityResult(
        summary_path=summary_path,
        by_family_path=by_family_path,
        figure_path=figure_path,
        metadata_path=metadata_path,
        scenario_count=len(summary),
        default_alert_count=default_alert_count,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, default=ROLLING_SCORING_SNAPSHOTS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=THRESHOLD_SENSITIVITY_OUTPUT)
    parser.add_argument(
        "--by-family-output",
        type=Path,
        default=THRESHOLD_SENSITIVITY_BY_FAMILY_OUTPUT,
    )
    parser.add_argument("--figure-output", type=Path, default=THRESHOLD_SENSITIVITY_FIGURE_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=THRESHOLD_SENSITIVITY_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_threshold_sensitivity_report(
            snapshots_path=args.snapshots,
            summary_path=args.summary_output,
            by_family_path=args.by_family_output,
            figure_path=args.figure_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _summarize_scenario(
    scored: pd.DataFrame,
    scenario: SensitivityScenario,
) -> dict[str, object]:
    severity_counts = _counts(scored["severity"])
    status_counts = _counts(scored["status"])
    alert_count = int((scored["severity"] != "none").sum())
    shadow_90 = _shadow_percentile_count(scored, 0.90)
    shadow_95 = _shadow_percentile_count(scored, 0.95)
    likely_driver = _likely_driver(
        alert_count=alert_count,
        ok_count=status_counts.get("ok", 0),
        zero_mad_count=status_counts.get("zero_mad", 0),
        insufficient_count=status_counts.get("insufficient_baseline", 0),
        shadow_95_count=shadow_95,
        scenario_type=scenario.scenario_type,
    )
    return {
        "scenario_id": scenario.scenario_id,
        "scenario_type": scenario.scenario_type,
        "baseline_observations": scenario.baseline_observations,
        "min_baseline_observations": scenario.min_baseline_observations,
        "rule_label": scenario.rule_label,
        "row_count": int(len(scored)),
        "alert_count": alert_count,
        "info_count": severity_counts.get("info", 0),
        "watch_count": severity_counts.get("watch", 0),
        "high_count": severity_counts.get("high", 0),
        "critical_count": severity_counts.get("critical", 0),
        "ok_count": status_counts.get("ok", 0),
        "zero_mad_count": status_counts.get("zero_mad", 0),
        "insufficient_baseline_count": status_counts.get("insufficient_baseline", 0),
        "shadow_percentile_ge_90_count": shadow_90,
        "shadow_percentile_ge_95_count": shadow_95,
        "max_robust_z": _safe_max(scored["robust_z"]),
        "max_percentile_rank": _safe_max(scored["rolling_percentile_rank"]),
        "likely_driver": likely_driver,
        "interpretation": _interpretation(
            scenario=scenario,
            alert_count=alert_count,
            likely_driver=likely_driver,
        ),
        "limitation": (
            "threshold sensitivity on bounded read-only Polymarket files; "
            "non-default scenarios are diagnostics only"
        ),
        "claim_scope": "descriptive_threshold_sensitivity_only",
    }


def _summarize_by_family(
    scored: pd.DataFrame,
    scenario: SensitivityScenario,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    group_columns = ["anomaly_family", "metric_name", "tier"]
    for keys, group in scored.groupby(group_columns, sort=True, dropna=False):
        values = dict(zip(group_columns, keys))
        status_counts = _counts(group["status"])
        rows.append(
            {
                "scenario_id": scenario.scenario_id,
                **values,
                "row_count": int(len(group)),
                "alert_count": int((group["severity"] != "none").sum()),
                "ok_count": status_counts.get("ok", 0),
                "zero_mad_count": status_counts.get("zero_mad", 0),
                "insufficient_baseline_count": status_counts.get("insufficient_baseline", 0),
                "shadow_percentile_ge_95_count": _shadow_percentile_count(group, 0.95),
                "max_robust_z": _safe_max(group["robust_z"]),
                "max_percentile_rank": _safe_max(group["rolling_percentile_rank"]),
            }
        )
    return rows


def _write_sensitivity_figure(summary: pd.DataFrame, figure_path: Path) -> None:
    labels = summary["scenario_id"].astype(str).tolist()
    alert_counts = pd.to_numeric(summary["alert_count"], errors="coerce").fillna(0)
    shadow_counts = pd.to_numeric(
        summary["shadow_percentile_ge_95_count"],
        errors="coerce",
    ).fillna(0)

    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 5.5), constrained_layout=True)
    positions = range(len(labels))
    ax.bar(
        [position - 0.18 for position in positions],
        alert_counts,
        width=0.36,
        label="Rule C alerts",
        color="#315c72",
    )
    ax.bar(
        [position + 0.18 for position in positions],
        shadow_counts,
        width=0.36,
        label="Percentile >= 0.95 shadow rows",
        color="#b57f50",
    )
    ax.set_title("Monitor v2 threshold sensitivity on live baseline")
    ax.set_ylabel("Rows")
    ax.set_xticks(list(positions))
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.savefig(figure_path, dpi=150)
    plt.close(fig)


def _build_metadata(
    *,
    snapshots: pd.DataFrame,
    summary: pd.DataFrame,
    by_family: pd.DataFrame,
    snapshots_path: Path,
    summary_path: Path,
    by_family_path: Path,
    figure_path: Path,
    scenarios: Sequence[SensitivityScenario],
) -> dict[str, Any]:
    default_rows = summary[summary["scenario_type"] == "default"]
    default_alert_count = int(default_rows["alert_count"].sum())
    default_driver = (
        ""
        if default_rows.empty
        else str(default_rows.iloc[0]["likely_driver"])
    )
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_polymarket_threshold_sensitivity",
            "input_mode": "existing_bounded_scoring_snapshots",
            "default_rule": "Rule C combined-family confirmation",
            "default_rule_unchanged": True,
            "non_default_scenarios_are_diagnostic_only": True,
            "scenario_count": len(scenarios),
            "uses_existing_files_only": True,
        },
        "inputs": {
            "snapshots_path": str(snapshots_path),
            "snapshot_rows": int(len(snapshots)),
            "market_count": int(snapshots["market_id"].nunique()),
            "timestamp_count": int(snapshots["timestamp_utc"].nunique()),
        },
        "outputs": {
            "summary_path": str(summary_path),
            "by_family_path": str(by_family_path),
            "figure_path": str(figure_path),
            "summary_rows": int(len(summary)),
            "by_family_rows": int(len(by_family)),
            "default_alert_count": default_alert_count,
            "default_likely_driver": default_driver,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "scenarios": [scenario.__dict__ for scenario in scenarios],
        "interpretation": {
            "default_result": (
                "Rule C did not trigger in the observed production-like live "
                "baseline" if default_alert_count == 0 else
                "Rule C produced descriptive alerts in the observed baseline"
            ),
            "zero_alert_caveat": (
                "Zero alerts do not prove that the broader market was quiet, "
                "efficient, inefficient, causal, or usable for execution."
            ),
            "recommended_next_step": _recommended_next_step(summary),
        },
        "limitations": {
            "read_only_existing_files_only": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_rcp": True,
            "does_not_send_orders": True,
            "no_profitability_or_private_information_claim": True,
        },
    }


def _recommended_next_step(summary: pd.DataFrame) -> str:
    default = summary[summary["scenario_type"] == "default"]
    diagnostics = summary[summary["scenario_type"] != "default"]
    if default.empty:
        return "review_missing_default_scenario"
    if int(default.iloc[0]["alert_count"]) > 0:
        return "review_default_rule_alert_rows"
    if (pd.to_numeric(diagnostics["alert_count"], errors="coerce") > 0).any():
        return "review_diagnostic_alert_rows_before_any_rule_change"
    if int(default.iloc[0]["shadow_percentile_ge_95_count"]) > 0:
        return "review_zero_mad_percentile_shadow_rows_before_threshold_changes"
    return "consider_collecting_more_buckets_or_expanding_watchlist_after_review"


def _likely_driver(
    *,
    alert_count: int,
    ok_count: int,
    zero_mad_count: int,
    insufficient_count: int,
    shadow_95_count: int,
    scenario_type: str,
) -> str:
    if alert_count > 0 and scenario_type == "default":
        return "default_rule_c_alerts_present"
    if alert_count > 0:
        return "diagnostic_alerts_under_relaxed_baseline"
    if ok_count == 0 and zero_mad_count > 0:
        return "zero_mad_after_baseline_available"
    if shadow_95_count > 0 and zero_mad_count > 0:
        return "percentile_shadow_rows_but_zero_mad_blocks_robust_score"
    if insufficient_count > 0 and zero_mad_count == 0:
        return "insufficient_baseline"
    return "limited_metric_movement_under_rule_c"


def _interpretation(
    *,
    scenario: SensitivityScenario,
    alert_count: int,
    likely_driver: str,
) -> str:
    if scenario.scenario_type == "default":
        if alert_count == 0:
            return (
                "Default Rule C produced no alerts in this observed window; "
                f"main diagnostic driver: {likely_driver}."
            )
        return "Default Rule C produced descriptive alerts; review rows before wording."
    return (
        f"Diagnostic sensitivity only; produced {alert_count} non-default alert "
        f"rows; driver: {likely_driver}."
    )


def _shadow_percentile_count(scored: pd.DataFrame, threshold: float) -> int:
    percentiles = pd.to_numeric(scored["rolling_percentile_rank"], errors="coerce")
    return int((percentiles >= threshold).sum())


def _counts(values: Iterable[object]) -> dict[str, int]:
    counts = pd.Series(list(values)).value_counts().sort_index()
    return {str(key): int(value) for key, value in counts.items()}


def _safe_max(values: pd.Series) -> float | None:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return None
    return float(clean.max())


if __name__ == "__main__":
    raise SystemExit(main())
