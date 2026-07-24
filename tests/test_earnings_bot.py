"""Earnings-Bot: Polymarket-Verbindung fuer Live-Webcast-Events — 24.07.2026.

Erstes Earnings-Profil `earnings_pg_july29` (P&G, Event 715467). Die
Tests laufen offline gegen synthetische Gamma-Maerkte mit den echten
market_ids und Fragen des Events — sie belegen die Regel-Ableitung, die
Earnings-Gates (Anyone-Klausel, closed, groupItemThreshold-Falle), das
Wort-Matching der Komposita-Overrides und die Entscheidungs-Deckel,
nicht den Live-Abruf.
"""

from __future__ import annotations

import importlib
import json

import pytest

from operations.pipeline import config
from operations.pipeline.counter_engine import Segment, StreamingCounter

PROFIL = "earnings_pg_july29"


def _beschreibung(anyone: bool = True) -> str:
    """Gekuerzte Original-Description des Earnings-Templates.

    Byte-identisch je Event (AXP 715475: 1 Description fuer 21 Maerkte).
    anyone=False simuliert die Sprecherfilter-Variante der Elon-Serie
    ("What will Elon Musk say during Tesla ... earnings call?").
    """
    kern = ("mentioned by anyone during this event" if anyone
            else "said by Elon Musk during this event")
    return (
        "This market will resolve based on the next earnings announcement "
        "of Procter & Gamble currently scheduled to take place on July 29, "
        "2026 at 8:30 AM ET.\n\n"
        f'This market will resolve to "Yes" if the listed term is {kern}. '
        'Otherwise, the market will resolve to "No".\n\n'
        "If this event is definitely cancelled, or otherwise is not aired "
        'by July 30, 2026, 11:59 PM ET, "-No Qualifying Event-" will '
        'resolve to "Yes" and all other brackets will resolve to "No".\n\n'
        "The resolution source will be audio of the event."
    )


def _markt(mid: str, frage: str, *, closed: bool = False,
           anyone: bool = True, group_item_threshold: int = 0) -> dict:
    """Minimaler Gamma-Markt mit YES/NO-Token und der echten Frage."""
    return {
        "id": mid,
        "slug": f"will-pg-say-{mid}",
        "question": frage,
        "description": _beschreibung(anyone),
        "outcomes": json.dumps(["Yes", "No"]),
        "clobTokenIds": json.dumps([f"yes-{mid}", f"no-{mid}"]),
        "outcomePrices": json.dumps(["0.5", "0.5"]),
        "closed": closed,
        # ACHTUNG Falle: groupItemThreshold ist ein SORTIER-Index der
        # Event-Gruppe, KEINE Zaehlschwelle (AXP 715475: "Airline" traegt
        # 3, "Income 10+ times" traegt 0). Die Tests setzen bewusst
        # irrefuehrende Werte, um die Schwellen-Quelle festzunageln.
        "groupItemThreshold": group_item_threshold,
    }


# Echte market_ids/Fragen des Events (Gamma, 24.07.2026, Auszug).
EVENT_MARKETS = [
    _markt("2966428",
           'Will Procter & Gamble say "Quarter" 10+ times during earnings call?'),
    _markt("2966433",
           'Will Procter & Gamble say "Customer" 5+ times during earnings call?'),
    _markt("2966435",
           'Will Procter & Gamble say "Currency" during earnings call?',
           group_item_threshold=3),
    _markt("2966437",
           'Will Procter & Gamble say "World Cup" during earnings call?'),
    _markt("2966443",
           'Will Procter & Gamble say "Trump" during earnings call?'),
    _markt("2966445",
           'Will Procter & Gamble say "Toilet paper" during earnings call?'),
    _markt("2966448", "Will the earnings call not air?"),
]


@pytest.fixture
def profil(monkeypatch):
    """Aktiviert earnings_pg_july29 fuer die config-abgeleiteten Werte."""
    monkeypatch.setenv("BOT_PROFIL", PROFIL)
    importlib.reload(config)
    yield
    monkeypatch.delenv("BOT_PROFIL", raising=False)
    importlib.reload(config)


