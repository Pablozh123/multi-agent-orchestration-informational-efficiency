"""Compare wallet-pattern candidates with curated reference cases.

The similarity score is a deterministic pattern-overlap diagnostic. It is not a
probability, accusation, causal result, profitability result, or automated
decision.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from operations.analysis.run_h2_event_windows import RESULTS_DIR
from operations.analysis.wallet_reference_pattern_features import FEATURE_OUTPUT


SIMILARITY_OUTPUT = RESULTS_DIR / "wallet_reference_similarity_scores.csv"
SIMILARITY_SUMMARY_OUTPUT = RESULTS_DIR / "wallet_reference_similarity_summary.csv"
SIMILARITY_FIGURE_OUTPUT = RESULTS_DIR / "wallet_reference_similarity_matrix.png"
SIMILARITY_DASHBOARD_OUTPUT = RESULTS_DIR / "wallet_reference_similarity_dashboard.html"
SIMILARITY_METADATA_OUTPUT = RESULTS_DIR / "wallet_reference_similarity_metadata.json"

REQUIRED_FEATURE_COLUMNS: tuple[str, ...] = (
    "case_id",
    "case_type",
    "pattern_label",
    "feature_status",
    "fact_source",
    "evidence_status",
    "claim_scope",
    "requires_human_review",
)

SCORE_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "candidate_type",
    "reference_case_id",
    "reference_case_type",
    "similarity_score",
    "matched_pattern_count",
    "reference_pattern_count",
    "candidate_pattern_count",
    "matched_patterns",
    "missing_reference_patterns",
    "extra_candidate_patterns",
    "match_label",
    "claim_scope",
    "requires_human_review",
    "allowed_interpretation",
    "limitation",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "candidate_id",
    "candidate_type",
    "best_reference_case_id",
    "best_reference_case_type",
    "best_similarity_score",
    "matched_patterns",
    "match_label",
    "allowed_interpretation",
    "limitation",
)


@dataclass(frozen=True)
class ReferenceSimilarityResult:
    """Summary of generated reference-similarity artifacts."""

    scores_path: Path
    summary_path: Path
    figure_path: Path
    dashboard_path: Path
    metadata_path: Path
    candidate_count: int
    comparison_count: int
    max_non_self_similarity: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-friendly result summary."""

        return {
            "scores_path": str(self.scores_path),
            "summary_path": str(self.summary_path),
            "figure_path": str(self.figure_path),
            "dashboard_path": str(self.dashboard_path),
            "metadata_path": str(self.metadata_path),
            "candidate_count": self.candidate_count,
            "comparison_count": self.comparison_count,
            "max_non_self_similarity": self.max_non_self_similarity,
        }


def build_reference_similarity_scores(
    candidate_features: pd.DataFrame,
    reference_features: pd.DataFrame,
) -> pd.DataFrame:
    """Return pattern-overlap rows for candidates against references."""

    _validate_feature_frame(candidate_features, "candidate features")
    _validate_feature_frame(reference_features, "reference features")
    _reject_wallet_address_columns(candidate_features, "candidate features")
    _reject_wallet_address_columns(reference_features, "reference features")

    candidate_profiles = _profiles(candidate_features)
    reference_profiles = _profiles(reference_features)
    rows: list[dict[str, object]] = []
    for candidate_id, candidate in sorted(candidate_profiles.items()):
        candidate_patterns = candidate["patterns"]
        for reference_id, reference in sorted(reference_profiles.items()):
            reference_patterns = reference["patterns"]
            matched = sorted(candidate_patterns & reference_patterns)
            missing = sorted(reference_patterns - candidate_patterns)
            extra = sorted(candidate_patterns - reference_patterns)
            denominator = len(reference_patterns)
            score = 0.0 if denominator == 0 else len(matched) / denominator
            rows.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_type": candidate["case_type"],
                    "reference_case_id": reference_id,
                    "reference_case_type": reference["case_type"],
                    "similarity_score": round(score, 6),
                    "matched_pattern_count": len(matched),
                    "reference_pattern_count": len(reference_patterns),
                    "candidate_pattern_count": len(candidate_patterns),
                    "matched_patterns": _join(matched),
                    "missing_reference_patterns": _join(missing),
                    "extra_candidate_patterns": _join(extra),
                    "match_label": _match_label(score, len(matched), candidate_id == reference_id),
                    "claim_scope": "reference_pattern_similarity_only",
                    "requires_human_review": True,
                    "allowed_interpretation": _allowed_interpretation(
                        score=score,
                        is_self_match=candidate_id == reference_id,
                    ),
                    "limitation": (
                        "Equal-weight label overlap from curated reference-pattern "
                        "features; not a probability or misconduct finding."
                    ),
                }
            )
    return pd.DataFrame(rows, columns=SCORE_COLUMNS)


