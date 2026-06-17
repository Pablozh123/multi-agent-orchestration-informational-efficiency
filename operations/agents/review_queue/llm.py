"""Thin LLM abstraction with a deterministic mock default and audit logging.

``call_llm(role, system, user, audit_path=...)`` is the single seam every agent
uses to reach a language model. By default it routes to a DETERMINISTIC MOCK:

    - no network, no API key, no SDK import;
    - identical (role, system, user) -> identical output, always;
    - every call appends exactly one audit record.

Audit record shape (one JSONL line per call)::

    {"role": ..., "prompt_hash": <sha256 of system+user>, "ts_utc": ...,
     "backend": "mock", "output_hash": <sha256 of output>}

The prompt text itself is NOT stored (only its hash), so prompts that might
echo bounded artifact text never leak into the audit file. The audit append is
the only write this module performs.

Swapping in a real model (website repo) means providing a ``backend`` callable;
the audit contract stays identical. See STAGE3_HANDOFF.md. The mock is the
default precisely so the scaffold, CI, and the smoke test never touch a network
and never require a key.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

#: Default location for the LLM audit trail, relative to ``data_root`` (or used
#: as-is when absolute). Distinct from the MCP *tool* audit log.
DEFAULT_LLM_AUDIT_PATH: str = "data/results/stage3_llm_audit_log.jsonl"

#: Type of a backend: (system, user) -> assistant text.
LlmBackend = Callable[[str, str], str]


def _utc_now_iso() -> str:
    """UTC timestamp without microseconds, e.g. ``2026-06-16T12:00:00+00:00``."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mock_backend(system: str, user: str) -> str:
    """Deterministic, network-free mock LLM.

    The mock does not "understand" anything; it deterministically echoes a
    compact, bounded JSON envelope keyed off a stable hash of the prompt. Agents
    do not rely on the *content* being intelligent — they rely only on it being
    deterministic and audit-able. Real interpretation is wired later by swapping
    the backend (see STAGE3_HANDOFF.md).
    """
    digest = _sha256(system + "\x00" + user)
    return json.dumps(
        {
            "mock": True,
            "prompt_hash": digest,
            # A short deterministic token so callers can confirm round-trips.
            "echo_token": digest[:12],
        },
        sort_keys=True,
    )


def call_llm(
    role: str,
    system: str,
    user: str,
    *,
    audit_path: Optional[Union[str, Path]] = None,
    data_root: Optional[Union[str, Path]] = None,
    backend: Optional[LlmBackend] = None,
    audit_sink: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Call the (mock by default) LLM and append exactly one audit record.

    Parameters
    ----------
    role:
        Logical agent role making the call (e.g. ``"CaseNarrative"``). Recorded
        in the audit entry so every model interaction is attributable.
    system, user:
        Prompt halves. Hashed (not stored) for the audit trail.
    audit_path / data_root:
        Where to append the JSONL audit record. If ``audit_path`` is relative it
        is resolved under ``data_root`` (default: cwd). The parent dir is
        created if needed. This append is the module's only write.
    backend:
        Optional ``(system, user) -> str`` callable. Defaults to the
        deterministic, network-free :func:`mock_backend`. Production wires a real
        model here without changing the audit contract.
    audit_sink:
        Optional in-memory list. When provided, the audit record is also
        appended here. Tests use this to assert "one audit entry per LLM call"
        without reading the file. Does not replace the file append.

    Returns
    -------
    str
        The backend's raw text output.
    """
    chosen = backend or mock_backend
    backend_name = "mock" if chosen is mock_backend else getattr(
        chosen, "__name__", "custom"
    )

    output = chosen(system, user)

    entry: Dict[str, Any] = {
        "role": role,
        "prompt_hash": _sha256(system + "\x00" + user),
        "ts_utc": _utc_now_iso(),
        "backend": backend_name,
        "output_hash": _sha256(output),
    }

    # Resolve audit destination.
    if audit_path is None:
        base = Path(data_root) if data_root is not None else Path.cwd()
        resolved = base / DEFAULT_LLM_AUDIT_PATH
    else:
        candidate = Path(audit_path)
        if candidate.is_absolute():
            resolved = candidate
        else:
            base = Path(data_root) if data_root is not None else Path.cwd()
            resolved = base / candidate

    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

    if audit_sink is not None:
        audit_sink.append(entry)

    return output


__all__ = [
    "call_llm",
    "mock_backend",
    "DEFAULT_LLM_AUDIT_PATH",
    "LlmBackend",
]
