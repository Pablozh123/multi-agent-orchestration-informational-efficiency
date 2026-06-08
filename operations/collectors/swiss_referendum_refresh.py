"""Refresh the Swiss 10-million referendum comparison in one bounded command.

The runner collects one read-only Polymarket snapshot and regenerates the
deterministic poll comparison artifacts. It is not a daemon and does not use
authenticated channels, order endpoints, agents, MCP tools, ML, LLMs, or
database writes.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

import httpx
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.analysis.swiss_referendum_efficiency import (
    COMPARISON_OUTPUT,
    DASHBOARD_OUTPUT,
    FIGURE_OUTPUT,
    INFORMATION_RESPONSE_FIGURE_OUTPUT,
    INFORMATION_RESPONSE_OUTPUT,
    LATEST_SOURCE_COMPARISON_OUTPUT,
    METADATA_OUTPUT,
    POLYMARKET_HISTORY_INPUT,
    POLL_IMPACT_OUTPUT,
    POLL_REACTION_WINDOWS_OUTPUT,
    POLL_INPUT,
    REACTION_FIGURE_OUTPUT,
    SOURCE_AUDIT_OUTPUT,
    SUMMARY_OUTPUT,
    generate_swiss_referendum_efficiency_outputs,
)
from operations.collectors.swiss_referendum_history import (
    HISTORY_METADATA_OUTPUT,
    collect_swiss_referendum_price_history,
)
from operations.collectors.swiss_referendum_polymarket import (
    SNAPSHOT_METADATA_OUTPUT,
    SNAPSHOT_OUTPUT,
    collect_swiss_referendum_polymarket_snapshot,
)


REFRESH_METADATA_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_refresh_metadata.json"
RUNNING_STATUS_OUTPUT = RESULTS_DIR / "swiss_referendum_10mio_running_status.json"


@dataclass(frozen=True)
class SwissReferendumRefreshResult:
    """Summary of a bounded refresh run."""

    snapshots_path: Path
    comparison_path: Path
    history_path: Path
    latest_source_comparison_path: Path
    poll_impact_path: Path
    poll_reaction_windows_path: Path
    information_response_path: Path
    source_audit_path: Path
    figure_path: Path
    reaction_figure_path: Path
    information_response_figure_path: Path
    dashboard_path: Path
    summary_path: Path
    metadata_path: Path
    running_status_path: Path
    snapshot_row_count: int
    history_row_count: int
    comparison_row_count: int
    poll_impact_row_count: int
    latest_yes_probability: float
    latest_raw_yes_gap: float | None
    latest_decided_yes_gap: float | None
    latest_divergence_label: str

    def to_dict(self) -> dict[str, float | int | str | None]:
        """Return a JSON-friendly summary."""

        return {
            "snapshots_path": str(self.snapshots_path),
            "comparison_path": str(self.comparison_path),
            "history_path": str(self.history_path),
            "latest_source_comparison_path": str(self.latest_source_comparison_path),
            "poll_impact_path": str(self.poll_impact_path),
            "poll_reaction_windows_path": str(self.poll_reaction_windows_path),
            "information_response_path": str(self.information_response_path),
            "source_audit_path": str(self.source_audit_path),
            "figure_path": str(self.figure_path),
            "reaction_figure_path": str(self.reaction_figure_path),
            "information_response_figure_path": str(
                self.information_response_figure_path
            ),
            "dashboard_path": str(self.dashboard_path),
            "summary_path": str(self.summary_path),
            "metadata_path": str(self.metadata_path),
            "running_status_path": str(self.running_status_path),
            "snapshot_row_count": self.snapshot_row_count,
            "history_row_count": self.history_row_count,
            "comparison_row_count": self.comparison_row_count,
            "poll_impact_row_count": self.poll_impact_row_count,
            "latest_yes_probability": self.latest_yes_probability,
            "latest_raw_yes_gap": self.latest_raw_yes_gap,
            "latest_decided_yes_gap": self.latest_decided_yes_gap,
            "latest_divergence_label": self.latest_divergence_label,
        }


def refresh_swiss_referendum_comparison(
    *,
    source: str = "mock",
    append: bool = True,
    collected_at_utc: str | None = None,
    poll_input_path: Path = POLL_INPUT,
    snapshots_path: Path = SNAPSHOT_OUTPUT,
    snapshot_metadata_path: Path = SNAPSHOT_METADATA_OUTPUT,
    history_path: Path = POLYMARKET_HISTORY_INPUT,
    history_metadata_path: Path = HISTORY_METADATA_OUTPUT,
    comparison_path: Path = COMPARISON_OUTPUT,
    latest_source_comparison_path: Path = LATEST_SOURCE_COMPARISON_OUTPUT,
    poll_impact_path: Path = POLL_IMPACT_OUTPUT,
    poll_reaction_windows_path: Path = POLL_REACTION_WINDOWS_OUTPUT,
    information_response_path: Path = INFORMATION_RESPONSE_OUTPUT,
    source_audit_path: Path = SOURCE_AUDIT_OUTPUT,
    figure_path: Path = FIGURE_OUTPUT,
    reaction_figure_path: Path = REACTION_FIGURE_OUTPUT,
    information_response_figure_path: Path = INFORMATION_RESPONSE_FIGURE_OUTPUT,
    dashboard_path: Path = DASHBOARD_OUTPUT,
    summary_path: Path = SUMMARY_OUTPUT,
    efficiency_metadata_path: Path = METADATA_OUTPUT,
    refresh_metadata_path: Path = REFRESH_METADATA_OUTPUT,
    running_status_path: Path = RUNNING_STATUS_OUTPUT,
    collect_history: bool = True,
    history_hours_before: int = 24,
    history_hours_after: int = 48,
    history_fidelity_minutes: int = 60,
    fresh_snapshot_minutes: int = 60,
    client: httpx.Client | None = None,
) -> SwissReferendumRefreshResult:
    """Collect one snapshot and regenerate deterministic comparison outputs."""

    if source not in {"mock", "live"}:
        raise ValueError("source must be either 'mock' or 'live'")
    if fresh_snapshot_minutes < 1:
        raise ValueError("fresh_snapshot_minutes must be >= 1")

    snapshot_result = collect_swiss_referendum_polymarket_snapshot(
        source=source,
        snapshots_path=snapshots_path,
        metadata_path=snapshot_metadata_path,
        collected_at_utc=collected_at_utc,
        append=append,
        client=client,
    )
    history_result = None
    if collect_history:
        history_result = collect_swiss_referendum_price_history(
            source=source,
            poll_input_path=poll_input_path,
            snapshots_path=snapshots_path,
            history_path=history_path,
            metadata_path=history_metadata_path,
            hours_before=history_hours_before,
            hours_after=history_hours_after,
            fidelity_minutes=history_fidelity_minutes,
            client=client,
        )
    efficiency_result = generate_swiss_referendum_efficiency_outputs(
        poll_input_path=poll_input_path,
        polymarket_snapshots_path=snapshots_path,
        polymarket_history_path=history_path if collect_history else None,
        comparison_path=comparison_path,
        latest_source_comparison_path=latest_source_comparison_path,
        poll_impact_path=poll_impact_path,
        poll_reaction_windows_path=poll_reaction_windows_path,
        information_response_path=information_response_path,
        source_audit_path=source_audit_path,
        figure_path=figure_path,
        reaction_figure_path=reaction_figure_path,
        information_response_figure_path=information_response_figure_path,
        dashboard_path=dashboard_path,
        summary_path=summary_path,
        metadata_path=efficiency_metadata_path,
    )
    running_status = build_running_status(
        snapshots_path=snapshots_path,
        history_path=history_path if collect_history else None,
        comparison_path=comparison_path,
        latest_source_comparison_path=latest_source_comparison_path,
        poll_impact_path=poll_impact_path,
        poll_reaction_windows_path=poll_reaction_windows_path,
        information_response_path=information_response_path,
        source_audit_path=source_audit_path,
        figure_path=figure_path,
        reaction_figure_path=reaction_figure_path,
        information_response_figure_path=information_response_figure_path,
        dashboard_path=dashboard_path,
        summary_path=summary_path,
        efficiency_metadata_path=efficiency_metadata_path,
        fresh_snapshot_minutes=fresh_snapshot_minutes,
    )
    metadata = _build_metadata(
        source=source,
        append=append,
        collected_at_utc=collected_at_utc,
        snapshot_result=snapshot_result.to_dict(),
        history_result={} if history_result is None else history_result.to_dict(),
        efficiency_result=efficiency_result.to_dict(),
        running_status=running_status,
    )
    running_status_path.parent.mkdir(parents=True, exist_ok=True)
    running_status_path.write_text(
        json.dumps(running_status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    refresh_metadata_path.parent.mkdir(parents=True, exist_ok=True)
    refresh_metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return SwissReferendumRefreshResult(
        snapshots_path=snapshot_result.snapshots_path,
        comparison_path=efficiency_result.comparison_path,
        history_path=history_path,
        latest_source_comparison_path=efficiency_result.latest_source_comparison_path,
        poll_impact_path=efficiency_result.poll_impact_path,
        poll_reaction_windows_path=efficiency_result.poll_reaction_windows_path,
        information_response_path=efficiency_result.information_response_path,
        source_audit_path=efficiency_result.source_audit_path,
        figure_path=efficiency_result.figure_path,
        reaction_figure_path=efficiency_result.reaction_figure_path,
        information_response_figure_path=(
            efficiency_result.information_response_figure_path
        ),
        dashboard_path=efficiency_result.dashboard_path,
        summary_path=efficiency_result.summary_path,
        metadata_path=refresh_metadata_path,
        running_status_path=running_status_path,
        snapshot_row_count=snapshot_result.row_count,
        history_row_count=0 if history_result is None else history_result.row_count,
        comparison_row_count=efficiency_result.comparison_row_count,
        poll_impact_row_count=efficiency_result.poll_impact_row_count,
        latest_yes_probability=snapshot_result.latest_yes_probability,
        latest_raw_yes_gap=efficiency_result.latest_raw_yes_gap,
        latest_decided_yes_gap=efficiency_result.latest_decided_yes_gap,
        latest_divergence_label=efficiency_result.latest_divergence_label,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("mock", "live"), default="mock")
    parser.add_argument("--no-append", action="store_true")
    parser.add_argument("--collected-at-utc", default=None)
    parser.add_argument("--poll-input", type=Path, default=POLL_INPUT)
    parser.add_argument("--snapshots-output", type=Path, default=SNAPSHOT_OUTPUT)
    parser.add_argument("--snapshot-metadata-output", type=Path, default=SNAPSHOT_METADATA_OUTPUT)
    parser.add_argument("--history-output", type=Path, default=POLYMARKET_HISTORY_INPUT)
    parser.add_argument("--history-metadata-output", type=Path, default=HISTORY_METADATA_OUTPUT)
    parser.add_argument("--skip-history", action="store_true")
    parser.add_argument("--history-hours-before", type=int, default=24)
    parser.add_argument("--history-hours-after", type=int, default=48)
    parser.add_argument("--history-fidelity-minutes", type=int, default=60)
    parser.add_argument("--comparison-output", type=Path, default=COMPARISON_OUTPUT)
    parser.add_argument(
        "--latest-source-comparison-output",
        type=Path,
        default=LATEST_SOURCE_COMPARISON_OUTPUT,
    )
    parser.add_argument("--poll-impact-output", type=Path, default=POLL_IMPACT_OUTPUT)
    parser.add_argument(
        "--poll-reaction-windows-output",
        type=Path,
        default=POLL_REACTION_WINDOWS_OUTPUT,
    )
    parser.add_argument(
        "--information-response-output",
        type=Path,
        default=INFORMATION_RESPONSE_OUTPUT,
    )
    parser.add_argument("--source-audit-output", type=Path, default=SOURCE_AUDIT_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=FIGURE_OUTPUT)
    parser.add_argument("--reaction-figure-output", type=Path, default=REACTION_FIGURE_OUTPUT)
    parser.add_argument(
        "--information-response-figure-output",
        type=Path,
        default=INFORMATION_RESPONSE_FIGURE_OUTPUT,
    )
    parser.add_argument("--dashboard-output", type=Path, default=DASHBOARD_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SUMMARY_OUTPUT)
    parser.add_argument("--efficiency-metadata-output", type=Path, default=METADATA_OUTPUT)
    parser.add_argument("--refresh-metadata-output", type=Path, default=REFRESH_METADATA_OUTPUT)
    parser.add_argument("--running-status-output", type=Path, default=RUNNING_STATUS_OUTPUT)
    parser.add_argument("--fresh-snapshot-minutes", type=int, default=60)
    args = parser.parse_args(argv)

    try:
        result = refresh_swiss_referendum_comparison(
            source=args.source,
            append=not args.no_append,
            collected_at_utc=args.collected_at_utc,
            poll_input_path=args.poll_input,
            snapshots_path=args.snapshots_output,
            snapshot_metadata_path=args.snapshot_metadata_output,
            history_path=args.history_output,
            history_metadata_path=args.history_metadata_output,
            comparison_path=args.comparison_output,
            latest_source_comparison_path=args.latest_source_comparison_output,
            poll_impact_path=args.poll_impact_output,
            poll_reaction_windows_path=args.poll_reaction_windows_output,
            information_response_path=args.information_response_output,
            source_audit_path=args.source_audit_output,
            figure_path=args.figure_output,
            reaction_figure_path=args.reaction_figure_output,
            information_response_figure_path=args.information_response_figure_output,
            dashboard_path=args.dashboard_output,
            summary_path=args.summary_output,
            efficiency_metadata_path=args.efficiency_metadata_output,
            refresh_metadata_path=args.refresh_metadata_output,
            running_status_path=args.running_status_output,
            collect_history=not args.skip_history,
            history_hours_before=args.history_hours_before,
            history_hours_after=args.history_hours_after,
            history_fidelity_minutes=args.history_fidelity_minutes,
            fresh_snapshot_minutes=args.fresh_snapshot_minutes,
        )
    except (httpx.HTTPError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def build_running_status(
    *,
    snapshots_path: Path,
    history_path: Path | None,
    comparison_path: Path,
    latest_source_comparison_path: Path,
    poll_impact_path: Path,
    poll_reaction_windows_path: Path,
    information_response_path: Path,
    source_audit_path: Path,
    figure_path: Path,
    reaction_figure_path: Path,
    information_response_figure_path: Path,
    dashboard_path: Path,
    summary_path: Path,
    efficiency_metadata_path: Path,
    fresh_snapshot_minutes: int = 60,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    """Build a deterministic status block for the local running view."""

    if fresh_snapshot_minutes < 1:
        raise ValueError("fresh_snapshot_minutes must be >= 1")
    generated_at = (generated_at_utc or datetime.now(UTC)).replace(microsecond=0)
    snapshot_info = _snapshot_recency(
        snapshots_path=snapshots_path,
        generated_at_utc=generated_at,
        fresh_snapshot_minutes=fresh_snapshot_minutes,
    )
    required_outputs = {
        "snapshots": snapshots_path,
        "comparison": comparison_path,
        "latest_source_comparison": latest_source_comparison_path,
        "poll_impacts": poll_impact_path,
        "poll_reaction_windows": poll_reaction_windows_path,
        "information_response": information_response_path,
        "source_audit": source_audit_path,
        "figure": figure_path,
        "reaction_figure": reaction_figure_path,
        "information_response_figure": information_response_figure_path,
        "dashboard": dashboard_path,
        "summary": summary_path,
        "efficiency_metadata": efficiency_metadata_path,
    }
    if history_path is not None:
        required_outputs["history"] = history_path
    output_status = {
        name: {"path": str(path), "exists": path.exists()}
        for name, path in sorted(required_outputs.items())
    }
    all_outputs_exist = all(item["exists"] for item in output_status.values())
    ready = all_outputs_exist and snapshot_info["snapshot_recency_status"] == "fresh"
    return {
        "generated_at_utc": generated_at.isoformat(),
        "manual_refresh_command": (
            ".\\.venv\\Scripts\\python.exe -m "
            "operations.collectors.swiss_referendum_refresh --source live"
        ),
        "method": {
            "name": "swiss_referendum_10mio_running_status",
            "fresh_snapshot_minutes": fresh_snapshot_minutes,
            "manual_refresh_only": True,
            "read_only": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_order_endpoints": True,
        },
        "status": {
            **snapshot_info,
            "all_outputs_exist": all_outputs_exist,
            "ready_for_running_view": ready,
        },
        "outputs": output_status,
        "limitations": {
            "status_is_local_artifact_recency_only": True,
            "does_not_imply_market_data_completeness": True,
            "does_not_identify_causality_or_tradeability": True,
        },
    }


def _snapshot_recency(
    *,
    snapshots_path: Path,
    generated_at_utc: datetime,
    fresh_snapshot_minutes: int,
) -> dict[str, Any]:
    if not snapshots_path.exists():
        return {
            "latest_snapshot_at_utc": "",
            "snapshot_age_minutes": None,
            "snapshot_recency_status": "missing",
            "snapshot_row_count": 0,
        }
    frame = pd.read_csv(snapshots_path, dtype=str, keep_default_na=False)
    if "collected_at_utc" not in frame.columns:
        raise ValueError("snapshot file missing collected_at_utc column")
    if frame.empty:
        return {
            "latest_snapshot_at_utc": "",
            "snapshot_age_minutes": None,
            "snapshot_recency_status": "missing",
            "snapshot_row_count": 0,
        }
    collected = pd.to_datetime(frame["collected_at_utc"], errors="raise", utc=True)
    latest = collected.max()
    generated = pd.Timestamp(generated_at_utc).tz_convert("UTC")
    age_minutes = max(0.0, (generated - latest).total_seconds() / 60.0)
    return {
        "latest_snapshot_at_utc": latest.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "snapshot_age_minutes": round(age_minutes, 3),
        "snapshot_recency_status": (
            "fresh" if age_minutes <= fresh_snapshot_minutes else "stale"
        ),
        "snapshot_row_count": int(len(frame)),
    }


def _build_metadata(
    *,
    source: str,
    append: bool,
    collected_at_utc: str | None,
    snapshot_result: dict[str, Any],
    history_result: dict[str, Any],
    efficiency_result: dict[str, Any],
    running_status: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "swiss_referendum_10mio_bounded_refresh",
            "source": source,
            "append_to_snapshot_history": append,
            "requested_collected_at_utc": "" if collected_at_utc is None else collected_at_utc,
            "bounded_single_snapshot_refresh": True,
            "collects_bounded_price_history": bool(history_result),
            "not_a_background_daemon": True,
            "read_only": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_order_endpoints": True,
        },
        "outputs": {
            "snapshot_result": snapshot_result,
            "history_result": history_result,
            "efficiency_result": efficiency_result,
            "running_status": running_status,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "manual_refresh_only": True,
            "no_causal_claim_from_refresh": True,
            "no_profitability_or_tradeability_claim": True,
            "poll_release_impact_requires_pre_and_post_snapshots": True,
        },
    }


if __name__ == "__main__":
    raise SystemExit(main())
