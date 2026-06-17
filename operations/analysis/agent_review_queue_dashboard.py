"""Generate a static, read-only Agent Review-Queue dashboard.

This is the *separate website part* that surfaces the Stage 3 multi-agent layer.
It orchestrates the read-only review agents over the bounded Stage 2 MCP tool
layer and renders a ranked human-review queue as a static HTML page in the same
visual style as the monitor dashboards.

Hard boundaries (mirrored from AGENTS.md / ARCHITECTURE_DECISIONS / the
future_agent_contract and enforced by the agent package and re-asserted here):

    - The agents compute NO monitor metric. They only read bounded summaries
      through the four read-only MCP tools (<= 50 rows, wallet-redacted).
    - The only recommendations are review actions:
      {watch, check_source, escalate_human}. Never buy/sell, never an order,
      never investment advice, never profitability.
    - Every LLM call is audited. The LLM is a deterministic mock by default, so
      the page builds with no network and no API key.
    - No wallet address is emitted; this generator re-asserts the redaction.

The deterministic thesis core is untouched: this view only *interprets* bounded,
precomputed outputs and recommends *review* actions for a human.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Optional, Sequence, Union

from operations.agents.review_queue import (
    ALLOWED_PRIORITIES,
    ALLOWED_RECOMMENDATIONS,
    FORBIDDEN_OUTPUT_KEY_FRAGMENTS,
)
from operations.agents.review_queue.orchestrator import build_review_queue

#: Absolute repo root (cwd-independent): operations/analysis/<file> -> repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / "data" / "results"

DASHBOARD_OUTPUT = RESULTS_DIR / "agent_review_queue_dashboard.html"
DASHBOARD_METADATA_OUTPUT = RESULTS_DIR / "agent_review_queue_dashboard_metadata.json"
LLM_AUDIT_OUTPUT = RESULTS_DIR / "agent_review_queue_llm_audit_log.jsonl"

#: Sibling monitor pages we link to (same directory).
_MONITOR_DASHBOARD = "monitor_v2_polymarket_dashboard.html"
_ANOMALY_REVIEW_DASHBOARD = "monitor_anomaly_review_dashboard.html"

#: True 20-byte wallet pattern (0x + exactly 40 hex). Used for a defensive check.
_WALLET_RE = re.compile(r"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])")


@dataclass(frozen=True)
class DashboardResult:
    """Summary of the generated agent-review-queue dashboard artifacts."""

    dashboard_path: Path
    metadata_path: Path
    case_count: int
    high_count: int
    medium_count: int
    low_count: int
    backend: str

    def to_dict(self) -> dict[str, int | str]:
        return {
            "dashboard_path": str(self.dashboard_path),
            "metadata_path": str(self.metadata_path),
            "case_count": self.case_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "backend": self.backend,
        }


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, sub in value.items():
            yield key
            yield from _walk_keys(sub)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_keys(item)


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, sub in value.items():
            if isinstance(key, str):
                yield key
            yield from _walk_strings(sub)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


def _assert_guardrails(queue: dict[str, Any]) -> None:
    """Re-assert the hard output boundaries before writing anything."""
    for key in _walk_keys(queue):
        low = str(key).lower()
        for frag in FORBIDDEN_OUTPUT_KEY_FRAGMENTS:
            if frag in low:
                raise ValueError(f"forbidden key fragment '{frag}' in queue key '{key}'")
    for text in _walk_strings(queue):
        if _WALLET_RE.search(text):
            raise ValueError("wallet address leaked into the review queue")
    for item in queue.get("ranked_cases", []):
        rec = item.get("recommendation")
        if rec not in ALLOWED_RECOMMENDATIONS:
            raise ValueError(f"recommendation '{rec}' outside the allowed review set")
        if item.get("priority") not in ALLOWED_PRIORITIES:
            raise ValueError(f"priority '{item.get('priority')}' outside the allowed set")


def _counts(queue: dict[str, Any], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for item in queue.get("ranked_cases", []):
        key = str(item.get(field, ""))
        out[key] = out.get(key, 0) + 1
    return out


def generate_agent_review_queue_dashboard(
    *,
    data_root: Union[str, Path] = REPO_ROOT,
    dashboard_path: Path = DASHBOARD_OUTPUT,
    metadata_path: Path = DASHBOARD_METADATA_OUTPUT,
    llm_audit_path: Path = LLM_AUDIT_OUTPUT,
    backend: Optional[Any] = None,
    max_cases: int = 50,
) -> DashboardResult:
    """Run the agent pipeline over bounded MCP outputs and render the HTML page."""
    queue = build_review_queue(
        data_root=data_root,
        llm_audit_path=llm_audit_path,
        backend=backend,
        max_cases=max_cases,
    )
    _assert_guardrails(queue)

    backend_name = "mock" if backend is None else getattr(backend, "__name__", "custom")
    priority_counts = _counts(queue, "priority")
    recommendation_counts = _counts(queue, "recommendation")

    html = _render_dashboard(
        queue=queue,
        backend_name=backend_name,
        llm_audit_path=llm_audit_path,
        priority_counts=priority_counts,
        recommendation_counts=recommendation_counts,
    )
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(html, encoding="utf-8")

    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "method": {
            "name": "agent_review_queue_dashboard",
            "read_only": True,
            "uses_bounded_local_files": True,
            "does_not_collect_external_data": True,
            "does_not_write_database": True,
            "agents_compute_no_metric": True,
            "uses_agents_and_mcp": True,
            "agents": ["EventScout", "CaseNarrative", "SkepticReviewer", "Orchestrator"],
            "uses_llm": True,
            "llm_backend": backend_name,
            "every_llm_call_audited": True,
            "max_rows": 50,
            "recommendations_allowed": list(ALLOWED_RECOMMENDATIONS),
        },
        "outputs": {
            "case_count": int(queue.get("count", 0)),
            "priority_counts": priority_counts,
            "recommendation_counts": recommendation_counts,
            "contains_wallet_addresses": False,
            "contains_order_instructions": False,
            "dashboard_path": str(dashboard_path),
            "llm_audit_log": str(llm_audit_path),
        },
        "blocked_claims": queue.get("blocked_claims", ""),
        "limitations": {
            "human_review_required": True,
            "no_causal_or_profitability_claim": True,
            "no_private_information_proof": True,
            "review_recommendations_only": True,
        },
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return DashboardResult(
        dashboard_path=dashboard_path,
        metadata_path=metadata_path,
        case_count=int(queue.get("count", 0)),
        high_count=int(priority_counts.get("high", 0)),
        medium_count=int(priority_counts.get("medium", 0)),
        low_count=int(priority_counts.get("low", 0)),
        backend=backend_name,
    )


def _badge(text: str, kind: str) -> str:
    return f'<span class="badge badge-{escape(kind)}">{escape(text)}</span>'


def _counts_inline(counts: dict[str, int]) -> str:
    if not counts:
        return "n/a"
    return ", ".join(f"{escape(str(k))}: {v}" for k, v in sorted(counts.items()))


def _case_rows(queue: dict[str, Any]) -> str:
    rows: list[str] = []
    for idx, item in enumerate(queue.get("ranked_cases", []), start=1):
        priority = str(item.get("priority", ""))
        recommendation = str(item.get("recommendation", ""))
        rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td>{_badge(priority, priority)}</td>"
            f"<td>{_badge(recommendation, recommendation)}</td>"
            f"<td>{escape(str(item.get('question', '')))}</td>"
            f"<td>{escape(str(item.get('score', '')))}</td>"
            f"<td>{escape(str(item.get('narrative', '')))}</td>"
            f"<td>{escape(str(item.get('skeptic_note', '')))}</td>"
            f"<td>{escape(str(item.get('human_review_status', '')))}</td>"
            "</tr>"
        )
    if not rows:
        return (
            '<tr><td colspan="8">No bounded review cases in the current queue. '
            "Nothing is asserted.</td></tr>"
        )
    return "\n".join(rows)


def _render_dashboard(
    *,
    queue: dict[str, Any],
    backend_name: str,
    llm_audit_path: Path,
    priority_counts: dict[str, int],
    recommendation_counts: dict[str, int],
) -> str:
    case_rows = _case_rows(queue)
    count = int(queue.get("count", 0))
    allowed = ", ".join(ALLOWED_RECOMMENDATIONS)
    blocked = escape(str(queue.get("blocked_claims", "")))
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>Agenten-Review-Queue (Read-only)</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 28px; color: #17202a; }}
    h1 {{ margin-bottom: 4px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; margin-top: 12px; }}
    .metric {{ border: 1px solid #d7dde5; border-radius: 6px; padding: 12px; background: #f8fafc; }}
    .metric strong {{ display: block; font-size: 22px; margin-top: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 13px; }}
    th, td {{ border: 1px solid #d7dde5; padding: 7px; text-align: left; vertical-align: top; }}
    th {{ background: #eef2f7; }}
    code {{ background: #f1f5f9; padding: 2px 4px; border-radius: 4px; }}
    .note {{ background: #fff7e6; border: 1px solid #f0d08a; padding: 12px; border-radius: 6px; }}
    .pipeline {{ background: #f1f7fb; border: 1px solid #bcd4e6; padding: 12px; border-radius: 6px; }}
    .pipeline ol {{ margin: 8px 0 0 18px; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: bold; color: #fff; }}
    .badge-high, .badge-escalate_human {{ background: #b03a2e; }}
    .badge-medium, .badge-check_source {{ background: #b9770e; }}
    .badge-low, .badge-watch {{ background: #5d6d7e; }}
    .links a {{ color: #174f78; font-weight: bold; margin-right: 16px; }}
  </style>
</head>
<body>
  <h1>Agenten-Review-Queue</h1>
  <p class="note">Read-only Prüf-Workflow. Die Agenten berechnen keine Kennzahlen,
  sie ordnen nur bereits berechnete, begrenzte Monitor-Zusammenfassungen ein und
  empfehlen ausschliesslich Prüf-Handlungen ({allowed}). Kein Kauf/Verkauf, keine
  Order, keine Aussage über Kausalität, Insiderhandel, Fehlverhalten oder
  Profitabilität. Der Mensch entscheidet.</p>

  <section class="metrics">
    <div class="metric">Fälle in der Queue<strong>{count}</strong></div>
    <div class="metric">Hoch<strong>{priority_counts.get("high", 0)}</strong></div>
    <div class="metric">Mittel<strong>{priority_counts.get("medium", 0)}</strong></div>
    <div class="metric">Tief<strong>{priority_counts.get("low", 0)}</strong></div>
  </section>

  <div class="pipeline">
    <strong>Agenten-Orchestrierung</strong>
    <ol>
      <li><b>EventScout</b> sammelt belegte Ereigniskandidaten (Quelle + Zeitstempel), unbelegte werden verworfen.</li>
      <li><b>CaseNarrative</b> liest einen Fall über die read-only MCP-Schicht und beschreibt ihn neutral.</li>
      <li><b>SkepticReviewer</b> nennt benigne Gegenargumente und senkt die Konfidenz begrenzt (nie positiv).</li>
      <li><b>Orchestrator</b> vergibt Priorität und genau eine Prüf-Empfehlung und rankt die Queue.</li>
    </ol>
    <p style="margin:8px 0 0 0;">Empfehlungs-Verteilung: {escape(_counts_inline(recommendation_counts))}.</p>
  </div>

  <h2>Review-Queue (gerankt)</h2>
  <table>
    <thead><tr>
      <th>#</th><th>Priorität</th><th>Empfehlung</th><th>Frage</th><th>Score</th>
      <th>Narrativ (CaseNarrative)</th><th>Skeptiker-Hinweis</th><th>Review-Status</th>
    </tr></thead>
    <tbody>
{case_rows}
    </tbody>
  </table>

  <h2>Interpretationsgrenzen</h2>
  <p class="note">Diese Queue beweist weder private Information noch Fehlverhalten,
  Kausalität, Handelbarkeit, Profitabilität oder künftige Performance. Gesperrte
  Behauptungen: <code>{blocked}</code>. Risiko-Etiketten sind Beobachtungs-Marker,
  keine Befunde, und ersetzen keine manuelle Prüfung.</p>

  <h2>Methode und Audit</h2>
  <table>
    <tbody>
      <tr><th>LLM-Backend</th><td>{escape(backend_name)} (deterministisch, ohne Netz/Key sofern Mock)</td></tr>
      <tr><th>LLM-Audit-Log</th><td><code>{escape(llm_audit_path.name)}</code> (eine Zeile je LLM-Aufruf, nur Prompt-Hash)</td></tr>
      <tr><th>Datenzugriff</th><td>read-only MCP, maximal 50 Zeilen je Abfrage, Wallet-Adressen redigiert</td></tr>
      <tr><th>Agenten berechnen Kennzahlen</th><td>nein</td></tr>
    </tbody>
  </table>

  <p class="links">
    <a href="{_MONITOR_DASHBOARD}">&larr; Monitor-Dashboard</a>
    <a href="{_ANOMALY_REVIEW_DASHBOARD}">Anomalie-Review-Dashboard</a>
  </p>
</body>
</html>
"""


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: generate the static agent-review-queue dashboard."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--dashboard-output", type=Path, default=DASHBOARD_OUTPUT)
    parser.add_argument("--metadata-output", type=Path, default=DASHBOARD_METADATA_OUTPUT)
    parser.add_argument("--llm-audit-output", type=Path, default=LLM_AUDIT_OUTPUT)
    parser.add_argument("--max-cases", type=int, default=50)
    args = parser.parse_args(argv)

    try:
        result = generate_agent_review_queue_dashboard(
            data_root=args.data_root,
            dashboard_path=args.dashboard_output,
            metadata_path=args.metadata_output,
            llm_audit_path=args.llm_audit_output,
            max_cases=args.max_cases,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
