"""Tests fuer die Live-Run-Nachauswertung (runs.json)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from operations.pipeline.run_dashboard import (
    RUNS_FILE,
    RedactionGateError,
    build_aggregat,
    build_pilot_payload,
    build_postmortems_payload,
    build_run,
    build_runs_payload,
    discover_runs,
    klassifiziere_grund,
    parse_events,
    publish_payloads,
    publish_runs,
    _deckel_aus_reason,
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
    asks: list | None = None,
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
        "book_snapshot": {"asks": asks or [], "bids": []},
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


class TestTimingAnalytik:
    # Drop = 2026-07-03T23:21:22Z, Fill (default _decision) = 23:22:37Z (+75s).
    # Kurven/Counterfactual kommen aus dem TAPE (der Bot pausiert sein
    # Orderbuch-Log in der heissen Phase) -- No-Trades werden via 1-preis
    # auf die Wett-Seite normalisiert.
    TAPE_TIMING = {
        "maerkte": {
            "111": [
                {"ts_utc": "2026-07-03T23:20:00Z", "side": "BUY", "outcome": "Yes",
                 "preis": 0.40, "size": 5.0, "eigen": False},  # vor Drop
                {"ts_utc": "2026-07-03T23:21:30Z", "side": "BUY", "outcome": "Yes",
                 "preis": 0.62, "size": 5.0, "eigen": False},
                {"ts_utc": "2026-07-03T23:22:30Z", "side": "BUY", "outcome": "No",
                 "preis": 0.15, "size": 5.0, "eigen": False},  # Bid-Seite: fliegt raus
                {"ts_utc": "2026-07-03T23:22:37Z", "side": "BUY", "outcome": "Yes",
                 "preis": 0.85, "size": 7.0, "eigen": True},   # eigener Clip: raus
                {"ts_utc": "2026-07-03T23:22:50Z", "side": "SELL", "outcome": "Yes",
                 "preis": 0.80, "size": 4.0, "eigen": False},  # SELL: raus
                {"ts_utc": "2026-07-03T23:23:00Z", "side": "BUY", "outcome": "Yes",
                 "preis": 0.88, "size": 3.0, "eigen": False},
                {"ts_utc": "2026-07-03T23:24:00Z", "side": "BUY", "outcome": "Yes",
                 "preis": 0.93, "size": 3.0, "eigen": False},
                {"ts_utc": "2026-07-03T23:40:00Z", "side": "BUY", "outcome": "Yes",
                 "preis": 0.97, "size": 2.0, "eigen": False},
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
            tape=self.TAPE_TIMING,
        )

    def test_counterfactual_preise_nach_fill(self):
        run = self._run_mit_tape([_decision()])
        preise = run.wetten[0].preis_nach_fill
        # Fill 23:22:37 -> letzter FREMDER Yes-BUY davor = 0.62 (eigener
        # Clip, No-Trade und SELL zaehlen nicht); +30s -> 0.88;
        # +120s -> 0.93; +900s (23:37:37) -> immer noch 0.93
        assert preise["0"] == pytest.approx(0.62)
        assert preise["30"] == pytest.approx(0.88)
        assert preise["120"] == pytest.approx(0.93)
        assert preise["900"] == pytest.approx(0.93)

    def test_repricing_kurve_mit_priced_schwelle(self):
        run = self._run_mit_tape([_decision()])
        assert len(run.repricing) == 1
        kurve = run.repricing[0]
        # erster Trade-Preis > 0.90 bei 23:24:00 = 158 s nach Drop
        assert kurve.time_to_priced_s == pytest.approx(158.0)
        assert kurve.fill_nach_s == pytest.approx(75.0)
        assert kurve.seite == "YES"
        sekunden = [p[0] for p in kurve.punkte]
        assert sekunden == sorted(sekunden)
        assert min(sekunden) >= 0.0
        # nur fremde Yes-BUYs im Fenster: 0.62 / 0.88 / 0.93 / 0.97
        assert [p[1] for p in kurve.punkte] == [0.62, 0.88, 0.93, 0.97]

    def test_ohne_tape_bleibt_leer(self):
        run = _run([_decision()])
        assert run.wetten[0].preis_nach_fill == {}
        assert run.repricing == []

    def test_verpasste_chance_wird_bepreist(self):
        # market 111 ist closed mit outcome YES -> YES-Skip haette gewonnen
        run = _run([
            _decision(status="skipped_budget"),
            _decision(market_id="333", status="skipped_budget", action="NO"),
        ])
        assert run.verpasste_chancen[0].waere_gewonnen is True
        # market 333 ist offen -> keine Bewertung
        assert run.verpasste_chancen[1].waere_gewonnen is None


class TestKapazitaet:
    def test_deckel_aus_reason(self):
        assert _deckel_aus_reason("count 2 >= ziel 1, ask 0.85 <= 0.9") == 0.9
        assert _deckel_aus_reason("endstand 0 <= grenze 0.7, ask 0.5 <= 0.94") == 0.94
        assert _deckel_aus_reason("kein_yes_ask") is None

    def test_tiefe_und_run_kapazitaet_aus_snapshot(self):
        # Tiefe bis Deckel 0.9: 0.85*10 + 0.88*20 = 26.1 (0.95-Level nicht)
        asks = [
            {"price": "0.85", "size": "10"},
            {"price": "0.88", "size": "20"},
            {"price": "0.95", "size": "100"},
        ]
        run = _run([_decision(size_usd=13.05, asks=asks)])
        wette = run.wetten[0]
        assert wette.tiefe_usd_bis_deckel == pytest.approx(26.1)
        assert run.sichtbare_tiefe_usd == pytest.approx(26.1)
        assert run.einsatz_zu_sichtbarer_tiefe_pct == pytest.approx(50.0)

    def test_ohne_snapshot_bleibt_kapazitaet_none(self):
        run = _run([_decision()])
        assert run.wetten[0].tiefe_usd_bis_deckel is None
        assert run.sichtbare_tiefe_usd is None
        assert run.einsatz_zu_sichtbarer_tiefe_pct is None

    def test_aggregat_summiert_kapazitaet(self):
        asks = [{"price": "0.80", "size": "50"}]  # Tiefe 40.0
        run = _run([_decision(size_usd=10.0, asks=asks)])
        aggregat = build_aggregat([run, run])
        assert aggregat.sichtbare_tiefe_usd == pytest.approx(80.0)
        assert aggregat.einsatz_zu_sichtbarer_tiefe_pct == pytest.approx(25.0)


class TestPostmortemsUndPilot:
    def test_kuratierte_postmortems_quelle_validiert(self):
        payload = build_postmortems_payload(now_utc="2026-07-18T12:00:00+00:00")
        assert payload is not None
        assert payload.kennzeichnung == "curated/postmortem"
        assert len(payload.eintraege) >= 6
        achsen = {e.achse for e in payload.eintraege}
        assert "Risk discipline" in achsen
        # Jeder Eintrag traegt Fix und Referenz (Ehrlichkeits-Format).
        assert all(e.fix and e.referenz for e in payload.eintraege)

    def test_postmortems_none_ohne_quelldatei(self, tmp_path):
        assert build_postmortems_payload(quelle=tmp_path / "fehlt.json") is None

    def test_pilot_payload_aus_artefakten(self, tmp_path):
        (tmp_path / "watcher_metadata.json").write_text(
            json.dumps({
                "lauf_ts_utc": "2026-07-18T10:19:52Z",
                "parameter": {"arm2_min_preis": 0.9},
                "statistik": {"maerkte": 1715, "gekappt": 0},
            }),
            encoding="utf-8",
        )
        (tmp_path / "signals.csv").write_text(
            "ts_utc,arm,market_id,frage,seite,token_id,signal_preis,"
            "buchtiefe_usd,restlaufzeit_tage,end_date,regel,ausloesewert,"
            "status,hinweis\n"
            "2026-07-16T17:58:48Z,arm2,1,Frage A?,Yes,tok,0.957,305636.38,"
            "12.25,2026-07-29T00:00:00Z,r,a,signal,\n"
            "2026-07-18T10:19:52Z,arm2,2,Frage B?,No,tok,0.93,9999.28,8.11,"
            "2026-07-26T00:00:00Z,r,a,signal,\n"
            "2026-07-16T17:55:54Z,arm1,3,Frage C?,No,tok,0.504,117292.5,"
            "14.75,2026-07-31T12:00:00Z,r,a,kandidat_referenz_pruefen,\n",
            encoding="utf-8",
        )
        (tmp_path / "trades.csv").write_text(
            "zeitstempel_utc,markt,arm\n", encoding="utf-8"
        )
        payload = build_pilot_payload(
            pilot_dir=tmp_path, now_utc="2026-07-18T12:00:00+00:00"
        )
        assert payload is not None
        assert payload.protokoll.budget_usdc == 100.0
        assert payload.signal_zaehler == {
            "arm2:signal": 2, "arm1:kandidat_referenz_pruefen": 1,
        }
        # Neueste zuerst
        assert payload.signale_neueste[0].ts_utc == "2026-07-18T10:19:52Z"
        assert payload.trades == []

    def test_pilot_none_ohne_artefakte(self, tmp_path):
        assert build_pilot_payload(pilot_dir=tmp_path) is None

    def test_publish_payloads_schreibt_und_gated(self, tmp_path):
        ziele = publish_payloads(
            {"postmortems.json": "{\"ok\": true}"},
            publish_dir=tmp_path / "a",
            extra_publish_dir=tmp_path / "b",
        )
        assert len(ziele) == 2
        assert all(p.exists() for p in ziele)
        with pytest.raises(RedactionGateError):
            publish_payloads(
                {"x.json": '{"wallet": "0x' + "a" * 40 + '"}'},
                publish_dir=tmp_path / "c",
            )


class TestWalletAbgleich:
    def test_overlay_wird_gemerged(self, tmp_path, monkeypatch):
        import operations.pipeline.run_dashboard as rd

        run_dir = tmp_path / "live" / "testrun"
        run_dir.mkdir(parents=True)
        (run_dir / "decisions_log.jsonl").write_text(
            json.dumps(_decision()) + "\n", encoding="utf-8"
        )
        (run_dir / "bot_events.jsonl").write_text(
            "\n".join(json.dumps(e) for e in EVENTS), encoding="utf-8"
        )
        (run_dir / "gamma_event_snapshot.json").write_text(
            json.dumps(SNAPSHOT), encoding="utf-8"
        )
        overlay = tmp_path / "abgleich.json"
        overlay.write_text(json.dumps({
            "stand": "2026-07-18",
            "gesamt_netto_usd": 175.09,
            "events": {"testrun": {"netto_usd": 119.84,
                                   "kaeufe_usd": 288.09,
                                   "verkaeufe_usd": 0.0,
                                   "einloesungen_usd": 407.93}},
        }), encoding="utf-8")
        monkeypatch.setattr(rd, "WALLET_ABGLEICH_QUELLE", overlay)
        payload = rd.build_runs_payload(
            live_root=tmp_path / "live",
            resolutions_dir=tmp_path / "nores",
        )
        assert payload.runs[0].wallet_netto_usd == 119.84
        assert payload.runs[0].wallet_kaeufe_usd == 288.09
        assert payload.runs[0].wallet_einloesungen_usd == 407.93
        assert payload.aggregat.wallet_netto_usd == 175.09
        assert payload.aggregat.wallet_kaeufe_usd == 288.09
        assert payload.aggregat.wallet_abgleich_stand == "2026-07-18"

    def test_ohne_overlay_bleibt_none(self, tmp_path, monkeypatch):
        import operations.pipeline.run_dashboard as rd

        monkeypatch.setattr(
            rd, "WALLET_ABGLEICH_QUELLE", tmp_path / "fehlt.json"
        )
        run_dir = tmp_path / "live" / "t"
        run_dir.mkdir(parents=True)
        (run_dir / "decisions_log.jsonl").write_text(
            json.dumps(_decision()) + "\n", encoding="utf-8"
        )
        payload = rd.build_runs_payload(
            live_root=tmp_path / "live",
            resolutions_dir=tmp_path / "nores",
        )
        assert payload.runs[0].wallet_netto_usd is None
        assert payload.aggregat.wallet_netto_usd is None

    def test_kuratierte_quelldatei_konsistent(self):
        from operations.pipeline.run_dashboard import lade_wallet_abgleich

        abgleich = lade_wallet_abgleich()
        assert abgleich is not None
        events = abgleich["events"]
        summe = round(sum(e["netto_usd"] for e in events.values()), 2)
        assert summe == abgleich["gesamt_netto_usd"] == 175.09
        # Jedes Event: netto == einloesungen + verkaeufe - kaeufe
        for name, e in events.items():
            erwartet = round(
                e["einloesungen_usd"] + e["verkaeufe_usd"] - e["kaeufe_usd"], 2
            )
            assert e["netto_usd"] == erwartet, name
