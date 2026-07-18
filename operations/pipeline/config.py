"""Konfiguration des All-In Live-Bots (privates Projekt, Dry-Run-Standard)."""

from __future__ import annotations

import os as _os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STOP_FILE = REPO_ROOT / "data" / "live" / "STOP"

# Woerter aus dem FESTEN Intro/Outro-Rahmen der All-In-Show (laeuft in
# jeder Episode; belegt via YT-Captions E280+E281 und large-v3-Transkript
# des E281-Outros, 18.07.). Outro-Montage: "we'll let your winners ride /
# we open sourced it to the fans and they've just gone crazy with it /
# love you / queen of quinoa / your besties are gone / that's my dog
# taking a <notion> in your driveway / we should all just get a room and
# just have one big huge orgy because they're all just useless / it's
# like this like sexual tension that they just need to release somehow".
# Ein Schwelle-1-Markt auf so ein Wort loest praktisch sicher YES auf
# (E281-Praezedenz: Resolver zaehlte das Outro) -> NIE NO kaufen.
# Grosszuegig kuratiert: die Liste blockt NUR NO-Kaeufe; ein zu viel
# gelistetes Wort kostet hoechstens eine NO-Chance, die verloren haette.
ALLIN_BOILERPLATE = [
    "winner", "winners", "ride", "fan", "fans", "crazy", "love", "queen",
    "quinoa", "bestie", "besties", "gone", "dog", "driveway", "driveways",
    "open", "room", "big", "huge", "orgy", "useless", "sexual", "tension",
    "release", "somehow",
]

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
        "boilerplate_begriffe": ALLIN_BOILERPLATE,
        "serie_id": "11300",
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
    "allin_july10": {
        "live_dir": "allin_july10",
        "event_id": "678491",
        "event_slug": "what-will-be-said-on-the-next-all-in-podcast-july-10-20260707174212413",
        "rss_feed_url": "https://allinchamathjason.libsyn.com/rss",
        "yt_channel_id": "UCESLZhusAkFfsNsApnjF_Cg",
        "mp3_probe_muster": (
            "https://traffic.libsyn.com/secure/allinchamathjason/ALLIN-E{n}_Ch.mp3"
        ),
        "discovery_slug_filter": "all-in",
        "boilerplate_begriffe": ALLIN_BOILERPLATE,
        "serie_id": "11300",
        "max_usd_gesamt": 90.0,
        # Marktregel july-10: nur Episoden der offiziellen Playlist zaehlen
        # (Specials nicht). Lehre aus dem Cerebras/BFL-Fehltrigger 10.7.
        "yt_playlist_id": "PLn5MTSAqaf8peDZQ57QkJBzewJU1aUokl",
        # RSS/Feed: nur Hauptepisoden (ALLIN-E<n>) als Drop akzeptieren.
        "rss_nur_muster": r"ALLIN-E\d+_Ch\.mp3",
    },
    "mrbeast": {
        "live_dir": "mrbeast_next",
        "event_id": "662694",
        "event_slug": "what-will-mrbeast-say-during-his-next-youtube-video-20260702154826471",
        # Kein Podcast-Feed; Quelle ist ausschliesslich der YouTube-Kanal.
        # ACHTUNG Regelwerk: Es zaehlt nur, was MrBeast SELBST sagt. Ohne
        # Sprecher-Diarisierung zaehlt unser Zaehler alle Stimmen ->
        # systematisches Fehlkauf-Risiko. Profil nur bewusst scharf machen.
        "rss_feed_url": None,
        "yt_channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",  # MrBeast Hauptkanal
        "mp3_probe_muster": None,
        # Disjunkt zum Gaming-Event: "mrbeast" allein matcht auch
        # "...mrbeast-say-during-his-next-gaming..." -> Auto-Discovery
        # koennte sonst das falsche Event uebernehmen.
        "discovery_slug_filter": "mrbeast-say-during-his-next-youtube",
        "yt_min_dauer_s": 300,  # Hauptvideos 10-25 Min.; Shorts ausschliessen
        "max_usd_gesamt": 30.0,
        # Sprecher-Verifikation: YES nur aus MrBeast-zugerechneten Treffern.
        "zielsprecher_referenz": "data/live/mrbeast_next/referenz_stimme.npy",
    },
    "allin_july17": {
        "live_dir": "allin_july17",
        "event_id": "700931",
        "event_slug": "what-will-be-said-on-the-next-all-in-podcast-july-17",
        "rss_feed_url": "https://allinchamathjason.libsyn.com/rss",
        "yt_channel_id": "UCESLZhusAkFfsNsApnjF_Cg",
        # Prober-Muster stabil bis E280 -> naechste E281 (bewiesener Edge,
        # E280 gewann alle Fills). Direkte traffic.libsyn.com-URL.
        "mp3_probe_muster": (
            "https://traffic.libsyn.com/secure/allinchamathjason/"
            "ALLIN-E{n}_Ch.mp3"
        ),
        "discovery_slug_filter": "all-in",
        "boilerplate_begriffe": ALLIN_BOILERPLATE,
        "serie_id": "11300",
        # Voller Wallet-Pool (420.44 pUSD, 16.7.): 400 nutzbar, ~20 Puffer
        # fuer Fees/Parallel-Bots. All-In = groesster Edge -> volle Groesse.
        "max_usd_gesamt": 400.0,
        # Buch KOMPLETT bis 0.90 abraeumen, nicht bei 150 gedeckelt:
        # grosse 50-USD-FAK-Clips, bis zu 40 Clips -> effektiv budget-
        # limitiert. Gilt fuer YES UND NO (beide ueber denselben Sweep).
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
        "yt_playlist_id": "PLn5MTSAqaf8peDZQ57QkJBzewJU1aUokl",
        "rss_nur_muster": r"ALLIN-E\d+_Ch\.mp3",
    },
    "mrbeast_gaming": {
        "live_dir": "mrbeast_gaming",
        "event_id": "700921",
        "event_slug": (
            "what-will-mrbeast-say-during-his-next-gaming-youtube-video-"
            "20260713152829391"
        ),
        # Nur YouTube (@MrBeastGaming = EIGENER Kanal, NICHT der Hauptkanal
        # UCX6O...). Video-Pfad (Voll-Download), kein Feed/Prober.
        "rss_feed_url": None,
        "yt_channel_id": "UCIPPMRA040LQr5QPyJEbmXA",
        "mp3_probe_muster": None,
        # "gaming" allein waere zu breit (jedes fremde Gaming-Event);
        # disjunkt zum Hauptkanal-Filter (siehe Test).
        "discovery_slug_filter": "mrbeast-say-during-his-next-gaming",
        # Gaming-Videos 18-33 Min; 900s-Gate schliesst Shorts/Previews aus
        # (Marktregel: "Shorts, previews ... will not be considered").
        "yt_min_dauer_s": 900,
        # Armierung 18.07. abends (User: gesamtes Wallet freigegeben):
        # Wallet 530.28 pUSD -> 510 Pool, ~20 Puffer fuer Fees und
        # parallele Elon-Kaeufe (Wallet-Delta-Sync verhindert Ueberziehen).
        # Buch-Sweep wie All-In: grosse Clips, budget- statt clip-limitiert.
        "max_usd_gesamt": 510.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
        # Basisraten: Gamma-Serie mrbeast-gaming-mentions, 3 aufgeloeste
        # Vorwochen (562285/598836/647933, je 21-23 Maerkte) -> min_n auf 3
        # gesenkt, damit die Schicht wirkt; Veto sperrt dann 3/3-Woerter.
        # KEIN Boilerplate-Lexikon: Captions-Check 18.07. (Traitors- und
        # Minecraft-Video) — Videos starten direkt in der Praemisse und
        # enden im Content, kein fester Intro/Outro-Rahmen.
        "serie_id": "11933",
        "basisrate_min_n": 3,
        # SPRECHER-VERIFIKATION ZWINGEND: Marktregel wertet nur, was
        # MrBeast SELBST sagt — die Crew (Chandler/Karl/Darius sind sogar
        # Marktwoerter!) redet viel. YES nur aus MrBeast-zugerechneten
        # Treffern (ziel_count), NO aus dem Gesamtzaehler. Eigene
        # Referenz-Kopie (nicht der mrbeast-Pfad) -> Profil unabhaengig,
        # selbe MrBeast-Stimme.
        "zielsprecher_referenz": "data/live/mrbeast_gaming/referenz_stimme.npy",
        # Kalibriert 16.7. an "10 YouTubers vs 2 Traitors" (Hauptkanal-
        # Referenz auf Gaming-Audio): eindeutige MrBeast-Narration scort
        # 0.52-0.64, Crew <=0.35, ein grenzwertiges Segment bei 0.40.
        # Schwelle daher auf 0.50 angehoben (Standard 0.40): bei Schwelle-1-
        # Maerkten ist ein einziger Fehl-Treffer ein Falschkauf -> Praezision
        # vor Recall. Kosten: Undercount (schnelle Gameplay-Aussagen fallen
        # raus) — aber verpasster YES = kein Verlust, NO nutzt Gesamtzaehler.
        "sprecher_schwelle": 0.50,
    },
    "elon_july13": {
        "live_dir": "elon_july13",
        "event_id": "690237",
        "event_slug": (
            "what-will-elon-post-this-week-july-13-july-19-20260710174050678"
        ),
        # Kein Audio: Quelle sind X-Posts von @elonmusk (x_watch.py,
        # GraphQL-Web-Pfad mit Login-Cookies X_AUTH_TOKEN/X_CT0 aus .env).
        # Eigenes Skript elon_bot.py; die Audio-Felder bleiben leer.
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "what-will-elon-post",
        "max_usd_gesamt": 170.0,
        # Marktregeln (Event 690237, alle Schwelle 1):
        # - zaehlt: eigene Posts, Replies, EIGENER Text von Quote-Posts;
        #   NICHT: Reposts und der zitierte Fremdtext.
        # - Plural/Possessiv/Case zaehlen; andere Formen NICHT;
        #   Misspellings/Streckungen (Teslaaa) zaehlen NICHT;
        #   Symbole IM Wort (T3sla) disqualifizieren; Sigils davor
        #   (#/@/$) sind ok; Compounds zaehlen (killjoy fuer joy).
        # - Bildtext zaehlt nur klar ausgeschrieben (kein Auto-Trade,
        #   nur Hinweis-Event).
        # - Zeitraum 13.7. 00:00 ET bis 19.7. 23:59 ET.
        # NUR YES handeln (User-Vorgabe 13.7.): NO konvergiert die ganze
        # Woche gegen 1 — kein Geschwindigkeits-Edge auf der NO-Seite.
        "x_user_id": "44196397",  # @elonmusk (verifizierter Account)
        # Exakter Text-Match auf verifiziertem Account, keine ASR ->
        # sehr zuverlaessig. Deckel 0.97-0.03 = 0.94 (Rest-Risiko:
        # Quote- vs. Eigen-Text, Bild-Text ohne OCR, Regel-Randfaelle).
        "p_win": 0.97,
        "min_edge": 0.03,
        "periode_start_utc": "2026-07-13T04:00:00Z",  # 00:00 ET
        "periode_ende_utc": "2026-07-20T03:59:59Z",   # 19.7. 23:59 ET
        # UserTweetsAndReplies-Limit je 15-min-Fenster. Empirie 15.7.: der
        # 5s-Poll erschoepfte es regelmaessig (-> 10-Min-Blackouts, Texas-
        # Post verpasst). 8s (112/15min) gibt strukturelle Reserve; das
        # adaptive Pacing in elon_bot streckt bei Bedarf zusaetzlich, ohne
        # je zu blacken. Latenz 8s ist fuer einen Wochen-Markt egal.
        "x_poll_s": 8.0,
    },
    "trump_july13": {
        "live_dir": "trump_july13",
        "event_id": "690224",
        "event_slug": (
            "what-will-trump-post-this-week-july-13-july-19-"
            "20260710160104810"
        ),
        # Kein Audio: Quelle ist die oeffentliche Truth-Social-API von
        # @realDonaldTrump (truth_watch.py, curl_cffi-Chrome-Impersonation
        # gegen Cloudflare — der 403-Befund vom 16.07. ist damit geloest,
        # kein Login/Apify noetig). Eigenes Skript trump_bot.py.
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "what-will-trump-post",
        # Marktregeln (Event 690224, Serie trump-post-weekly, 11341):
        # wortgleich zur Elon-Serie — Plural/Possessiv/Case/Sigils
        # zaehlen, Compounds zaehlen, Misspellings/Symbole-im-Wort nicht,
        # ReTruths und zitierter Fremdtext nicht, eigener Text in
        # Quotes/Replies schon, Bildtext nur klar ausgeschrieben (kein
        # OCR -> nur medien_hinweis). NUR YES (wie Elon: NO konvergiert
        # die ganze Woche gegen 1, kein Speed-Edge).
        "x_user_id": None,
        "truth_user_id": "107780257626128497",  # @realDonaldTrump
        # 429-Befund 18.07.: Cloudflare drosselt schnelle Folgen ->
        # 15s-Poll (Wochen-Markt, Latenz sekundaer) + Backoff im Bot.
        "truth_poll_s": 15.0,
        # Text-Match auf verifiziertem Account, wie Elon: p_win 0.97
        # -> ASK_OBERGRENZE 0.94.
        "p_win": 0.97,
        "min_edge": 0.03,
        "periode_start_utc": "2026-07-13T04:00:00Z",  # 13.7. 00:00 ET
        "periode_ende_utc": "2026-07-20T03:59:59Z",   # 19.7. 23:59 ET
        # Geteiltes Wallet (530.28 pUSD, 18.07.): Vollpool-Prinzip wie
        # mrbeast_gaming; der Wallet-Delta-Sync des Executors verhindert
        # Ueberziehen bei parallelen Bots (first-come-first-served).
        "max_usd_gesamt": 510.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
    },
    "jre_july13": {
        "live_dir": "jre_july13",
        "event_id": "678516",
        "event_slug": (
            "what-will-be-said-on-the-first-joe-rogan-experience-episode-"
            "of-the-week-july-13-20260707144311074"
        ),
        # Megaphone-Feed, MP3-Namen zufaellig (GLT<10 Ziffern>) -> kein
        # Prober. YouTube ist Primaerquelle (JRE-Trump-Fall: YT ~40 Min.
        # vor RSS-pubDate; Feed-Drops historisch ~17:00 UTC Di-Fr).
        "rss_feed_url": "https://feeds.megaphone.fm/GLT1412515089",
        "yt_channel_id": "UCzQUP1qoWDoEbmsQxvdjxgQ",  # PowerfulJRE
        "mp3_probe_muster": None,
        "discovery_slug_filter": "joe-rogan-experience",
        "max_usd_gesamt": 100.0,
        # Marktregel july-13: "JRE MMA Show episodes will not count for
        # this market, only Joe Rogan Experience episodes." Hauptepisoden
        # heissen im RSS "#2524 - Gast", auf YouTube "Joe Rogan
        # Experience #2524 - Gast" -> Pflichtmuster deckt beide Formate.
        # MMA-Shows tragen ebenfalls "#<n> -" im Titel ("JRE MMA Show
        # #182 - ...") -> zusaetzliches Verbotsmuster. Fight Companion /
        # JRE Toon haben keine #<n>-Nummer und scheitern am Pflichtmuster.
        "titel_muster": r"(?:joe rogan experience\s*)?#\d{3,5}\s*-",
        "titel_verboten": r"mma\s*show",
        "yt_kanalseite_immer": True,
    },
    "lemonade_july15": {
        "live_dir": "lemonade_july15",
        "event_id": "686210",
        "event_slug": (
            "what-will-be-said-on-the-next-lemonade-stand-podcast-"
            "july-15-20260709163957166"
        ),
        # Vox/Megaphone-Feed (nur Hauptepisoden, woechentlich Mi ~19:00 UTC;
        # pubDate historisch teils +15-115 Min. verspaetet). MP3-Namen sind
        # zufaellig (VMP<10 Ziffern>) -> KEIN URL-Prober, wie bei JRE.
        "rss_feed_url": "https://feeds.megaphone.fm/VMP5629614579",
        # ACHTUNG zwei Kanaele (Befund 13.7.): @LemonadeStandPodcast =
        # UCwVevVbti5Uuxj6Mkl5NHRA (Hauptepisoden, RESOLUTIONSQUELLE laut
        # Marktregel); @LemonadeStandClips = UCurXaZAZPKtl8EgH1ymuZgg
        # (Daily-Clips, irrelevant). Nur der Podcast-Kanal wird beobachtet.
        "yt_channel_id": "UCwVevVbti5Uuxj6Mkl5NHRA",  # @LemonadeStandPodcast
        "mp3_probe_muster": None,
        "discovery_slug_filter": "lemonade-stand",
        # Voller Pool: Wallet 178.54 pUSD (E280-Gewinne, Elon 0 gebunden),
        # 175 = fast alles nutzbar, ~3.5 Fee-/Rundungspuffer. Der Executor
        # deckelt zusaetzlich am echten Wallet-Stand (Wallet-Delta-Sync),
        # kann also nie ueberziehen — auch bei parallelem Elon-Bot.
        "max_usd_gesamt": 175.0,
        # Marktregel (Event 686210): JEDES Video des Kanals mit
        # "Lemonade Stand" im Titel qualifiziert ("mentioned by anyone",
        # keine Playlist, keine Sprecher-Verifikation). Das Titel-Muster
        # ist damit die Positiv-Identifikation fuer RSS- UND YT-Drops.
        "titel_muster": r"lemonade\s*stand",
        # Kanalseite /videos bei jedem Poll zusaetzlich zum XML-Feed lesen
        # (30s-Cache): Redundanz, falls der Feed nachhaengt oder 404 liefert.
        "yt_kanalseite_immer": True,
        # Hauptepisoden ~90 Min.; 900s Sanity-Gate gegen Trailer/Shorts,
        # laesst jede echte Episode durch.
        "yt_min_dauer_s": 900,
    },
}

