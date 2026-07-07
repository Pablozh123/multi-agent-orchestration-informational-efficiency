import datetime as _dt
if not hasattr(_dt, "UTC"):
    _dt.UTC = _dt.timezone.utc

from operations.analysis.agent_review_queue_eval import (
    check_determinism,
    evaluate,
    load_reference_contexts,
)


def test_eval_runs_and_is_safe():
    result = evaluate()
    summary = result["summary"]
    assert summary["n_cases"] >= 1
    assert summary["safety"]["passed"] is True
    for key in ("precision", "recall", "f1", "tp", "fp", "fn", "tn"):
        assert key in summary


def test_eval_is_deterministic():
    assert check_determinism() is True


def test_reference_contexts_loaded():
    reference = load_reference_contexts()
    assert reference
    assert any(
        v in ("reference_hit", "partial_reference_overlap", "no_reference_overlap")
        for v in reference.values()
    )
