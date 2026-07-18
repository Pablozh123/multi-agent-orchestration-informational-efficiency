"""Truth-Social-Watcher: oeffentliche Mastodon-API von @realDonaldTrump.

Cloudflare blockt normale HTTP-Clients (403, Befund 16.07.); mit
Chrome-TLS-Impersonation via curl_cffi antwortet die API OHNE Login
(Befund 18.07.: HTTP 200 auf accounts/lookup und /statuses, keine
Rate-Limit-Header). Konservativ trotzdem: Poll >= TRUTH_POLL_S plus
Backoff bei 4xx/5xx (TruthFehler traegt den Status).

Regel-Abbildung des Wochen-Markts (Event-Serie trump-post-weekly):
- ReTruths (reblog) zaehlen NICHT -> ist_repost, Text bleibt leer.
- Quote-Truths: der EIGENE content zaehlt, der zitierte Fremdtext
  (quote.content) NICHT -> nur content wird extrahiert.
- Replies zaehlen (eigener Text) -> normales content-Feld.
- Links fliegen KOMPLETT aus dem Text: Truth rendert URLs als
  <a>-Span-Ketten; ein Marktwort INNERHALB einer URL soll keinen
  Auto-Kauf ausloesen (Resolver-Wertung unklar, konservativ).
- Bilder/Videos: hat_medien -> der Bot loggt nur einen Hinweis (kein OCR).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

TRUMP_USER_ID = "107780257626128497"  # @realDonaldTrump (verifiziert)
_BASIS_URL = "https://truthsocial.com/api/v1/accounts/{uid}/statuses"
_WHITESPACE = re.compile(r"\s+")


@dataclass
class TruthPost:
    post_id: int
    created_utc: str   # "%Y-%m-%dT%H:%M:%SZ" (Millisekunden entfernt)
    text: str          # eigener Text, ohne Links und ohne Fremd-Quote
    ist_repost: bool   # ReTruth -> zaehlt nicht
    ist_reply: bool
    hat_medien: bool
    hat_quote: bool


class TruthFehler(RuntimeError):
    """HTTP-Fehler der Truth-API; status fuer Backoff-Entscheidungen."""

    def __init__(self, status: int, body: str = "") -> None:
        super().__init__(f"truth_api HTTP {status}: {body[:120]}")
        self.status = status


def _text_aus_html(html: str | None) -> str:
    """Sichtbarer Text ohne Links (siehe Modul-Docstring)."""
    if not html:
        return ""
    from bs4 import BeautifulSoup

    baum = BeautifulSoup(html, "html.parser")
    for a in baum.find_all("a"):
        a.decompose()
    return _WHITESPACE.sub(" ", baum.get_text(" ")).strip()


def _zeit_normalisiert(created_at: str) -> str:
    """'2026-07-18T02:18:32.394Z' -> '2026-07-18T02:18:32Z'."""
    roh = (created_at or "").replace("Z", "+00:00")
    dt = datetime.fromisoformat(roh).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_status(d: dict) -> TruthPost:
    ist_repost = d.get("reblog") is not None
    return TruthPost(
        post_id=int(d["id"]),
        created_utc=_zeit_normalisiert(d.get("created_at", "")),
        # ReTruth: content ist der FREMDE Post -> nicht matchen.
        text="" if ist_repost else _text_aus_html(d.get("content")),
        ist_repost=ist_repost,
        ist_reply=d.get("in_reply_to_id") is not None,
        hat_medien=bool(d.get("media_attachments")),
        hat_quote=bool(d.get("quote") or d.get("quote_id")),
    )


class TruthWatcher:
    """Pollt die Status-Liste; neueste zuerst (API-Reihenfolge).

    Haelt eine persistente Session: ohne sie bekommt jeder Request eine
    frische TLS-Verbindung ohne Cloudflare-Cookies (__cf_bm) und wird
    nach wenigen Aufrufen mit 429 gedrosselt (Befund 18.07.). Bei
    403/429 wird die Session verworfen und beim naechsten Aufruf neu
    aufgebaut (frische Bot-Marke nach dem Backoff des Aufrufers).
    """

    def __init__(self, user_id: str = TRUMP_USER_ID,
                 timeout_s: float = 20.0) -> None:
        self.user_id = user_id
        self.timeout_s = timeout_s
        self._session = None

    def _sess(self):
        if self._session is None:
            from curl_cffi import requests as creq

            self._session = creq.Session(impersonate="chrome")
        return self._session

    def hole_posts(self, since_id: int | None = None,
                   max_id: int | None = None,
                   limit: int = 40) -> list[TruthPost]:
        params: dict[str, str] = {
            "limit": str(limit),
            "exclude_replies": "false",  # eigener Reply-Text zaehlt
        }
        if since_id is not None:
            params["since_id"] = str(since_id)
        if max_id is not None:
            params["max_id"] = str(max_id)
        r = self._sess().get(
            _BASIS_URL.format(uid=self.user_id), params=params,
            timeout=self.timeout_s,
        )
        if r.status_code != 200:
            if r.status_code in (403, 429):
                self._session = None  # naechster Aufruf mit frischer Session
            raise TruthFehler(r.status_code, r.text or "")
        return [parse_status(d) for d in r.json()]