PROFIL = _os.environ.get("BOT_PROFIL", "allin_july10")
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
# EV-Deckel je Profil statt global 0.90 (Analyse via sizing_analyse.py,
# 13.7.): kaufe nur, solange der Grenzgewinn je Share (p_win - preis)
# ueber EV_MIN_EDGE liegt. p_win = Fair Value nach Trigger (P(Seite
# loest auf | wir kauften)). Empirie: E279/E280 sauber, beide
# Fehltrigger waren Episoden-Bugs (jetzt gefixt), KEINE Wort-Fehl-
# transkriptionen -> Wort-Matching zuverlaessig. Konservativ: Audio
# bleibt bei 0.90 (p_win 0.93), Elon-Text hoeher (0.97 -> Deckel 0.94).
HARD_ASK_DECKEL = 0.97         # absolute Obergrenze, modellunabhaengig
EV_P_WIN = float(_P.get("p_win", 0.93))
EV_MIN_EDGE = float(_P.get("min_edge", 0.03))
ASK_OBERGRENZE = round(min(HARD_ASK_DECKEL, EV_P_WIN - EV_MIN_EDGE), 4)
# NO-Deckel NIEDRIGER als YES: YES kaufen wir auf einem GESEHENEN Wort
# (zuverlaessig), NO wetten wir auf die ABWESENHEIT — ein einziger
# ASR-Verpasser macht die NO falsch (E281 18.7.: "Tension" verpasst, NO
# @0.88 verloren). Nur billige NO (Puffer fuer gelegentliche Misses):
# NO@0.80 -> +EV bis ~20% Verpasserrate; NO@0.88 kippt schon bei ~12%.
NO_ASK_OBERGRENZE = float(_P.get("no_ask_obergrenze", 0.80))
YES_SCHWELLE_PUFFER = 2        # YES ab Zaehler >= Schwelle + Puffer
NO_ANTEIL = 0.7               # NO nur wenn Endstand <= 70% der Schwelle

