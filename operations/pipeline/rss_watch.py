"""RSS-Drop-Detektion fuer den All-In-Feed (libsyn)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from email.utils import parsedate_to_datetime

from operations.pipeline import config

_ITEM = re.compile(r"<item>(.*?)</item>", re.S)
_TITLE = re.compile(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", re.S)
_GUID = re.compile(r"<guid[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</guid>", re.S)
_PUBDATE = re.compile(r"<pubDate>(.*?)</pubDate>")
_ENCLOSURE = re.compile(r'<enclosure[^>]*url="([^"]+)"')


@dataclass
class FeedItem:
    guid: str
    title: str
    pubdate_utc: str
    audio_url: str | None


def parse_feed(xml_text: str, max_items: int = 5) -> list[FeedItem]:
    items = []
    for roh in _ITEM.findall(xml_text)[:max_items]:
        guid = _GUID.search(roh)
        title = _TITLE.search(roh)
        pd = _PUBDATE.search(roh)
        enc = _ENCLOSURE.search(roh)
        pub_iso = ""
        if pd:
            try:
                pub_iso = parsedate_to_datetime(pd.group(1)).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                )
            except (TypeError, ValueError):
                pub_iso = pd.group(1)
        items.append(
            FeedItem(
                guid=(guid.group(1).strip() if guid else ""),
                title=(title.group(1).strip() if title else ""),
                pubdate_utc=pub_iso,
                audio_url=(enc.group(1) if enc else None),
            )
        )
    return items


def fetch_feed_items(max_items: int = 5) -> list[FeedItem]:
    import httpx
    from tenacity import retry, stop_after_attempt, wait_random_exponential

    # Accept-Encoding: identity gegen defekte Gzip-Antworten am
    # megaphone-Edge-Cache (Error -3 while decompressing, 2026-07-06).
    kopf = dict(config.HTTP_HEADERS)
    kopf["Accept-Encoding"] = "identity"

    @retry(stop=stop_after_attempt(3), wait=wait_random_exponential(1, 8), reraise=True)
    def _abruf() -> str:
        resp = httpx.get(
            config.RSS_FEED_URL,
            headers=kopf,
            timeout=30.0,
            follow_redirects=True,
        )
        resp.raise_for_status()
        return resp.text

    return parse_feed(_abruf(), max_items=max_items)


_EPISODEN_NR = re.compile(r"ALLIN-E(\d+)_Ch\.mp3")


def naechste_episoden_nummer(items: list[FeedItem] | None = None) -> int:
    """Hoechste E-Nummer im Feed plus 1 (Hauptepisoden-Muster)."""
    if items is None:
        items = fetch_feed_items(max_items=15)
    nummern = []
    for it in items:
        m = _EPISODEN_NR.search(it.audio_url or "")
        if m:
            nummern.append(int(m.group(1)))
    if not nummern:
        raise ValueError("Keine ALLIN-E<n>_Ch.mp3 im Feed gefunden")
    return max(nummern) + 1


class Mp3UrlProber:
    """Probt die vorhersagbare CDN-URL der naechsten Hauptepisode per HEAD.

    Umgeht den Feed-Cache komplett: die MP3 liegt typischerweise ab
    pubDate auf dem CDN, waehrend das Feed-XML bis zu einer Stunde
    nachhaengen kann (E279-Befund). Feuert erst, wenn die Datei bei zwei
    aufeinanderfolgenden Checks dieselbe Content-Length meldet, damit
    kein halb hochgeladener Stand verarbeitet wird.
    """

    def __init__(self, naechste_nr: int, head_fn=None, muster: str | None = None) -> None:
        muster = muster or config.MP3_PROBE_MUSTER
        if not muster:
            raise ValueError("Kein MP3-Probe-Muster im aktiven Profil")
        self.urls = [muster.format(n=n) for n in (naechste_nr, naechste_nr + 1)]
        self._letzte_laenge: dict[str, str] = {}
        self._head_fn = head_fn

    def _head(self, url: str) -> tuple[int, str | None]:
        if self._head_fn is not None:
            return self._head_fn(url)
        import httpx

        r = httpx.head(url, headers=config.HTTP_HEADERS, timeout=10,
                       follow_redirects=True)
        return r.status_code, r.headers.get("content-length")

    def poll(self) -> str | None:
        """URL der fertigen Datei oder None."""
        for url in self.urls:
            try:
                status, laenge = self._head(url)
            except Exception:  # noqa: BLE001 - einzelner Fehlversuch egal
                continue
            if status != 200 or not laenge:
                self._letzte_laenge.pop(url, None)
                continue
            if self._letzte_laenge.get(url) == laenge:
                return url
            self._letzte_laenge[url] = laenge
        return None


_YT_ENTRY = re.compile(r"<entry>(.*?)</entry>", re.S)
_YT_VIDEO_ID = re.compile(r"<yt:videoId>(.*?)</yt:videoId>")
_YT_TITLE = re.compile(r"<title>(.*?)</title>")
_YT_PUBLISHED = re.compile(r"<published>(.*?)</published>")


@dataclass
class YtVideo:
    video_id: str
    title: str
    published_utc: str

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"


def parse_yt_feed(xml_text: str, max_items: int = 10) -> list[YtVideo]:
    videos = []
    for roh in _YT_ENTRY.findall(xml_text)[:max_items]:
        vid = _YT_VIDEO_ID.search(roh)
        titel = _YT_TITLE.search(roh)
        pub = _YT_PUBLISHED.search(roh)
        if vid:
            videos.append(YtVideo(
                video_id=vid.group(1).strip(),
                title=(titel.group(1).strip() if titel else ""),
                published_utc=(pub.group(1).strip() if pub else ""),
            ))
    return videos


_YT_SEITEN_ID = re.compile(r'"videoId":"([A-Za-z0-9_-]{11})"')


def parse_yt_kanalseite(html: str, max_items: int = 10) -> list[YtVideo]:
    """Video-IDs aus der Kanal-Videoseite (Fallback ohne Feed).

    Titel/Datum fehlen hier; die Voll-Episoden-Pruefung laeuft ohnehin
    ueber yt-dlp-Metadaten.
    """
    gesehen: list[str] = []
    for vid in _YT_SEITEN_ID.findall(html):
        if vid not in gesehen:
            gesehen.append(vid)
        if len(gesehen) >= max_items:
            break
    return [YtVideo(video_id=v, title="(kanalseite)", published_utc="")
            for v in gesehen]


def fetch_yt_videos(max_items: int = 10) -> list[YtVideo]:
    """Neueste Kanal-Videos: Feed zuerst, Kanalseite als Fallback.

    Der YouTube-Feed-Endpoint liefert intermittierend 404 (beobachtet
    2026-07-07); die Videoseite haengt an anderer Infrastruktur.
    """
    import httpx
    from tenacity import retry, stop_after_attempt, wait_random_exponential

    @retry(stop=stop_after_attempt(2), wait=wait_random_exponential(1, 4), reraise=True)
    def _feed() -> str:
        resp = httpx.get(config.YT_FEED_URL, headers=config.HTTP_HEADERS,
                         timeout=30.0, follow_redirects=True)
        resp.raise_for_status()
        return resp.text

    try:
        return parse_yt_feed(_feed(), max_items=max_items)
    except Exception:  # noqa: BLE001 - Fallback auf Kanalseite
        # SOCS-Cookie umgeht die EU-Consent-Zwischenseite.
        resp = httpx.get(
            f"https://www.youtube.com/channel/{config.YT_CHANNEL_ID}/videos",
            headers=config.HTTP_HEADERS, cookies={"SOCS": "CAI"},
            timeout=30.0, follow_redirects=True,
        )
        resp.raise_for_status()
        return parse_yt_kanalseite(resp.text, max_items=max_items)


class YouTubeWatcher:
    """Meldet neue Videos des Kanals seit der Baseline (Clips inklusive;
    die Voll-Episoden-Pruefung uebernimmt der Bot via yt-dlp-Metadaten)."""

    def __init__(self) -> None:
        self.bekannt: set[str] = set()

    def initialisiere(self) -> int:
        videos = fetch_yt_videos()
        self.bekannt = {v.video_id for v in videos}
        return len(self.bekannt)

    def poll(self) -> list[YtVideo]:
        videos = fetch_yt_videos()
        neue = [v for v in videos if v.video_id not in self.bekannt]
        for v in neue:
            self.bekannt.add(v.video_id)
        return neue


class RssWatcher:
    """Meldet das erste Feed-Item, das neuer als die Baseline ist."""

    def __init__(self, baseline_guid: str | None = None) -> None:
        self.baseline_guid = baseline_guid

    def initialisiere(self) -> FeedItem | None:
        items = fetch_feed_items(max_items=1)
        if items:
            self.baseline_guid = items[0].guid
            return items[0]
        return None

    def poll(self) -> FeedItem | None:
        """Neues Item gegenueber Baseline oder None."""
        items = fetch_feed_items(max_items=3)
        if not items:
            return None
        neu = items[0]
        if self.baseline_guid and neu.guid != self.baseline_guid:
            return neu
        return None
