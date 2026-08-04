"""Startscan des Elon-Bots: Abdeckung nur ueber Posts mit Feed-Position.

Befund 4.8.2026 (Armierung `elon_august3` an Tag 2, startscan_seiten=12):
Der Scan brach nach 2 Seiten / 44 Posts ab und meldete
"erreicht_periodenstart": true, obwohl 5 echte Posts der laufenden
Periode (2026-08-03 05:35-13:47) noch nicht geladen waren. Ursache war
ein von Elon zitierter Post von 2014, den `parse_timeline` als eigenen
Post fuehrt; nach post_id sortiert steht er am Array-Ende und erfuellte
das Abbruchkriterium `alle[-1].created_utc <= start`.

Am 4.8.2026 gegen die Live-Antwort geprueft: der 2014er Post haengt
unter `quoted_status_result`, der angepinnte Post kommt als eigene
`TimelinePinEntry`-Instruktion auf JEDER Seite mit. Beide belegen keine
Scan-Tiefe — die Tests halten das fest.
"""

from __future__ import annotations

from datetime import datetime, timezone

from operations.pipeline.elon_bot import _aeltester_im_feed, startscan
from operations.pipeline.x_watch import (
    XPost,
    hat_feed_position,
    parse_timeline,
)

USER_ID = "44196397"
START = datetime(2026, 8, 3, 4, 0, 0, tzinfo=timezone.utc)


def _id(zeit: str) -> int:
    """Snowflake-id zu einer Zeit (Umkehrung von x_watch._snowflake_utc)."""
    ms = int(datetime.strptime(zeit, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=timezone.utc).timestamp() * 1000)
    return (ms - 1288834974657) << 22


def _post(zeit: str, *, angepinnt: bool = False,
          eingebettet: bool = False) -> XPost:
    return XPost(
        post_id=_id(zeit), text=f"post {zeit}", created_utc=zeit,
        ist_repost=False, ist_reply=False, hat_medien=False,
        ist_angepinnt=angepinnt, ist_eingebettet=eingebettet,
    )


def _seite(*posts: XPost) -> list[XPost]:
    """Seite wie parse_timeline sie liefert: absteigend nach post_id."""
    return sorted(posts, key=lambda p: -p.post_id)


class FakeWatcher:
    """Liefert vorgegebene Folgeseiten; zaehlt die Abrufe."""

    def __init__(self, seiten: list[list[XPost]]) -> None:
        self.seiten = seiten
        self.abrufe = 0

    def hole_posts(self, cursor: str | None = None):
        self.abrufe += 1
        i = int(cursor)
        naechster = str(i + 1) if i + 1 < len(self.seiten) else None
        return self.seiten[i], naechster


# Seite 1 kommt aus dem regulaeren Poll und wird an startscan uebergeben.
SEITE1 = _seite(_post("2026-08-04T12:00:00Z"), _post("2026-08-04T06:00:00Z"))
# Seite 2 endet auf dem zitierten Uralt-Post (2014) — die alte Falle.
ZITAT_2014 = _post("2014-08-03T02:33:24Z", eingebettet=True)
SEITE2 = _seite(_post("2026-08-04T05:00:00Z"), _post("2026-08-03T20:00:00Z"),
                ZITAT_2014)
# Erst Seite 3 blaettert ueber den Periodenstart hinaus zurueck.
SEITE3 = _seite(_post("2026-08-03T13:47:14Z"), _post("2026-08-03T05:35:38Z"),
                _post("2026-08-03T03:30:00Z"))


def test_zitat_steht_am_array_ende() -> None:
    """Praemisse des Fehlers: das Zitat sortiert ans Seitenende."""
    assert SEITE2[-1] is ZITAT_2014
    assert not hat_feed_position(ZITAT_2014)


def test_scan_blaettert_ueber_zitierten_uraltpost_hinweg() -> None:
    w = FakeWatcher([SEITE2, SEITE3])
    alle, daten = startscan(w, SEITE1, "0", START, seiten_max=12)

    assert daten["seiten_geblaettert"] == 2, "Scan stoppte am Zitat"
    assert daten["erreicht_periodenstart"] is True
    # Gemeldet wird der aelteste Post MIT Feed-Position, nicht das Zitat.
    assert daten["aeltester"] == "2026-08-03T03:30:00Z"
    assert daten["aeltester_mit_fremdposition"] == "2014-08-03T02:33:24Z"
    assert daten["ohne_feed_position"] == 1
    # Die zuvor verlorenen Periodenposts sind geladen.
    geladen = {p.created_utc for p in alle}
    assert {"2026-08-03T13:47:14Z", "2026-08-03T05:35:38Z"} <= geladen