def build_reference_similarity_summary(scores: pd.DataFrame) -> pd.DataFrame:
    """Return one best-match row per candidate."""

    _require_columns(scores, SCORE_COLUMNS, "similarity scores")
    rows: list[dict[str, object]] = []
    for candidate_id, group in scores.groupby("candidate_id", sort=True):
        sorted_group = group.sort_values(
            ["similarity_score", "matched_pattern_count", "reference_case_id"],
            ascending=[False, False, True],
        )
        best = sorted_group.iloc[0].to_dict()
        rows.append(
            {
                "candidate_id": candidate_id,
                "candidate_type": best["candidate_type"],
                "best_reference_case_id": best["reference_case_id"],
                "best_reference_case_type": best["reference_case_type"],
                "best_similarity_score": best["similarity_score"],
                "matched_patterns": best["matched_patterns"],
                "match_label": best["match_label"],
                "allowed_interpretation": best["allowed_interpretation"],
                "limitation": best["limitation"],
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def generate_wallet_reference_similarity(
    *,
    candidate_features_path: Path = FEATURE_OUTPUT,
    reference_features_path: Path = FEATURE_OUTPUT,
    scores_path: Path = SIMILARITY_OUTPUT,
    summary_path: Path = SIMILARITY_SUMMARY_OUTPUT,
    figure_path: Path = SIMILARITY_FIGURE_OUTPUT,
    dashboard_path: Path = SIMILARITY_DASHBOARD_OUTPUT,
    metadata_path: Path = SIMILARITY_METADATA_OUTPUT,
) -> ReferenceSimilarityResult:
    """Write similarity scores, summary, figure, dashboard, and metadata."""

    candidate_features = _read_features(candidate_features_path, "candidate features")
    reference_features = _read_features(reference_features_path, "reference features")
    scores = build_reference_similarity_scores(candidate_features, reference_features)
    summary = build_reference_similarity_summary(scores)

    for path, frame in ((scores_path, scores), (summary_path, summary)):
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)

    _write_similarity_figure(scores, figure_path)
    _write_similarity_dashboard(
        scores=scores,
        summary=summary,
        features=candidate_features,
        figure_path=figure_path,
        dashboard_path=dashboard_path,
    )
    metadata = _build_metadata(
        scores=scores,
        summary=summary,
        candidate_features_path=candidate_features_path,
        reference_features_path=reference_features_path,
        scores_path=scores_path,
        summary_path=summary_path,
        figure_path=figure_path,
        dashboard_path=dashboard_path,
    )
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return ReferenceSimilarityResult(
        scores_path=scores_path,
        summary_path=summary_path,
        figure_path=figure_path,
        dashboard_path=dashboard_path,
        metadata_path=metadata_path,
        candidate_count=int(scores["candidate_id"].nunique()),
        comparison_count=int(len(scores)),
        max_non_self_similarity=_max_non_self_similarity(scores),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-features", type=Path, default=FEATURE_OUTPUT)
    parser.add_argument("--reference-features", type=Path, default=FEATURE_OUTPUT)
    parser.add_argument("--scores-output", type=Path, default=SIMILARITY_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=SIMILARITY_SUMMARY_OUTPUT)
    parser.add_argument("--figure-output", type=Path, default=SIMILARITY_FIGURE_OUTPUT)
    parser.add_argument("--dashboard-output", type=Path, default=SIMILARITY_DASHBOARD_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=SIMILARITY_METADATA_OUTPUT)
    args = parser.parse_args(argv)

    try:
        result = generate_wallet_reference_similarity(
            candidate_features_path=args.candidate_features,
            reference_features_path=args.reference_features,
            scores_path=args.scores_output,
            summary_path=args.summary_output,
            figure_path=args.figure_output,
            dashboard_path=args.dashboard_output,
            metadata_path=args.metadata_output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def _profiles(features: pd.DataFrame) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    triggered = features[features["feature_status"] == "triggered"].copy()
    for case_id, group in triggered.groupby("case_id", sort=True):
        case_type = str(group["case_type"].iloc[0])
        profiles[str(case_id)] = {
            "case_type": case_type,
            "patterns": set(group["pattern_label"].astype(str).tolist()),
        }
    for case_id, group in features.groupby("case_id", sort=True):
        profiles.setdefault(
            str(case_id),
            {
                "case_type": str(group["case_type"].iloc[0]),
                "patterns": set(),
            },
        )
    return profiles


def _write_similarity_figure(scores: pd.DataFrame, figure_path: Path) -> None:
    pivot = scores.pivot(
        index="candidate_id",
        columns="reference_case_id",
        values="similarity_score",
    ).fillna(0.0)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    fig_width = max(7.5, len(pivot.columns) * 2.4)
    fig_height = max(4.8, len(pivot.index) * 1.0)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), constrained_layout=True)
    image = ax.imshow(pivot.to_numpy(), vmin=0, vmax=1, cmap="YlGnBu")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=20, ha="right")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Reference case")
    ax.set_ylabel("Candidate")
    ax.set_title("Wallet reference-case pattern similarity")
    for row_index, row_label in enumerate(pivot.index):
        for col_index, col_label in enumerate(pivot.columns):
            value = float(pivot.loc[row_label, col_label])
            ax.text(col_index, row_index, f"{value:.2f}", ha="center", va="center")
    fig.colorbar(image, ax=ax, label="Pattern-overlap score")
    fig.savefig(figure_path, dpi=150)
    plt.close(fig)


