"""Orchestrator-Agent (Pydantic AI, Sonnet) mit parallelen Sub-Agents.

Ruft Market-, Sentiment- und Whale-Agent parallel via asyncio.gather auf,
persistiert jeden Call in llm_audit_log und schreibt am Ende einen
Changelog-Eintrag nach logs/changelog/{run_id}.json.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent

from operations.agents.market_agent import MarketDataResult, market_agent
from operations.agents.sentiment_agent import (
    SentimentAnalysisResult,
    sentiment_agent,
)
from operations.agents.whale_agent import WhaleActivityResult, whale_agent
from operations.audit.logger import AuditCall, AuditLogger, compute_cost

load_dotenv()


CHANGELOG_DIR = Path("logs/changelog")


# --- Output schema -------------------------------------------------------


class AnalysisReport(BaseModel):
    """Synthese-Output des Orchestrators."""

    run_id: str
    question: str
    market_result: MarketDataResult
    sentiment_result: SentimentAnalysisResult
    whale_result: WhaleActivityResult
    synthesis: str = Field(
        description="2–5 Saetze Synthese, deutsch-akademisch."
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Max. 5 Bullet Points.",
    )
    divergences: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


# --- Synthesis sub-agent --------------------------------------------------


_PROMPT_PATH = Path(__file__).parent.parent.parent / "directives" / "roles" / "orchestrator.md"


def _load_system_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


class _Synthesis(BaseModel):
    """Reines Synthese-Artefakt — wird in `AnalysisReport` eingebettet."""

    synthesis: str
    key_findings: list[str]
    divergences: list[str]
    confidence: float


ORCHESTRATOR_MODEL_ID = "anthropic:claude-sonnet-4-5"

synthesis_agent = Agent(
    model=ORCHESTRATOR_MODEL_ID,
    output_type=_Synthesis,
    system_prompt=_load_system_prompt(),
    retries=2,
)


# --- Audit helpers -------------------------------------------------------


def _extract_usage(result: Any) -> tuple[int, int, int]:
    """Best-effort Extraktion von (input_tokens, output_tokens, cached_tokens).

    Pydantic AI exponiert Usage unterschiedlich je nach Version; wir
    fallen auf 0 zurueck, wenn das Attribut fehlt (z.B. bei TestModel).
    """
    try:
        usage = result.usage()
        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0
        cached_tokens = getattr(usage, "cached_tokens", 0) or 0
        return int(input_tokens), int(output_tokens), int(cached_tokens)
    except Exception:  # noqa: BLE001
        return 0, 0, 0


def _log_sub_agent(
    session: Any,
    agent_name: str,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    result: Any,
) -> None:
    """Hilfsfunktion — persistiert einen Sub-Agent-Call ins Audit-Log."""
    in_tok, out_tok, cached = _extract_usage(result)
    call = AuditCall(
        run_id=session.run_id,
        model=model_id,
        user_prompt=user_prompt,
        response=str(result.output),
        input_tokens=in_tok,
        output_tokens=out_tok,
        cached_tokens=cached,
        tools_called=[agent_name],
        tool_results_summary=f"{agent_name} completed",
        system_prompt=system_prompt,
    )
    session.log(call)


# --- Orchestration --------------------------------------------------------


async def run_analysis(
    question: str,
    run_id: str | None = None,
) -> AnalysisReport:
    """Fuehrt eine Multi-Agent-Analyse fuer eine Forschungsfrage aus.

    Args:
        question: Natursprachliche Forschungsfrage.
        run_id: Optional — falls None wird eine UUID generiert.

    Returns:
        Strukturierter AnalysisReport.
    """
    if run_id is None:
        run_id = str(uuid.uuid4())

    logger = AuditLogger()

    market_prompt = f"Sub-Task Market: {question}"
    sentiment_prompt = f"Sub-Task Sentiment: {question}"
    whale_prompt = f"Sub-Task Whale: {question}"

    with logger.session(run_id) as session:
        market_task = market_agent.run(market_prompt)
        sentiment_task = sentiment_agent.run(sentiment_prompt)
        whale_task = whale_agent.run(whale_prompt)

        market_res, sentiment_res, whale_res = await asyncio.gather(
            market_task, sentiment_task, whale_task
        )

        # Persist each sub-agent call
        _log_sub_agent(
            session, "market_agent",
            "claude-haiku-4-5-20251001",
            market_agent._system_prompts[0] if market_agent._system_prompts else "",
            market_prompt,
            market_res,
        )
        _log_sub_agent(
            session, "sentiment_agent",
            "claude-sonnet-4-5",
            sentiment_agent._system_prompts[0] if sentiment_agent._system_prompts else "",
            sentiment_prompt,
            sentiment_res,
        )
        _log_sub_agent(
            session, "whale_agent",
            "claude-haiku-4-5-20251001",
            whale_agent._system_prompts[0] if whale_agent._system_prompts else "",
            whale_prompt,
            whale_res,
        )

        # Synthesis
        synth_input = (
            f"Forschungsfrage: {question}\n\n"
            f"Market: {market_res.output.model_dump_json()}\n\n"
            f"Sentiment: {sentiment_res.output.model_dump_json()}\n\n"
            f"Whale: {whale_res.output.model_dump_json()}\n\n"
            "Synthetisiere diese Ergebnisse zu einem AnalysisReport."
        )
        synth_res = await synthesis_agent.run(synth_input)

        _log_sub_agent(
            session, "orchestrator_synthesis",
            "claude-sonnet-4-5",
            synthesis_agent._system_prompts[0] if synthesis_agent._system_prompts else "",
            synth_input,
            synth_res,
        )

    report = AnalysisReport(
        run_id=run_id,
        question=question,
        market_result=market_res.output,
        sentiment_result=sentiment_res.output,
        whale_result=whale_res.output,
        synthesis=synth_res.output.synthesis,
        key_findings=synth_res.output.key_findings,
        divergences=synth_res.output.divergences,
        confidence=synth_res.output.confidence,
    )

    _write_changelog(report, [market_res, sentiment_res, whale_res, synth_res])

    return report


def _write_changelog(
    report: AnalysisReport,
    results: list[Any],
) -> None:
    """Schreibt den Run-Changelog nach logs/changelog/{run_id}.json."""
    CHANGELOG_DIR.mkdir(parents=True, exist_ok=True)

    tokens_in = 0
    tokens_out = 0
    cost = 0.0
    for res in results:
        in_tok, out_tok, cached = _extract_usage(res)
        tokens_in += in_tok
        tokens_out += out_tok
        # Rough cost per agent — we don't know model here so assume Sonnet
        # for synthesis and the others pay their own rates; the audit log
        # has the exact breakdown.
        cost += compute_cost("claude-sonnet-4-5", in_tok, out_tok, cached)

    payload = {
        "run_id": report.run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "question": report.question,
        "agents_invoked": ["market", "sentiment", "whale", "orchestrator"],
        "key_findings": report.key_findings,
        "divergences": report.divergences,
        "confidence": report.confidence,
        "tokens_used": {"input": tokens_in, "output": tokens_out},
        "cost_usd_estimate": round(cost, 6),
    }
    path = CHANGELOG_DIR / f"{report.run_id}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
