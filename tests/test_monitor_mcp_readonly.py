"""Tests for the read-only monitor MCP tool layer (Stage 2).

Runs two ways:

    python3 tests/test_monitor_mcp_readonly.py     # plain asserts + own main
    pytest tests/test_monitor_mcp_readonly.py      # discovered as test_* fns

No external dependencies are required for the plain run. Hermetic mini-fixtures
under ``tests/fixtures/`` are used, never the real data. Each test that writes
an audit log points it at a unique temp directory so audit-count assertions are
isolated.

Coverage:
    (a) every response is hard-capped to <= 50 rows
    (b) no 0x+40-hex wallet address appears in any output
    (c) exactly one audit entry is appended per tool call
    (d) get_method_limits surfaces every documented limit key
    (e) an unknown case_id is handled cleanly (found=False, no crash, no leak)
    (f) determinism: identical inputs yield identical payloads
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

# Make ``operations`` importable whether run from the repo root, the staging
# root, or the tests directory.
_THIS = Path(__file__).resolve()
_ROOT = _THIS.parent.parent
for _candidate in (_ROOT, _ROOT / "operations" / "mcp"):
    sys.path.insert(0, str(_candidate))

try:
    from operations.mcp import monitor_readonly as mr  # type: ignore
    from operations.mcp import server as srv  # type: ignore
except ImportError:  # fall back to flat import when packages are unavailable
    import monitor_readonly as mr  # type: ignore
    import server as srv  # type: ignore


FIXTURE_ROOT = _THIS.parent / "fixtures"

#: Any 0x+40-hex token NOT followed by another hex char (a real wallet address).
_WALLET_PATTERN = re.compile(r"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])")

#: A planted wallet present verbatim in the source fixtures; it must never leak.
_PLANTED_WALLETS = (
    "0x1111111111111111111111111111111111111111",
    "0x2222222222222222222222222222222222222222",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _walk_strings(value):
    """Yield every string found anywhere in a nested structure."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk_strings(item)


def _count_rows(payload) -> int:
    """Count the largest bounded row collection in a tool payload."""
    counts = [0]
    if isinstance(payload, dict):
        for key in ("rows", "artifacts"):
            if isinstance(payload.get(key), list):
                counts.append(len(payload[key]))
        sections = payload.get("sections")
        if isinstance(sections, dict):
            counts.append(sum(len(v) for v in sections.values() if isinstance(v, list)))
    return max(counts)


def _audit_lines(audit_file: Path):
    if not audit_file.exists():
        return []
    text = audit_file.read_text(encoding="utf-8").strip()
    return [line for line in text.splitlines() if line.strip()]


def _fresh_audit(tmpdir: str) -> Path:
    """Return a fresh per-call audit path inside a temp dir."""
    return Path(tmpdir) / "audit.jsonl"


def _all_tool_calls(data_root, audit_path):
    """Invoke every tool once and return the list of payloads (fixed order)."""
    return [
        mr.get_anomaly_review_summary(data_root=data_root, audit_path=audit_path),
        mr.get_anomaly_case("FIXCASE-1", data_root=data_root, audit_path=audit_path),
        mr.list_monitor_artifacts(data_root=data_root, audit_path=audit_path),
        mr.get_method_limits(data_root=data_root, audit_path=audit_path),
    ]


# ---------------------------------------------------------------------------
# (a) Row cap
# ---------------------------------------------------------------------------

def test_responses_respect_row_cap():
    with tempfile.TemporaryDirectory() as tmp:
        payloads = _all_tool_calls(FIXTURE_ROOT, _fresh_audit(tmp))
    for payload in payloads:
        assert _count_rows(payload) <= mr.MAX_ROWS
        assert int(payload.get("row_count", 0)) <= mr.MAX_ROWS


def test_row_cap_holds_on_oversized_artifact():
    """Synthesize a 60-row queue and confirm get_anomaly_case still caps at 50."""
    header = (
        "case_id,timestamp_utc,market_id,market_slug,question,review_priority,"
        "priority_basis,trigger_family,market_move_context,wallet_flow_context,"
        "concentration_context,event_context_status,reference_overlap_status,"
        "review_label,missing_evidence,human_review_status,"
        "review_status_updated_at_utc,review_note,reviewer,review_source_url,"
        "event_source_url,allowed_interpretation,blocked_claims,source_artifacts"
    )
    with tempfile.TemporaryDirectory() as tmp:
        results_dir = Path(tmp) / "data" / "results"
        results_dir.mkdir(parents=True)
        lines = [header]
        for _ in range(60):  # all share one case_id
            lines.append(
                "BULK," + ",".join(["x"] * (header.count(",")))
            )
        (results_dir / "monitor_anomaly_review_queue.csv").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        payload = mr.get_anomaly_case(
            "BULK", data_root=tmp, audit_path=_fresh_audit(tmp)
        )
        assert payload["sections"]["queue"].__len__() == mr.MAX_ROWS
        assert payload["row_count"] <= mr.MAX_ROWS