def _write_similarity_dashboard(
    *,
    scores: pd.DataFrame,
    summary: pd.DataFrame,
    features: pd.DataFrame,
    figure_path: Path,
    dashboard_path: Path,
) -> None:
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    triggered = features[features["feature_status"] == "triggered"].copy()
    pattern_rows = _pattern_profile_rows(triggered)
    summary_rows = _table_rows(
        summary,
        (
            "candidate_id",
            "best_reference_case_id",
            "best_similarity_score",
            "match_label",
            "matched_patterns",
        ),
    )
    score_rows = _table_rows(
        scores.sort_values(
            ["candidate_id", "similarity_score", "reference_case_id"],
            ascending=[True, False, True],
        ),
        (
            "candidate_id",
            "reference_case_id",
            "similarity_score",
            "matched_pattern_count",
            "reference_pattern_count",
            "match_label",
            "matched_patterns",
        ),
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Wallet Reference Similarity</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #17202a; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 12px; }}
    .metric {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    img {{ max-width: 100%; border: 1px solid #d7dde5; border-radius: 6px; }}
    code {{ background: #f1f5f9; padding: 2px 4px; border-radius: 4px; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h1>Wallet Reference Similarity</h1>
  <p class="note">Read-only diagnostic view. Scores are equal-weight pattern overlap, not probability, proof, causality, tradeability, or profitability evidence.</p>
  <section class="metrics">
    <div class="metric">Candidates<strong>{scores["candidate_id"].nunique()}</strong></div>
    <div class="metric">References<strong>{scores["reference_case_id"].nunique()}</strong></div>
    <div class="metric">Comparisons<strong>{len(scores)}</strong></div>
    <div class="metric">Max non-self score<strong>{_max_non_self_similarity(scores):.2f}</strong></div>
  </section>
  <h2>Best Match Summary</h2>
  <table>
    <thead><tr><th>Candidate</th><th>Best reference</th><th>Score</th><th>Label</th><th>Matched patterns</th></tr></thead>
    <tbody>{summary_rows}</tbody>
  </table>
  <h2>Similarity Matrix</h2>
  <img src="{escape(figure_path.name)}" alt="Wallet reference-case similarity matrix">
  <h2>Reference Pattern Profiles</h2>
  <table>
    <thead><tr><th>Case</th><th>Triggered patterns</th></tr></thead>
    <tbody>{pattern_rows}</tbody>
  </table>
  <h2>All Comparisons</h2>
  <table>
    <thead><tr><th>Candidate</th><th>Reference</th><th>Score</th><th>Matched</th><th>Reference total</th><th>Label</th><th>Matched patterns</th></tr></thead>
    <tbody>{score_rows}</tbody>
  </table>
  <h2>How To Read This</h2>
  <p>High overlap means a candidate shares neutral pattern labels with a reference case. It only tells a human reviewer where to look first. Unknown fields remain unknown until direct source data are available.</p>
</body>
</html>
"""
    dashboard_path.write_text(html, encoding="utf-8")


def _build_metadata(
    *,
    scores: pd.DataFrame,
    summary: pd.DataFrame,
    candidate_features_path: Path,
    reference_features_path: Path,
    scores_path: Path,
    summary_path: Path,
    figure_path: Path,
    dashboard_path: Path,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "method": {
            "name": "wallet_reference_case_similarity",
            "score_definition": "matched_triggered_reference_patterns / triggered_reference_patterns",
            "pattern_weights": "equal_weight_v1",
            "uses_existing_files_only": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "does_not_use_llms": True,
            "does_not_use_agents_or_mcp": True,
            "does_not_use_ml": True,
            "does_not_use_rcp": True,
        },
        "inputs": {
            "candidate_features_path": str(candidate_features_path),
            "reference_features_path": str(reference_features_path),
        },
        "outputs": {
            "scores_path": str(scores_path),
            "summary_path": str(summary_path),
            "figure_path": str(figure_path),
            "dashboard_path": str(dashboard_path),
            "candidate_count": int(scores["candidate_id"].nunique()),
            "reference_count": int(scores["reference_case_id"].nunique()),
            "comparison_count": int(len(scores)),
            "summary_count": int(len(summary)),
            "max_non_self_similarity": _max_non_self_similarity(scores),
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
        },
        "limitations": {
            "descriptive_pattern_overlap_only": True,
            "not_a_probability_model": True,
            "not_a_causal_test": True,
            "not_a_trade_or_profitability_signal": True,
            "requires_human_review": True,
        },
    }


def _match_label(score: float, matched_count: int, is_self_match: bool) -> str:
    if is_self_match and score == 1:
        return "reference_self_profile"
    if score == 1:
        return "complete_reference_overlap"
    if score > 0:
        return "partial_reference_overlap"
    if matched_count == 0:
        return "no_reference_overlap"
    return "review_required"


def _allowed_interpretation(*, score: float, is_self_match: bool) -> str:
    if is_self_match and score == 1:
        return "Reference case reproduces its own pattern profile for calibration."
    if score == 1:
        return "Candidate shares all triggered labels of the reference case; review evidence before use."
    if score > 0:
        return "Candidate shares some neutral labels with the reference case; use as a review cue only."
    return "No triggered reference labels overlap in the current feature set."


def _pattern_profile_rows(triggered: pd.DataFrame) -> str:
    rows: list[str] = []
    for case_id, group in triggered.groupby("case_id", sort=True):
        patterns = ", ".join(sorted(group["pattern_label"].astype(str).tolist()))
        rows.append(f"<tr><td>{escape(str(case_id))}</td><td>{escape(patterns)}</td></tr>")
    return "\n".join(rows)


def _table_rows(frame: pd.DataFrame, columns: Sequence[str]) -> str:
    rows: list[str] = []
    for item in frame.loc[:, list(columns)].to_dict(orient="records"):
        cells = "".join(f"<td>{escape(_format_cell(item[column]))}</td>" for column in columns)
        rows.append(f"<tr>{cells}</tr>")
    return "\n".join(rows)


def _format_cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _join(values: Sequence[str]) -> str:
    return ",".join(values)


def _max_non_self_similarity(scores: pd.DataFrame) -> float:
    non_self = scores[scores["candidate_id"] != scores["reference_case_id"]]
    if non_self.empty:
        return 0.0
    return float(pd.to_numeric(non_self["similarity_score"], errors="coerce").fillna(0).max())


def _read_features(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{label} file not found: {path}")
    frame = pd.read_csv(path, keep_default_na=False)
    if frame.empty:
        raise ValueError(f"{label} file is empty: {path}")
    return frame


def _validate_feature_frame(frame: pd.DataFrame, label: str) -> None:
    _require_columns(frame, REQUIRED_FEATURE_COLUMNS, label)
    invalid_status = sorted(
        set(frame["feature_status"].astype(str)) - {"triggered", "unknown"}
    )
    if invalid_status:
        raise ValueError(f"{label} contains invalid feature_status values: {invalid_status}")


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _reject_wallet_address_columns(frame: pd.DataFrame, label: str) -> None:
    forbidden = [column for column in frame.columns if "wallet_address" in column.lower()]
    if forbidden:
        raise ValueError(f"{label} must not contain wallet-address columns: {forbidden}")


if __name__ == "__main__":
    raise SystemExit(main())
