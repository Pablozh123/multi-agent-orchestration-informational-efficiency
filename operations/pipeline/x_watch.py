"""X-Feed fuer den Elon-Post-Bot: GraphQL UserTweetsAndReplies mit
Login-Cookies (auth_token + ct0 aus dem Browser, in .env).

Warum dieser Weg (Analyse 13.7.):
- Gast-GraphQL und die Profil-HTML-Seite liefern nur kuratierte ALTE
  Highlights (2022-2025), keine Live-Timeline.
- syndication.twitter.com antwortet 429.
- xtracker.io fuehrt nur Aggregat-Zaehler ohne Texte.
- X-API Basic (200 USD/Mt.) waere langsamer (10 req/15min) als der
  Web-Login-Pfad (~50 req/15min -> 16s-Poll wie aktives Scrollen).

Cookies: X_AUTH_TOKEN und X_CT0 in .env (vom User selbst eingetragen).
Der Poll nutzt denselben oeffentlichen Web-Bearer wie x.com im Browser.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import dataclass

WEB_BEARER = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D"
    "1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)
ELON_USER_ID = "44196397"

# Analyse 13.7.: Von den Timeline-Operationen ist ueber den Web-GraphQL-
# Pfad mit Login-Cookies NUR UserTweets serverseitig geroutet (200);
# UserTweetsAndReplies und SearchTimeline liefern 404 (verlangen
# vermutlich einen x-client-transaction-id-Header, den X fuer die
# haeufig gecachte UserTweets-Query nicht erzwingt). Folge: der native
# Feed sieht Standalone-Posts + eigene Threads, aber KEINE Replies an
# fremde Accounts. Diese Luecke deckt optional der Apify-Zweitkanal
# (elon_bot.py, nur mit APIFY_TOKEN) ueber "from:elonmusk" ab.
#
# QueryIds rotieren mit Frontend-Deploys -> werden bevorzugt LIVE aus dem
# main-Bundle gezogen (aktuelle_query_ids); die Konstante ist nur der
# Fallback, falls die Extraktion scheitert.
FALLBACK_QUERY_IDS = [
    # UTAR-Fallback ZWINGEND (Befund 16.7.): fehlte hier komplett -> wenn
    # der main.js-Parse die UTAR-qid mal nicht fand, gab es keinen
    # UTAR-Kandidaten und der Bot blieb dauerhaft ohne Fremd-Replies.
    ("UserTweetsAndReplies", "FIFgycIi-CNJcV0R-135Uw"),  # verifiziert 16.7.
    ("UserTweets", "E3opETHurmVJflFsUBVuUQ"),
    ("UserTweets", "hr4gzZONlq23okjU8fIe_A"),
]

_QID_CACHE: dict[str, str] = {}


def aktuelle_query_ids() -> dict[str, str]:
    """Zieht queryId je operationName live aus dem x.com-main-Bundle."""
    global _QID_CACHE
    if _QID_CACHE:
        return _QID_CACHE
    import httpx

    kopf = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/126.0 Safari/537.36")}
    html = httpx.get("https://x.com", headers=kopf, timeout=20,
                     follow_redirects=True).text
    m = re.search(
        r"https://abs\.twimg\.com/responsive-web/client-web/main\.[a-f0-9]+\.js",
        html)
    if not m:
        return {}
    js = httpx.get(m.group(0), headers=kopf, timeout=40).text
    paare = re.findall(
        r'queryId:"([\w-]+)",operationName:"(\w+)"', js)
    _QID_CACHE = {op: qid for qid, op in paare}
    return _QID_CACHE


@dataclass
class XPost:
    post_id: int
    text: str
    created_utc: str
    ist_repost: bool
    ist_reply: bool
    hat_medien: bool
    # Feed-Position (Befund 4.8.2026): nur Posts, die X als eigenen
    # Timeline-Eintrag ausliefert, belegen, wie weit ein Scan
    # zurueckgeblaettert ist. Angepinnte Posts haengt X an JEDE Seite,
    # Zitate/Repost-Originale haengen unter einem anderen Post — beide
    # koennen beliebig alt sein und taeuschen sonst Scan-Tiefe vor.
    ist_angepinnt: bool = False
    ist_eingebettet: bool = False


def hat_feed_position(p: XPost) -> bool:
    """True, wenn der Post eine eigene Position im Feed belegt."""
    return not (p.ist_angepinnt or p.ist_eingebettet)


# Unter diesen Schluesseln haengen fremd-positionierte Posts: das Zitat
# unter dem zitierenden Post, das Original unter dem Repost.
EINGEBETTET_UNTER = ("quoted_status_result", "retweeted_status_result")


def _snowflake_utc(post_id: int) -> str:
    from datetime import datetime, timezone

    ms = (post_id >> 22) + 1288834974657
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def parse_timeline(antwort: dict, user_id: str = ELON_USER_ID) -> list[XPost]:
    """Alle Posts DES Users aus einer Timeline-Antwort (rekursiv).

    Timeline-Module enthalten auch fremde Tweets (Konversationen) —
    gezaehlt wird nur user_id. Reposts (retweeted_status) fliegen raus,
    der eigene Text von Quotes/Replies bleibt (Marktregel).

    Posts ohne eigene Feed-Position werden markiert statt verworfen:
    angepinnte (TimelinePinEntry) und eingebettete (quoted_status_result
    / retweeted_status_result). Sie sind echte Posts des Users und
    zaehlen fuers Matching, belegen aber keine Scan-Tiefe.
    """
    posts: dict[int, XPost] = {}

    def _walk(knoten, angepinnt: bool = False,
              eingebettet: bool = False) -> None:
        if isinstance(knoten, list):
            for k in knoten:
                _walk(k, angepinnt, eingebettet)
            return
        if not isinstance(knoten, dict):
            return
        if knoten.get("type") == "TimelinePinEntry":
            angepinnt = True
        legacy = knoten.get("legacy")
        if (
            isinstance(legacy, dict)
            and "full_text" in legacy
            and str(legacy.get("user_id_str")) == user_id
        ):
            try:
                pid = int(knoten.get("rest_id") or legacy.get("id_str"))
            except (TypeError, ValueError):
                pid = None
            if pid is not None:
                text = str(legacy.get("full_text") or "")
                ist_repost = ("retweeted_status_result" in legacy
                              or text.startswith("RT @"))
                medien = bool((legacy.get("entities") or {}).get("media")
                              or (legacy.get("extended_entities") or {}).get("media"))
                neu = XPost(
                    post_id=pid,
                    text=text,
                    created_utc=_snowflake_utc(pid),
                    ist_repost=ist_repost,
                    ist_reply=bool(legacy.get("in_reply_to_status_id_str")),
                    hat_medien=medien,
                    ist_angepinnt=angepinnt,
                    ist_eingebettet=eingebettet,
                )
                # Derselbe Post kann mehrfach in einer Antwort stehen
                # (angepinnt UND als regulaerer Eintrag, oder zusaetzlich
                # als Zitat) — die Fundstelle mit Feed-Position gewinnt.
                alt = posts.get(pid)
                if alt is None or (not hat_feed_position(alt)
                                   and hat_feed_position(neu)):
                    if alt is not None:
                        neu.text = alt.text  # note_tweet-Volltext behalten
                    posts[pid] = neu
        # note_tweet (lange Posts): voller Text liegt separat
        note = knoten.get("note_tweet")
        if isinstance(note, dict):
            try:
                pid = int(knoten.get("rest_id") or 0)
            except (TypeError, ValueError):
                pid = 0
            nt = (((note.get("note_tweet_results") or {}).get("result") or {})
                  .get("text"))
            if pid in posts and nt:
                posts[pid].text = str(nt)
        for schluessel, v in knoten.items():
            if isinstance(v, (dict, list)):
                _walk(v, angepinnt,
                      eingebettet or schluessel in EINGEBETTET_UNTER)

    _walk(antwort)
    return sorted(posts.values(), key=lambda p: -p.post_id)


class _TxnIdManager:
    """Erzeugt x-client-transaction-id-Header (X-Anti-Bot).

    Ohne diesen Header liefern UserTweetsAndReplies und SearchTimeline
    404 (Befund 13.7.); nur UserTweets ist ausgenommen. Der Header wird
    aus der Home-Seite + ondemand-Datei berechnet (SVG-Animationsframes);
    X rotiert diese Daten -> periodischer Neuaufbau. Schlaegt der Aufbau
    fehl (Lib fehlt oder Algorithmus gedreht), liefert txn() None und der
    Watcher faellt auf UserTweets (ohne Replies) zurueck.
    """

    NEUAUFBAU_S = 2400.0  # alle 40 min neu bauen

    def __init__(self, ua: str) -> None:
        self._ua = ua
        self._ct = None
        self._gebaut_um = 0.0
        self._fehler: str | None = None

    def _baue(self) -> None:
        import time as _t

        import requests
        from bs4 import BeautifulSoup
        from x_client_transaction import ClientTransaction
        from x_client_transaction.utils import (
            get_ondemand_file_url,
            handle_x_migration,
        )

        # Retry: der Home-/ondemand-Abruf haengt am selben X-Edge wie die
        # API und wird beim Start (parallel zum Startscan) gern gedrosselt.
        # Ein einmaliger Fehlschlag degradierte sonst die Reply-Abdeckung
        # (Befund 16.7.: 2 Neustarts blieben ohne Fremd-Replies).
        letzter: Exception | None = None
        for versuch in range(3):
            try:
                sess = requests.Session()
                sess.headers.update({"User-Agent": self._ua})
                home = handle_x_migration(sess)
                ond = BeautifulSoup(
                    sess.get(get_ondemand_file_url(home), timeout=15).text,
                    "html.parser")
                self._ct = ClientTransaction(home, ond)
                return
            except Exception as ex:  # noqa: BLE001 - bis zu 3 Versuche
                letzter = ex
                if versuch < 2:
                    _t.sleep(2.0)
        raise letzter if letzter else RuntimeError("tid-Build fehlgeschlagen")

    def txn(self, method: str, path: str) -> str | None:
        import time as _t

        if self._ct is None or _t.time() - self._gebaut_um > self.NEUAUFBAU_S:
            try:
                self._baue()
                self._gebaut_um = _t.time()
                self._fehler = None
            except Exception as ex:  # noqa: BLE001 - Fallback greift
                self._fehler = str(ex)[:200]
                if self._ct is None:
                    return None
        try:
            return self._ct.generate_transaction_id(method=method, path=path)
        except Exception as ex:  # noqa: BLE001
            self._fehler = str(ex)[:200]
            return None


class XWatcher:
    """Pollt @elonmusk-Timeline via Web-GraphQL.

    Primaer UserTweetsAndReplies (mit transaction-id -> enthaelt auch
    Elons Replies an fremde Accounts); Fallback UserTweets (kein
    transaction-id noetig, aber ohne Fremd-Replies)."""

    def __init__(self, auth_token: str, ct0: str,
                 user_id: str = ELON_USER_ID) -> None:
        self.user_id = user_id
        self._ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36")
        self._headers = {
            "User-Agent": self._ua,
            "Authorization": "Bearer " + WEB_BEARER,
            "x-csrf-token": ct0,
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-active-user": "yes",
            "content-type": "application/json",
        }
        self._cookies = {"auth_token": auth_token, "ct0": ct0}
        self._features: dict[str, bool] = {}
        self._query: tuple[str, str] | None = None
        self.letzter_fehler: str | None = None
        # Ratelimit je Query (Befund 13.7.): UserTweetsAndReplies 500/15min,
        # UserTweets nur 50/15min. Nach jedem Call gesetzt; der Aufrufer
        # pact budgetbewusst (nie ins 429).
        self.rate_remaining: int | None = None
        self.rate_reset: int | None = None
        self._txn = _TxnIdManager(self._ua)
        # Live-qids aus dem main-Bundle; UserTweetsAndReplies zuerst
        # (Reply-Abdeckung), dann UserTweets (immer geroutet).
        live = {}
        try:
            live = aktuelle_query_ids()
        except Exception:  # noqa: BLE001 - Fallback greift
            live = {}
        # Kandidaten strikt in Prioritaet: ERST alle UserTweetsAndReplies
        # (live-qid + UTAR-Fallbacks), DANN UserTweets. So wird UTAR immer
        # zuerst probiert — auch wenn der main.js-Parse die UTAR-qid mal
        # nicht liefert (sonst gewinnt UserTweets und die Reply-Abdeckung
        # heilt nie, Befund 16.7.).
        self._kandidaten: list[tuple[str, str]] = []

        def _add(op: str, qid: str | None) -> None:
            if qid and (op, qid) not in self._kandidaten:
                self._kandidaten.append((op, qid))

        _add("UserTweetsAndReplies", live.get("UserTweetsAndReplies"))
        for op, qid in FALLBACK_QUERY_IDS:
            if op == "UserTweetsAndReplies":
                _add(op, qid)
        _add("UserTweets", live.get("UserTweets"))
        for op, qid in FALLBACK_QUERY_IDS:
            if op == "UserTweets":
                _add(op, qid)

    @property
    def reply_abdeckung(self) -> bool:
        """True, wenn die aktive Query Fremd-Replies liefert."""
        return bool(self._query and self._query[0] == "UserTweetsAndReplies")

    def _rufe(self, name: str, qid: str, cursor: str | None = None) -> "object":
        import httpx

        variablen = {
            "userId": self.user_id, "count": 40,
            "includePromotedContent": False,
            "withCommunity": True, "withVoice": False,
            "withQuickPromoteEligibilityTweetFields": False,
            "withV2Timeline": True,
        }
        if cursor:
            variablen["cursor"] = cursor
        pfad = f"/i/api/graphql/{qid}/{name}"
        kopf = dict(self._headers)
        # UserTweets ist ohne transaction-id geroutet; die anderen Ops
        # brauchen ihn zwingend (sonst 404).
        if name != "UserTweets":
            tid = self._txn.txn("GET", pfad)
            if tid is None:
                # Kein Header baubar -> diese Op ueberspringen (404-sicher).
                raise _KeinTxnId(name)
            kopf["x-client-transaction-id"] = tid
        url = (f"https://x.com{pfad}"
               f"?variables={urllib.parse.quote(json.dumps(variablen))}"
               f"&features={urllib.parse.quote(json.dumps(self._features))}")
        # 12s statt 20s: die Timeline-Antwort (~500KB) kommt normal in <1s;
        # 12s trennt echte Haenger schneller ab (kuerzeres Blindfenster).
        return httpx.get(url, headers=kopf, cookies=self._cookies,
                         timeout=httpx.Timeout(12.0, connect=8.0))

    def hole_posts(
        self, cursor: str | None = None
    ) -> tuple[list[XPost], str | None]:
        """(Posts, Bottom-Cursor); wirft bei Auth-/Netzfehlern.

        429 wird als eigener Fehlertyp gemeldet (Aufrufer soll backoffen),
        401/403 deuten auf abgelaufene Cookies.
        """
        # Immer in Prioritaetsreihenfolge (UserTweetsAndReplies zuerst):
        # so heilt sich die Reply-Abdeckung selbst, sobald eine transiente
        # transaction-id-Stoerung vorbei ist — statt dauerhaft auf
        # UserTweets haengenzubleiben (Befund 16.7.: tid schlug beim
        # Neustart einmal fehl -> Bot blieb ohne Fremd-Replies). Kostet
        # nichts: bei kaputtem tid wirft UTAR _KeinTxnId OHNE HTTP-Call,
        # dann pollt UserTweets. self._query bleibt nur Feature-Flag-Merker.
        kandidaten = list(self._kandidaten)
        letzte = ""
        for name, qid in kandidaten:
            for _ in range(8):  # Feature-Flags iterativ ergaenzen
                try:
                    r = self._rufe(name, qid, cursor)
                except _KeinTxnId:
                    # transaction-id nicht baubar -> Op ueberspringen,
                    # naechster Kandidat (i.d.R. UserTweets ohne Replies).
                    letzte = f"{name}: kein transaction-id"
                    break
                try:
                    if "x-rate-limit-remaining" in r.headers:
                        self.rate_remaining = int(
                            r.headers["x-rate-limit-remaining"])
                    if "x-rate-limit-reset" in r.headers:
                        self.rate_reset = int(r.headers["x-rate-limit-reset"])
                except (TypeError, ValueError):
                    pass
                if r.status_code == 200:
                    daten = r.json()
                    fehler = daten.get("errors") or []
                    fehlend = []
                    for f in fehler:
                        fehlend += re.findall(
                            r"cannot be null: ([\w, ]+)", str(f.get("message")))
                    if fehlend:
                        for grp in fehlend:
                            for f in grp.split(","):
                                self._features[f.strip()] = False
                        continue
                    self._query = (name, qid)
                    self.letzter_fehler = None
                    m = re.search(
                        r'"cursorType"\s*:\s*"Bottom"[^}]*?"value"\s*:\s*"([^"]+)"',
                        r.text) or re.search(
                        r'"value"\s*:\s*"([^"]+)"[^}]*?"cursorType"\s*:\s*"Bottom"',
                        r.text)
                    return parse_timeline(daten, self.user_id), (
                        m.group(1) if m else None)
                if r.status_code == 429:
                    raise RateLimit(f"{name}: HTTP 429")
                if r.status_code in (401, 403):
                    raise AuthFehler(f"{name}: HTTP {r.status_code} "
                                     f"{r.text[:120]}")
                if r.status_code == 400:  # meist Feature-Flags
                    fehlend = re.findall(r"cannot be null: ([\w, ]+)", r.text)
                    if fehlend:
                        for grp in fehlend:
                            for f in grp.split(","):
                                self._features[f.strip()] = False
                        continue
                letzte = f"{name}/{qid}: HTTP {r.status_code} {r.text[:120]}"
                break
        self.letzter_fehler = letzte or "keine QueryId funktionierte"
        raise RuntimeError(self.letzter_fehler)


class RateLimit(RuntimeError):
    pass


class AuthFehler(RuntimeError):
    pass


class _KeinTxnId(RuntimeError):
    """transaction-id fuer eine tid-pflichtige Op nicht baubar."""


# Apify-Actor fuer den Reply-Kanal: liefert ueber die Twitter-Advanced-
# Search-Syntax auch Elons Replies an fremde Accounts (Luecke des nativen
# UserTweets-Feeds). $0.00025/Tweet.
APIFY_ACTOR = "kaitoeasyapi~twitter-x-data-tweet-scraper-pay-per-result-cheapest"


class ApifyReplyFetcher:
    """Holt Elons Posts+Replies via Apify-Search (nur mit APIFY_TOKEN).

    Ergaenzt den nativen Feed um Replies an fremde Accounts. Laeuft
    seltener (Kosten/Latenz) und liefert dieselben XPost-Objekte.
    """

    def __init__(self, token: str, user_id: str = ELON_USER_ID,
                 handle: str = "elonmusk") -> None:
        self.token = token
        self.user_id = user_id
        self.handle = handle

    def hole(self, since_unix: int, until_unix: int,
             max_items: int = 100) -> list[XPost]:
        import httpx

        query = (f"from:{self.handle} filter:replies "
                 f"since_time:{since_unix} until_time:{until_unix}")
        payload = {
            "twitterContent": query,
            "maxItems": max(20, max_items),
            "queryType": "Latest",
        }
        r = httpx.post(
            f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items",
            params={"token": self.token, "timeout": 120},
            json=payload, timeout=180,
        )
        r.raise_for_status()
        posts: list[XPost] = []
        for it in r.json():
            posts.append(_apify_zu_xpost(it, self.user_id))
        return [p for p in posts if p is not None]


def _apify_zu_xpost(it: dict, user_id: str) -> "XPost | None":
    """Ein Apify-Dataset-Item in ein XPost uebersetzen (defensiv)."""
    from datetime import datetime, timezone

    autor = it.get("author") or {}
    if str(autor.get("id") or it.get("author_id") or "") not in ("", user_id):
        # Fremde Autoren (z.B. Konversationspartner) ignorieren.
        if str(autor.get("id")) != user_id:
            return None
    try:
        pid = int(it.get("id") or it.get("id_str") or it.get("tweetId"))
    except (TypeError, ValueError):
        return None
    text = str(it.get("text") or it.get("full_text") or it.get("fullText") or "")
    created = it.get("createdAt") or it.get("created_at")
    iso = _snowflake_utc(pid)
    if created:
        for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%dT%H:%M:%S.%fZ",
                    "%Y-%m-%dT%H:%M:%SZ"):
            try:
                iso = datetime.strptime(created, fmt).astimezone(
                    timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                break
            except (TypeError, ValueError):
                continue
    ist_rt = bool(it.get("isRetweet") or str(text).startswith("RT @"))
    return XPost(
        post_id=pid, text=text, created_utc=iso,
        ist_repost=ist_rt, ist_reply=bool(it.get("isReply")
                                          or it.get("inReplyToId")),
        hat_medien=bool(it.get("media") or it.get("extendedEntities")),
    )