# NO-Schutzschichten (Auftrag 18.07., nach dem Tension-Verlust E281):
# 1. Boilerplate-Lexikon: Woerter aus dem festen Intro/Outro der Show
#    (siehe ALLIN_BOILERPLATE) -> nie NO, das Wort faellt jede Woche.
# 2. Basisraten-Veto: Woerter, die laut Serien-Historie fast jede Woche
#    fallen (>= BASISRATE_VETO YES-Quote bei >= BASISRATE_MIN_N
#    aufgeloesten Wochen), werden bei Zaehlerstand 0 NICHT als NO
#    gekauft — ein 0-Zaehler bei einem Dauerbrenner ist eher unser
#    Messfehler als echte Abwesenheit (Beispiel: anthropic 16/16 YES).
# 3. Gap-Verify: VAD-verworfene Audio-Fenster (Musik/Jingles) vor der
#    NO-Runde ohne VAD nachtranskribieren. Modell MUSS large-v3 sein:
#    small fand das E281-Outro auch ohne VAD nur 0/3 Laeufen,
#    large-v3 2/2 (Messung 18.07.). Funde blocken nur NO, nie YES.
BOILERPLATE_BEGRIFFE = frozenset(
    str(w).lower() for w in _P.get("boilerplate_begriffe", []))
