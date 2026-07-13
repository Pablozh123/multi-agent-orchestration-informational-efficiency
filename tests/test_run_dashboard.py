"""Tests fuer die Live-Run-Nachauswertung (runs.json)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from operations.pipeline.run_dashboard import (
    RUNS_FILE,
    RedactionGateError,
    build_run,
    build_runs_payload,
    discover_runs,
    klassifiziere_grund,
    parse_events,
    publish_runs,
    _sweep_clips,
)


def _decision(
    *,
    ts: str = "2026-07-03T23:22:37Z",
    market_id: str = "111",
    action: str = "YES",
    reason: str = "count 2 >= ziel 1, ask 0.85 <= 0.9",
    limit_price: float | None = 0.85,
    status: str = "live_fill",
    size_usd: float = 5.97,
    size_shares: float = 7.02,
    detail: str = "",
) -> dict:
    return {
        "wall_ts_utc": ts,
        "decision": {
            "market_id": market_id,
            "action": action,
            "reason": reason,
            "limit_price": limit_price,
        },
        "result": {
            "market_id": market_id,
            "action": action,
            "limit_price": limit_price,
            "size_usd": size_usd,
            "size_shares": size_shares,
            "status": status,
            "detail": detail,
        },
        "book_snapshot": {"asks": [], "bids": []},
    }


EVENTS = [
    {"wall_ts_utc": "2026-07-03T10:09:15Z", "art": "start", "modus": "LIVE",
     "aktive_maerkte": 20},
    {"wall_ts_utc": "2026-07-03T23:21:22Z", "art": "drop_erkannt",
     "quelle": "libsyn_rss", "titel": "Testepisode",
     "pubdate_utc": "2026-07-03T22:12:00Z"},
    {"wall_ts_utc": "2026-07-03T23:22:44Z", "art": "fertig",
     "ausgegeben_usd": 5.97},
]

SNAPSHOT = {
    "event_id": "652614",
    "slug": "test-event-slug",
    "markets": [
        {"id": "111", "question": 'Will "Tourism" be said?'},
        {"id": "222", "question": 'Will "Model" be said?'},
        {"id": "333", "question": 'Will "IPO" be said?'},
    ],
}

RESOLUTIONS = {
    "profil": "testrun",
    "event_slug": "test-event-slug",
    "maerkte": {
        "111": {"frage": 'Will "Tourism" be said?', "closed": True,
                "outcome_yes": True, "aktueller_yes_preis": None},
        "333": {"frage": 'Will "IPO" be said?', "closed": False,
                "outcome_yes": None, "aktueller_yes_preis": 0.67},
    },
}


def _run(decisions: list[dict]):
    return build_run(
        profil="testrun",
        events=EVENTS,
        decisions=decisions,
        snapshot=SNAPSHOT,
        resolutions=RESOLUTIONS,
    )


class TestBausteine:
    def test_parse_events_liest_drop_und_fertig(self):
        info = parse_events(EVENTS)
        assert info["modus"] == "LIVE"
        assert info["n_maerkte"] == 20
        assert info["drop_quelle"] == "libsyn_rss"
        assert info["pubdate_utc"] == "2026-07-03T22:12:00Z"
        assert info["drop_erkannt_utc"] == "2026-07-03T23:21:22Z"

    def test_parse_events_erster_drop_gewinnt_bei_restart(self):
        events = EVENTS + [{
            "wall_ts_utc": "2026-07-03T23:59:00Z", "art": "drop_erkannt",
            "quelle": "youtube", "titel": "Restart-Duplikat",
            "pubdate_utc": "2026-07-03T22:12:00Z",
        }]
        info = parse_events(events)
        assert info["drop_erkannt_utc"] == "2026-07-03T23:21:22Z"
        assert info["drop_quelle"] == "libsyn_rss"
        assert info["episode_titel"] == "Testepisode"

    def test_parse_events_decodiert_html_entities_im_titel(self):
        events = [{"art": "drop_erkannt", "quelle": "youtube",
                   "titel": "Cerebras &amp; Black Forest Labs",
                   "pubdate_utc": None, "wall_ts_utc": None}]
        assert parse_events(events)["episode_titel"] == (
            "Cerebras & Black Forest Labs"
        )

    def test_sweep_clips(self):
        assert _sweep_clips("Sweep: 5 Clips, ['0xabc:23.8@<= 0.9']") == 5
        assert _sweep_clips("einzelner Fill") == 1
        assert _sweep_clips("") == 1

    def test_klassifiziere_grund(self):
        assert klassifiziere_grund("yes_ask 0.98 > 0.85") == "bereits_eingepreist"
        assert klassifiziere_grund("no_ask 0.99 > 0.9") == "bereits_eingepreist"
        assert klassifiziere_grund("kein_yes_ask") == "kein_angebot"
        assert klassifiziere_grund("endstand 5 ueber Grenze") == "regel_nicht_erfuellt"


class TestBuildRun:
    def test_gewonnene_wette_pnl_und_roi(self):
        run = _run([_decision()])
        assert run.einsatz_usd == 5.97
        [wette] = run.wetten
        assert wette.frage == 'Will "Tourism" be said?'
        assert wette.aufgeloest and wette.gewonnen
        assert wette.payout_usd == 7.02
        assert wette.pnl_usd == 1.05
        assert wette.roi_pct == pytest.approx(17.6, abs=0.1)
        assert run.realisierter_pnl_usd == 1.05

    def test_offene_wette_ohne_pnl_mit_aktuellem_preis(self):
        run = _run([
            _decision(market_id="333", limit_price=0.63, size_usd=102.39,
                      size_shares=113.76,
                      detail="Sweep: 5 Clips, ['0xabc:23.8@<= 0.9']")
        ])
        [wette] = run.wetten
        assert not wette.aufgeloest
        assert wette.gewonnen is None and wette.pnl_usd is None
        assert wette.aktueller_yes_preis == 0.67
        assert wette.sweep_clips == 5
        assert wette.avg_fill_preis == pytest.approx(0.9001, abs=0.001)
        assert run.realisierter_pnl_usd is None

    def test_verlorene_wette(self):
        resolutions = {"maerkte": {"111": {"frage": "f", "closed": True,
                                           "outcome_yes": False,
                                           "aktueller_yes_preis": None}}}
        run = build_run(profil="t", events=EVENTS, decisions=[_decision()],
                        snapshot=SNAPSHOT, resolutions=resolutions)
        [wette] = run.wetten
        assert wette.gewonnen is False
        assert wette.payout_usd == 0.0
        assert wette.pnl_usd == -5.97

    def test_no_seite_gewinnt_wenn_outcome_no(self):
        resolutions = {"maerkte": {"111": {"frage": "f", "closed": True,
                                           "outcome_yes": False,
                                           "aktueller_yes_preis": None}}}
        run = build_run(
            profil="t", events=EVENTS,
            decisions=[_decision(action="NO", limit_price=0.3,
                                 size_usd=3.0, size_shares=10.0)],
            snapshot=SNAPSHOT, resolutions=resolutions,
        )
        [wette] = run.wetten
        assert wette.seite == "NO" and wette.gewonnen is True
        assert wette.payout_usd == 10.0

    def test_latenzen_aus_zeitstempeln(self):
        run = _run([_decision()])
        assert run.erkennungslatenz_s == pytest.approx(4162.0)
        assert run.erste_entscheidung_s == pytest.approx(75.0)
        assert run.erster_fill_s == pytest.approx(75.0)

    def test_skipped_budget_wird_verpasste_chance(self):
        run = _run([
            _decision(market_id="222", status="skipped_budget",
                      reason="count 3 >= ziel 1, ask 0.83 <= 0.9",
                      limit_price=0.83, size_usd=0.0, size_shares=0.0),
        ])
        assert not run.wetten
        [chance] = run.verpasste_chancen
        assert chance.frage == 'Will "Model" be said?'
        assert chance.limit_preis == 0.83
        assert chance.grund == "budget_exhausted"

    def test_eingepreist_zaehlt_nur_ask_grenzen(self):
        run = _run([
            _decision(market_id="222", status="no_action", action="NONE",
                      reason="yes_ask 0.98 > 0.85", limit_price=None,
                      size_usd=0.0, size_shares=0.0),
            _decision(market_id="222", status="no_action", action="NONE",
                      reason="endstand 5 > grenze 0.7", limit_price=None,
                      size_usd=0.0, size_shares=0.0),
        ])
        assert run.eingepreist == 1
        assert run.zaehler == {"no_action": 2}


class TestPayloadUndPublish:
    def _payload(self, tmp_path: Path):
        live = tmp_path / "live" / "testrun"
        live.mkdir(parents=True)
        (live / "decisions_log.jsonl").write_text(
            json.dumps(_decision()) + "\n", encoding="utf-8"
        )
        (live / "bot_events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in EVENTS) + "\n", encoding="utf-8"
        )
        (live / "gamma_event_snapshot.json").write_text(
            json.dumps(SNAPSHOT), encoding="utf-8"
        )
        resolutions_dir = tmp_path / "res"
        resolutions_dir.mkdir()
        (resolutions_dir / "resolutions_testrun.json").write_text(
            json.dumps(RESOLUTIONS), encoding="utf-8"
        )
        return build_runs_payload(
            live_root=tmp_path / "live",
            resolutions_dir=resolutions_dir,
            now_utc="2026-07-10T12:00:00+00:00",
        )

    def test_discover_runs_braucht_decisions_log(self, tmp_path: Path):
        (tmp_path / "leer").mkdir()
        voll = tmp_path / "voll"
        voll.mkdir()
        (voll / "decisions_log.jsonl").write_text("", encoding="utf-8")
        assert [p.name for p in discover_runs(tmp_path)] == ["voll"]
        assert discover_runs(tmp_path / "fehlt") == []

    def test_payload_aggregat(self, tmp_path: Path):
        payload = self._payload(tmp_path)
        assert payload.aggregat.n_runs == 1
        assert payload.aggregat.n_wetten == 1
        assert payload.aggregat.gewonnen == 1
        assert payload.aggregat.realisierter_pnl_usd == 1.05
        assert payload.aggregat.roi_realisiert_pct == pytest.approx(17.6, abs=0.1)
        assert payload.aggregat.offener_einsatz_usd == 0.0
        assert payload.kennzeichnung == "live/descriptive"

    def test_publish_schreibt_beide_ordner(self, tmp_path: Path):
        payload = self._payload(tmp_path)
        primary = tmp_path / "publish"
        extra = tmp_path / "website"
        written = publish_runs(payload, publish_dir=primary,
                               extra_publish_dir=extra)
        assert [p.name for p in written] == [RUNS_FILE, RUNS_FILE]
        data = json.loads((primary / RUNS_FILE).read_text(encoding="utf-8"))
        assert set(data) == {"hinweis", "stand_utc", "kennzeichnung",
                             "aggregat", "runs"}
        assert data == json.loads((extra / RUNS_FILE).read_text(encoding="utf-8"))

    def test_gate_blockt_wallet_adresse(self, tmp_path: Path):
        payload = self._payload(tmp_path)
        payload.runs[0].episode_titel = (
            "0x204f72f35326db932158cba6adff0b9a1da95e14"
        )
        with pytest.raises(RedactionGateError):
            publish_runs(payload, publish_dir=tmp_path / "p")


class TestRace:
    TAPE = {
        "maerkte": {
            "111": [
                {"ts_utc": "2026-07-03T23:20:00Z", "side": "BUY",
                 "outcome": "Yes", "preis": 0.4, "size": 100.0,
                 "eigen": False},  # vor dem Drop -- zaehlt nicht
                {"ts_utc": "2026-07-03T23:21:40Z", "side": "BUY",
                 "outcome": "Yes", "preis": 0.5, "size": 10.0,
                 "eigen": False},
                {"ts_utc": "2026-07-03T23:22:00Z", "side": "BUY",
                 "outcome": "Yes", "preis": 0.6, "size": 5.0,
                 "eigen": False},
                {"ts_utc": "2026-07-03T23:22:36Z", "side": "BUY",
                 "outcome": "Yes", "preis": 0.85, "size": 7.0,
                 "eigen": True},  # eigener Clip -- nie fremd
                {"ts_utc": "2026-07-03T23:24:37Z", "side": "BUY",
                 "outcome": "Yes", "preis": 0.9, "size": 3.0,
                 "eigen": False},
            ],
            "333": [
                {"ts_utc": "2026-07-03T23:26:37Z", "side": "BUY",
                 "outcome": "Yes", "preis": 0.7, "size": 2.0,
                 "eigen": False},
            ],
        }
    }

    def _run_mit_tape(self, decisions: list[dict]):
        return build_run(
            profil="testrun",
            events=EVENTS,
            decisions=decisions,
            snapshot=SNAPSHOT,
            resolutions=RESOLUTIONS,
            tape=self.TAPE,
        )

    def test_race_zaehlt_fremde_vor_uns_und_verfolger(self):
        run = self._run_mit_tape([_decision()])
        wette = run.wetten[0]
        assert wette.fremde_davor == 2
        assert wette.tape_rang == 3
        assert wette.fremdvolumen_davor_usd == pytest.approx(8.0)
        assert wette.verfolger_s == pytest.approx(120.0)

    def test_race_first_ohne_fremde_davor(self):
        run = self._run_mit_tape(
            [_decision(market_id="333", ts="2026-07-03T23:22:37Z")]
        )
        wette = run.wetten[0]
        assert wette.tape_rang == 1
        assert wette.fremde_davor == 0
        assert wette.verfolger_s == pytest.approx(240.0)

    def test_race_ohne_tape_bleibt_none(self):
        run = _run([_decision()])
        wette = run.wetten[0]
        assert wette.tape_rang is None
        assert wette.verfolger_s is None
        assert run.race is None

    def test_race_info_aggregiert_first_und_median(self):
        run = self._run_mit_tape(
            [
                _decision(),
                _decision(market_id="333", ts="2026-07-03T23:22:37Z"),
            ]
        )
        assert run.race is not None
        assert run.race.wetten_mit_tape == 2
        assert run.race.first_on == 1
        assert run.race.fremde_trades_vor_uns == 2
        assert run.race.median_verfolger_s == pytest.approx(180.0)
