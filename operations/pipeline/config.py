"""Konfiguration des All-In Live-Bots (privates Projekt, Dry-Run-Standard)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STOP_FILE = REPO_ROOT / "data" / "live" / "STOP"

# ---------------------------------------------------------------- Profile
# Ein Profil je Event/Show. Umschalten ueber PROFIL.
PROFILE = {
    "allin_july3": {
        "live_dir": "allin_july3",
        "event_id": "652614",
        "event_slug": "what-will-be-said-on-the-next-all-in-podcast-july-3-20260630164419941",
        "rss_feed_url": "https://allinchamathjason.libsyn.com/rss",
        "yt_channel_id": "UCESLZhusAkFfsNsApnjF_Cg",  # All-In Podcast
        # Hauptepisoden-Muster stabil (E276-E279) -> Prober aktiv
        "mp3_probe_muster": (
            "https://traffic.libsyn.com/secure/allinchamathjason/ALLIN-E{n}_Ch.mp3"
        ),
        "discovery_slug_filter": "all-in",
    },
    "jre_july6": {
        "live_dir": "jre_july6",
        "event_id": "659934",
        "event_slug": "what-will-be-said-on-the-first-joe-rogan-experience-episode-of-the-week-july-6-20260702150712902",
        # Megaphone-Feed; MP3-Namen sind zufaellig (GLT<10 Ziffern>.mp3),
        # daher KEIN URL-Prober. Referenzquelle laut Marktbeschreibung ist
        # YouTube (@joerogan); beim JRE-Trump-Fall lag YouTube ~40 Min. vor
        # dem RSS-pubDate -> YouTube ist Primaerquelle.
        "rss_feed_url": "https://feeds.megaphone.fm/GLT1412515089",
        "yt_channel_id": "UCzQUP1qoWDoEbmsQxvdjxgQ",  # PowerfulJRE
        "mp3_probe_muster": None,
        "discovery_slug_filter": "joe-rogan-experience",
    },
}

PROFIL = "jre_july6"
_P = PROFILE[PROFIL]

LIVE_DIR = REPO_ROOT / "data" / "live" / _P["live_dir"]
GAMMA_SNAPSHOT = LIVE_DIR / "gamma_event_snapshot.json"
EVENT_ID = _P["event_id"]
EVENT_SLUG = _P["event_slug"]
RSS_FEED_URL = _P["rss_feed_url"]
DISCOVERY_SLUG_FILTER = _P["discovery_slug_filter"]

GAMMA_EVENT_URL = f"https://gamma-api.polymarket.com/events/{EVENT_ID}"
CLOB_BOOK_URL = "https://clob.polymarket.com/book"
CLOB_HOST = "https://clob.polymarket.com"
CHAIN_ID = 137

HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# Entscheidungs- und Risikoparameter
ASK_OBERGRENZE = 0.90          # Kaeufe bis 90 Cent (User-Vorgabe 2026-07-04)
YES_SCHWELLE_PUFFER = 2        # YES ab Zaehler >= Schwelle + Puffer
NO_ANTEIL = 0.7               # NO nur wenn Endstand <= 70% der Schwelle
ASR_KONFIDENZ_HOMOPHON = 0.8  # Homophon-Treffer nur ab Konfidenz > 0.8

# Level-Sweep: je Markt wiederholte FAK-Clips von 15 USD, solange der
# beste Ask <= ASK_OBERGRENZE liegt (duenne Level nacheinander abraeumen).
# Kein Pro-Markt-Limit mehr; harte Grenze ist der Gesamtpool.
MAX_USD_PRO_MARKT = 15.0       # Clip-Groesse je Einzelorder
MAX_CLIPS_PRO_MARKT = 10       # Sicherheitsgrenze gegen Endlos-Sweep
MAX_USD_GESAMT = 130.0         # Deposit-Wallet-Guthaben als Pool (nach Tourism-Payout)
MAX_NACHBESSERUNGEN = 1

# 20s-Chunks: YES-Entscheidungen fallen pro Chunk (nicht erst am Ende).
# Mit GPU-Transkription (~1-2s je Chunk) dominiert die Chunk-Grenze die
# Latenz, daher kurze Chunks.
CHUNK_SEKUNDEN = 20
RSS_POLL_S = 15

# Chunk-Ueberlappung gegen an der Grenze zerschnittene Woerter; Dedup
# ueber Wort-Zeitstempel (nur Woerter ab der Chunk-Grenze zaehlen).
OVERLAP_S = 2.0

# MP3-URL-Prober (nur wenn das Profil ein vorhersagbares Muster hat).
# Lehre aus E279: pubDate 22:12, Feed-Sichtbarkeit erst 23:21 (Feed-Cache).
MP3_PROBE_MUSTER = _P["mp3_probe_muster"]
PROBER_POLL_S = 5

# YouTube-Watcher: Kanal aus dem Profil, nur Voll-Episoden (keine Clips,
# keine Livestreams).
YT_CHANNEL_ID = _P["yt_channel_id"]
YT_FEED_URL = (
    "https://www.youtube.com/feeds/videos.xml?channel_id=" + YT_CHANNEL_ID
)
YT_MIN_DAUER_S = 1800  # unter 30 Minuten = Clip, kein Episoden-Drop
BUCH_LOG_INTERVALL_S = 120

# Homophon-anfaellige Begriffe (Basisform, kleingeschrieben). Treffer auf
# diese Begriffe zaehlen nur bei ASR-Konfidenz oberhalb ASR_KONFIDENZ_HOMOPHON.
HOMOPHON_BEGRIFFE = {"red", "read", "blue", "blew", "right", "write"}

# Bekannte Wortvarianten je Basisbegriff (kleingeschrieben).
VARIANTEN_MAP = {
    "ai": ["AI", "A.I.", "artificial intelligence"],
    "artificial intelligence": ["artificial intelligence", "AI", "A.I."],
    "elon": ["Elon", "Elon Musk"],
    "musk": ["Musk"],
}
