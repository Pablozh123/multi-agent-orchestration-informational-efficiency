"""Maintain a compact registry of bounded monitor live-window runs."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from operations.analysis.monitor_v2_dashboard import DASHBOARD_METADATA_OUTPUT
from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.collectors.polymarket_monitor_refresh import REFRESH_METADATA_OUTPUT
from operations.collectors.polymarket_rolling_history import ROLLING_SCORING_METADATA_OUTPUT


REGISTRY_OUTPUT = RESULTS_DIR / "monitor_v2_live_window_registry.csv"
REGISTRY_METADATA_OUTPUT = RESULTS_DIR / "monitor_v2_live_window_registry_metadata.json"

REGISTRY_COLUMNS = (
    "run_id",
    "run_label",
    "generated_at_utc",
    "source",
    "market_count",
    "bucket_count",
    "market_snapshot_row_count",
    "wallet_tier_snapshot_row_count",
    "scoring_row_count",
    "summary_row_count",
    "alert_count",
    "baseline_readiness",
    "baseline_observations",
    "min_baseline_observations",
    "production_like_baseline_available",
    "severity_counts_json",
    "status_counts_json",
    "refresh_metadata_path",
    "scoring_metadata_path",
    "dashboard_metadata_path",
    "claim_scope",
)


@dataclass(frozen=True)
class LiveWindowRegistryResult:
    """Summary of a live-window registry update."""

    registry_path: Path
    metadata_path: Path
    run_id: str
    row_count: int

    def to_dict(self) -> dict[str, int | str]:
        """Return a JSON-friendly registry summary."""

        return {
            "registry_path": str(self.registry_path),
            "metadata_path": str(self.metadata_path),
            "run_id": self.run_id,
            "row_count": self.row_count,
        }


def update_live_window_registry(
    *,
    refresh_metadata_path: Path = REFRESH_METADATA_OUTPUT,
    scoring_metadata_path: Path = ROLLING_SCORING_METADATA_OUTPUT,
    dashboard_metadata_path: Path = DASHBOARD_METADATA_OUTPUT,
    registry_path: Path = REGISTRY_OUTPUT,
    metadata_path: Path = REGISTRY_METADATA_OUTPUT,
    run_id: str | None = None,
    run_label: str = "",
) -> LiveWindowRegistryResult:
    """Upsert one compact live-window summary into the registry."""

    row = build_registry_row(
        refresh_metadata_path=refresh_metadata_path,
        scoring_metadata_path=scoring_metadata_path,
        dashboard_metadata_path=dashboard_metadata_path,
        run_id=run_id,
        run_label=run_label,
    )
    rows = _read_registry(registry_path)
    rows = [existing for existing in rows if existing["run_id"] != row["run_id"]]
    rows.append(row)
    rows.sort(key=lambda item: item["generated_at_utc"])

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "monitor_v2_live_window_registry",
            "compact_summary_only": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_llms": True,
            "does_not_send_orders": True,
        },
        "outputs": {
            "registry_path": str(registry_path),
            "row_count": len(rows),
            "latest_run_id": rows[-1]["run_id"],
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "latest_raw_artifacts_may_be_overwritten": True,
            "registry_preserves_compact_run_summaries_only": True,
            "no_causal_or_profitability_claim": True,
        },
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return LiveWindowRegistryResult(
        registry_path=registry_path,
        metadata_path=metadata_path,
        run_id=row["run_id"],
        row_count=len(rows),
    )


def build_registry_row(
    *,
    refresh_metadata_path: Path,
    scoring_metadata_path: Path,
    dashboard_metadata_path: Path,
    run_id: str | None = None,
    run_label: str = "",
) -> dict[str, str]:
    """Build one compact registry row from monitor metadata files."""

    refresh = _read_json(refresh_metadata_path)
    scoring = _read_json(scoring_metadata_path)
    dashboard = _read_json(dashboard_metadata_path)
    _assert_safe_outputs(refresh, scoring, dashboard)

    refresh_outputs = refresh.get("outputs", {})
    refresh_method = refresh.get("method", {})
    scoring_inputs = scoring.get("inputs", {})
    scoring_outputs = scoring.get("outputs", {})
    scoring_method = scoring.get("method", {})
    dashboard_outputs = dashboard.get("outputs", {})
    generated_at = str(refresh.get("generated_at_utc", ""))
    stable_run_id = run_id or _run_id_from_timestamp(generated_at)

    return {
        "run_id": stable_run_id,
        "run_label": run_label,
        "generated_at_utc": generated_at,
        "source": str(refresh_method.get("source", "")),
        "market_count": _as_str(dashboard_outputs.get("market_count", scoring_inputs.get("watchlist_row_count", 0))),
        "bucket_count": _as_str(refresh_outputs.get("bucket_count", dashboard_outputs.get("bucket_count", 0))),
        "market_snapshot_row_count": _as_str(scoring_inputs.get("market_snapshot_row_count", 0)),
        "wallet_tier_snapshot_row_count": _as_str(scoring_inputs.get("wallet_tier_snapshot_row_count", 0)),
        "scoring_row_count": _as_str(scoring_outputs.get("alert_row_count", 0)),
        "summary_row_count": _as_str(scoring_outputs.get("summary_row_count", dashboard_outputs.get("summary_row_count", 0))),
        "alert_count": _as_str(refresh_outputs.get("alert_count", scoring_outputs.get("alert_count", 0))),
        "baseline_readiness": str(
            refresh_outputs.get(
                "baseline_readiness",
                scoring_method.get("baseline_readiness", ""),
            )
        ),
        "baseline_observations": _as_str(refresh_method.get("baseline_observations", 0)),
        "min_baseline_observations": _as_str(refresh_method.get("min_baseline_observations", 0)),
        "production_like_baseline_available": str(
            bool(scoring_method.get("production_like_baseline_available", False))
        ),
        "severity_counts_json": json.dumps(
            scoring_outputs.get("severity_counts", {}),
            sort_keys=True,
        ),
        "status_counts_json": json.dumps(
            scoring_outputs.get("status_counts", {}),
            sort_keys=True,
        ),
        "refresh_metadata_path": str(refresh_metadata_path),
        "scoring_metadata_path": str(scoring_metadata_path),
        "dashboard_metadata_path": str(dashboard_metadata_path),
        "claim_scope": "descriptive_monitor_window_only",
    }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-metadata", type=Path, default=REFRESH_METADATA_OUTPUT)
    parser.add_argument("--scoring-metadata", type=Path, default=ROLLING_SCORING_METADATA_OUTPUT)
    parser.add_argument("--dashboard-metadata", type=Path, default=DASHBOARD_METADATA_OUTPUT)
    parser.add_argument("--registry-output", type=Path, default=REGISTRY_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=REGISTRY_METADATA_OUTPUT)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--run-label", default="")
    args = parser.parse_args(argv)

    try:
        result = update_live_window_registry(
            refresh_metadata_path=args.refresh_metadata,
            scoring_metadata_path=args.scoring_metadata,
            dashboard_metadata_path=args.dashboard_metadata,
            registry_path=args.registry_output,
            metadata_path=args.metadata_output,
            run_id=args.run_id,
            run_label=args.run_label,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _read_registry(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"metadata file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assert_safe_outputs(*metadata_items: dict[str, Any]) -> None:
    for item in metadata_items:
        outputs = item.get("outputs", {})
        if outputs.get("contains_wallet_addresses") is True:
            raise ValueError("metadata reports wallet-address exposure")
        if outputs.get("contains_order_instructions") is True:
            raise ValueError("metadata reports order instructions")


def _run_id_from_timestamp(value: str) -> str:
    compact = re.sub(r"[^0-9A-Za-z]+", "", value.replace("+00:00", "Z"))
    if not compact:
        raise ValueError("generated_at_utc is required when run_id is omitted")
    return f"window_{compact}"


def _as_str(value: object) -> str:
    return str(0 if value is None else value)


if __name__ == "__main__":
    raise SystemExit(main())
