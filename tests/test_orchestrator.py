"""Orchestrator-Tests mit TestModel-Mocks fuer alle Sub-Agents.

Verifiziert:
  - Alle drei Sub-Agents werden parallel aufgerufen.
  - llm_audit_log enthaelt >= 4 Eintraege mit gemeinsamer run_id.
  - Changelog-JSON wird nach logs/changelog/{run_id}.json geschrieben.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel

from operations.agents.market_agent import market_agent
from operations.agents.orchestrator import (
    AnalysisReport,
    CHANGELOG_DIR,
    run_analysis,
    synthesis_agent,
)
from operations.agents.sentiment_agent import sentiment_agent
from operations.agents.whale_agent import whale_agent


DB_PATH = Path("data/thesis.db")


@pytest.mark.asyncio
async def test_run_analysis_with_mocked_agents() -> None:
    """End-to-end mit TestModel fuer alle vier Agents."""
    run_id = f"test-{uuid.uuid4()}"

    # Count audit log rows before
    conn = sqlite3.connect(str(DB_PATH))
    before = conn.execute(
        "SELECT COUNT(*) FROM llm_audit_log WHERE run_id = ?", (run_id,)
    ).fetchone()[0]
    conn.close()
    assert before == 0

    with (
        market_agent.override(model=TestModel()),
        sentiment_agent.override(model=TestModel()),
        whale_agent.override(model=TestModel()),
        synthesis_agent.override(model=TestModel()),
    ):
        report = await run_analysis(
            "Smoke-test orchestrator parallel run.",
            run_id=run_id,
        )

    # Output shape
    assert isinstance(report, AnalysisReport)
    assert report.run_id == run_id
    assert report.question.startswith("Smoke-test")

    # Audit log: exactly 4 entries (market, sentiment, whale, synthesis)
    conn = sqlite3.connect(str(DB_PATH))
    after = conn.execute(
        "SELECT COUNT(*) FROM llm_audit_log WHERE run_id = ?", (run_id,)
    ).fetchone()[0]
    tools = conn.execute(
        "SELECT tools_called FROM llm_audit_log WHERE run_id = ?", (run_id,)
    ).fetchall()
    conn.close()

    assert after == 4, f"expected 4 audit rows, got {after}"
    tool_labels = {json.loads(row[0])[0] for row in tools if row[0]}
    assert "market_agent" in tool_labels
    assert "sentiment_agent" in tool_labels
    assert "whale_agent" in tool_labels
    assert "orchestrator_synthesis" in tool_labels

    # Changelog file exists
    changelog_path = CHANGELOG_DIR / f"{run_id}.json"
    assert changelog_path.exists()
    payload = json.loads(changelog_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == run_id
    assert set(payload["agents_invoked"]) == {
        "market", "sentiment", "whale", "orchestrator"
    }

    # Cleanup: remove test audit rows + changelog file so repeated runs stay clean
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM llm_audit_log WHERE run_id = ?", (run_id,))
    conn.commit()
    conn.close()
    changelog_path.unlink(missing_ok=True)
