"""Thin read-only MCP entry point for the monitor anomaly-review tools.

All testable logic lives in ``monitor_readonly.py``. This module only wires the
four contract tools into a server surface:

    - If an MCP library is installed (``mcp`` / FastMCP), the tools are
      registered with it.
    - Otherwise a minimal stdlib JSON dispatcher is provided so the contract is
      still callable and inspectable without external dependencies. The
      ``__main__`` block lists the registered tools and runs one bounded example
      call per tool.

The server adds no logic of its own: it forwards to the bounded, audited tool
functions, which enforce the 50-row cap, wallet redaction, and audit logging.
No raw SQL, no database writes (beyond the audit append), no order/trading path.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, Optional

try:  # Support both package import and direct-script execution.
    from . import monitor_readonly as mr
except ImportError:  # pragma: no cover - direct ``python server.py`` fallback
    import monitor_readonly as mr  # type: ignore


#: Tool name -> callable, sourced from the single registry in monitor_readonly.
TOOL_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = dict(mr.TOOLS)

#: Lightweight, MCP-agnostic descriptors for the four tools (name + arguments).
TOOL_SPECS = [
    {
        "name": "get_anomaly_review_summary",
        "description": "Return the single bounded anomaly-review summary row.",
        "arguments": [],
    },
    {
        "name": "get_anomaly_case",
        "description": "Return the bounded review record for one case_id.",
        "arguments": ["case_id"],
    },
    {
        "name": "list_monitor_artifacts",
        "description": "List the bounded monitor artifacts exposed read-only.",
        "arguments": [],
    },
    {
        "name": "get_method_limits",
        "description": "Return documented read-only contract limits.",
        "arguments": [],
    },
]


def dispatch(
    tool: str,
    arguments: Optional[Dict[str, Any]] = None,
    *,
    data_root: Optional[str] = None,
    audit_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Minimal JSON dispatch used when no MCP library is available.

    Looks up ``tool`` in the registry and forwards ``arguments`` plus the
    optional ``data_root`` / ``audit_path``. Unknown tools return a structured
    error rather than raising, so a caller cannot crash the dispatcher with a
    bad name. No tool outside the four-tool contract is reachable.
    """
    arguments = dict(arguments or {})
    func = TOOL_REGISTRY.get(tool)
    if func is None:
        return {
            "error": "unknown_tool",
            "tool": tool,
            "available_tools": sorted(TOOL_REGISTRY),
        }
    if data_root is not None:
        arguments.setdefault("data_root", data_root)
    if audit_path is not None:
        arguments.setdefault("audit_path", audit_path)
    return func(**arguments)


def build_mcp_server():  # pragma: no cover - exercised only when mcp installed
    """Register the four tools with an MCP server if a library is available.

    Returns the server instance on success, or ``None`` if no supported MCP
    library is importable (in which case callers fall back to ``dispatch``).
    """
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except Exception:
        return None

    server = FastMCP("monitor-readonly")

    @server.tool()
    def get_anomaly_review_summary() -> Dict[str, Any]:
        return mr.get_anomaly_review_summary()

    @server.tool()
    def get_anomaly_case(case_id: str) -> Dict[str, Any]:
        return mr.get_anomaly_case(case_id)

    @server.tool()
    def list_monitor_artifacts() -> Dict[str, Any]:
        return mr.list_monitor_artifacts()

    @server.tool()
    def get_method_limits() -> Dict[str, Any]:
        return mr.get_method_limits()

    return server


def _example_run(data_root: Optional[str] = None, audit_path: Optional[str] = None) -> None:
    """List the tools and run one bounded example call per tool (stdout only)."""
    print("Registered read-only monitor tools:")
    for spec in TOOL_SPECS:
        args = ", ".join(spec["arguments"]) if spec["arguments"] else "(none)"
        print(f"  - {spec['name']}({args}): {spec['description']}")

    print("\nExample bounded calls:")
    examples = [
        ("get_method_limits", {}),
        ("list_monitor_artifacts", {}),
        ("get_anomaly_review_summary", {}),
        ("get_anomaly_case", {"case_id": "__example_unknown_case__"}),
    ]
    for tool, arguments in examples:
        result = dispatch(tool, arguments, data_root=data_root, audit_path=audit_path)
        print(f"\n# {tool} {arguments}")
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True)[:1200])


if __name__ == "__main__":
    server = build_mcp_server()
    if server is not None:  # pragma: no cover - only when mcp lib present
        print("MCP library detected; starting monitor-readonly server.")
        server.run()
    else:
        print("No MCP library available; running stdlib dispatch demo.\n")
        _example_run()
