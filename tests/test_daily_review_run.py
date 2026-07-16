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
        "narrative": "Deterministic summary text.",
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


def test_gate_blocks_json_form_key_pairs() -> None:
    # JSON-serialisierte Key/Value-Paare ("api_key": "...") muessen anschlagen.
    for text in (
        '{"api_key": "abcdefabcdefabcdef"}',
        json.dumps({"nested": {"private_key": "abcdefabcdefabcdef12"}}),
    ):
        with pytest.raises(drr.RedactionGateError):
            drr.run_redaction_gate({"audit.json": text})


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
        "ranked_cases": [
            _queue_result()["ranked_cases"][0],
            {**_queue_result()["ranked_cases"][0], "case_id": "b", "priority": "low", "recommendation": "watch", "confidence_adjustment": None},
            {**_queue_result()["ranked_cases"][0], "case_id": "a", "priority": "medium", "recommendation": "check_source"},
        ],
    }
    payload = drr.build_queue_payload(
        result,
        queue_csv_rows=[{"case_id": "monitor_candidate_x", "timestamp_utc": "2026-07-01T00:00:00Z"}],
        now_utc="2026-07-08T00:00:00+00:00",
        backend_name="mock",
    )
    assert [f.score_band for f in payload.faelle] == ["high", "medium", "low"]
    assert [f.empfehlung for f in payload.faelle] == ["escalate_human", "check_source", "watch"]
    assert payload.faelle[0].zeitfenster == "2026-07-01T00:00:00Z"
    assert payload.faelle[0].skeptic_abschlag == -0.1
    assert payload.stand_utc == "2026-07-08T00:00:00+00:00"
    assert "mock" in payload.hinweis
    dumped = json.loads(payload.model_dump_json())
    assert set(dumped.keys()) == {"hinweis", "stand_utc", "faelle"}
    assert set(dumped["faelle"][0].keys()) == {
        "id", "markt_slug", "zeitfenster", "score_band", "empfehlung",
        "empfehlung_grund", "begruendung", "skeptic_begruendung",
        "skeptic_abschlag", "signale", "ts",
    }
    assert "Band high" in dumped["faelle"][0]["empfehlung_grund"]


def test_queue_payload_rejects_non_whitelist_recommendation() -> None:
    with pytest.raises(ValueError):
        drr.build_queue_payload(
            _queue_result(recommendation="buy_now"),
            queue_csv_rows=[],
            now_utc="2026-07-08T00:00:00+00:00",
            backend_name="mock",
        )


def test_queue_payload_rejects_bad_band_fail_closed() -> None:
    with pytest.raises(ValidationError):
        drr.build_queue_payload(
            _queue_result(priority="urgent"),
            queue_csv_rows=[],
            now_utc="2026-07-08T00:00:00+00:00",
            backend_name="mock",
        )


def test_queue_payload_rejects_positive_abschlag() -> None:
    # Prioritaet ist nur senkbar: positiver "Abschlag" verletzt das Schema.
    with pytest.raises(ValidationError):
        drr.build_queue_payload(
            _queue_result(confidence_adjustment=0.2),
            queue_csv_rows=[],
            now_utc="2026-07-08T00:00:00+00:00",
            backend_name="mock",
        )


_QUEUE_CSV_ROW = {
    "case_id": "monitor_candidate_x",
    "timestamp_utc": "2026-05-23T19:25:00Z",
    "question": "Will X happen?",
    "trigger_family": "active_wallet_activity,concentration",
    "priority_basis": "source_priority=high; max_severity=high; max_percentile_rank=1.000; family_count=3",
    "wallet_flow_context": "total_observed_amount_usd=64.2802; active_wallets=1.0000; trade_count=1.0000; materiality=below_one_percent_of_reference",
    "concentration_context": "concentration_context=present; triggered_patterns=large_trade_flow,market_concentration",
    "event_context_status": "nearest_event_only",
    "reference_overlap_status": "reference_hit",
    "human_review_status": "source_check_pending",
    "missing_evidence": "manual review; news check",
}


def test_case_reasoning_from_signal_fields() -> None:
    text = drr.case_reasoning(_QUEUE_CSV_ROW)
    assert "Will X happen?" in text
    assert "active wallet activity, concentration" in text
    assert "severity high" in text and "100th percentile" in text
    assert "$64" in text and "1 wallet(s)" in text
    assert "materiality below 1%" in text
    assert "large trade flow" in text
    assert "no confirmed link" in text
    assert "Reference pattern: hit" in text
    assert "source check pending" in text
    assert "2 verification steps open" in text
    assert "not a finding" in text


