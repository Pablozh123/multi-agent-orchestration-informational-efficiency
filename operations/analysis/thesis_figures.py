"""Generate thesis-facing figures from existing deterministic result artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_RESULTS_DIR = Path("data/results")


FigureWriter = Callable[[Path, Path], Path]


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required source artifact is missing: {path}")


def _save_figure(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()
    return path


def plot_h2_event_window_car(input_dir: Path, output_dir: Path) -> Path:
    """Plot final daily CAR-style H2 movements by event and selected window."""

    source = input_dir / "h2_event_window_summary.csv"
    _require_file(source)

    frame = pd.read_csv(source)
    required = {"event_id", "window_label", "final_cumulative_abnormal_change"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"H2 summary is missing columns: {sorted(missing)}")

    frame = frame.copy()
    frame["label"] = frame["event_id"].str.replace("evt_2024_", "", regex=False)
    frame["label"] = frame["label"].str.slice(0, 34)
    frame = frame.sort_values(["label", "window_label"])

    plt.figure(figsize=(10, max(5, len(frame) * 0.35)))
    colors = frame["window_label"].map(
        {
            "primary_0d_to_1d": "#2f6f9f",
            "secondary_minus_1d_to_3d": "#d9822b",
        }
    ).fillna("#6b7280")
    plt.barh(
        frame["label"] + " | " + frame["window_label"],
        frame["final_cumulative_abnormal_change"],
        color=colors,
    )
    plt.axvline(0, color="#222222", linewidth=0.8)
    plt.xlabel("Final cumulative abnormal change")
    plt.ylabel("Event window")
    plt.title("H2 daily event-window movements")
    return _save_figure(output_dir / "thesis_h2_event_window_car.png")


def plot_h3_wallet_tier_counts(input_dir: Path, output_dir: Path) -> Path:
    """Plot H3 wallet counts per dataset-relative tier."""

    source = input_dir / "h3_wallet_distribution_inventory.json"
    _require_file(source)

    payload = json.loads(source.read_text(encoding="utf-8"))
    tier_counts = payload.get("tier_counts")
    if not isinstance(tier_counts, dict) or not tier_counts:
        raise ValueError("H3 wallet inventory is missing non-empty tier_counts.")

    frame = pd.DataFrame(
        [{"tier": tier, "wallet_count": count} for tier, count in tier_counts.items()]
    ).sort_values("tier")

    plt.figure(figsize=(9, 5))
    plt.bar(frame["tier"], frame["wallet_count"], color="#3b7a57")
    plt.yscale("log")
    plt.xlabel("Dataset-relative wallet tier")
    plt.ylabel("Wallet count (log scale)")
    plt.title("H3 wallet tier counts")
    plt.xticks(rotation=20, ha="right")
    return _save_figure(output_dir / "thesis_h3_wallet_tier_counts.png")


def plot_h3_lead_time_amount(input_dir: Path, output_dir: Path) -> Path:
    """Plot H3 lead-time total wallet activity by tier and relative day."""

    source = input_dir / "h3_lead_time_histograms.csv"
    _require_file(source)

    frame = pd.read_csv(source)
    required = {"tier", "relative_day", "total_amount_usd", "window_label"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"H3 lead-time histogram is missing columns: {sorted(missing)}")

    frame = frame[frame["window_label"] == frame["window_label"].iloc[0]].copy()
    frame = frame.sort_values(["tier", "relative_day"])

    plt.figure(figsize=(10, 6))
    for tier, group in frame.groupby("tier"):
        plt.plot(group["relative_day"], group["total_amount_usd"], marker="o", label=tier)
    plt.yscale("log")
    plt.xlabel("Relative day")
    plt.ylabel("Total amount USD (log scale)")
    plt.title("H3 lead-time wallet activity by tier")
    plt.legend(fontsize="small")
    return _save_figure(output_dir / "thesis_h3_lead_time_amount.png")


def plot_h3_granger_pvalues(input_dir: Path, output_dir: Path) -> Path:
    """Plot H3 Granger p-values by lag and tier for successful tests."""

    source = input_dir / "h3_granger_results.csv"
    _require_file(source)

    frame = pd.read_csv(source)
    required = {"tier", "lag_days", "p_value", "status"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"H3 Granger results are missing columns: {sorted(missing)}")

    frame = frame[frame["status"] == "ok"].copy()
    if frame.empty:
        raise ValueError("H3 Granger results contain no successful rows.")

    pivot = frame.pivot_table(
        index="tier",
        columns="lag_days",
        values="p_value",
        aggfunc="min",
    ).sort_index()

    plt.figure(figsize=(9, 4.8))
    image = plt.imshow(pivot.to_numpy(), aspect="auto", cmap="viridis_r", vmin=0, vmax=1)
    plt.colorbar(image, label="p-value")
    plt.xticks(range(len(pivot.columns)), [str(col) for col in pivot.columns])
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.xlabel("Lag days")
    plt.ylabel("Dataset-relative wallet tier")
    plt.title("H3 Granger diagnostic p-values")
    return _save_figure(output_dir / "thesis_h3_granger_pvalues.png")


def generate_figures(
    input_dir: Path = DEFAULT_RESULTS_DIR,
    output_dir: Path = DEFAULT_RESULTS_DIR,
) -> dict[str, str]:
    """Generate all thesis-facing figures and metadata."""

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    writers: dict[str, FigureWriter] = {
        "h2_event_window_car": plot_h2_event_window_car,
        "h3_wallet_tier_counts": plot_h3_wallet_tier_counts,
        "h3_lead_time_amount": plot_h3_lead_time_amount,
        "h3_granger_pvalues": plot_h3_granger_pvalues,
    }

    figures = {
        name: str(writer(input_dir, output_dir))
        for name, writer in writers.items()
    }
    metadata = {
        "source_artifacts": [
            str(input_dir / "h2_event_window_summary.csv"),
            str(input_dir / "h3_wallet_distribution_inventory.json"),
            str(input_dir / "h3_lead_time_histograms.csv"),
            str(input_dir / "h3_granger_results.csv"),
        ],
        "figures": figures,
        "calculation_note": (
            "Figures are deterministic visualisations of existing result artifacts; "
            "no new statistical metrics are calculated."
        ),
    }
    metadata_path = output_dir / "thesis_figures_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    figures["metadata"] = str(metadata_path)
    return figures


def main() -> None:
    figures = generate_figures()
    for name, path in figures.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
