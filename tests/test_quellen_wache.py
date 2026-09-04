"""Tests fuer die Quellen-Wache: Normalisierung, Aenderungserkennung, Sperre, Markt-Hook, CLI."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from operations.pipeline import quellen_wache as qw

T0 = datetime(2026, 12, 4, 5, 0, tzinfo=timezone.utc)


def _cfg(url="u", art="html", takt_s=60, markt=None):
    cfg = {"url": url, "art": art, "takt_s": takt_s}
    if markt:
        cfg["markt_event_id"] = markt
    return cfg


def _holer(sequenz):
    """Fake-Holer: gibt die Antworten der Reihe nach zurueck, merkt sich Header."""
    gesehen = []

    def h(url, headers):
        gesehen.append(dict(headers))
        return sequenz.pop(0)
    h.gesehen = gesehen
    return h


# -------------------------------------------------------- Normalisierung

def test_normalisiere_html_entfernt_script_und_tags():
    body = b"<html><script>var t=Date.now()</script><!-- c --><p>Status:  OPEN</p><style>x</style></html>"
    assert qw.normalisiere(body, "html") == "Status: OPEN"


def test_normalisiere_json_ist_reihenfolgeunabhaengig():
    a = qw.normalisiere(b'{"b": 1, "a": [1, 2]}', "json")
    b = qw.normalisiere(b'{"a": [1, 2], "b": 1}', "json")
    assert a == b and qw.hash_von(a) == qw.hash_von(b)


def test_diff_ausschnitt_zeigt_neue_zeile():
    d = qw.diff_ausschnitt("a\nb\nc", "a\nb\nc\nGrant: Jane Doe, December 3, 2026")
    assert d.startswith("+Grant: Jane Doe")


# --------------------------------------------------- Aenderungserkennung

def test_erstsichtung_dann_unveraendert_dann_aenderung(tmp_path):
    protokoll = tmp_path / "e.jsonl"
    zustand = qw.leerer_zustand()
    holer = _holer([
        qw.Antwort(200, {"ETag": "v1", "Last-Modified": "Thu, 03 Dec 2026 10:00:00 GMT"}, b"<p>A</p>"),
        qw.Antwort(304, {}, b""),
        qw.Antwort(200, {"ETag": "v2"}, b"<p>A</p><p>B</p>"),
    ])
    cfg = _cfg()
    assert qw.pruefe_quelle("q", cfg, zustand, protokoll, holer, jetzt=T0) == "erstsichtung"
    assert qw.pruefe_quelle("q", cfg, zustand, protokoll, holer,
                            jetzt=T0 + timedelta(seconds=61)) == "unveraendert"
    # Conditional GET traegt die gespeicherten Header
    assert holer.gesehen[1]["If-None-Match"] == "v1"
    assert holer.gesehen[1]["If-Modified-Since"].startswith("Thu, 03 Dec")
    assert qw.pruefe_quelle("q", cfg, zustand, protokoll, holer,
                            jetzt=T0 + timedelta(seconds=122)) == "aenderung"
    zeilen = [json.loads(z) for z in protokoll.read_text(encoding="utf-8").splitlines()]
    assert [z["art"] for z in zeilen] == ["erstsichtung", "aenderung"]
    assert zeilen[1]["diff"] == "+B"
    assert zeilen[1]["vorherige_aenderung_utc"] == "2026-12-04T05:00:00Z"
    assert zustand["quellen"]["q"]["etag"] == "v2"


def test_nicht_faellig_vor_ablauf_des_quellentakts(tmp_path):
    zustand = qw.leerer_zustand()
    holer = _holer([qw.Antwort(200, {}, b"x"), qw.Antwort(200, {}, b"y")])
    cfg = _cfg(takt_s=300)
    qw.pruefe_quelle("q", cfg, zustand, tmp_path / "e.jsonl", holer, jetzt=T0)
    assert qw.pruefe_quelle("q", cfg, zustand, tmp_path / "e.jsonl", holer,
                            jetzt=T0 + timedelta(seconds=120)) == "nicht_faellig"
    assert len(holer.gesehen) == 1


def test_fehler_fuehrt_in_verdoppelte_sperre_und_sperre_ende(tmp_path):
    protokoll = tmp_path / "e.jsonl"
    zustand = qw.leerer_zustand()
    holer = _holer([qw.Antwort(403, {}, b""), qw.Antwort(403, {}, b""), qw.Antwort(200, {}, b"ok")])
    cfg = _cfg(takt_s=1)
    assert qw.pruefe_quelle("q", cfg, zustand, protokoll, holer, jetzt=T0) == "fehler"
    q = zustand["quellen"]["q"]
    assert q["sperre_s"] == qw.SPERRE_START_S
    # waehrend der Sperre: kein Poll
    assert qw.pruefe_quelle("q", cfg, zustand, protokoll, holer,
                            jetzt=T0 + timedelta(seconds=10)) == "gesperrt"
    assert len(holer.gesehen) == 1
    # nach Ablauf erneut Fehler -> Verdopplung, aber kein zweites sperre-Ereignis
    assert qw.pruefe_quelle("q", cfg, zustand, protokoll, holer,
                            jetzt=T0 + timedelta(seconds=61)) == "fehler"
    assert q["sperre_s"] == 2 * qw.SPERRE_START_S
    assert qw.pruefe_quelle("q", cfg, zustand, protokoll, holer,
                            jetzt=T0 + timedelta(seconds=200)) == "erstsichtung"
    arten = [json.loads(z)["art"] for z in protokoll.read_text(encoding="utf-8").splitlines()]
    assert arten == ["sperre", "sperre_ende", "erstsichtung"]


# ------------------------------------------------------------ Markt-Hook

def test_aenderung_mit_markt_hook_und_nachfassungen(tmp_path):
    protokoll = tmp_path / "e.jsonl"
    zustand = qw.leerer_zustand()
    holer = _holer([qw.Antwort(200, {}, b"alt"), qw.Antwort(200, {}, b"neu")])
    ereignis = {"markets": [{"id": "77", "question": "Shutdown ends December 5?",
                             "bestBid": "0.30", "bestAsk": "0.35"}]}
    cfg = _cfg(art="text", takt_s=1, markt="4711")
    qw.pruefe_quelle("q", cfg, zustand, protokoll, holer, lambda url: ereignis, jetzt=T0)
    assert qw.pruefe_quelle("q", cfg, zustand, protokoll, holer, lambda url: ereignis,
                            jetzt=T0 + timedelta(seconds=5)) == "aenderung"
    assert [nf["minute"] for nf in zustand["offene_nachfassungen"]] == [1, 5, 30]
    # +1 min faellig, +5/+30 nicht
    n = qw.nachfassungen(zustand, protokoll, lambda url: ereignis, jetzt=T0 + timedelta(seconds=66))
    assert n == 1 and [nf["minute"] for nf in zustand["offene_nachfassungen"]] == [5, 30]
    zeilen = [json.loads(z) for z in protokoll.read_text(encoding="utf-8").splitlines()]
    aend = next(z for z in zeilen if z["art"] == "aenderung")
    assert aend["buch_t0"]["77"]["bid"] == "0.30" and aend["markt_event_id"] == "4711"
    nf = next(z for z in zeilen if z["art"] == "nachfassung")
    assert nf["minute"] == 1 and nf["buch"]["77"]["ask"] == "0.35"


def test_markt_quotes_faengt_fehler_ab():
    def kaputt(url):
        raise RuntimeError("503")
    assert "fehler" in qw.markt_quotes("1", kaputt)


# ------------------------------------------------------------ Zustand/CLI

def test_zustand_roundtrip_und_defekte_datei(tmp_path):
    pfad = tmp_path / "zustand.json"
    z = qw.leerer_zustand()
    z["quellen"]["q"] = {"hash": "h"}
    qw.schreibe_zustand(pfad, z)
    assert qw.lade_zustand(pfad)["quellen"]["q"]["hash"] == "h"
    pfad.write_text("{kaputt", encoding="utf-8")
    assert qw.lade_zustand(pfad) == qw.leerer_zustand()


def test_lade_quellen_override_ergaenzt_defaults(tmp_path):
    pfad = tmp_path / "q.json"
    pfad.write_text(json.dumps({"quellen": {"x": {"url": "http://x"}, "y": {"art": "json"}}}),
                    encoding="utf-8")
    q = qw.lade_quellen(pfad)
    assert q == {"x": {"url": "http://x", "art": "html", "takt_s": qw.TAKT_S}}
    assert set(qw.lade_quellen(None)) == set(qw.STANDARD_QUELLEN)


def test_main_einmal_schreibt_protokoll_und_zustand(tmp_path, capsys):
    pfad = tmp_path / "q.json"
    pfad.write_text(json.dumps({"quellen": {"a": {"url": "http://a", "art": "text"},
                                            "b": {"url": "http://b", "art": "text"}}}),
                    encoding="utf-8")
    antworten = {"http://a": qw.Antwort(200, {}, b"A"), "http://b": qw.Antwort(500, {}, b"")}
    rc = qw.main(["--einmal", "--quellen", str(pfad), "--wurzel", str(tmp_path / "w")],
                 holer=lambda url, h: antworten[url], schlaf=lambda s: None)
    assert rc == 0
    zustand = json.loads((tmp_path / "w" / "zustand.json").read_text(encoding="utf-8"))
    assert zustand["quellen"]["a"]["hash"] and zustand["quellen"]["b"]["sperre_s"] == qw.SPERRE_START_S
    out = capsys.readouterr().out
    assert "a=erstsichtung" in out and "b=fehler" in out


def test_main_max_zyklen_beendet_schleife(tmp_path):
    pfad = tmp_path / "q.json"
    pfad.write_text(json.dumps({"quellen": {"a": {"url": "http://a", "art": "text", "takt_s": 1}}}),
                    encoding="utf-8")
    geschlafen = []
    rc = qw.main(["--quellen", str(pfad), "--wurzel", str(tmp_path / "w"), "--max-zyklen", "3",
                  "--takt-s", "1"], holer=lambda url, h: qw.Antwort(200, {}, b"A"),
                 schlaf=geschlafen.append)
    assert rc == 0 and geschlafen == [1.0, 1.0]