# ---------------------------------------------------------------------------
# (b) Wallet-address guard
# ---------------------------------------------------------------------------

def test_no_wallet_address_in_any_output():
    with tempfile.TemporaryDirectory() as tmp:
        payloads = _all_tool_calls(FIXTURE_ROOT, _fresh_audit(tmp))
    for payload in payloads:
        for text in _walk_strings(payload):
            assert not _WALLET_PATTERN.search(text), f"wallet leaked in: {text!r}"
        for planted in _PLANTED_WALLETS:
            assert planted not in json.dumps(payload)


def test_market_token_id_is_preserved():
    """64-hex market token ids must survive redaction (not be clipped)."""
    with tempfile.TemporaryDirectory() as tmp:
        payload = mr.get_anomaly_case(
            "FIXCASE-1", data_root=FIXTURE_ROOT, audit_path=_fresh_audit(tmp)
        )
    blob = json.dumps(payload)
    assert "0xabc1230000000000000000000000000000000000000000000000000000000def" in blob
    assert mr.WALLET_REDACTION_PLACEHOLDER in blob  # the planted wallet was masked


def test_audit_log_does_not_leak_wallets():
    with tempfile.TemporaryDirectory() as tmp:
        audit = _fresh_audit(tmp)
        # case_id that itself contains a wallet-looking token
        mr.get_anomaly_case(
            "0x3333333333333333333333333333333333333333",
            data_root=FIXTURE_ROOT,
            audit_path=audit,
        )
        for line in _audit_lines(audit):
            assert not _WALLET_PATTERN.search(line)


# ---------------------------------------------------------------------------
# (c) Exactly one audit entry per call
# ---------------------------------------------------------------------------

def test_exactly_one_audit_entry_per_call():
    cases = [
        ("get_anomaly_review_summary", lambda a: mr.get_anomaly_review_summary(data_root=FIXTURE_ROOT, audit_path=a)),
        ("get_anomaly_case", lambda a: mr.get_anomaly_case("FIXCASE-1", data_root=FIXTURE_ROOT, audit_path=a)),
        ("list_monitor_artifacts", lambda a: mr.list_monitor_artifacts(data_root=FIXTURE_ROOT, audit_path=a)),
        ("get_method_limits", lambda a: mr.get_method_limits(data_root=FIXTURE_ROOT, audit_path=a)),
    ]
    for tool_name, call in cases:
        with tempfile.TemporaryDirectory() as tmp:
            audit = _fresh_audit(tmp)
            call(audit)
            lines = _audit_lines(audit)
            assert len(lines) == 1, f"{tool_name}: expected 1 audit line, got {len(lines)}"
            entry = json.loads(lines[0])
            assert entry["tool"] == tool_name
            assert set(entry.keys()) == {"tool", "args", "row_count", "ts_utc"}
            assert isinstance(entry["row_count"], int)


def test_audit_entries_accumulate_one_per_call():
    with tempfile.TemporaryDirectory() as tmp:
        audit = _fresh_audit(tmp)
        mr.get_method_limits(data_root=FIXTURE_ROOT, audit_path=audit)
        mr.get_method_limits(data_root=FIXTURE_ROOT, audit_path=audit)
        mr.list_monitor_artifacts(data_root=FIXTURE_ROOT, audit_path=audit)
        assert len(_audit_lines(audit)) == 3


# ---------------------------------------------------------------------------
# (d) get_method_limits documented keys
# ---------------------------------------------------------------------------

def test_method_limits_contains_documented_keys():
    with tempfile.TemporaryDirectory() as tmp:
        payload = mr.get_method_limits(data_root=FIXTURE_ROOT, audit_path=_fresh_audit(tmp))
    limits = payload["limits"]
    for key in mr.METHOD_LIMIT_KEYS:
        assert key in limits, f"missing documented limit key: {key}"
    assert limits["max_rows"] == 50
    assert limits["raw_sql_allowed"] is False
    assert limits["wallet_address_exposure_allowed_by_default"] is False
    assert limits["order_or_trading_path_allowed"] is False
    assert limits["llm_audit_log_required"] is True
    assert sorted(limits["tools"]) == sorted(
        [
            "get_anomaly_review_summary",
            "get_anomaly_case",
            "list_monitor_artifacts",
            "get_method_limits",
        ]
    )


