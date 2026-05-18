"""Thesis MCP Server — Demonstrationslayer (CLAUDE.md v2.1 §10).

Duenner FastMCP-Server, der die Funktionen aus `operations.tools.db_tools`
als MCP-Tools exponiert. Gedacht fuer die Integration in Claude Desktop
oder andere MCP-Clients.

Wichtig: Der Server ist *nicht* der produktive Pfad der Thesis. Die Haupt-
Architektur verwendet Pydantic-AI-Agents direkt (siehe
`operations/agents/`). Dieser Server existiert nur, um das Tool-Ecosystem
auch ausserhalb der Agent-Pipeline nutzbar zu machen.

Start in Claude Desktop:
    python -m operations.mcp.thesis_mcp_server

Oder direkt:
    python operations/mcp/thesis_mcp_server.py
"""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from operations.tools import db_tools


mcp = FastMCP("thesis")


# --- Thin wrappers around db_tools ---------------------------------------


@mcp.tool
def get_polymarket_prices(
    start_date: str,
    end_date: str,
    resolution: str = "daily",
) -> list[dict[str, Any]]:
    """Liefert Polymarket-Preiszeilen fuer ein Zeitfenster (max. 50 Zeilen).

    Args:
        start_date: ISO-Datum YYYY-MM-DD.
        end_date: ISO-Datum YYYY-MM-DD.
        resolution: 'daily' oder 'raw'.
    """
    return db_tools.fetch_polymarket_prices((start_date, end_date), resolution=resolution)


@mcp.tool
def get_whale_activity(
    wallet: str | None = None,
    week: str | None = None,
    min_usd: float | None = None,
) -> list[dict[str, Any]]:
    """Liefert Whale-Trades mit optionalen Filtern (max. 50 Zeilen)."""
    return db_tools.query_whale_activity(wallet=wallet, week=week, min_usd=min_usd)


@mcp.tool
def get_sentiment(
    start_date: str,
    end_date: str,
    theme: str | None = None,
) -> list[dict[str, Any]]:
    """Liefert GDELT-Sentiment-Zeilen fuer ein Zeitfenster (max. 50)."""
    return db_tools.fetch_sentiment_data((start_date, end_date), theme=theme)


@mcp.tool
def get_poll_forecasts(
    start_date: str,
    end_date: str,
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Liefert Poll-Forecasts fuer ein Zeitfenster (max. 50)."""
    return db_tools.query_poll_data((start_date, end_date), source=source)


@mcp.tool
def get_events_in_window(
    start_date: str,
    end_date: str,
    event_type: str | None = None,
) -> list[dict[str, Any]]:
    """Liefert Events (events_timeline) fuer ein Zeitfenster (max. 50)."""
    return db_tools.query_events_in_window((start_date, end_date), event_type=event_type)


@mcp.tool
def get_data_summary(
    table: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any]:
    """Aggregierte Zusammenfassung einer Core-Tabelle fuer ein Zeitfenster."""
    return db_tools.generate_data_summary(table, (start_date, end_date))


@mcp.tool
def get_precomputed_summary(metric_name: str) -> list[dict[str, Any]]:
    """Liest Pre-computed Summaries aus analysis_summaries."""
    return db_tools.get_precomputed_summary(metric_name)


@mcp.tool
async def run_full_analysis(question: str) -> dict[str, Any]:
    """Full Multi-Agent-Analyse via Orchestrator.

    Achtung: fuehrt Live-LLM-Calls gegen die Anthropic API aus — nur mit
    gueltigem ANTHROPIC_API_KEY in der .env verwenden.
    """
    # Lazy import — avoids loading the heavy agent graph when only the
    # read-only tools are used.
    from operations.agents.orchestrator import run_analysis

    report = await run_analysis(question)
    return report.model_dump()


# --- Entrypoint ----------------------------------------------------------


def main() -> None:
    """Startet den MCP-Server im stdio-Transport."""
    mcp.run()


if __name__ == "__main__":
    main()