SERIE_ID = _P.get("serie_id")
BASISRATE_VETO = float(_P.get("basisrate_veto", 0.8))
BASISRATE_MIN_N = int(_P.get("basisrate_min_n", 4))
GAP_VERIFY_AKTIV = bool(_P.get("gap_verify_aktiv", True))
GAP_MIN_LUECKE_S = float(_P.get("gap_min_luecke_s", 15.0))
GAP_RAND_S = 5.0               # Fenster-Ueberlappung in die Abdeckung
GAP_MODELL = str(_P.get("gap_modell", "large-v3"))
ASR_KONFIDENZ_HOMOPHON = 0.8  # Homophon-Treffer nur ab Konfidenz > 0.8

# Level-Sweep: je Markt wiederholte FAK-Clips, solange der beste Ask
# <= ASK_OBERGRENZE liegt (duenne Level nacheinander abraeumen). Kein
# Pro-Markt-Notional-Limit; die harte Grenze ist der Gesamtpool.
# Clip-Groesse und Clip-Anzahl je Profil: All-In (groesster Edge, voller
# Pool) raeumt mit grossen Clips das ganze Buch bis 0.90 ab, budget-
# limitiert statt bei 10x15=150 gedeckelt.
MAX_USD_PRO_MARKT = float(_P.get("max_usd_pro_markt", 15.0))  # Clip-Groesse
MAX_CLIPS_PRO_MARKT = int(_P.get("max_clips_pro_markt", 10))  # Sweep-Obergrenze
MAX_USD_GESAMT = _P.get("max_usd_gesamt", 130.0)  # je Profil (Pool geteilt bei Parallelbetrieb)
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
    ("https://www.youtube.com/feeds/videos.xml?channel_id=" + YT_CHANNEL_ID)
    if YT_CHANNEL_ID else None
)
YT_MIN_DAUER_S = _P.get("yt_min_dauer_s", 1800)  # Clips ausschliessen, je Profil
_ziel_ref = _P.get("zielsprecher_referenz")
ZIELSPRECHER_REFERENZ = (REPO_ROOT / _ziel_ref) if _ziel_ref else None
# Similarity-Schwelle je Profil (Standard 0.40 aus speaker.py). Hoeher =
# praeziser (weniger Falsch-Zurechnung), niedriger Recall.
SPRECHER_SCHWELLE = float(_P.get("sprecher_schwelle", 0.40))
YT_PLAYLIST_ID = _P.get("yt_playlist_id")
RSS_NUR_MUSTER = _P.get("rss_nur_muster")
# Pflicht-Titel-Muster (case-insensitive) fuer RSS- und YouTube-Drops.
# Entspricht der Marktregel "Video mit '<Muster>' im Titel qualifiziert".
TITEL_MUSTER = _P.get("titel_muster")
# Verbots-Titel-Muster: Kandidat wird verworfen, wenn es matcht (z.B.
# JRE "MMA Show", die trotz #<n>-Nummer laut Marktregel nicht zaehlt).
TITEL_VERBOTEN = _P.get("titel_verboten")
# Kanalseite /videos bei jedem YT-Poll mitlesen (nicht nur als Fallback),
# wenn der XML-Feed die relevanten Videos nicht listet (Lemonade Stand).
YT_KANALSEITE_IMMER = _P.get("yt_kanalseite_immer", False)
BUCH_LOG_INTERVALL_S = 120