def test_queue_signale_chips() -> None:
    chips = drr.queue_signale(_QUEUE_CSV_ROW)
    assert chips["severity"] == "high"
    assert chips["percentile"] == "100th"
    assert chips["concentration"] == "present"
    assert chips["reference"] == "hit"
    assert chips["flow"].startswith("$64")


def test_queue_payload_uses_case_reasoning_when_row_present() -> None:
    payload = drr.build_queue_payload(
        _queue_result(),
        queue_csv_rows=[_QUEUE_CSV_ROW],
        now_utc="2026-07-10T00:00:00+00:00",
        backend_name="mock",
    )
    fall = payload.faelle[0]
    assert "severity high" in fall.begruendung  # deterministisch, nicht das Agenten-Template
    assert fall.skeptic_begruendung == "Benigne Erklaerung moeglich."
    assert fall.signale["reference"] == "hit"


def test_run_collector_status_in_meta(tmp_path, monkeypatch) -> None:
    _patch_paths(tmp_path, monkeypatch)
    result = drr.run_daily_review(
        publish_dir=tmp_path / "publish",
        collect=True,
        collect_fn=lambda: "ok (samples=2/2, alerts=5, baseline=ready)",
        refresh_fn=lambda: "ok (test)",
        snapshots_fn=lambda: {},
        build_review_queue_fn=_fake_build_review_queue,
    )
    assert result.schritte["collector"].startswith("ok (samples=2/2")
    import json as _json
    meta = _json.loads((tmp_path / "publish" / "meta.json").read_text(encoding="utf-8"))
    assert "collector" in meta["schritte"]


# ---------------------------------------------------------------------------
# kategorie_karte.json
# ---------------------------------------------------------------------------


def test_kategorie_karte_exact_fields() -> None:
    summary = [{
        "kategorie": "Politik", "tag_slug": "politics", "n_maerkte": "73",
        "n_events": "17", "trefferquote_t1": "0.9315", "brier_t1": "0.0361",
        "n_t7": "12", "trefferquote_t7": "0.4167", "brier_t7": "0.3521",
        "median_volumen_usd": "9883931.33", "volumen_schwelle_usd": "10000",
        "n_t1_aus_clob": "2", "n_ausgeschlossen_in_auswertung": "3",
        "n_alt": "13", "n_neu": "60",
    }]
    beispiele = [{
        "kategorie": "Sport", "ereignis": "Spiel", "markt_frage": "Frage?",
        "t0_utc": "2026-06-01T00:00:00Z", "minuten_bis_erste_reaktion": "2.0",
        "minuten_bis_konvergenz": "210.0", "praezisions_hinweis": "Obergrenze",
    }]
    payload = drr.build_kategorie_karte(
        summary_rows=summary, beispiel_rows=beispiele, now_utc="2026-07-08T00:00:00+00:00"
    )
    dumped = json.loads(payload.model_dump_json())
    assert set(dumped.keys()) == {"hinweis", "stand_utc", "kategorien", "beispiele"}
    assert set(dumped["kategorien"][0].keys()) == {
        "kategorie", "brier_t7", "trefferquote_t7", "brier_t1",
        "trefferquote_t1", "n_maerkte", "n_t7", "median_volumen_usd",
    }
    assert set(dumped["beispiele"][0].keys()) == {
        "kategorie", "ereignis", "markt_frage", "minuten_bis_konvergenz",
        "minuten_bis_erste_reaktion", "t0_utc", "praezisions_hinweis",
    }


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
            "korrekt_aufgeloestes_outcome": "YES",
            "status": "ok",
        },
        {
            "event": "fall_teilstatus",
            "drop_ts_utc": "2026-06-02T00:00:00Z",
            "minuten_bis_erste_reaktion": "3.0",
            "minuten_bis_konvergenz": "",
            "stunden_im_handelbaren_fenster": "",
            "endpreis": "",
            "korrekt_aufgeloestes_outcome": "NO",
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
            "korrekt_aufgeloestes_outcome": "NO",
            "status": "ausgeschlossen_zuordnungsambiguitaet",
        },
    ]
    payload = drr.build_mentions_latenz(
        mentions_rows=rows, now_utc="2026-07-08T00:00:00+00:00"
    )
    assert [f.event for f in payload.faelle] == ["fall_ok"]
    assert payload.faelle[0].korrekt_aufgeloestes_outcome == "YES"
    assert {a.event for a in payload.ausschluesse} == {
        "fall_teilstatus",
        "allin_next_episode",
    }
    dumped = json.loads(payload.model_dump_json())
    assert set(dumped["ausschluesse"][0].keys()) == {"event", "status"}
    assert set(dumped["faelle"][0].keys()) == {
        "event", "minuten_bis_erste_reaktion", "minuten_bis_konvergenz",
        "stunden_im_handelbaren_fenster", "korrekt_aufgeloestes_outcome", "status",
    }


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
        live_dir=live, profil="allin_july3", now_utc="2026-07-08T00:00:00+00:00"
    )
    assert payload.kennzeichnung == "observed/paper"
    assert len(payload.eintraege) == 1
    entry = payload.eintraege[0]
    assert entry.action == "YES"
    assert entry.reason.startswith("count 3")
    assert entry.limit_price == 0.82
    assert entry.size_usd == 12.3
    assert entry.bestes_angebot == 0.82  # min ask
    assert entry.bestes_gebot == 0.80  # max bid
    dumped = json.loads(payload.model_dump_json())
    assert set(dumped.keys()) == {
        "hinweis", "stand_utc", "kennzeichnung", "eintraege", "wortzaehler_endstaende",
    }
    assert set(dumped["eintraege"][0].keys()) == {
        "action", "reason", "limit_price", "bestes_angebot", "bestes_gebot", "size_usd",
    }
    text = json.dumps(dumped)
    for forbidden in ("size_shares", "token_id", "detail", "market_id", "pnl", "wall_ts"):
        assert forbidden not in text
    assert payload.wortzaehler_endstaende == {"tariff": 3, "ai": 7}