@pytest.fixture
def snapshot(profil, tmp_path, monkeypatch):
    """Gamma-Snapshot des Events auf der Platte, wie ihn der Bot liest."""
    pfad = tmp_path / "gamma_event_snapshot.json"
    pfad.write_text(json.dumps(
        {"event_id": "715467", "slug": config.PROFILE[PROFIL]["event_slug"],
         "markets": EVENT_MARKETS}), encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    return pfad


# ------------------------------------------------ Profil-Grundwerte


def test_profil_grunddaten(profil) -> None:
    p = config.PROFILE[PROFIL]
    assert p["event_id"] == "715467"
    assert p["discovery_slug_filter"] in p["event_slug"]
    # Kein Drop-Watcher: der Earnings-Bot laeuft rein ueber Live-Audio.
    assert p["rss_feed_url"] is None
    assert p["yt_channel_id"] is None
    assert p["mp3_probe_muster"] is None
    # Eigenes Live-Verzeichnis, disjunkt zu allen anderen Profilen.
    assert p["live_dir"] == PROFIL
    andere = [q["live_dir"] for name, q in config.PROFILE.items()
              if name != PROFIL]
    assert p["live_dir"] not in andere


def test_discovery_filter_disjunkt_zu_anderen_profilen(profil) -> None:
    # Der Filter darf nie ein fremdes Event greifen (und umgekehrt).
    for name, q in config.PROFILE.items():
        if name == PROFIL:
            continue
        assert config.PROFILE[PROFIL]["discovery_slug_filter"] not in q["event_slug"]
        assert q["discovery_slug_filter"] not in config.PROFILE[PROFIL]["event_slug"]


def test_call_start_und_zeitzone(profil) -> None:
    # 29.07.2026 08:30 AM ET = 12:30 UTC (Juli = EDT, UTC-4). Die
    # 22:30/21:30-Verwechslung der Web-Recherche (EST statt EDT) haette
    # die erste Stunde des Calls gekostet.
    assert config.CALL_START_UTC == "2026-07-29T12:30:00Z"
    from datetime import datetime

    start = datetime.strptime(config.CALL_START_UTC, "%Y-%m-%dT%H:%M:%SZ")
    assert (start.hour, start.minute) == (12, 30)
    assert config.CALL_MAX_MINUTEN == 120.0


def test_deckel_yes_only_und_chunks(profil) -> None:
    # Audio-Standard: 0.93 - 0.03 = 0.90.
    assert config.ASK_OBERGRENZE == 0.90
    # NO-Seite aus: Live-Capture ohne Abdeckungsgarantie (analog hotones).
    assert config.NO_ASK_OBERGRENZE == 0.0
    assert config.GAP_VERIFY_AKTIV is False
    # Kurze Chunks fuer den Livestream; andere Profile unveraendert 20.
    assert config.CHUNK_SEKUNDEN == 10
    assert config.PROFILE["allin_july17"].get("chunk_sekunden") is None


def test_andere_profile_unveraendert() -> None:
    # Default-Profil (allin_july10): CHUNK_SEKUNDEN bleibt 20, kein
    # Earnings-Feld gesetzt.
    importlib.reload(config)
    assert config.CHUNK_SEKUNDEN == 20
    assert config.CALL_START_UTC is None
    assert config.CALL_MAX_MINUTEN == 120.0


# ------------------------------------------------ Earnings-Gates


def _rules(snapshot):
    from operations.pipeline.earnings_bot import baue_earnings_rules

    return {r.market_id: r for r in baue_earnings_rules()}


def test_schwelle_aus_frage_nicht_aus_groupitemthreshold(snapshot) -> None:
    rules = _rules(snapshot)
    # Zaehl-Brackets aus dem Fragetext.
    assert rules["2966428"].schwelle == 10
    assert rules["2966433"].schwelle == 5
    # "Currency" traegt groupItemThreshold=3 (Sortier-Index!) und ist
    # trotzdem ein Ein-Nennungs-Markt.
    assert rules["2966435"].schwelle == 1
    assert rules["2966435"].status == "active"


def test_anyone_klausel_gate(snapshot, tmp_path, monkeypatch) -> None:
    # Sprecherfilter-Variante (Elon-Serie): Description ohne Anyone-
    # Klausel -> SKIP, sonst zaehlt unser Zaehler alle Stimmen.
    maerkte = EVENT_MARKETS + [
        _markt("999001", 'Will Elon Musk say "Tesla" during earnings call?',
               anyone=False),
    ]
    pfad = tmp_path / "snapshot_sprecher.json"
    pfad.write_text(json.dumps({"event_id": "x", "markets": maerkte}),
                    encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    rules = _rules(pfad)
    assert rules["999001"].status == "skip"
    assert rules["999001"].skip_grund == (
        "keine_anyone_klausel_sprecherfilter_moeglich")
    assert rules["2966443"].status == "active"


def test_geschlossener_markt_wird_geskippt(snapshot, tmp_path, monkeypatch) -> None:
    maerkte = EVENT_MARKETS + [
        _markt("999002", 'Will Procter & Gamble say "China" during earnings call?',
               closed=True),
    ]
    pfad = tmp_path / "snapshot_closed.json"
    pfad.write_text(json.dumps({"event_id": "x", "markets": maerkte}),
                    encoding="utf-8")
    monkeypatch.setattr(config, "GAMMA_SNAPSHOT", pfad)
    rules = _rules(pfad)
    assert rules["999002"].status == "skip"
    assert rules["999002"].skip_grund == "markt_geschlossen"


def test_not_air_markt_bleibt_negationsskip(snapshot) -> None:
    # "Will the earnings call not air?" ist kein Wortzaehl-Markt; der
    # bestehende Negations-Skip aus build_rule greift.
    rules = _rules(snapshot)
    assert rules["2966448"].status == "skip"
    assert rules["2966448"].skip_grund == "negationsmarkt_ohne_wortzaehlung"


def test_komposita_override_world_cup_und_toilet_paper(snapshot) -> None:
    rules = _rules(snapshot)
    assert rules["2966437"].varianten == ["World Cup", "World-Cup", "Worldcup"]
    assert rules["2966445"].varianten == [
        "Toilet paper", "Toilet-paper", "Toiletpaper"]
    # Bindestrich-Schreibweise zaehlt genau einmal (PDF "Hyphenated
    # Constructs"; die strikten Wortgrenzen sehen "World-Cup" ohne
    # Override nicht, weil "-" kein Whitespace ist).
    z = StreamingCounter(rules["2966437"])
    z.ingest_chunk(1, [Segment(text="They sponsor the World-Cup broadcast.",
                               confidence=0.95)], "t")
    assert z.count == 1
    z.ingest_chunk(2, [Segment(text="the worldcup and the world cup",
                               confidence=0.95)], "t")
    assert z.count == 3


# ------------------------------------------------ Entscheidungs-Deckel


def test_yes_bracket_trigger_mit_puffer(snapshot) -> None:
    from operations.pipeline.decision import entscheide_yes

    rules = _rules(snapshot)
    quarter = rules["2966428"]  # Schwelle 10, Ziel 10 + Puffer 2 = 12
    assert entscheide_yes(quarter, 11, 0.85).action == "NONE"
    d = entscheide_yes(quarter, 12, 0.85)
    assert d.action == "YES"
    assert d.token_id == quarter.yes_token_id
    # Deckel 0.90 haelt.
    assert entscheide_yes(quarter, 12, 0.91).action == "NONE"


def test_no_seite_ist_gesperrt(snapshot) -> None:
    from operations.pipeline.decision import entscheide_no

    rules = _rules(snapshot)
    trump = rules["2966443"]
    # Endstand 0, NO-Ask billig — trotzdem kein Trade: Deckel 0.0.
    assert entscheide_no(trump, 0, 0.50).action == "NONE"


# ------------------------------------------------ Audio-Kommando


def test_ffmpeg_befehl_geraet_und_stream(tmp_path) -> None:
    from operations.pipeline.earnings_bot import ffmpeg_befehl

    wav = tmp_path / "call_audio.wav"
    geraet = ffmpeg_befehl("CABLE Output (VB-Audio Virtual Cable)",
                           "geraet", wav)
    assert ["-f", "dshow"] == geraet[geraet.index("-f"):geraet.index("-f") + 2]
    assert "audio=CABLE Output (VB-Audio Virtual Cable)" in geraet

    stream = ffmpeg_befehl("https://example.com/x.m3u8", "stream", wav)
    # Am juengsten HLS-Segment starten (Messprotokoll §4.2) und mit
    # Browser-UA anfragen (WAF-Befund Recherche §11).
    assert "-live_start_index" in stream
    assert stream[stream.index("-live_start_index") + 1] == "-1"
    assert "-user_agent" in stream
    # Whisper-Eingangsformat: mono, 16 kHz, PCM, wachsende WAV.
    for wert in ("-ac", "-ar", "pcm_s16le"):
        assert wert in stream
    assert stream[-1] == str(wav)