# Vorscan: Maerkte, deren YES-Ask zuletzt ueber der Obergrenze lag, werden
# im heissen Chunk-Pfad fuer einige Chunks nicht erneut gefetcht (spart
# 200-400ms je totem Markt und Chunk). Am Episodenende einmaliger Re-Check.
VORSCAN_PAUSE_CHUNKS = 15

# Elon-Post-Bot (Profil elon_july13): X-Feed-Parameter.
X_USER_ID = _P.get("x_user_id")
PERIODE_START_UTC = _P.get("periode_start_utc")
PERIODE_ENDE_UTC = _P.get("periode_ende_utc")
X_POLL_S = float(_P.get("x_poll_s", 16.0))

# Trump-Post-Bot (Serie trump-post-weekly): Truth-Social-Parameter.
# Kein Login noetig (curl_cffi-Chrome-Impersonation, Befund 18.07.);
# Poll konservativ, Cloudflare-Drosselung via Backoff im Bot.
TRUTH_USER_ID = _P.get("truth_user_id")
TRUTH_POLL_S = float(_P.get("truth_poll_s", 15.0))

# Nachlauf nach der NO-Runde: Market Maker ziehen beim Drop die Quotes
# und stellen sie erst Minuten spaeter wieder rein (JRE #2523: alle Asks
# gepullt, 0 Trades; E280: NOs wurden nach unserer Runde noch zu
# 0.50-0.70 gehandelt). Offene YES-/NO-Kandidaten werden deshalb noch
# NACHLAUF_MINUTEN lang alle NACHLAUF_POLL_S re-checkt und gekauft,
# sobald wieder ein Ask <= Obergrenze mit Liquiditaet da ist.
NACHLAUF_MINUTEN = 45
NACHLAUF_POLL_S = 90

# Homophon-anfaellige Begriffe (Basisform, kleingeschrieben). Treffer auf
# diese Begriffe zaehlen nur bei ASR-Konfidenz oberhalb ASR_KONFIDENZ_HOMOPHON.
HOMOPHON_BEGRIFFE = {"red", "read", "blue", "blew", "right", "write"}

# Bekannte Wortvarianten je Basisbegriff (kleingeschrieben).
# Event-Mentions-Contract (Polymarket-PDF, "Expanded Acronyms"): die
# Langform eines Akronyms zaehlt NICHT ("artificial intelligence" ist
# keine Erwaehnung von "AI") — Langformen zaehlen nur, wenn die Frage sie
# selbst zitiert (dann kommen sie als eigener Begriff herein). "A.I."
# bleibt als reine ASR-Schreibvariante desselben gesprochenen Worts.
VARIANTEN_MAP = {
    "ai": ["AI", "A.I."],
    "artificial intelligence": ["artificial intelligence"],
    "elon": ["Elon", "Elon Musk"],
    "musk": ["Musk"],
}
