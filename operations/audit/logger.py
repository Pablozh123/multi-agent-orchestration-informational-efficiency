"""Audit-Logger fuer LLM-Calls (CLAUDE.md v2.1 §9).

Jeder Agent-Call wird in `llm_audit_log` persistiert, damit die Thesis-
Ergebnisse reproduzierbar sind. Fields: call_id, run_id, model, tier,
System-Prompt-Hash, Tokens, Cost-USD, Tool-Calls.

Der Logger ist synchron — das reicht, weil wir nur nach Abschluss jedes
Agent-Runs einmal schreiben. Kein Logging wird parallel zum LLM-Call
gemacht.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DB_PATH = Path("data/thesis.db")


# --- Pricing table (USD per 1M tokens) -----------------------------------
#
# Quelle: anthropic.com/pricing, Stand 2026-03. Batch-API-Rabatt ist
# separat einzurechnen, hier ist nur der Standardpreis.

_PRICING_PER_M_TOKENS: dict[str, dict[str, float]] = {
    "claude-haiku-4-5-20251001": {
        "input": 1.00, "output": 5.00, "cached_read": 0.10,
    },
    "claude-sonnet-4-5": {
        "input": 3.00, "output": 15.00, "cached_read": 0.30,
    },
    "claude-sonnet-4-6": {
        "input": 3.00, "output": 15.00, "cached_read": 0.30,
    },
    "claude-opus-4-6": {
        "input": 15.00, "output": 75.00, "cached_read": 1.50,
    },
}

# Tier classification per CLAUDE.md v2.1 §3.1
_TIER_BY_MODEL: dict[str, int] = {
    "claude-haiku-4-5-20251001": 1,
    "claude-sonnet-4-5": 2,
    "claude-sonnet-4-6": 2,
    "claude-opus-4-6": 3,
}


# --- Helpers -------------------------------------------------------------


def hash_prompt(prompt: str) -> str:
    """SHA-256 des System-Prompts fuer den Audit-Log."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def compute_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
) -> float:
    """Berechnet die Kosten eines LLM-Calls in USD.

    Args:
        model: Normalisierter Modellname (ohne 'anthropic:' Praefix).
        input_tokens: Neue Input-Tokens.
        output_tokens: Output-Tokens.
        cached_tokens: Cache-Read-Tokens (werden vom Input abgezogen und
                       separat mit Cache-Read-Preis multipliziert).

    Returns:
        Gesamtkosten in USD.
    """
    model = model.replace("anthropic:", "")
    prices = _PRICING_PER_M_TOKENS.get(model)
    if not prices:
        return 0.0
    fresh_input = max(0, input_tokens - cached_tokens)
    cost = (
        fresh_input * prices["input"] / 1_000_000
        + output_tokens * prices["output"] / 1_000_000
        + cached_tokens * prices["cached_read"] / 1_000_000
    )
    return round(cost, 6)


def tier_for_model(model: str) -> int:
    """Gibt den Tier (1=Haiku, 2=Sonnet, 3=Opus) fuer ein Modell zurueck."""
    return _TIER_BY_MODEL.get(model.replace("anthropic:", ""), 0)


# --- Logger --------------------------------------------------------------


@dataclass
class AuditCall:
    """Eine einzelne Audit-Zeile."""

    run_id: str
    model: str
    user_prompt: str = ""
    response: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    tools_called: list[str] = field(default_factory=list)
    tool_results_summary: str = ""
    system_prompt: str = ""
    system_prompt_version: str = "v2.1"
    consistency_group_id: str | None = None
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_row(self) -> tuple[Any, ...]:
        """Serialisiert die Zeile fuer INSERT in llm_audit_log."""
        model_clean = self.model.replace("anthropic:", "")
        return (
            self.call_id,
            self.run_id,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
            model_clean,
            tier_for_model(self.model),
            hash_prompt(self.system_prompt) if self.system_prompt else None,
            self.system_prompt_version,
            self.user_prompt,
            self.response,
            self.input_tokens,
            self.output_tokens,
            compute_cost(
                model_clean,
                self.input_tokens,
                self.output_tokens,
                self.cached_tokens,
            ),
            self.cached_tokens,
            json.dumps(self.tools_called),
            self.tool_results_summary,
            self.consistency_group_id,
        )


class AuditLogger:
    """Schreibt Audit-Zeilen in `llm_audit_log`.

    Benutzung:
        logger = AuditLogger()
        with logger.session("run-123") as session:
            session.log(AuditCall(run_id="run-123", model="...", ...))
    """

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db_path = db_path

    def _insert(self, row: tuple[Any, ...]) -> None:
        conn = sqlite3.connect(str(self._db_path))
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO llm_audit_log
                    (call_id, run_id, timestamp, model, tier,
                     system_prompt_hash, system_prompt_version,
                     user_prompt, response,
                     input_tokens, output_tokens, cost_usd, cached_tokens,
                     tools_called, tool_results_summary, consistency_group_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )
            conn.commit()
        finally:
            conn.close()

    def log(self, call: AuditCall) -> str:
        """Persistiert einen AuditCall und gibt dessen call_id zurueck."""
        self._insert(call.to_row())
        return call.call_id

    @contextmanager
    def session(self, run_id: str) -> Iterator["_AuditSession"]:
        """Kontextmanager fuer einen ganzen Agent-Run."""
        session = _AuditSession(self, run_id)
        try:
            yield session
        finally:
            # Nothing to clean up — each call is committed on log().
            pass


class _AuditSession:
    """Scoped helper, damit Aufrufer nicht jedes Mal die run_id mitgeben."""

    def __init__(self, parent: AuditLogger, run_id: str) -> None:
        self._parent = parent
        self.run_id = run_id
        self.call_ids: list[str] = []

    def log(self, call: AuditCall) -> str:
        """Fix up run_id wenn noetig und delegiere ans AuditLogger."""
        if call.run_id != self.run_id:
            call = AuditCall(
                run_id=self.run_id,
                model=call.model,
                user_prompt=call.user_prompt,
                response=call.response,
                input_tokens=call.input_tokens,
                output_tokens=call.output_tokens,
                cached_tokens=call.cached_tokens,
                tools_called=call.tools_called,
                tool_results_summary=call.tool_results_summary,
                system_prompt=call.system_prompt,
                system_prompt_version=call.system_prompt_version,
                consistency_group_id=call.consistency_group_id,
                call_id=call.call_id,
            )
        call_id = self._parent.log(call)
        self.call_ids.append(call_id)
        return call_id
