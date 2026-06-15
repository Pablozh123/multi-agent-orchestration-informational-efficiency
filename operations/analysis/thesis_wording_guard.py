"""Build German thesis wording guardrails from the evidence map.

The guard table is a deterministic drafting aid. It translates each Evidence
ID into allowed German wording, blocked overclaims, the required artifact
reference, and the limitation that must stay visible in the thesis text.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd


DEFAULT_REPO_ROOT = Path(".")
DEFAULT_RESULTS_DIR = Path("data/results")
DEFAULT_DOCS_DIR = Path("docs/research")

WORDING_GUARD_OUTPUT = "thesis_wording_guard.csv"
WORDING_GUARD_DOC_OUTPUT = "THESIS_WORDING_GUARD.md"

WORDING_GUARD_COLUMNS: tuple[str, ...] = (
    "guard_id",
    "evidence_id",
    "thesis_area",
    "item_type",
    "allowed_thesis_wording_de",
    "blocked_thesis_wording_de",
    "required_artifact_reference",
    "required_limitation_de",
    "final_use_gate",
    "thesis_section",
)


@dataclass(frozen=True)
class WordingGuardResult:
    """Generated wording guard paths and counts."""

    wording_guard_path: Path
    docs_path: Path
    guard_rows: int
    thesis_facing_rows: int
    deferred_rows: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "wording_guard_path": str(self.wording_guard_path),
            "docs_path": str(self.docs_path),
            "guard_rows": self.guard_rows,
            "thesis_facing_rows": self.thesis_facing_rows,
            "deferred_rows": self.deferred_rows,
        }


def generate_wording_guard(
    *,
    repo_root: Path = DEFAULT_REPO_ROOT,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    docs_dir: Path = DEFAULT_DOCS_DIR,
) -> WordingGuardResult:
    """Generate the German wording guard CSV and Markdown document."""

    repo_root = Path(repo_root)
    results_dir = _resolve_under(repo_root, results_dir)
    docs_dir = _resolve_under(repo_root, docs_dir)
    evidence_map = _read_csv(results_dir / "thesis_evidence_map.csv")
    guard = build_wording_guard(evidence_map=evidence_map)
    _validate_wording_guard(guard)

    results_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    guard_path = results_dir / WORDING_GUARD_OUTPUT
    docs_path = docs_dir / WORDING_GUARD_DOC_OUTPUT
    guard.to_csv(guard_path, index=False)
    docs_path.write_text(_render_wording_guard_doc(guard), encoding="utf-8")

    return WordingGuardResult(
        wording_guard_path=guard_path,
        docs_path=docs_path,
        guard_rows=len(guard),
        thesis_facing_rows=int(
            guard["final_use_gate"].isin(
                {
                    "thesis_text_allowed_after_source_review",
                    "draft_allowed_with_explicit_source_review_gate",
                }
            ).sum()
        ),
        deferred_rows=int((guard["final_use_gate"] == "future_work_or_appendix_only").sum()),
    )


def build_wording_guard(*, evidence_map: pd.DataFrame) -> pd.DataFrame:
    """Build one wording-guard row per Evidence ID."""

    _require_columns(
        evidence_map,
        (
            "evidence_id",
            "thesis_area",
            "item_type",
            "primary_artifact",
            "main_limitation",
            "thesis_readiness",
        ),
        "evidence map",
    )
    rows: list[dict[str, object]] = []
    for index, row in enumerate(evidence_map.to_dict(orient="records"), start=1):
        evidence_id = str(row["evidence_id"])
        wording = _WORDING_BY_EVIDENCE_ID.get(
            evidence_id,
            _fallback_wording(
                evidence_id=evidence_id,
                thesis_area=str(row["thesis_area"]),
                primary_artifact=str(row["primary_artifact"]),
                main_limitation=str(row["main_limitation"]),
            ),
        )
        rows.append(
            {
                "guard_id": f"wording_guard_{index:02d}_{evidence_id}",
                "evidence_id": evidence_id,
                "thesis_area": str(row["thesis_area"]),
                "item_type": str(row["item_type"]),
                "allowed_thesis_wording_de": wording["allowed"],
                "blocked_thesis_wording_de": wording["blocked"],
                "required_artifact_reference": str(row["primary_artifact"]),
                "required_limitation_de": wording["limitation"],
                "final_use_gate": _final_use_gate(str(row["thesis_readiness"])),
                "thesis_section": _thesis_section(str(row["thesis_area"])),
            }
        )
    return pd.DataFrame(rows, columns=WORDING_GUARD_COLUMNS)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    args = parser.parse_args(argv)

    try:
        result = generate_wording_guard(
            repo_root=args.repo_root,
            results_dir=args.results_dir,
            docs_dir=args.docs_dir,
        )
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


_WORDING_BY_EVIDENCE_ID: dict[str, dict[str, str]] = {
    "method_h1_brier_dm": {
        "allowed": "H1 misst Prognosequalitaet ueber Brier-Verluste und den Vergleich vorberechneter Verlustreihen.",
        "blocked": "Nicht schreiben: Polymarket reagiert schneller, Polymarket ist generell ueberlegen, oder RCP sei ohne Transformation eine Wahrscheinlichkeit.",
        "limitation": "Wiederholte Tageszeilen und ein einzelner Wahlkontext begrenzen die Generalisierung.",
    },
    "interpretation_h1_bounded_advantage": {
        "allowed": "Polymarket zeigt in definierten spaeten und kompatiblen Poll-Vergleichsscopes eine begrenzte Staerke.",
        "blocked": "Nicht schreiben: Polymarket ist immer besser, die Arbeit beweise viele unabhaengige Wahlen, oder die Ursache sei geklaert.",
        "limitation": "Das volle State-Date-Panel und andere Scopes bleiben Gegenbeispiele zur breiten Behauptung.",
    },
    "interpretation_h1_broad_claim_not_proven": {
        "allowed": "Die breite Aussage, dass Polymarket traditionelle Quellen generell schlaegt, bleibt nicht bewiesen.",
        "blocked": "Nicht schreiben: allgemeine Ueberlegenheit, universelle Forecast-Dominanz oder ein starker Viele-Faelle-Beweis.",
        "limitation": "Die Evidenz mischt Tageszeilen, State-Outcomes, transformierte Polls und quellenspezifische Scopes.",
    },
    "method_h2_event_window": {
        "allowed": "H2 nutzt vorab kuratierte oeffentliche Ereignisse und feste Tagesfenster.",
        "blocked": "Nicht schreiben: Intraday-Reaktionsgeschwindigkeit oder nachtraeglich ausgewaehlte Ereignisse.",
        "limitation": "Tagespreise koennen kein Minuten- oder Stunden-Timing identifizieren.",
    },
    "interpretation_h2_daily_response": {
        "allowed": "Kuratierte Ereignisse zeigen sichtbare taegliche Polymarket-Bewegungen.",
        "blocked": "Nicht schreiben: sofortige Marktreaktion, kausaler Ereignisbeweis oder Intraday-Speed.",
        "limitation": "Richtung und Groesse sind Event-Window-Diagnostik, keine kausalen Intraday-Schaetzungen.",
    },
    "method_h3_wallet_tiers": {
        "allowed": "Wallet-Gruppen werden dataset-relativ aus beobachteten Verteilungen abgeleitet.",
        "blocked": "Nicht schreiben: fixe Whale-Schwellen, identifizierte private Informationswallets oder Personenzuschreibungen.",
        "limitation": "Die beobachteten Walletdaten sind BUY-only und quellengefiltert.",
    },
    "method_h3_granger_timing": {
        "allowed": "Lead-Lag-Korrelationen und Granger-Tests werden als predictive timing diagnostics gelesen.",
        "blocked": "Nicht schreiben: Kausalitaetsbeweis, private Informationen oder Profitabilitaetsbeweis.",
        "limitation": "Taegliche Aggregation, Mehrfachtests und BUY-only-Extraktion begrenzen die Aussage.",
    },
    "interpretation_h3_top_tier_signal": {
        "allowed": "Das oberste Wallet-Tier zeigt im aktuellen H3-Baseline-Output die deutlichste Timingdiagnostik.",
        "blocked": "Nicht schreiben: Insiderbeweis, Fehlverhalten, handelbare Strategie oder Gewinnsignal.",
        "limitation": "Die Signalstaerke ist diagnostisch und braucht Sensitivitaets- sowie Multiple-Testing-Vorsicht.",
    },
    "method_monitor_prototype": {
        "allowed": "Der Monitor kombiniert Marktbewegung, aggregierte Wallet-Tiers, Konzentration und Ereigniskontext als Review-Cues.",
        "blocked": "Nicht schreiben: thesis-facing Evidenz vor Human Review, private Informationsnutzung oder Trading-Signal.",
        "limitation": "Aktuelle Cases bleiben source-check-pending und fuer thesis-facing Claims blockiert.",
    },
    "interpretation_monitor_review_queue": {
        "allowed": "Die Queue ist ein Review-Workflow und Appendix-Material, kein Beweis fuer Ursachen oder Ineffizienz.",
        "blocked": "Nicht schreiben: Kausalclaim, Fehlverhalten, Effizienzschluss, Profitclaim oder Handelsstrategie.",
        "limitation": "Alle aktuellen Cases brauchen manuelle Quellen- und Thesis-Use-Pruefung.",
    },
    "method_swiss_running_comparison": {
        "allowed": "Der Swiss-Track trennt nach dem offiziellen Resultat Stimmenanteilsnaehe und binaere Ablehnungs-Proxy-Signale.",
        "blocked": "Nicht schreiben: Mispricing-Beweis, Effizienzbeweis, Handelssignal oder Polymarket-Stimmenanteilsprognose.",
        "limitation": "Polymarket-Preise sind Annahmewahrscheinlichkeiten, Umfragen sind Stimmenanteile.",
    },
    "interpretation_swiss_gap_pending": {
        "allowed": "Im Swiss-Fall waren finale Umfragen naeher am Ja-Stimmenanteil, waehrend Polymarket das Ablehnungssignal klarer zeigte.",
        "blocked": "Nicht schreiben: Polymarket war in jeder Hinsicht besser, Effizienzbeweis oder Tradeability.",
        "limitation": "Die binaere Poll-Brier-Zeile ist nur ein Proxy und keine echte Win-Probability-Kalibrierung.",
    },
    "future_agent_pipeline_guarded": {
        "allowed": "Agenten werden nur als spaeterer, auditierter Workflow ueber bounded summaries beschrieben.",
        "blocked": "Nicht schreiben: agentenberechnete Metriken, rohe Tabellenprompts, autonome Trades oder unlogged LLM-Interpretation.",
        "limitation": "Implementierung bleibt bis zu separatem Goal, Tests und llm_audit_log-Integration deferred.",
    },
}


def _validate_wording_guard(frame: pd.DataFrame) -> None:
    _require_columns(frame, WORDING_GUARD_COLUMNS, "wording guard")
    if frame["guard_id"].duplicated().any():
        raise ValueError("Wording guard contains duplicate guard_id values.")
    if frame["evidence_id"].duplicated().any():
        raise ValueError("Wording guard contains duplicate evidence_id values.")
    for column in (
        "allowed_thesis_wording_de",
        "blocked_thesis_wording_de",
        "required_artifact_reference",
        "required_limitation_de",
        "final_use_gate",
    ):
        if frame[column].astype(str).str.len().eq(0).any():
            raise ValueError(f"Wording guard contains empty {column}.")
    joined = "\n".join(frame.astype(str).agg(" ".join, axis=1).tolist())
    if chr(223) in joined:
        raise ValueError("Wording guard must use Swiss spelling without sharp-s.")
    lower_joined = joined.lower()
    required_terms = (
        "nicht schreiben",
        "brier",
        "intraday",
        "kausal",
        "gewinn",
        "llm_audit_log",
    )
    missing = [term for term in required_terms if term not in lower_joined]
    if missing:
        raise ValueError("Wording guard missing required boundary terms: " + ", ".join(missing))


def _render_wording_guard_doc(guard: pd.DataFrame) -> str:
    display = guard[
        [
            "evidence_id",
            "thesis_area",
            "allowed_thesis_wording_de",
            "blocked_thesis_wording_de",
            "required_artifact_reference",
            "required_limitation_de",
            "final_use_gate",
        ]
    ]
    counts = guard["final_use_gate"].value_counts().sort_index().to_dict()
    return (
        "# Thesis Wording Guard\n\n"
        "This file is a drafting guard for German thesis prose. It converts each "
        "Evidence ID into allowed wording, blocked overclaims, the artifact that "
        "must be cited, and the limitation that must remain visible.\n\n"
        "## Counts\n\n"
        f"- Guard rows: {len(guard)}\n"
        f"- Thesis text allowed after source review: {int(counts.get('thesis_text_allowed_after_source_review', 0))}\n"
        f"- Draft allowed with explicit source-review gate: {int(counts.get('draft_allowed_with_explicit_source_review_gate', 0))}\n"
        f"- Future work or appendix only: {int(counts.get('future_work_or_appendix_only', 0))}\n\n"
        "## Guard Rows\n\n"
        + _markdown_table(display)
        + "\n\n"
        "## Use Rule\n\n"
        "Use these formulations when drafting the BA thesis. Do not remove the "
        "artifact reference or the limitation. Do not use blocked formulations "
        "without new deterministic evidence and reviewed sources.\n"
    )


def _fallback_wording(
    *,
    evidence_id: str,
    thesis_area: str,
    primary_artifact: str,
    main_limitation: str,
) -> dict[str, str]:
    return {
        "allowed": (
            f"{thesis_area} darf nur vorsichtig anhand von `{primary_artifact}` "
            f"und Evidence-ID `{evidence_id}` formuliert werden."
        ),
        "blocked": "Nicht schreiben: weitergehende Behauptungen ohne deterministisches Artefakt und Quellenreview.",
        "limitation": main_limitation,
    }


def _final_use_gate(thesis_readiness: str) -> str:
    if thesis_readiness == "thesis_facing_ready":
        return "thesis_text_allowed_after_source_review"
    if thesis_readiness in {
        "appendix_prototype_only",
        "descriptive_pending_result",
        "post_result_mapped_bounded",
    }:
        return "draft_allowed_with_explicit_source_review_gate"
    return "future_work_or_appendix_only"


def _thesis_section(thesis_area: str) -> str:
    return {
        "H1": "H1 result chapter",
        "H2": "H2 event-window chapter",
        "H3": "H3 wallet-timing chapter",
        "monitor_prototype": "appendix_or_discussion",
        "swiss_referendum": "discussion_bounded_final_case",
        "future_agents": "future_work",
    }.get(thesis_area, "general_thesis_text")


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required wording guard input missing: {path}")
    return pd.read_csv(path)


def _resolve_under(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], name: str) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def _markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    header = "| " + " | ".join(_escape_markdown_cell(column) for column in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for record in frame.to_dict(orient="records"):
        rows.append(
            "| "
            + " | ".join(_escape_markdown_cell(record.get(column, "")) for column in columns)
            + " |"
        )
    return "\n".join([header, separator, *rows])


def _escape_markdown_cell(value: object) -> str:
    text = str(value).replace("\n", " ").strip()
    return text.replace("|", "\\|")


if __name__ == "__main__":
    raise SystemExit(main())