def test_abdeckung_erst_wenn_periode_wirklich_erreicht() -> None:
    """Ohne Seite 3 darf keine Abdeckung gemeldet werden."""
    w = FakeWatcher([SEITE2, SEITE3])
    _, daten = startscan(w, SEITE1, "0", START, seiten_max=1)

    assert daten["seiten_geblaettert"] == 1
    assert daten["erreicht_periodenstart"] is False
    assert daten["aeltester"] == "2026-08-03T20:00:00Z"


def test_angepinnter_uraltpost_belegt_keine_abdeckung() -> None:
    """X haengt den angepinnten Post an jede Seite — auch einen von 2014."""
    pin = _post("2014-08-03T02:33:24Z", angepinnt=True)
    seiten = [_seite(_post("2026-08-04T05:00:00Z"), pin),
              _seite(_post("2026-08-03T20:00:00Z"), pin)]
    w = FakeWatcher(seiten)
    _, daten = startscan(w, _seite(*SEITE1, pin), "0", START, seiten_max=12)

    assert daten["erreicht_periodenstart"] is False
    assert daten["aeltester"] == "2026-08-03T20:00:00Z"
    assert w.abrufe == 2, "Scan muss bis zum Seitenende blaettern"


def test_leere_folgeseite_beendet_scan() -> None:
    w = FakeWatcher([[]])
    alle, daten = startscan(w, SEITE1, "0", START, seiten_max=12)

    assert daten["seiten_geblaettert"] == 0
    assert daten["erreicht_periodenstart"] is False
    assert len(alle) == len(SEITE1)


def test_aeltester_im_feed_ignoriert_fremdpositionen() -> None:
    assert _aeltester_im_feed([]) is None
    assert _aeltester_im_feed([ZITAT_2014]) is None
    aeltester = _aeltester_im_feed([*SEITE1, ZITAT_2014])
    assert aeltester is not None
    assert aeltester.created_utc == "2026-08-04T06:00:00Z"


# --- parse_timeline: woher die Markierungen kommen -------------------

def _tweet(pid: int, **extra: object) -> dict:
    return {
        "rest_id": str(pid),
        "legacy": {"full_text": f"text {pid}", "user_id_str": USER_ID,
                   "id_str": str(pid)},
        **extra,
    }


def _antwort(instruktionen: list[dict]) -> dict:
    return {"data": {"user": {"result": {"timeline": {"timeline": {
        "instructions": instruktionen}}}}}}


def _eintrag(tweet: dict) -> dict:
    return {"entryId": f"tweet-{tweet['rest_id']}",
            "content": {"itemContent": {"tweet_results": {"result": tweet}}}}


def test_parse_timeline_markiert_pin_und_zitat() -> None:
    pin_id = _id("2014-08-03T02:33:24Z")
    zitat_id = _id("2015-06-01T10:00:00Z")
    normal_id = _id("2026-08-04T12:00:00Z")
    antwort = _antwort([
        {"type": "TimelinePinEntry", "entry": _eintrag(_tweet(pin_id))},
        {"type": "TimelineAddEntries", "entries": [_eintrag(
            _tweet(normal_id,
                   quoted_status_result={"result": _tweet(zitat_id)}))]},
    ])
    nach_id = {p.post_id: p for p in parse_timeline(antwort, USER_ID)}

    assert nach_id[pin_id].ist_angepinnt
    assert not nach_id[pin_id].ist_eingebettet
    assert nach_id[zitat_id].ist_eingebettet
    assert hat_feed_position(nach_id[normal_id])
    assert not hat_feed_position(nach_id[pin_id])
    assert not hat_feed_position(nach_id[zitat_id])


def test_parse_timeline_regulaerer_eintrag_schlaegt_fremdposition() -> None:
    """Derselbe Post als Pin UND als regulaerer Eintrag zaehlt fuer die
    Abdeckung — in beiden Reihenfolgen."""
    pid = _id("2026-08-04T12:00:00Z")
    pin = {"type": "TimelinePinEntry", "entry": _eintrag(_tweet(pid))}
    regulaer = {"type": "TimelineAddEntries", "entries": [
        _eintrag(_tweet(pid))]}

    for instruktionen in ([pin, regulaer], [regulaer, pin]):
        posts = parse_timeline(_antwort(instruktionen), USER_ID)
        assert len(posts) == 1
        assert hat_feed_position(posts[0])


def test_parse_timeline_behaelt_note_tweet_volltext() -> None:
    """Der Langtext darf beim Dedup nicht auf den Kurztext zurueckfallen."""
    pid = _id("2026-08-04T12:00:00Z")
    lang = {"note_tweet": {"note_tweet_results": {"result": {
        "text": "voller Langtext"}}}}
    antwort = _antwort([
        {"type": "TimelinePinEntry", "entry": _eintrag(_tweet(pid, **lang))},
        {"type": "TimelineAddEntries", "entries": [_eintrag(_tweet(pid))]},
    ])
    posts = parse_timeline(antwort, USER_ID)

    assert len(posts) == 1
    assert posts[0].text == "voller Langtext"
    assert hat_feed_position(posts[0])