def test_pipeline_forward_missing_source_is_fail_soft(tmp_path: Path) -> None:
    payload = drr.build_pipeline_forward(
        live_dir=tmp_path / "does_not_exist",
        profil="allin_july3",
        now_utc="2026-07-08T00:00:00+00:00",
    )
    assert payload.eintraege == []
    assert "not present" in payload.hinweis


# ---------------------------------------------------------------------------
# audit.json / meta.json
# ---------------------------------------------------------------------------


def test_audit_counters_and_hashes_only() -> None:
    llm_sink = [
        {"role": "CaseNarrative", "prompt_hash": "h1", "ts_utc": "t", "backend": "mock", "output_hash": "o1"},
        {"role": "SkepticReviewer", "prompt_hash": "h2", "ts_utc": "t", "backend": "mock", "output_hash": "o2"},
        {"role": "CaseNarrative", "prompt_hash": "h3", "ts_utc": "t", "backend": "mock", "output_hash": "o3"},
    ]
    payload = drr.build_audit(llm_sink=llm_sink, now_utc="2026-07-08T00:00:00+00:00")
    assert payload.n_eintraege == 3
    assert payload.rollen_zaehler == {"CaseNarrative": 2, "SkepticReviewer": 1}
    assert payload.backend_zaehler == {"mock": 3}
    assert payload.prompt_hashes == ["h1", "h2", "h3"]
    text = payload.model_dump_json()
    for forbidden in ("model", "cost", "user_prompt", "response", "claude"):
        assert forbidden not in text
    dumped = json.loads(text)
    assert set(dumped.keys()) == {
        "hinweis", "stand_utc", "n_eintraege", "rollen_zaehler",
        "backend_zaehler", "prompt_hashes", "output_hashes",
    }


def test_meta_disclaimer_is_text_list() -> None:
    payload = drr.build_meta(
        now_utc="2026-07-08T00:00:00+00:00", backend_name="mock", schritte={"a": "ok"}
    )
    assert isinstance(payload.disclaimer, list)
    assert all(isinstance(t, str) for t in payload.disclaimer)
    assert payload.stand_utc == "2026-07-08T00:00:00+00:00"


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


def _patch_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(drr, "QUEUE_CSV_PATH", tmp_path / "queue.csv")
    monkeypatch.setattr(drr, "MENTIONS_CSV_PATH", tmp_path / "mentions.csv")
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


def test_run_daily_review_writes_all_six(tmp_path: Path, monkeypatch) -> None:
    publish = tmp_path / "publish"
    extra = tmp_path / "public_data"
    _patch_paths(tmp_path, monkeypatch)

    drr.run_daily_review(
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
    assert queue["faelle"][0]["empfehlung"] == "escalate_human"
    assert queue["stand_utc"]
    meta = json.loads((publish / "meta.json").read_text(encoding="utf-8"))
    assert isinstance(meta["disclaimer"], list) and meta["disclaimer"]
    assert meta["schritte"]["monitor_refresh"] == "ok (test)"
    audit = json.loads((publish / "audit.json").read_text(encoding="utf-8"))
    assert audit["n_eintraege"] == 1
    assert audit["rollen_zaehler"] == {"CaseNarrative": 1}
    for name in drr.PUBLISH_FILES:
        data = json.loads((publish / name).read_text(encoding="utf-8"))
        assert "hinweis" in data and "stand_utc" in data, name


def test_run_daily_review_gate_blocks_everything(tmp_path: Path, monkeypatch) -> None:
    publish = tmp_path / "publish"
    _patch_paths(tmp_path, monkeypatch)

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