def test_method_limits_falls_back_without_metadata():
    """Missing metadata file -> conservative defaults, all keys still present."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "data" / "results").mkdir(parents=True)
        payload = mr.get_method_limits(data_root=tmp, audit_path=_fresh_audit(tmp))
    limits = payload["limits"]
    for key in mr.METHOD_LIMIT_KEYS:
        assert key in limits
    assert limits["max_rows"] <= mr.MAX_ROWS
    assert limits["raw_sql_allowed"] is False


# ---------------------------------------------------------------------------
# (e) Unknown case_id
# ---------------------------------------------------------------------------

def test_unknown_case_id_handled_cleanly():
    with tempfile.TemporaryDirectory() as tmp:
        audit = _fresh_audit(tmp)
        payload = mr.get_anomaly_case(
            "does-not-exist-123", data_root=FIXTURE_ROOT, audit_path=audit
        )
        assert payload["found"] is False
        assert payload["row_count"] == 0
        assert all(rows == [] for rows in payload["sections"].values())
        assert "message" in payload
        # still exactly one audit entry, row_count 0
        lines = _audit_lines(audit)
        assert len(lines) == 1
        assert json.loads(lines[0])["row_count"] == 0


def test_empty_case_id_does_not_crash():
    with tempfile.TemporaryDirectory() as tmp:
        payload = mr.get_anomaly_case("", data_root=FIXTURE_ROOT, audit_path=_fresh_audit(tmp))
        assert payload["found"] is False


def test_known_case_id_returns_all_sections():
    with tempfile.TemporaryDirectory() as tmp:
        payload = mr.get_anomaly_case("FIXCASE-1", data_root=FIXTURE_ROOT, audit_path=_fresh_audit(tmp))
    assert payload["found"] is True
    assert payload["row_count"] >= 4  # one row per section
    for section in ("queue", "case_review_packet", "status_transition", "decision_readiness"):
        assert len(payload["sections"][section]) == 1


# ---------------------------------------------------------------------------
# (f) Determinism
# ---------------------------------------------------------------------------

def _strip_ts(payload):
    """Remove volatile timestamp fields before comparing for determinism."""
    return json.dumps(payload, sort_keys=True)


def test_determinism_identical_inputs():
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        first = _all_tool_calls(FIXTURE_ROOT, _fresh_audit(tmp1))
        second = _all_tool_calls(FIXTURE_ROOT, _fresh_audit(tmp2))
    for a, b in zip(first, second):
        # payloads carry no timestamps, so they must be byte-identical
        assert _strip_ts(a) == _strip_ts(b)


# ---------------------------------------------------------------------------
# Server / dispatch surface
# ---------------------------------------------------------------------------

def test_server_dispatch_routes_known_tool():
    with tempfile.TemporaryDirectory() as tmp:
        result = srv.dispatch(
            "get_method_limits", {}, data_root=str(FIXTURE_ROOT), audit_path=str(_fresh_audit(tmp))
        )
    assert result["tool"] == "get_method_limits"
    assert "limits" in result


def test_server_dispatch_unknown_tool_is_structured_error():
    result = srv.dispatch("not_a_tool", {})
    assert result["error"] == "unknown_tool"
    assert "available_tools" in result
    assert len(result["available_tools"]) == 4


def test_server_registers_exactly_four_tools():
    assert sorted(srv.TOOL_REGISTRY) == sorted(
        [
            "get_anomaly_review_summary",
            "get_anomaly_case",
            "list_monitor_artifacts",
            "get_method_limits",
        ]
    )
    assert len(srv.TOOL_SPECS) == 4


# ---------------------------------------------------------------------------
# Plain-python runner (no pytest required)
# ---------------------------------------------------------------------------

def _run_all():
    tests = [
        (name, obj)
        for name, obj in sorted(globals().items())
        if name.startswith("test_") and callable(obj)
    ]
    passed = 0
    failed = []
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"PASS {name}")
        except AssertionError as exc:
            failed.append((name, f"AssertionError: {exc}"))
            print(f"FAIL {name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failed.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
    print("\n" + "=" * 60)
    print(f"TOTAL {len(tests)}  PASSED {passed}  FAILED {len(failed)}")
    if failed:
        for name, reason in failed:
            print(f"  - {name}: {reason}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(_run_all())
