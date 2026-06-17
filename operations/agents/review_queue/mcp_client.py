"""Thin adapter that encapsulates the four Stage 2 read-only MCP tools.

The agent layer must never touch CSVs, SQL, or the database directly. It only
talks to the MCP read-only layer through this client. The client wraps the four
contract tools and nothing else:

    - get_anomaly_review_summary()
    - get_anomaly_case(case_id)
    - list_monitor_artifacts()
    - get_method_limits()

Wiring strategy
---------------
To keep the scaffold *self-contained and independently testable* without copying
the MCP read-logic by hand, this module imports the real Stage 2 module. It
resolves the implementation in this order:

    1. The vendored read-only copy shipped next to this file
       (``agents/_vendored_monitor_readonly.py``). This is the default so the
       scaffold runs green with no repo on ``sys.path``.
    2. If an env var ``STAGE3_MCP_FROM_REPO`` points at a thesis repo root, the
       canonical ``operations.mcp.monitor_readonly`` module is imported from
       there instead (so the website repo can later bind to the live module).

In production (website repo) this client is the single seam to swap for a real
MCP transport (HTTP/stdio to the deployed MCP server) — see STAGE3_HANDOFF.md.
Until then it calls the in-process read-only functions, which already enforce
the 50-row cap, wallet redaction, and the audit append.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

# ---------------------------------------------------------------------------
# Resolve the underlying read-only MCP implementation (no logic is copied).
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent


def _load_mcp_module():
    """Return the Stage 2 read-only module without duplicating its logic."""
    repo_root = os.environ.get("STAGE3_MCP_FROM_REPO")
    if repo_root:
        # Bind to the canonical module inside a thesis/website repo checkout.
        root = Path(repo_root).resolve()
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        return importlib.import_module("operations.mcp.monitor_readonly")

    # Default: load the vendored read-only copy that ships with the scaffold.
    vendored = _THIS_DIR / "_vendored_monitor_readonly.py"
    spec = importlib.util.spec_from_file_location(
        "stage3_vendored_monitor_readonly", vendored
    )
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"Cannot load vendored MCP module at {vendored}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_MCP = _load_mcp_module()

#: Re-export the canonical wallet redaction so agents can re-assert it on their
#: own derived text without re-implementing the pattern.
redact_wallet_addresses: Callable[[Any], Any] = _MCP.redact_wallet_addresses
MAX_ROWS: int = _MCP.MAX_ROWS
WALLET_REDACTION_PLACEHOLDER: str = _MCP.WALLET_REDACTION_PLACEHOLDER


class McpReadOnlyClient:
    """Bounded, read-only facade over exactly the four contract tools.

    Parameters
    ----------
    data_root:
        Directory that contains the ``data/`` tree (a fixture root in tests, the
        repo/deployment root in production). Forwarded verbatim to the MCP layer.
    audit_path:
        Optional audit-sink override forwarded to the MCP layer. The MCP layer
        writes one audit record per tool call; this is the *tool* audit trail,
        distinct from the *LLM* audit trail in ``agents.llm``.
    """

    def __init__(
        self,
        data_root: Optional[Union[str, Path]] = None,
        audit_path: Optional[Union[str, Path]] = None,
    ) -> None:
        self._data_root = data_root
        self._audit_path = audit_path

    # -- the four tools, and only these four -------------------------------

    def get_anomaly_review_summary(self) -> Dict[str, Any]:
        """Bounded review summary (contract row_count = 1)."""
        return _MCP.get_anomaly_review_summary(
            data_root=self._data_root, audit_path=self._audit_path
        )

    def get_anomaly_case(self, case_id: str) -> Dict[str, Any]:
        """Bounded multi-section review record for one ``case_id``."""
        return _MCP.get_anomaly_case(
            case_id, data_root=self._data_root, audit_path=self._audit_path
        )

    def list_monitor_artifacts(self) -> Dict[str, Any]:
        """Inventory of the bounded artifacts the read-only layer may expose."""
        return _MCP.list_monitor_artifacts(
            data_root=self._data_root, audit_path=self._audit_path
        )

    def get_method_limits(self) -> Dict[str, Any]:
        """Documented contract limits / blocked claims."""
        return _MCP.get_method_limits(
            data_root=self._data_root, audit_path=self._audit_path
        )


__all__ = [
    "McpReadOnlyClient",
    "redact_wallet_addresses",
    "MAX_ROWS",
    "WALLET_REDACTION_PLACEHOLDER",
]
