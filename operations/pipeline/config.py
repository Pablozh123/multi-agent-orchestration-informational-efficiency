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

# Festes JRE-Intro-Jingle, laeuft musikunterlegt am Anfang JEDER Episode
# (per YT-Captions #2526 UND #2527 wortidentisch belegt, 18.07.):
# "Joe Rogan podcast. Check it out. / The Joe Rogan Experience. /
# TRAIN BY DAY. JOE ROGAN PODCAST BY NIGHT. All day." Kein festes Outro
# (beide Episoden enden im Gespraech). Gleiche Fallenklasse wie das
# All-In-Outro (Musik -> VAD-Drop moeglich, Resolver zaehlt trotzdem).
JRE_BOILERPLATE = [
    "joe", "rogan", "podcast", "check", "experience", "train", "day",
    "night", "all",
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
    "allin_july24": {
        "live_dir": "allin_july24",
        "event_id": "715508",
        "event_slug": (
            "what-will-be-said-on-the-next-all-in-podcast-july-24-"
            "20260717155813224"
        ),
        # E282-Woche (Drop Fr 24.07. ~22-23 UTC). Quellen wie july17:
        # Prober auf traffic.libsyn.com (Muster 23.07. verifiziert:
        # E281 HTTP 200 mit bekannter Laenge, E282 noch 404 -> Prober
        # feuert bei Minute 0), RSS nur ALLIN-E<n>-Hauptepisoden,
        # Playlist-Diff als Positiv-Identifikation, YT als Fallback.
        "rss_feed_url": "https://allinchamathjason.libsyn.com/rss",
        "yt_channel_id": "UCESLZhusAkFfsNsApnjF_Cg",
        "mp3_probe_muster": (
            "https://traffic.libsyn.com/secure/allinchamathjason/"
            "ALLIN-E{n}_Ch.mp3"
        ),
        "discovery_slug_filter": "all-in",
        "yt_playlist_id": "PLn5MTSAqaf8peDZQ57QkJBzewJU1aUokl",
        "rss_nur_muster": r"ALLIN-E\d+_Ch\.mp3",
        # NO-Seite AKTIV mit dem vollen Schutzschild (User-Freigabe
        # 23.07.): Seiten-Deckel 0.80 bis in den FAK-Sweep (PR #16),
        # Basisraten-Veto ueber Serie 11300 (E281-E2E: alle 8 Sperren
        # loesten real YES auf), Boilerplate-Lexikon (Tension-Lehre),
        # Gap-Verify mit large-v3 ohne VAD vor der NO-Runde.
        "boilerplate_begriffe": ALLIN_BOILERPLATE,
        "serie_id": "11300",
        # Volles Kapital (User 23.07.): Cash 397.02 pUSD + ~119 Hot-Ones-
        # Rueckfluss (UMA proposed) -> Obergrenze 500; der Executor
        # deckelt zusaetzlich am echten Wallet-Delta.
        "max_usd_gesamt": 500.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
        # Nachlauf 90 wie jre/lemonade: E280-NOs wurden noch lange nach
        # der Runde zu 0.50-0.70 gehandelt — genau dieses Fenster.
        "nachlauf_minuten": 90,
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
    "trump_july27": {
        "live_dir": "trump_july27",
        "event_id": "745692",
        "event_slug": (
            "what-will-trump-post-this-week-july-27-august-2-"
            "20260724154919527"
        ),
        # Quelle wie july13/july20: oeffentliche Truth-Social-API von
        # @realDonaldTrump (truth_watch.py, curl_cffi-Impersonation),
        # eigenes Skript trump_bot.py, NUR YES. Regeltext am 27.07. per
        # Diff gegen den july20-Snapshot gegengelesen: WORTGLEICH bis auf
        # die Datumsangaben, Beschreibungs-Schablone ueber alle 17
        # Maerkte identisch — Matcher traegt unveraendert.
        # ABGRENZUNG wie july20: Serie 11341 "trump-post-weekly" (DIESES
        # Event) wertet GESCHRIEBENE Truths — unser Bot. Die parallele
        # Serie 11277 "trump-weekly-mentions" ("What will Trump SAY")
        # wertet NUR Gesprochenes -> nie mit diesem Profil handeln.
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "what-will-trump-post",
        "x_user_id": None,
        "truth_user_id": "107780257626128497",  # @realDonaldTrump
        "truth_poll_s": 15.0,
        "p_win": 0.97,
        "min_edge": 0.03,
        "periode_start_utc": "2026-07-27T04:00:00Z",  # 27.07. 00:00 ET
        "periode_ende_utc": "2026-08-03T03:59:59Z",   # 02.08. 23:59 ET
        # Budget: Vorwochen-Wert uebernommen (400/50/40, User-Vorgabe
        # 23.07. fuer trump_july20) — vor dem Scharfschalten am realen
        # Wallet-Stand bestaetigen (Runbook ELON_TRUMP_JULY27). Geteiltes
        # Wallet mit mrbeast_gaming, allin_july24 und elon_july27; der
        # Executor-Delta-Sync verhindert Ueberziehen, aber ein Profil
        # kann dem anderen den Pool wegkaufen.
        "max_usd_gesamt": 400.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
    },
    "trump_july20": {
        "live_dir": "trump_july20",
        "event_id": "715499",
        "event_slug": (
            "what-will-trump-post-this-week-july-20-july-26-"
            "20260717143433877"
        ),
        # Quelle wie july13: oeffentliche Truth-Social-API von
        # @realDonaldTrump (truth_watch.py, curl_cffi-Impersonation),
        # eigenes Skript trump_bot.py, NUR YES.
        # ACHTUNG ABGRENZUNG (geprueft 23.07.): Polymarket listet diese
        # Woche ZWEI Trump-Serien. 11341 "trump-post-weekly" (DIESES
        # Event) wertet GESCHRIEBENE Truths — unser Bot. 11277
        # "trump-weekly-mentions" (Event 723717 "What will Trump SAY")
        # wertet ausschliesslich GESPROCHENES ("Written usages ... will
        # not count") und braucht eine voellig andere Quelle (Reden,
        # Pressekonferenzen, Videos) -> NICHT mit diesem Profil handeln.
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "what-will-trump-post",
        "x_user_id": None,
        "truth_user_id": "107780257626128497",  # @realDonaldTrump
        "truth_poll_s": 15.0,
        "p_win": 0.97,
        "min_edge": 0.03,
        "periode_start_utc": "2026-07-20T04:00:00Z",  # 20.7. 00:00 ET
        "periode_ende_utc": "2026-07-27T03:59:59Z",   # 26.7. 23:59 ET
        # Wallet-Stand 23.07.: 420.13 pUSD, geteilt mit mrbeast/lemonade/
        # hotones -> 400 statt 510 (Executor deckelt zusaetzlich am
        # echten Wallet-Delta, kann also nie ueberziehen).
        "max_usd_gesamt": 400.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
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
    "jre_july20": {
        "live_dir": "jre_july20",
        "event_id": "704429",
        "event_slug": (
            "what-will-be-said-on-the-first-joe-rogan-experience-episode-"
            "of-the-week-july-20-20260714183012846"
        ),
        # Quellen wie july13: Megaphone-Feed (GLT-Zufallsnamen, kein
        # Prober), YouTube @joerogan ist Primaer- UND Resolutionsquelle
        # (Marktregel 704429), Feed-Drops historisch Di-Fr ~17:00 UTC.
        "rss_feed_url": "https://feeds.megaphone.fm/GLT1412515089",
        "yt_channel_id": "UCzQUP1qoWDoEbmsQxvdjxgQ",  # PowerfulJRE
        "mp3_probe_muster": None,
        "discovery_slug_filter": "joe-rogan-experience",
        "titel_muster": r"(?:joe rogan experience\s*)?#\d{3,5}\s*-",
        "titel_verboten": r"mma\s*show",  # "JRE MMA Show ... will not count"
        "yt_kanalseite_immer": True,
        # Armierung 18.07. (Vollpool-Prinzip wie mrbeast/trump; geteiltes
        # Wallet, Executor-Delta-Sync verhindert Ueberziehen).
        "max_usd_gesamt": 510.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
        # NO-Schutzschichten: Serie rogan-mentions fuer Basisraten
        # (Dauerbrenner wie right/crazy/different werden gesperrt),
        # Intro-Jingle-Lexikon (siehe JRE_BOILERPLATE).
        "serie_id": "11275",
        "boilerplate_begriffe": JRE_BOILERPLATE,
        # Nachlauf verlaengert: JRE-Buecher sind duenn und MMs traege
        # (#2523: alle Asks beim Drop gepullt, 0 Trades; E280-NOs wurden
        # noch lange nach der Runde guenstig gehandelt).
        "nachlauf_minuten": 90,
    },
    "lemonade_july22": {
        "live_dir": "lemonade_july22",
        "event_id": "708407",
        "event_slug": (
            "what-will-be-said-on-the-next-lemonade-stand-podcast-"
            "july-22-20260715172625707"
        ),
        # Quellen wie july15: Vox/Megaphone-Feed (VMP-Zufallsnamen, kein
        # Prober), Drop Mi ~19:00 UTC, pubDate teils +15-115 Min verspaetet
        # -> RSS+YT parallel, first-wins. NUR der Podcast-Kanal (der
        # Clips-Kanal UCurXa... ist irrelevant, Befund 13.07.).
        "rss_feed_url": "https://feeds.megaphone.fm/VMP5629614579",
        "yt_channel_id": "UCwVevVbti5Uuxj6Mkl5NHRA",  # @LemonadeStandPodcast
        "mp3_probe_muster": None,
        "discovery_slug_filter": "lemonade-stand",
        # Marktregel 708407 (geprueft 22.07.): jedes Kanal-Video mit
        # "Lemonade Stand" im Titel qualifiziert, "mentioned by anyone",
        # No-Qualifying erst 31.07. -> Titel-Muster = Positiv-Identifikation.
        "titel_muster": r"lemonade\s*stand",
        "yt_kanalseite_immer": True,
        "yt_min_dauer_s": 900,
        # Armierung 22.07. (Vollpool-Prinzip, geteiltes Wallet mit
        # mrbeast_gaming; Executor-Delta-Sync verhindert Ueberziehen).
        "max_usd_gesamt": 510.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
        # Basisraten: Serie lemonade-stand, 7 voll aufgeloeste Vorwochen —
        # Ritual-/Fuellwoerter (actually/think/money 0.91-0.97 vorgepreist)
        # sperren sich damit empirisch selbst. BEWUSST kein Boilerplate-
        # Lexikon: Captions-Check zweier Episoden (22.07.) zeigt kein
        # festes Intro/Outro-Jingle (nur den Host-Opener "Ladies and
        # gentlemen", danach divergent) — Ritual-Woerter deckt die
        # Basisraten-Schicht besser belegt ab.
        "serie_id": "11828",
        # Duenne Buecher der jungen Show -> langes Nachlauf-Fenster wie JRE.
        "nachlauf_minuten": 90,
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
    "hotones_july23": {
        # Event 731776 "What will Jon Bernthal or Tom Holland say on Hot
        # Ones?" (Serie 12334 hot-ones-mentions, 22 Maerkte, Auftritt
        # 23.07.2026 11:00 ET = 15:00 UTC, Deadline 24.07. 23:59 ET).
        # BESONDERHEIT: Der Markt wertet nur Aussagen von Bernthal ODER
        # Holland, waehrend Host Sean Evans den groesseren Redeanteil hat.
        # Deshalb ZWEI Zielsprecher (Union) — YES nur aus deren Treffern.
        # Empirischer Beleg fuer die Gast-only-Zurechnung: der einzige
        # aufgeloeste Serien-Vorgaenger (Radcliffe, Event 214212, 19.02.)
        # loeste "Scoville"/"Sauce 5+"/"Wing 10+" zu NO auf, obwohl der
        # Host diese Woerter sicher sagt.
        "live_dir": "hotones_july23",
        "event_id": "731776",
        "event_slug": (
            "what-will-jon-bernthal-or-tom-holland-say-on-hot-ones-"
            "20260721145535497"
        ),
        # KEIN Audio-Feed: der einzige Hot-Ones-Podcast ("The Classic
        # Interviews", Acast) ist ein Archiv, letzte Folge 29.08.2018 ->
        # tot. Der Watcher laeuft rein ueber YouTube (@FirstWeFeast).
        "rss_feed_url": None,
        "mp3_probe_muster": None,
        "rss_nur_muster": None,
        # @FirstWeFeast; belegt via <link rel="canonical"> + "rssUrl" auf
        # der Kanalseite (22.07.2026).
        "yt_channel_id": "UCPD_bxCRGpmmeQcbe2kpPaA",
        # Eng an DIESES Event binden, nicht an den Serien-Slug: Serie 12334
        # ist MONATLICH; ein breiter Filter (say-on-hot-ones) wuerde beim
        # Auto-Roll im August auf die naechste Hot-Ones-Folge (anderer Gast)
        # springen — mit stehen gebliebenen Bernthal/Holland-Referenzen.
        # Der Slug-Substring ist disjunkt zu allen bestehenden Profilen.
        "discovery_slug_filter": "jon-bernthal-or-tom-holland",
        # Positiv-Identifikation. Kern "spicy wings": Hausformat in 425 von
        # 439 Episodentiteln, in KEINEM Nebenformat-Titel (Versus / Heat
        # Eaters / Pro Moves / Slice Joint / Hot Kitchen / Wing Pong) und
        # stabil im YouTube-Titel-A/B-Test (Pv2txXubvRY lief zeitgleich als
        # "Goes Into Fight or Flight ..." und "Wants to Throw Hands ...").
        # Duo-Folgen lassen historisch "While Eating" weg ("... Bond Over
        # Spicy Wings") -> NICHT auf "while eating" ankern. Namen als
        # Redundanz gegen einen Sondertitel der Duo-Folge.
        "titel_muster": r"spicy\s*wings|bernthal|holland",
        # Der Namens-Zweig liesse sonst eine "Hot Ones Versus"-Folge mit
        # Bernthal/Holland durch (Versus laeuft 1280s, ueber jedem Dauer-
        # Gate). Marktregel: "their appearance ON Hot Ones", Resolutions-
        # quelle "the released episode" -> Nebenformate raus.
        "titel_verboten": (
            r"hot\s*ones\s*versus|hotonesversus|wing\s*pong|pro\s*moves|"
            r"slice\s*joint|heat\s*eaters|hot\s*kitchen|truth\s*or\s*dab"
        ),
        # S30-Hauptfolgen 1244-1596s (Mittel 1426s). 1000s laesst 244s
        # Puffer und toetet die belegte Falle kVJuKJgbfrg (195s mit EXAKTEM
        # Hauptfolgen-Titel "... While Eating Spicy Wings | Hot Ones") sowie
        # Sauce-Lineup (355s) und Teaser-Shorts (61s).
        "yt_min_dauer_s": 1000,
        # KEINE Playlist-Gate: "Hot Ones Season 30" enthaelt Shorts und das
        # Sauce-Lineup, und die Pflege haengt Stunden nach (der Heat-Eaters-
        # Upload vom 22.07. fehlte 5,5h spaeter noch in seiner Playlist).
        # In bot.py ist die Playlist ein HARTER Ausschluss -> wuerde den
        # Drop verwerfen.
        "yt_playlist_id": None,
        # Kanalseite /videos bei jedem Poll mitlesen (Langform-Tab, andere
        # Infrastruktur als videos.xml) — Redundanz gegen Feed-Nachlauf/404.
        "yt_kanalseite_immer": True,
        # Duenne Buecher der monatlichen Serie (Serien-Liquiditaet ~2000 USD)
        # -> langes Nachlauf-Fenster wie JRE.
        "nachlauf_minuten": 90,
        # Serie hot-ones-mentions. Nur 1 aufgeloester Vorgaenger (Radcliffe)
        # -> Basisraten-Schicht strukturell wirkungslos (min_n 4 nicht
        # erreichbar, und der Serien-Slug traegt den Gastnamen, sodass sich
        # Wochen nie matchen). Die NO-Absicherung traegt hier NICHT ueber
        # Basisraten; siehe no_ask_obergrenze.
        "serie_id": "12334",
        # ZWEI Referenzstimmen (Union). Erst nach Kalibrierung scharf
        # schalten; bauen mit operations.pipeline.baue_referenz_quellen
        # (benannte Solo-Clips + Positiv-/Negativ-Kontrollen).
        "zielsprecher_referenzen": [
            "data/live/hotones_july23/referenz_bernthal.npy",
            "data/live/hotones_july23/referenz_holland.npy",
        ],
        # Zwei Referenzen = zwei Chancen, den Host faelschlich zuzurechnen
        # (Union erhoeht die Falsch-Positiv-Rate). Bei 18 Schwelle-1-Maerkten
        # ist ein einziger Falsch-Positiv ein Fehlkauf -> Schwelle 0.50
        # statt 0.40 (analog mrbeast_gaming), vor dem Scharfschalten gegen
        # Sean-Evans-Audio kalibrieren.
        "sprecher_schwelle": 0.50,
        # Profil-eigene Homophon-Fallen (globales Default-Set waere hier
        # falsch): mate/made/maid, soccer/sucker, wedding/weeding,
        # brother/bother. Bei Segment-Konfidenz <= 0.8 wandern strikte
        # Treffer aus dem YES-Zaehler (Schutz gegen ASR-Fehl-YES auf
        # Schwelle-1-Maerkten). PDF: "Homophones ... do not qualify".
        "homophon_begriffe": {"mate", "soccer", "wedding", "brother"},
        # Varianten-Override je Markt (Frage-Ableitung ist dort falsch):
        # - 3026024 Spider/Spider-man: "Spider"+"Spider-man" zaehlen
        #   "Spider-Man" DOPPELT (Bindestrich ist keine Buchstabengrenze)
        #   -> YES feuerte bei 4 statt 5+. ["Spider","Spiderman"] zaehlt
        #   "Spider-Man"=1 ("Spider" deckt es ab), "Spiderman"=1. PDF
        #   "Name Components": ein Vollname zaehlt einmal.
        # - Getrennte/bindestrich-Komposita, die die strikten Wortgrenzen
        #   sonst verwerfen (PDF "Hyphenated Constructs"/"Compound Words":
        #   Leerzeichen ODER Bindestrich qualifiziert).
        # - ASR-Schreibvarianten desselben gesprochenen Eigennamens.
        "markt_varianten_override": {
            "3026024": ["Spider", "Spiderman"],
            "3026043": ["Ice Cream", "Ice-Cream", "Icecream"],
            "3026035": ["World Cup", "World-Cup", "Worldcup"],
            "3026039": ["Pitbull", "Pit bull", "Pit-bull"],
            "3026036": ["Morocco", "Marocco"],
        },
        # NO-SEITE FUER DIESEN LAUF AUS (no_ask_obergrenze 0.0 -> entscheide_no
        # verwirft jeden NO-Kandidaten). Grund: Der NO-Zweig entscheidet auf
        # dem erweiterten GESAMT-Zaehler (alle Stimmen, bot.py NO-Runde), der
        # Markt wertet aber nur den Gast. Auf Hot Ones (Host-dominiert) ist
        # der Gesamtzaehler kein tauglicher Proxy fuer die Gast-Abwesenheit,
        # und eine Gast-only-NO-Schicht ist noch nicht kalibriert. Analog zu
        # elon_july13/trump_july13 wird nur YES gehandelt, bis die Gast-only-
        # NO-Zuordnung belegt ist. Siehe Handover-Notiz.
        "no_ask_obergrenze": 0.0,
        # Budget 400 (User-Vorgabe 23.07.) mit Standard-Sweep wie die
        # Vollprofile (allin_july17: 50 USD je Markt, 40 Clips, budget-
        # statt clip-limitiert). ACHTUNG duenne Buecher (Serien-Liquiditaet
        # ~2000 USD, mehrere Maerkte nur 8-17 USD Tiefe unter dem Deckel) —
        # der Sweep raeumt nur vorhandene Level ab und stoppt am Deckel,
        # aber 50/Markt kann bei duennen Buechern spuerbar slippen. Geteiltes
        # Wallet mit mrbeast_gaming: vor dem Scharfschalten Wallet-Stand
        # gegenpruefen (Executor-Delta-Sync verhindert Ueberziehen).
        "max_usd_gesamt": 400.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
    },
    "elon_july20": {
        # Event 715491 "What will Elon post this week? (July 20 - July 26)",
        # 17 Maerkte. Nachfolger von elon_july13; der Regeltext ist
        # WORTGLEICH zur Vorwoche (23.07. an der Gamma-Beschreibung von
        # Markt 2966514 gegengelesen): Plural/Possessiv/Case zaehlen,
        # Sigils (#/@/$) davor sind ok, Compounds zaehlen, Misspellings
        # und Symbole IM Wort disqualifizieren, eigener Text in Quote-
        # und Reply-Posts zaehlt, zitierter Fremdtext und Reposts nicht,
        # Bildtext nur klar ausgeschrieben. Damit traegt der bestehende
        # Matcher aus elon_bot.py unveraendert.
        "live_dir": "elon_july20",
        "event_id": "715491",
        "event_slug": (
            "what-will-elon-post-this-week-july-20-july-26-"
            "20260717142325168"
        ),
        # Kein Audio: Quelle sind X-Posts von @elonmusk (x_watch.py,
        # GraphQL-Web-Pfad mit Login-Cookies X_AUTH_TOKEN/X_CT0 aus .env).
        # Eigenes Skript elon_bot.py; die Audio-Felder bleiben leer.
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "what-will-elon-post",
        "x_user_id": "44196397",  # @elonmusk (verifizierter Account)
        # NUR YES (User-Vorgabe 13.07., am 23.07. fuer diese Woche
        # bestaetigt): die NO-Seite konvergiert die ganze Woche gegen 1,
        # dort gibt es keinen Geschwindigkeits-Edge. elon_bot.py kennt
        # ohnehin nur den YES-Zweig — kein NO-Pfad zu sperren.
        # Deckel wie Vorwoche: 0.97 - 0.03 = 0.94.
        "p_win": 0.97,
        "min_edge": 0.03,
        "periode_start_utc": "2026-07-20T04:00:00Z",  # 20.07. 00:00 ET
        "periode_ende_utc": "2026-07-27T03:59:59Z",   # 26.07. 23:59 ET
        # 8s wie july13 (adaptives Pacing streckt bei Bedarf zusaetzlich).
        "x_poll_s": 8.0,
        # Budget 400 (User-Vorgabe 23.07.) mit dem grossen Sweep der
        # Vollprofile (allin_july17: 50 USD je Clip, 40 Clips, budget-
        # statt cliplimitiert). Grund fuer den grossen Clip HIER: Die
        # ausfuehrbare YES-Tiefe unter dem 0.94-Deckel liegt bei 22-255
        # USD je Markt (CLOB, 23.07.) — mit 15-USD-Clips braucht das
        # 4-6 sequenzielle Netzrunden, und genau die Sekunden fehlten in
        # der Vorwoche: Beim Trigger verschwand die Ask-Seite komplett
        # (Buchlog elon_july13, "Always" 13.07.: keine Ask-Zeile von
        # 18:39 bis 20:56). Nach oben ist nichts zu verlieren, der
        # Deckel 0.94 bleibt hart. Geteiltes Wallet mit mrbeast_gaming,
        # lemonade_july22 und hotones_july23 — der Executor-Delta-Sync
        # verhindert Ueberziehen, aber ein Profil kann dem anderen den
        # Pool wegkaufen; vor dem Scharfschalten Wallet-Stand pruefen.
        "max_usd_gesamt": 400.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
        # ARMIERUNG MITTEN IN DER PERIODE (23.07., Tag 4 von 7). Der
        # Startscan muss deshalb weiter zurueckreichen als die 4 Seiten
        # eines Montag-Starts — sonst bleiben die Posts vom 20.-23.07.
        # ungeprueft und ein vom Markt uebersehener Treffer (Fall
        # "Birth Tourism", allin_july3) faellt hinten runter. 12 Seiten
        # decken die bisherige Woche ab; der Bot bricht ohnehin ab,
        # sobald der aelteste geladene Post vor dem Periodenstart liegt.
        "startscan_seiten": 12,
    },
    "earnings_axp_july24": {
        # Event 715475 "What will American Express say during their next
        # earnings call?" — Call 24.07.2026 08:30 AM ET = 12:30 UTC (EDT,
        # von der Nutzerin am Call-Tag live bestaetigt). Kurzfristige
        # Armierung am Call-Tag; Design und Gates identisch zu
        # earnings_pg_july29 (siehe dort und Runbook). Alle Wortmaerkte
        # sind Einzelbegriffe -> keine Komposita-Overrides noetig.
        "live_dir": "earnings_axp_july24",
        "event_id": "715475",
        "event_slug": ("what-will-american-express-say-during-their-next-"
                       "earnings-call-20260717164416058"),
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": (
            "american-express-say-during-their-next-earnings"),
        "call_start_utc": "2026-07-24T12:30:00Z",
        "call_max_minuten": 120.0,
        "chunk_sekunden": 10,
        # YES-only wie pg_july29: Live-Capture ohne Abdeckungsgarantie.
        "no_ask_obergrenze": 0.0,
        "gap_verify_aktiv": False,
        "trigger_verify_aktiv": True,
        # Budget-Platzhalter; vor --live durch User-Vorgabe bestaetigen.
        "max_usd_gesamt": 100.0,
        "nachlauf_minuten": 30,
    },
    "earnings_pg_july29": {
        # Event 715467 "What will Procter & Gamble say during their next
        # earnings call?" — 22 Maerkte, davon 8 Zaehl-Brackets (Income/
        # Quarter/Fiscal/Innovation/Revenue/Consumer/Profit 10+, Customer
        # 5+). Erhoben via Gamma am 24.07.2026. Die Zaehl-Brackets sind
        # laut Recherche 22.07. der einzig verteidigungsfaehige Rest-Edge
        # dieser Marktklasse (Verarbeitungs-, kein Latenzvorsprung);
        # Einzelwort-Maerkte repricen in ~4 s gegen unsere 10-15 s.
        "live_dir": "earnings_pg_july29",
        "event_id": "715467",
        "event_slug": ("what-will-procter-gamble-say-during-their-next-"
                       "earnings-call-20260717164206363"),
        # Kein Drop-Watcher: Der Call startet zur bekannten Uhrzeit als
        # Live-Webcast. Audio via Loopback-Geraet (Nutzer spielt den
        # Webcast selbst ab — kein automatisierter Login, keine
        # Zugangsdaten im Bot) oder direkte Stream-URL. Eigenes Skript
        # earnings_bot.py; die Feed-Felder bleiben leer.
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "procter-gamble-say-during-their-next-earnings",
        # Call laut Gamma-Beschreibung 29.07.2026 08:30 AM ET = 12:30 UTC
        # (EDT). VOR der Armierung an der IR-Quelle gegenpruefen: beim
        # Dow-Call nannte Polymarket 9 AM, die Firma selbst 8 AM ET
        # (Messprotokoll 23.07., §8) — eine Stunde zu spaet armiert.
        "call_start_utc": "2026-07-29T12:30:00Z",
        "call_max_minuten": 120.0,
        # 10s-Chunks: Beim Livestream ist die Chunk-Fuellzeit der
        # dominante Latenzposten (Messprotokoll §4.3: Transkription
        # selbst ~0.4 s bei small/cuda). Fuer Zaehl-Brackets ist Latenz
        # zweitrangig; 10 s halten den Rueckstand trotzdem klein.
        "chunk_sekunden": 10,
        # Deckel: Audio-Standard p_win 0.93 - 0.03 = 0.90 (Defaults).
        # NO-SEITE AUS: Live-Capture hat keine belegte Abdeckungs-
        # garantie (spaeter Einstieg, Aussetzer der Quelle) — der
        # erweiterte Zaehler ist dann kein tauglicher Abwesenheits-
        # Proxy (E281-Lehre, verschaerft). Analog hotones_july23
        # YES-only, bis die Abdeckung kalibriert ist; Gap-Verify
        # entfaellt damit ebenfalls (grosser large-v3-Nachpass ohne
        # NO-Nutzen).
        "no_ask_obergrenze": 0.0,
        "gap_verify_aktiv": False,
        # Trigger-Verifikation an (AXP-Lehre 24.07.): jeder YES-Trigger
        # wird vor dem Kauf per large-v3 bestaetigt, fail-closed.
        "trigger_verify_aktiv": True,
        # Komposita-Schreibvarianten (PDF "Hyphenated Constructs"/
        # "Compound Words": Leerzeichen ODER Bindestrich qualifiziert;
        # die strikten Wortgrenzen-Patterns sehen "World-Cup"/
        # "Toilet-paper" sonst nicht — Vorbild hotones_july23).
        "markt_varianten_override": {
            "2966437": ["World Cup", "World-Cup", "Worldcup"],
            "2966445": ["Toilet paper", "Toilet-paper", "Toiletpaper"],
        },
        # Budget-Platzhalter bis zur User-Vorgabe bei der Armierung;
        # Standard-Clips (15 USD, 10 je Markt). Dry-Run ist ohnehin
        # der Standardmodus des Bots.
        "max_usd_gesamt": 100.0,
        # Earnings-Buecher stehen nach dem Call sofort auf 0.99+
        # (Recherche §3.3: Vorpreisungs-Markt) — kurzes Fenster genuegt.
        "nachlauf_minuten": 30,
    },
    "earnings_pypl_july28": {
        # Event 745733 "What will PayPal say during their next earnings
        # call?" — Q2-Call Di 28.07.2026 08:00 AM ET = 12:00 UTC
        # (IR-Eventseite am 27.07. verifiziert; Webcast auf der
        # Q4-Inc-Plattform events.q4inc.com/attendee/222501806 —
        # REGISTRIERUNG noetig, Handarbeit im Browser am Vortag;
        # Quellen: RECHERCHE_EARNINGS_QUELLEN_2026-07-27.md §2).
        # 19 Maerkte: 4 Brackets (Quarter 15+, Consumer 10+,
        # Transaction 5+, Merchant 5+ — alle >0.96 vorgepreist, 27.07.)
        # und ein dickes Mittelfeld fuer den AXP-Aufmerksamkeits-Kanal
        # (Stablecoin 0.61, Agentic Commerce 0.52, Braintree 0.405,
        # Stripe 0.30, Cash Back 0.265, Anthropic/Claude 0.20, ...).
        # Design und Gates identisch zu earnings_pg_july29.
        "live_dir": "earnings_pypl_july28",
        "event_id": "745733",
        "event_slug": ("what-will-paypal-say-during-their-next-earnings-"
                       "call-20260724221739505"),
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "paypal-say-during-their-next-earnings",
        "call_start_utc": "2026-07-28T12:00:00Z",
        # PayPal-Calls laufen ~60 min; Puffer fuer Q&A-Ueberzieher.
        "call_max_minuten": 90.0,
        "chunk_sekunden": 10,
        "no_ask_obergrenze": 0.0,
        "gap_verify_aktiv": False,
        "trigger_verify_aktiv": True,
        # Bindestrich-/Zusammenschreibungen (PDF "Hyphenated
        # Constructs"/"Compound Words"; ASR wechselt die Schreibweise):
        "markt_varianten_override": {
            "3094216": ["Stablecoin", "Stable Coin", "Stable-Coin"],
            "3094223": ["Cash Back", "Cash-Back", "Cashback"],
        },
        # Volles Budget freigegeben (User 28.07. frueh, "wie letztes
        # Mal, volle Sweeps"): Vollprofil-Muster der grossen Laeufe —
        # Buch bis zum Deckel abraeumen, budget- statt clip-limitiert.
        # Wallet geteilt mit Boeing (16:30), Graham (20:00) und den
        # Wochen-Bots; Executor-Delta-Sync verhindert Ueberziehen.
        "max_usd_gesamt": 650.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
        "nachlauf_minuten": 30,
    },
    "earnings_ba_july28": {
        # Event 745748 "What will Boeing say during their next earnings
        # call?" — Q2-Call Di 28.07.2026 10:30 AM ET = 14:30 UTC
        # (Boeing-PM 01.07.; Webcast ueber die Events-Seite von
        # boeing.com/investors, kein Registrierungszwang in der PM —
        # konkreten Player-Link am Vortag pruefen; Quellen: Recherche
        # §2). 20 Maerkte: 4 Brackets (Quarter 15+, Consumer 10+,
        # Airplane 10+, Customer 3+), Mittelfeld u.a. Guidance 0.475,
        # Philippine Airlines 0.495, Tariff 0.38, Iran 0.355, Airbus
        # 0.245 (27.07.). Die Phrase "Philippine Airlines" traegt der
        # Regel-Parser nativ (flexible Leerzeichen im Pattern) — keine
        # Overrides noetig, alle uebrigen Fragen sind Einzelbegriffe.
        "live_dir": "earnings_ba_july28",
        "event_id": "745748",
        "event_slug": ("what-will-boeing-say-during-their-next-earnings-"
                       "call-20260724221853543"),
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "boeing-say-during-their-next-earnings",
        "call_start_utc": "2026-07-28T14:30:00Z",
        # Boeing-Calls 60-90 min.
        "call_max_minuten": 120.0,
        "chunk_sekunden": 10,
        "no_ask_obergrenze": 0.0,
        "gap_verify_aktiv": False,
        "trigger_verify_aktiv": True,
        # Erster Lauf mit large-v3 als HAUPT-Transcriber (User-Entscheid
        # 28.07. nach dem Braintree-Miss; Benchmark +0.53 s/Chunk).
        # Verify bleibt an: gleicher Modell-Typ, aber VAD-freier Blick
        # aufs groessere Fenster — der Agentic-Fall bewies den Wert;
        # die Modell-Instanz wird geteilt (kein doppeltes VRAM).
        "transcriber_modell": "large-v3",
        # Volles Budget freigegeben (User 28.07. frueh) — Vollprofil-
        # Sweep wie PayPal; real verfuegbar ist, was PayPal (12:00)
        # uebrig laesst (Executor-Delta-Sync am Wallet).
        "max_usd_gesamt": 650.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
        "nachlauf_minuten": 30,
    },
    "trump_michigan_july27": {
        # Event 745732 "What will Trump say during remarks in Michigan?"
        # — Rede am GM Proving Ground Milford, Mo 27.07.2026 15:00 ET =
        # 19:00 UTC (WXYZ/C-SPAN, 27.07.; C-SPAN listet 14:50 ET). 26
        # Maerkte, davon 6 Zaehl-Brackets (Percent 15+, Joe/Biden 12+,
        # Oil/Gas 10+, Hell 7+, Trump 5+, Job 20+). Quellen und Konzept:
        # RECHERCHE_EARNINGS_QUELLEN_2026-07-27.md §4.
        # SPRECHERGEBUNDEN: Resolution ist "if Trump says the listed
        # term" — es gibt KEINE Anyone-Klausel. Zwei Gates zusaetzlich
        # zum Earnings-Design: (1) ECAPA-Sprecher-Verifikation, YES nur
        # aus Trump-zugerechneten Treffern (ziel_count, wie
        # mrbeast_gaming); (2) Operator-Marker SPRECHER_AKTIV im
        # live_dir — der Kaufpfad bleibt gesperrt, bis der Operator
        # Trumps Redebeginn markiert (Vorprogramm-Musik und Vorredner
        # laufen auf demselben Stream).
        "live_dir": "trump_michigan_july27",
        "event_id": "745732",
        "event_slug": ("what-will-trump-say-during-remarks-in-michigan-"
                       "20260724162420350"),
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        # Disjunkt zu "what-will-trump-post" (Truth-Social-Profile) und
        # zur "trump-weekly-mentions"-Serie (sagt "during-remarks" nicht).
        "discovery_slug_filter": "trump-say-during-remarks-in-michigan",
        "call_start_utc": "2026-07-27T19:00:00Z",
        # Trump-Events starten regelmaessig 30-60 min verspaetet, die
        # Rede selbst laeuft 60-90 min — grosszuegiges Fenster, Ctrl+C
        # beendet ohnehin frueher.
        "call_max_minuten": 180.0,
        "chunk_sekunden": 10,
        # YES-only wie alle Live-Capture-Profile: keine belegte
        # Abdeckungsgarantie, und der Gesamtzaehler ist bei einem
        # sprechergebundenen Markt ohnehin kein Abwesenheits-Proxy
        # (Hot-Ones-Begruendung, verschaerft).
        "no_ask_obergrenze": 0.0,
        "gap_verify_aktiv": False,
        "trigger_verify_aktiv": True,
        # Ersetzt das Anyone-Gate: Maerkte sind nur aktiv, wenn die
        # Beschreibung exakt die sprechergebundene Klausel traegt.
        "sprecher_klausel_muster": r"if\s+Trump\s+says\s+the\s+listed\s+term",
        # ECAPA-Referenz im Live-Klon bauen (baue_referenz_quellen:
        # Solo-Clips einer frueheren Rede plus Negativ-Kontrollen wie
        # Moderatoren/Vorredner). Schwelle 0.50 wie mrbeast_gaming/
        # hotones: Praezision vor Recall — ein Falsch-Positiv ist ein
        # Fehlkauf, ein verpasster YES kostet 0.
        "zielsprecher_referenz": (
            "data/live/trump_michigan_july27/referenz_stimme.npy"),
        "sprecher_schwelle": 0.50,
        "markt_varianten_override": {
            # "Percent" 15+: Whisper schreibt gesprochenes "percent" in
            # Ziffernkontexten als "%" ("50%") — ohne "%"-Variante
            # wuerde der Zaehler massiv untererfassen; "per cent" als
            # seltene ASR-Schreibvariante derselben Aussprache.
            "3094188": ["Percent", "per cent", "%"],
            # ASR setzt Kommas in den Slogan: "Drill, baby, drill".
            "3094204": ["Drill Baby Drill", "Drill, Baby, Drill"],
            # Akronyme: Punkt-Schreibweisen als ASR-Varianten ("A.I."-
            # Vorbild in VARIANTEN_MAP).
            "3114659": ["USMCA", "U.S.M.C.A.", "NAFTA", "N.A.F.T.A."],
        },
        # Auto-Marker fuer den Fernstart (User unterwegs): sobald im
        # 5-Chunk-Fenster 6 Trump-zugerechnete Segmente (>= 1 s) laufen,
        # setzt der Bot den Marker selbst. Ohne ECAPA-Verifier feuert
        # das nie (fail-closed); Hand-Marker bleibt jederzeit moeglich.
        "sprecher_marker_auto_segmente": 6,
        # Stream-Selbstheilung (nachgeruestet 27.07. abends nach dem
        # Lauf): dieselben Kanaele wie der Fernstart.
        "reconnect_kanaele": [
            "https://www.youtube.com/@WhiteHouse/live",
            "https://www.youtube.com/@RSBN/live",
            "https://www.youtube.com/@FOX2Detroit/live",
        ],
        "stream_titel_muster": "trump",
        # Budget-Vorgabe User 27.07.: Fokus YES-Einzelwoerter — faellt
        # ein unwahrscheinliches Wort, ist der Payoff gross; Kappe 100
        # USD je Markt als 2 FAK-Clips a 50 (grosse Clips, weil Asks
        # nach dem Fall in Sekunden verschwinden — Elon-Lehre). Die
        # Zaehl-Brackets laufen mit derselben Kappe mit (YES ab
        # Schwelle + 2). Gesamtpool 650 (User-Korrektur 27.07. abends,
        # vorher 400); der Executor deckelt zusaetzlich am echten
        # Wallet-Delta und kann nie ueberziehen.
        "max_usd_gesamt": 650.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 2,
        "nachlauf_minuten": 30,
    },
    "trump_graham_july28": {
        # Event 745731 "What will Trump say during tribute to Lindsey
        # Graham?" — Trauerfeier fuer Senator Graham, Washington
        # National Cathedral, Di 28.07.2026 14:00 ET = 18:00 UTC
        # (Zeremonie-Beginn; Trumps Tribute-Slot liegt IRGENDWO darin).
        # 20 Maerkte, Liq 66k, Einzelwoerter/Phrasen 0.3-0.8, einziges
        # Zaehl-Bracket "Hell" 2+. VIELE Fremdredner (Geistliche,
        # Familie, Politiker) — die Sprecherbindung traegt alles.
        # LEHREN AUS MICHIGAN (27.07., Runbook §5): (1) Die Referenz
        # MUSS aus der Event-Uebertragungskette stammen: Studio-
        # Referenz erreichte auf PA-Audio max 0.396 und haette JEDEN
        # echten Trump-Treffer verworfen; die PA-Referenz (aus dem
        # Michigan-Mitschnitt, Transkript-verifizierte Trump-Passagen)
        # trennt scharf — Trump min 0.610, Gaeste max 0.287, AXP-Fremde
        # max -0.040. Union mit der Studio-Referenz deckt beide
        # Domaenen. (2) Stream-Rotation friert die Quelle ein ->
        # reconnect_kanaele + Stall-Detektor. (3) Verschiebt die
        # Kathedral-Akustik die Zurechnung erneut, ist --fenster-modus
        # der Fallback (Operator-Fenster statt ECAPA; Neustart mitten
        # in der Zeremonie kostet nichts, solange Trump noch nicht
        # gesprochen hat — nur seine Worte zaehlen).
        "live_dir": "trump_graham_july28",
        "event_id": "745731",
        "event_slug": ("what-will-trump-say-during-tribute-to-lindsey-"
                       "graham-20260724170556632"),
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "trump-say-during-tribute-to-lindsey-graham",
        "call_start_utc": "2026-07-28T18:00:00Z",
        # Zeremonie 1.5-2.5 h, Trumps Slot unbekannt -> langes Fenster.
        "call_max_minuten": 240.0,
        "chunk_sekunden": 10,
        "no_ask_obergrenze": 0.0,
        "gap_verify_aktiv": False,
        "trigger_verify_aktiv": True,
        "sprecher_klausel_muster": r"if\s+Trump\s+says\s+the\s+listed\s+term",
        # Union: PA-Referenz (Michigan-Mitschnitt 610-810s, Trump-only)
        # + Studio-Referenz (WH-Ansprachen). Kopien im eigenen live_dir
        # (Hot-Ones-Regel: Profil unabhaengig).
        "zielsprecher_referenzen": [
            "data/live/trump_graham_july28/referenz_stimme_pa.npy",
            "data/live/trump_graham_july28/referenz_stimme_studio.npy",
        ],
        "sprecher_schwelle": 0.50,
        "sprecher_marker_auto_segmente": 6,
        # Kathedrale streamt selbst (kommentarfrei), C-SPAN und News
        # als Backup; Titel-Gate passend zum Funeral — die 24/7-News-
        # Dauerstreams ("ABC News Live") fallen durch.
        "reconnect_kanaele": [
            "https://www.youtube.com/@WNCathedral/live",
            "https://www.youtube.com/@cspan/live",
            "https://www.youtube.com/@ABCNews/live",
            "https://www.youtube.com/@NBCNews/live",
        ],
        "stream_titel_muster": "graham|lindsey|funeral|memorial|tribute",
        # Budget wie Michigan-Vorgabe (User 27.07.): 100 je Markt
        # (2 FAK-Clips a 50), Pool 650; Executor-Delta-Sync deckelt.
        "max_usd_gesamt": 650.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 2,
        "nachlauf_minuten": 30,
    },
    "elon_july27": {
        # Event 745693 "What will Elon post this week? (July 27 - August
        # 2)", 14 Maerkte, beim Armieren am 27.07. alle offen. Nachfolger
        # von elon_july20. Der Regeltext ist WORTGLEICH zu july13/july20
        # (27.07. per Diff gegen den july20-Snapshot gegengelesen, nur die
        # Datumsangaben wechseln; Beschreibungs-Schablone ueber alle 14
        # Maerkte identisch): Plural/Possessiv/Case zaehlen, Sigils
        # (#/@/$) davor sind ok, Compounds zaehlen, Misspellings und
        # Symbole IM Wort disqualifizieren, eigener Text in Quote- und
        # Reply-Posts zaehlt, zitierter Fremdtext und Reposts nicht,
        # Bildtext nur klar ausgeschrieben. Der Matcher aus elon_bot.py
        # traegt damit unveraendert.
        "live_dir": "elon_july27",
        "event_id": "745693",
        "event_slug": (
            "what-will-elon-post-this-week-july-27-august-2-"
            "20260724155239115"
        ),
        # Quelle unveraendert: X-Posts von @elonmusk (x_watch.py,
        # GraphQL-Web-Pfad mit Login-Cookies X_AUTH_TOKEN/X_CT0 aus .env).
        "rss_feed_url": None,
        "yt_channel_id": None,
        "mp3_probe_muster": None,
        "discovery_slug_filter": "what-will-elon-post",
        "x_user_id": "44196397",  # @elonmusk (verifizierter Account)
        # NUR YES wie july13/july20 (User-Vorgabe 13.07.); elon_bot.py
        # hat keinen NO-Zweig. Deckel wie Vorwochen: 0.97 - 0.03 = 0.94.
        "p_win": 0.97,
        "min_edge": 0.03,
        "periode_start_utc": "2026-07-27T04:00:00Z",  # 27.07. 00:00 ET
        "periode_ende_utc": "2026-08-03T03:59:59Z",   # 02.08. 23:59 ET
        "x_poll_s": 8.0,
        # Budget: Vorwochen-Vorgabe uebernommen (400/50/40, User 23.07.
        # fuer elon_july20) — vor dem Scharfschalten am realen Wallet-
        # Stand bestaetigen (Runbook ELON_TRUMP_JULY27). Der Befund aus
        # zwei Wochen null Fills: Es scheiterte nie am Budget, sondern an
        # der beim Trigger verschwindenden Ask-Seite; der grosse Clip
        # bleibt das Zeitargument (Leiter in 1-2 Netzrunden abraeumen
        # statt 4-6). Geteiltes Wallet mit mrbeast_gaming, allin_july24
        # und trump_july27.
        "max_usd_gesamt": 400.0,
        "max_usd_pro_markt": 50.0,
        "max_clips_pro_markt": 40,
        # Armierung am Abend von Tag 1: kein Tag-4-Rueckstand wie bei
        # july20, aber bei Elons Post-Frequenz (oft >80 Posts+Replies am
        # Tag) reichen die 4 Default-Seiten (~80 Eintraege) fuer den
        # angebrochenen Tag nicht sicher zurueck bis 04:00 UTC. 8 Seiten
        # sind reine Reserve — der Scan bricht ohnehin ab, sobald der
        # aelteste geladene Post vor dem Periodenstart liegt. Kontrolle:
        # startscan-Event muss "erreicht_periodenstart": true zeigen.
        "startscan_seiten": 8,
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
# 4. NO-Konsens-Vollpass (Auftrag 25.07., nach dem innovation-Verlust
#    E282): die GANZE Episode vor der NO-Runde einmal mit
#    NO_KONSENS_MODELL (large-v3, batched) nachhoeren. small verhoert
#    Woerter im Crosstalk (E282: "innovation" bei 3470.2s als "Master
#    virtue signaling" — NO @0.13 verlor 20.86 USD; large-v3 hoert es).
#    Deckt Verhoerer INNERHALB abgedeckter Fenster ab — die VAD-Loch-
#    Klasse (E281) bleibt Domaene des Gap-Verify danach. Funde blocken
#    nur NO, nie YES. ~170s je 90-Min-Episode auf der 3060 (Forensik
#    E281+E282); vertretbar, weil NO-Asks nach dem Drop stehen
#    (E280: 30+ Min; E281/E282: Nachlauf-Buchlogs).
BOILERPLATE_BEGRIFFE = frozenset(
    str(w).lower() for w in _P.get("boilerplate_begriffe", []))
SERIE_ID = _P.get("serie_id")
BASISRATE_VETO = float(_P.get("basisrate_veto", 0.8))
BASISRATE_MIN_N = int(_P.get("basisrate_min_n", 4))
GAP_VERIFY_AKTIV = bool(_P.get("gap_verify_aktiv", True))
GAP_MIN_LUECKE_S = float(_P.get("gap_min_luecke_s", 15.0))
GAP_RAND_S = 5.0               # Fenster-Ueberlappung in die Abdeckung
GAP_MODELL = str(_P.get("gap_modell", "large-v3"))
# Vollpass-Schalter je Profil. Default AKTIV: bot.py laeuft nur fuer
# Audio-Profile (Elon/Trump-Textbots haben eigene Skripte und erreichen
# den Pfad nie); Modell folgt GAP_MODELL, per Profil uebersteuerbar.
NO_KONSENS_AKTIV = bool(_P.get("no_konsens_aktiv", True))
NO_KONSENS_MODELL = str(_P.get("no_konsens_modell", GAP_MODELL))
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
# Latenz, daher kurze Chunks. Profil-Override chunk_sekunden: beim
# Live-Capture (Earnings-Webcast) ist die Chunk-Fuellzeit der dominante
# Latenzposten -> 10s (Messprotokoll 22.07., §4.3/4.4).
CHUNK_SEKUNDEN = int(_P.get("chunk_sekunden", 20))
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
# Sprecher-Verifikation: ein Profil nennt entweder EINE Referenzstimme
# (zielsprecher_referenz, MrBeast-Fall) oder MEHRERE
# (zielsprecher_referenzen, Hot-Ones-Fall "Bernthal ODER Holland").
# Mehrere Referenzen werden als Union ausgewertet (siehe speaker.py).
_ziel_ref = _P.get("zielsprecher_referenz")
_ziel_refs = list(_P.get("zielsprecher_referenzen", []))
if _ziel_ref and _ziel_ref not in _ziel_refs:
    _ziel_refs.insert(0, _ziel_ref)
ZIELSPRECHER_REFERENZEN = [REPO_ROOT / p for p in _ziel_refs]
# Rueckwaertskompatibel: erste Referenz bleibt als Einzelpfad lesbar
# (baue_referenz.py, Tests, Startwache-Vorpruefung).
ZIELSPRECHER_REFERENZ = ZIELSPRECHER_REFERENZEN[0] if ZIELSPRECHER_REFERENZEN else None
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

# Elon-Post-Bot (Profile elon_*): X-Feed-Parameter.
X_USER_ID = _P.get("x_user_id")
PERIODE_START_UTC = _P.get("periode_start_utc")
PERIODE_ENDE_UTC = _P.get("periode_ende_utc")
X_POLL_S = float(_P.get("x_poll_s", 16.0))
# Seiten, die der Startscan maximal zurueckblaettert, um die Historie seit
# PERIODE_START_UTC nachzuziehen. 4 reicht fuer einen Start am Perioden-
# anfang; wer mitten in der Woche armiert, braucht mehr (Profil-Override).
# Abbruch erfolgt ohnehin frueher, sobald der aelteste geladene Post vor
# dem Periodenstart liegt.
X_STARTSCAN_SEITEN = int(_P.get("startscan_seiten", 4))

# Trump-Post-Bot (Serie trump-post-weekly): Truth-Social-Parameter.
# Kein Login noetig (curl_cffi-Chrome-Impersonation, Befund 18.07.);
# Poll konservativ, Cloudflare-Drosselung via Backoff im Bot.
TRUTH_USER_ID = _P.get("truth_user_id")
TRUTH_POLL_S = float(_P.get("truth_poll_s", 15.0))

# Earnings-Call-Bot (Profile earnings_*): Der Call startet zur bekannten
# Uhrzeit als Live-Webcast (kein Drop-Ereignis). call_start_utc ist die
# an der IR-Quelle gegenzupruefende Startzeit (die Zeitangabe der
# Polymarket-Beschreibung war beim Dow-Call falsch, Messprotokoll §8);
# call_max_minuten begrenzt den Lauf, falls niemand Ctrl+C drueckt.
CALL_START_UTC = _P.get("call_start_utc")
CALL_MAX_MINUTEN = float(_P.get("call_max_minuten", 120.0))
# Haupt-Transcriber-Modell. Benchmark PayPal-Audio 28.07.: large-v3
# kostet je 10s-Chunk nur +0.53 s (0.78 statt 0.24, p95 0.87) — ~5 %
# der Gesamtlatenzkette — und fand bei "Braintree" 10 Nennungen, wo
# small im Livepfad 2 hoerte (Eigennamen-Recall). Ist das Verify-Modell
# identisch, teilen sich Haupt- und Verify-Pfad EINE Instanz (VRAM).
TRANSCRIBER_MODELL = str(_P.get("transcriber_modell", "small"))
# Trigger-Verifikation: jeden YES-Trigger vor dem Kauf mit dem grossen
# Modell nachpruefen (fail-closed, siehe trigger_verify.py). AXP-Lehre
# 24.07.: Schwelle-1-Kaeufe gegen zweifelnde Maerkte haengen an einem
# einzigen ASR-Treffer — die Nachpruefung kostet ~1-3 s (Modell warm)
# und schuetzt gegen die E281-Homophon-Klasse.
TRIGGER_VERIFY_AKTIV = bool(_P.get("trigger_verify_aktiv", False))
TRIGGER_VERIFY_MODELL = str(_P.get("trigger_verify_modell", GAP_MODELL))
# Sprechergebundene Live-Events ("What will Trump say during ..."): Die
# Resolution wertet nur den benannten Sprecher, eine Anyone-Klausel gibt
# es nicht. Das Profil nennt das Klausel-Muster, das STATT der Anyone-
# Klausel in der Markt-Beschreibung stehen muss (sonst SKIP); zusaetzlich
# bleibt der Kaufpfad gesperrt, bis der Operator die Marker-Datei anlegt
# (Redebeginn des Zielsprechers — Vorprogramm und Vorredner laufen auf
# demselben Stream). None = normales Earnings-Event mit Anyone-Gate.
SPRECHER_KLAUSEL_MUSTER = _P.get("sprecher_klausel_muster")
SPRECHER_MARKER = LIVE_DIR / "SPRECHER_AKTIV"
# Stream-Selbstheilung (Michigan-Lehre 27.07.): YouTube rotiert das
# HLS-Manifest (Redebeginn/Sender-Umschaltung) — ffmpeg haengt dann oft
# still am toten Manifest und die WAV friert ein (zweimal passiert,
# zusammen ~65 min blind). Waechst die WAV laenger als STREAM_STALL_S
# nicht, loest der Bot die /live-Kanaele neu auf (Titel-Gate
# STREAM_TITEL_MUSTER) und bindet eine frische Quelle an — die
# Markt-Zaehler bleiben erhalten (transcriber.neue_quelle).
RECONNECT_KANAELE = [str(u) for u in _P.get("reconnect_kanaele", [])]
STREAM_TITEL_MUSTER = str(_P.get("stream_titel_muster", "trump"))
STREAM_STALL_S = float(_P.get("stream_stall_s", 25.0))
# Auto-Marker: N Zielsprecher-zugerechnete Segmente (>= 1 s) im
# rollenden 5-Chunk-Fenster setzen den Marker automatisch — fuer den
# Fernstart ohne Operator am Rechner. 0 = aus; wirkt nur mit aktivem
# ECAPA-Verifier (ohne Referenz gibt es keine Zurechnungen, also nie
# einen Auto-Marker: fail-closed).
SPRECHER_MARKER_AUTO_SEGMENTE = int(_P.get("sprecher_marker_auto_segmente", 0))

# Nachlauf nach der NO-Runde: Market Maker ziehen beim Drop die Quotes
# und stellen sie erst Minuten spaeter wieder rein (JRE #2523: alle Asks
# gepullt, 0 Trades; E280: NOs wurden nach unserer Runde noch zu
# 0.50-0.70 gehandelt). Offene YES-/NO-Kandidaten werden deshalb noch
# NACHLAUF_MINUTEN lang alle NACHLAUF_POLL_S re-checkt und gekauft,
# sobald wieder ein Ask <= Obergrenze mit Liquiditaet da ist.
# Profil-Override nachlauf_minuten: duenne/traege Buecher (JRE) brauchen
# ein laengeres Fenster als der 45er-Default.
NACHLAUF_MINUTEN = float(_P.get("nachlauf_minuten", 45))
NACHLAUF_POLL_S = 90

# Homophon-anfaellige Begriffe (Basisform, kleingeschrieben). Treffer auf
# diese Begriffe zaehlen nur bei ASR-Konfidenz oberhalb ASR_KONFIDENZ_HOMOPHON.
# Profil-Override homophon_begriffe: manche Events tragen eigene Homophon-
# Fallen (Hot Ones: mate/made/maid, soccer/sucker, wedding/weeding,
# brother/bother). Ohne Override bleibt das globale Default-Set aktiv,
# damit bestehende Profile (All-In/JRE/Lemonade/MrBeast) unveraendert sind.
HOMOPHON_BEGRIFFE = set(
    _P.get("homophon_begriffe", {"red", "read", "blue", "blew", "right", "write"}))

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

# Profil-lokaler Varianten-Override je Markt (market_id -> Variantenliste).
# Fuer Faelle, die die globale VARIANTEN_MAP nicht sauber loesen kann, ohne
# andere Profile zu beruehren: ASR-Schreibvarianten von Eigennamen
# (Zendaya/Zendeya, Morocco/Marocco), getrennt/bindestrich geschriebene
# Komposita (Pit bull, World-Cup) und die Entschaerfung der Praefix-
# Doppelzaehlung ("Spider"+"Spider-man" zaehlen "Spider-Man" doppelt ->
# stattdessen ["Spider","Spiderman"], "Spider" allein deckt "Spider-Man"
# ab, weil der Bindestrich keine Buchstabengrenze ist). Greift NUR fuer
# das aktive Profil; ohne Eintrag bleibt die Frage-Ableitung unveraendert.
MARKT_VARIANTEN_OVERRIDE = {
    str(k): list(v) for k, v in _P.get("markt_varianten_override", {}).items()
}
