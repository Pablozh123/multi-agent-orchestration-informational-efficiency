"""Tests fuer den taeglichen Review-Lauf mit Publish-Schritt."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from operations.pipeline import daily_review_run as drr


def _queue_result(**overrides):
    case = {
        "case_id": "monitor_candidate_x",
        "question": "Testfrage?",
        "market_slug": "test-markt",
        "priority": "high",
        "score": 0.9,
        "recommendation": "escalate_human",
        "narrative": "Deterministische Zusammenfassung.",
        "skeptic_note": "Benigne Erklaerung moeglich.",
        "confidence_adjustment": -0.1,
        "human_review_status": "needs_human_review",
        "allowed_interpretation": "statistische Auffaelligkeit",
    }
    case.update(overrides)
    return {
        "queue_kind": "anomaly_review_priority_queue",
        "count": 1,
        "ranked_cases": [case],
        "steps": [],
        "allowed_interpretation": "statistische Auffaelligkeit",
        "blocked_claims": "causality; tradeability",
    }


# ---------------------------------------------------------------------------
# Redaktions-Gate
# ---------------------------------------------------------------------------


def test_gate_blocks_wallet_address() -> None:
    text = json.dumps({"x": "0x" + "a" * 40})
    with pytest.raises(drr.RedactionGateError):
        drr.run_redaction_gate({"queue.json": text})


def test_gate_allows_condition_id_64_hex() -> None:
    # Condition-/Token-Ids (0x + 64 hex) und sha256-Hashes sind KEINE
    # Wallet-Adressen.
    text = json.dumps({"condition_id": "0x" + "a" * 64, "prompt_hash": "b" * 64})
    drr.run_redaction_gate({"mentions_latenz.json": text})


def test_gate_blocks_wallet_variants() -> None:
    # Grosses 0X-Praefix und nackte 40-Hex-Sequenzen entkommen nicht.
    for value in ("0X" + "a" * 40, "wallet " + "b" * 40 + " gekauft"):
        with pytest.raises(drr.RedactionGateError):
            drr.run_redaction_gate({"queue.json": json.dumps({"v": value})})


def test_gate_blocks_json_form_key_pairs() -> None:
    # JSON-serialisierte Key/Value-Paare ("api_key": "...") muessen anschlagen.
    for text in (
        '{"api_key": "abcdefabcdefabcdef"}',
        json.dumps({"nested": {"private_key": "abcdefabcdefabcdef12"}}),
    ):
        with pytest.raises(drr.RedactionGateError):
            drr.run_redaction_gate({"audit.json": text})


def test_gate_blocks_key_like_strings() -> None:
    for secret in (
        "sk-ant-abc12345678",
        "ghp_" + "a" * 24,
        "AKIA" + "A" * 16,
        "-----BEGIN RSA PRIVATE KEY-----",
        'api_key = "abcdefabcdefabcdef"',
    ):
        with pytest.raises(drr.RedactionGateError):
            drr.run_redaction_gate({"audit.json": json.dumps({"v": secret})})


def test_gate_error_does_not_leak_value() -> None:
    secret = "sk-ant-supersecretvalue123"
    try:
        drr.run_redaction_gate({"meta.json": secret})
    except drr.RedactionGateError as exc:
        assert secret not in str(exc)
    else:  # pragma: no cover
        pytest.fail("Gate haette anschlagen muessen")


def test_gate_clean_payload_passes() -> None:
    drr.run_redaction_gate({"queue.json": json.dumps({"ok": True})})


# ---------------------------------------------------------------------------
# queue.json
# ---------------------------------------------------------------------------


def test_queue_payload_maps_and_sorts() -> None:
    result = {
        "queue_kind": "anomaly_review_priority_queue",
        "count": 3,
        "ranked_cases": [
            _queue_result()["ranked_cases"][0],
            {**_queue_result()["ranked_cases"][0], "case_id": "b", "priority": "low", "score": 0.2, "recommendation": "watch", "confidence_adjustment": None},
            {**_queue_result()["ranked_cases"][0], "case_id": "a", "priority": "medium", "score": 0.5, "recommendation": "check_source"},
        ],
        "steps": [],
        "allowed_interpretation": "x",
        "blocked_claims": "y",
    }
    payload = drr.build_queue_payload(
        result,
        queue_csv_rows=[{"case_id": "monitor_candidate_x", "timestamp_utc": "2026-07-01T00:00:00Z"}],
        now_utc="2026-07-07T00:00:00+00:00",
        backend_name="mock",
    )
    assert [c.score_band for c in payload.cards] == ["high", "medium", "low"]
    assert payload.cards[0].empfehlung == "eskalation_mensch"
    assert payload.cards[0].zeitfenster == "2026-07-01T00:00:00Z"
    assert payload.cards[0].skeptic_abschlag == -0.1
    assert payload.cards[1].empfehlung == "quelle_pruefen"
    assert payload.cards[2].empfehlung == "beobachten"
    assert payload.count == 3


def test_queue_payload_rejects_non_whitelist_recommendation() -> None:
    with pytest.raises(ValueError):
        drr.build_queue_payload(
            _queue_result(recommendation="buy_now"),
            queue_csv_rows=[],
            now_utc="2026-07-07T00:00:00+00:00",
            backend_name="mock",
        )


def test_queue_payload_rejects_bad_band_fail_closed() -> None:
    with pytest.raises(ValidationError):
        drr.build_queue_payload(
            _queue_result(priority="urgent"),
            queue_csv_rows=[],
            now_utc="2026-07-07T00:00:00+00:00",
            backend_name="mock",
        )


def test_queue_payload_rejects_positive_abschlag() -> None:
    # Prioritaet ist nur senkbar: positiver "Abschlag" verletzt das Schema.
    with pytest.raises(ValidationError):
        drr.build_queue_payload(
            _queue_result(confidence_adjustment=0.2),
            queue_csv_rows=[],
            now_utc="2026-07-07T00:00:00+00:00",
            backend_name="mock",
        )


# ---------------------------------------------------------------------------
# mentions_latenz.json
# ---------------------------------------------------------------------------


def test_mentions_ok_exact_match_and_exclusions() -> None:
    rows = [
        {
            "event": "fall_ok",
            "drop_ts_utc": "2026-06-01T00:00:00Z",
            "minuten_bis_erste_reaktion": "4.0",
            "minuten_bis_konvergenz": "12.5",
            "stunden_im_handelbaren_fenster": "1.25",
            "endpreis": "0.97",
            "status": "ok",
        },
        {
            "event": "fall_teilstatus",
            "drop_ts_utc": "2026-06-02T00:00:00Z",
            "minuten_bis_erste_reaktion": "3.0",
            "minuten_bis_konvergenz": "",
            "stunden_im_handelbaren_fenster": "",
            "endpreis": "",
            # darf NICHT als ok durchgehen (kein startswith-Match)
            "status": "ok_spaeter;keine_konvergenz_im_fenster",
        },
        {
            "event": "allin_next_episode",
            "drop_ts_utc": "2026-06-03T00:00:00Z",
            "minuten_bis_erste_reaktion": "",
            "minuten_bis_konvergenz": "",
            "stunden_im_handelbaren_fenster": "",
            "endpreis": "",
            "status": "ausgeschlossen_zuordnungsambiguitaet",
        },
    ]
    # Reales Producer-Schema (mentions_latency.py): ausgeschlossene_events
    # enthaelt NUR {event, status}; der Grund wird aus dem Status abgeleitet.
    metadata = {
        "ausgeschlossene_events": [
            {"event": "allin_next_episode", "status": "ausgeschlossen_zuordnungsambiguitaet"}
        ],
        "limitationen": ["Nur punktfoermige Drops."],
    }
    payload = drr.build_mentions_latenz(
        mentions_rows=rows, metadata=metadata, now_utc="2026-07-07T00:00:00+00:00"
    )
    assert [f.event for f in payload.faelle] == ["fall_ok"]
    assert {a.event for a in payload.ausschluesse} == {
        "fall_teilstatus",
        "allin_next_episode",
    }
    grund = {a.event: a.grund for a in payload.ausschluesse}
    assert grund["allin_next_episode"] == "Seed-Ausschluss: zuordnungsambiguitaet"
    assert grund["fall_teilstatus"].startswith("Messstatus:")
    assert payload.limitationen == ["Nur punktfoermige Drops."]


# ---------------------------------------------------------------------------
# pipeline_forward.json
# ---------------------------------------------------------------------------


def _write_live_fixture(tmp_path: Path) -> Path:
    live = tmp_path / "allin_july3"
    live.mkdir(parents=True)
    record = {
        "wall_ts_utc": "2026-07-03T20:00:00Z",
        "decision": {
            "market_id": "111",
            "action": "YES",
            "token_id": "123456",
            "outcome": "Yes",
            "limit_price": 0.82,
            "reason": "count 3 >= ziel 3, ask 0.82 <= 0.9",
        },
        "result": {
            "market_id": "111",
            "action": "YES",
            "token_id": "123456",
            "limit_price": 0.82,
            "size_usd": 12.3,
            "size_shares": 15.0,
            "status": "dry_run_fill",
            "detail": "DRY_RUN",
        },
        "book_snapshot": {
            "asks": [{"price": "0.84", "size": "5"}, {"price": "0.82", "size": "15"}],
            "bids": [{"price": "0.78", "size": "9"}, {"price": "0.80", "size": "20"}],
            "timestamp": "1720300000",
            "min_order_size": 5,
            "neg_risk": False,
        },
    }
    (live / "decisions_log.jsonl").write_text(
        json.dumps(record) + "\n", encoding="utf-8"
    )
    events = [
        {"wall_ts_utc": "t1", "art": "chunk", "index": 1, "staende": {"tariff": 2}},
        {"wall_ts_utc": "t2", "art": "fertig", "endstaende": {"tariff": 3, "ai": 7}, "ausgegeben_usd": 12.3},
    ]
    (live / "bot_events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
    )
    return live


def test_pipeline_forward_whitelist_only(tmp_path: Path) -> None:
    live = _write_live_fixture(tmp_path)
    payload = drr.build_pipeline_forward(
        live_dir=live, profil="allin_july3", now_utc="2026-07-07T00:00:00+00:00"
    )
    assert payload.kennzeichnung == "beobachtend/paper"
    assert payload.quelle_vorhanden is True
    assert len(payload.eintraege) == 1
    entry = payload.eintraege[0]
    assert entry.action == "YES"
    assert entry.reason.startswith("count 3")
    assert entry.limit_price == 0.82
    assert entry.size_usd == 12.3
    assert entry.best_ask == 0.82  # min ask
    assert entry.best_bid == 0.80  # max bid
    dumped = json.loads(payload.model_dump_json())
    text = json.dumps(dumped)
    for forbidden in ("size_shares", "token_id", "detail", "market_id", "pnl"):
        assert forbidden not in text
    assert payload.wortzaehler_endstaende == {"tariff": 3, "ai": 7}


def test_pipeline_forward_missing_source_is_fail_soft(tmp_path: Path) -> None:
    payload = drr.build_pipeline_forward(
        live_dir=tmp_path / "does_not_exist",
        profil="allin_july3",
        now_utc="2026-07-07T00:00:00+00:00",
    )
    assert payload.quelle_vorhanden is False
    assert payload.eintraege == []
    assert "nicht vorhanden" in payload.hinweis


# ---------------------------------------------------------------------------
# audit.json
# ---------------------------------------------------------------------------


def test_audit_only_hashes_and_counters() -> None:
    llm_sink = [
        {"role": "CaseNarrative", "prompt_hash": "h1", "ts_utc": "t", "backend": "mock", "output_hash": "o1"},
        {"role": "SkepticReviewer", "prompt_hash": "h2", "ts_utc": "t", "backend": "mock", "output_hash": "o2"},
    ]
    mcp_records = [
        {"tool": "get_anomaly_review_summary", "args": {"x": 1}, "row_count": 5, "ts_utc": "t"},
        {"tool": "get_anomaly_case", "args": {"case_id": "c"}, "row_count": 1, "ts_utc": "t"},
        {"tool": "get_anomaly_case", "args": {"case_id": "d"}, "row_count": 1, "ts_utc": "t"},
    ]
    payload = drr.build_audit(
        llm_sink=llm_sink,
        mcp_records=mcp_records,
        backend_name="mock",
        now_utc="2026-07-07T00:00:00+00:00",
    )
    assert payload.llm_calls == 2
    assert payload.prompt_hashes == ["h1", "h2"]
    assert payload.mcp_tool_calls == {
        "get_anomaly_review_summary": 1,
        "get_anomaly_case": 2,
    }
    assert payload.mcp_rows_returned_total == 7
    text = payload.model_dump_json()
    for forbidden in ("args", "model", "cost", "user_prompt", "response"):
        assert forbidden not in text


# ---------------------------------------------------------------------------
# Lauf-Integration (Schritte injiziert, keine echten Rechenlaeufe)
# ---------------------------------------------------------------------------


def _fake_build_review_queue(**kwargs):
    sink = kwargs.get("llm_audit_sink")
    if sink is not None:
        sink.append(
            {"role": "CaseNarrative", "prompt_hash": "h", "ts_utc": "t", "backend": "mock", "output_hash": "o"}
        )
    return _queue_result()


def test_run_daily_review_writes_all_six(tmp_path: Path, monkeypatch) -> None:
    publish = tmp_path / "publish"
    extra = tmp_path / "public_data"
    monkeypatch.setattr(drr, "MCP_AUDIT_PATH", tmp_path / "mcp_audit.jsonl")
    monkeypatch.setattr(drr, "QUEUE_CSV_PATH", tmp_path / "queue.csv")
    monkeypatch.setattr(drr, "MENTIONS_CSV_PATH", tmp_path / "mentions.csv")
    monkeypatch.setattr(drr, "MENTIONS_METADATA_PATH", tmp_path / "mm.json")
    monkeypatch.setattr(drr, "LIVE_BASE_DIR", tmp_path / "live")
    summary = tmp_path / "v2.csv"
    summary.write_text(
        "kategorie,tag_slug,n_maerkte,n_events,trefferquote_t1,brier_t1,n_t7,"
        "trefferquote_t7,brier_t7,median_volumen_usd,volumen_schwelle_usd,"
        "n_t1_aus_clob,n_ausgeschlossen_in_auswertung,n_alt,n_neu\n"
        "Politik,politics,10,5,0.9,0.05,8,0.8,0.1,50000,10000,3,1,7,3\n",
        encoding="utf-8",
    )
    examples = tmp_path / "ex.csv"
    examples.write_text(
        "kategorie,ereignis,markt_frage,t0_utc,minuten_bis_erste_reaktion,"
        "minuten_bis_konvergenz,praezisions_hinweis\n"
        "Sport,Spiel,Frage?,2026-06-01T00:00:00Z,2.0,210.0,Obergrenze enthaelt Spieldauer\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(drr, "SUMMARY_V2_PATH", summary)
    monkeypatch.setattr(drr, "LATENCY_EXAMPLES_PATH", examples)

    result = drr.run_daily_review(
        publish_dir=publish,
        extra_publish_dir=extra,
        refresh_fn=lambda: "ok (test)",
        snapshots_fn=lambda: {"category_efficiency_snapshot": "ok"},
        build_review_queue_fn=_fake_build_review_queue,
    )

    for name in drr.PUBLISH_FILES:
        assert (publish / name).exists(), name
        assert (extra / name).exists(), name
    queue = json.loads((publish / "queue.json").read_text(encoding="utf-8"))
    assert queue["backend"] == "mock"
    assert queue["cards"][0]["empfehlung"] == "eskalation_mensch"
    meta = json.loads((publish / "meta.json").read_text(encoding="utf-8"))
    assert meta["disclaimer"]["keine_finanzberatung"]
    assert meta["schritte"]["monitor_refresh"] == "ok (test)"
    audit = json.loads((publish / "audit.json").read_text(encoding="utf-8"))
    assert audit["llm_calls"] == 1


def test_run_daily_review_gate_blocks_everything(tmp_path: Path, monkeypatch) -> None:
    publish = tmp_path / "publish"
    monkeypatch.setattr(drr, "MCP_AUDIT_PATH", tmp_path / "mcp_audit.jsonl")
    monkeypatch.setattr(drr, "QUEUE_CSV_PATH", tmp_path / "queue.csv")
    monkeypatch.setattr(drr, "MENTIONS_CSV_PATH", tmp_path / "mentions.csv")
    monkeypatch.setattr(drr, "MENTIONS_METADATA_PATH", tmp_path / "mm.json")
    monkeypatch.setattr(drr, "LIVE_BASE_DIR", tmp_path / "live")
    for name, content in (("v2.csv", "kategorie,tag_slug,n_maerkte,n_events,trefferquote_t1,brier_t1,n_t7,trefferquote_t7,brier_t7,median_volumen_usd,volumen_schwelle_usd,n_t1_aus_clob,n_ausgeschlossen_in_auswertung,n_alt,n_neu\n"), ("ex.csv", "kategorie,ereignis,markt_frage,t0_utc,minuten_bis_erste_reaktion,minuten_bis_konvergenz,praezisions_hinweis\n")):
        (tmp_path / name).write_text(content, encoding="utf-8")
    monkeypatch.setattr(drr, "SUMMARY_V2_PATH", tmp_path / "v2.csv")
    monkeypatch.setattr(drr, "LATENCY_EXAMPLES_PATH", tmp_path / "ex.csv")

    def poisoned_queue(**kwargs):
        return _queue_result(narrative="Wallet 0x" + "a" * 40 + " hat gekauft")

    with pytest.raises(drr.RedactionGateError):
        drr.run_daily_review(
            publish_dir=publish,
            refresh_fn=lambda: "ok (test)",
            snapshots_fn=lambda: {},
            build_review_queue_fn=poisoned_queue,
        )
    assert not publish.exists()


def test_mentions_cache_complete(tmp_path: Path) -> None:
    seed = tmp_path / "seed.csv"
    cache = tmp_path / "cache"
    cache.mkdir()
    seed.write_text(
        "event,drop_ts_utc,condition_id,clob_token_id,korrekt_aufgeloestes_outcome,ausschluss\n"
        "a,2026-01-01T00:00:00Z,0x" + "b" * 64 + ",1,YES,\n"
        "b,2026-01-01T00:00:00Z,0x" + "c" * 64 + ",2,NO,zuordnungsambiguitaet\n",
        encoding="utf-8",
    )
    assert drr.mentions_cache_complete(seed, cache) is False
    (cache / "prices_a.json").write_text("{}", encoding="utf-8")
    # Zeile b ist ausgeschlossen -> Cache dafuer nicht noetig
    assert drr.mentions_cache_complete(seed, cache) is True
