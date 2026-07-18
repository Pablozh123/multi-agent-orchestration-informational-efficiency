"""Deskriptive Nachauswertung der eigenen Live-Runs fuer die Website.

Liest die privaten Run-Verzeichnisse (``<live-root>/<profil>/`` mit
``bot_events.jsonl``, ``decisions_log.jsonl``, ``gamma_event_snapshot.json``)
READ-ONLY und joint die oeffentliche Marktaufloesung aus dem committeten
Cache ``data/raw/live_runs/resolutions_<profil>.json``. Ergebnis ist ein
einzelnes ``runs.json`` (pydantic fail-closed, Redaktions-Gate vor jedem
Write) mit Wetten, realisiertem PnL/ROI, Reaktionslatenzen und verpassten
Chancen je Run.

Grundsaetze wie im Tageslauf: keine Wallet-Adressen, keine Keys, keine
Order-Funktionen. Der einzige optionale Netzpfad ist ``--fetch-resolutions``
(read-only Gamma-Abruf der Marktaufloesungen in den Cache).

Aufruf:
  python -m operations.pipeline.run_dashboard \
      --live-root D:/pfad/zu/data/live --publish-dir <website>/public/data
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict

from operations.pipeline.daily_review_run import (
    LIVE_BASE_DIR,
    RedactionGateError,
    run_redaction_gate,
)
from operations.pipeline.orderbook import ausfuehrbare_tiefe_usd

REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLISH_DIR_DEFAULT = REPO_ROOT / "data" / "publish"
RESOLUTIONS_DIR_DEFAULT = REPO_ROOT / "data" / "raw" / "live_runs"

RUNS_FILE = "runs.json"
POSTMORTEMS_FILE = "postmortems.json"
PILOT_FILE = "pilot.json"

#: Kuratierte Vorfall-Liste (getrackte Quelldatei, kein generiertes Artefakt).
POSTMORTEMS_QUELLE = REPO_ROOT / "data" / "results" / "mentions_run_postmortems.json"

#: Read-only Pilot-Artefakte des Echtgeld-Mini-Piloten (Protokoll V2).
PILOT_DIR_DEFAULT = REPO_ROOT / "pilot"

#: Kuratierter Wallet-Abgleich (Geldfluss-Wahrheit je Event, ohne Adressen).
WALLET_ABGLEICH_QUELLE = REPO_ROOT / "data" / "results" / "wallet_abgleich_2026-07-18.json"

#: Fill-Status, die als platzierte Wette zaehlen (wie post_resolution).
FILL_STATUS = ("dry_run_fill", "live_fill", "live_partial")

HINWEIS = (
    "Descriptive post-run review of our own small-stake live runs of the "
    "mentions bot. Reconstructed read-only from the run logs; resolutions "
    "from public Gamma data. Stakes/shares are log estimates: where the FAK "
    "order status returned no fill price, the price cap is assumed, which "
    "overstates the stake. Cash truth per event is the curated wallet "
    "reconciliation (wallet_netto_usd). No trading recommendation, no "
    "return forecast."
)

GAMMA_EVENTS_URL = "https://gamma-api.polymarket.com/events"
DATA_API_TRADES_URL = "https://data-api.polymarket.com/trades"
HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

TAPE_QUELLE = "data-api.polymarket.com/trades (oeffentlich, read-only)"


# ---------------------------------------------------------------------------
# pydantic-Schemas (fail-closed)
# ---------------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WetteEintrag(_Strict):
    frage: str
    seite: Literal["YES", "NO"]
    entscheidungs_preis: Optional[float]
    avg_fill_preis: Optional[float]
    shares: float
    einsatz_usd: float
    sweep_clips: int
    fill_status: str
    fill_ts_utc: str
    aufgeloest: bool
    gewonnen: Optional[bool]
    payout_usd: Optional[float]
    pnl_usd: Optional[float]
    roi_pct: Optional[float]
    aktueller_yes_preis: Optional[float]
    # Race gegen das oeffentliche Trade-Tape (None ohne Tape-Cache).
    # Zeitanker ist die geloggte Fill-Zeit des Bots; Chain-Timestamps koennen
    # wenige Sekunden davon abweichen.
    tape_rang: Optional[int] = None
    fremde_davor: Optional[int] = None
    fremdvolumen_davor_usd: Optional[float] = None
    verfolger_s: Optional[float] = None
    # Latenz-Counterfactual: letzter FREMDER Kauf-Preis der Wett-Seite N
    # Sekunden nach dem eigenen Fill, gezaehlt AB dem Drop (Ask-seitig;
    # eigene Clips und Gegenseiten-Trades ausgeschlossen; None = seit Drop
    # kaufte bis dahin niemand sonst). Keys "0"/"30"/"60"/"120"/"300"/"900".
    preis_nach_fill: Dict[str, Optional[float]] = {}
    # Kapazitaetsmass: ausfuehrbare Ask-Tiefe (USD) im Entscheidungs-Snapshot
    # bis zur geloggten Kaufobergrenze. Untergrenze, da der Snapshot auf die
    # obersten 10 Level gekuerzt ist; None ohne Snapshot/parsebare Grenze.
    tiefe_usd_bis_deckel: Optional[float] = None


class VerpassteChance(_Strict):
    frage: str
    seite: str
    limit_preis: Optional[float]
    grund: str
    # Nachtraegliche Bepreisung: haette die uebersprungene Seite gewonnen?
    waere_gewonnen: Optional[bool] = None


class RepricingKurve(_Strict):
    """Fremd-Kaufpreis-Verlauf eines gehandelten Markts ab Drop (1h Fenster).

    ``punkte``: [sekunden_seit_drop, preis] -- jeder FREMDE Taker-BUY der
    Wett-Seite ein Punkt (Ask-seitig; eigene Clips ausgeschlossen).
    ``time_to_priced_s``: Sekunden bis ein fremder Kauf ueber der
    Bot-Kaufgrenze 0.90 liegt (None = im Fenster nie).
    """

    frage: str
    seite: str
    time_to_priced_s: Optional[float]
    fill_nach_s: Optional[float]
    punkte: List[List[float]]


class RaceInfo(_Strict):
    """Run-weite Zusammenfassung des Drop-Rennens uebers oeffentliche Tape."""

    quelle: str
    wetten_mit_tape: int
    first_on: int
    fremde_trades_vor_uns: int
    median_verfolger_s: Optional[float]


class RunEintrag(_Strict):
    profil: str
    event_slug: str
    episode_titel: str
    modus: str
    drop_quelle: str
    pubdate_utc: Optional[str]
    drop_erkannt_utc: Optional[str]
    erkennungslatenz_s: Optional[float]
    erste_entscheidung_s: Optional[float]
    erster_fill_s: Optional[float]
    n_maerkte: int
    n_entscheidungen: int
    zaehler: Dict[str, int]
    eingepreist: int
    einsatz_usd: float
    realisierter_pnl_usd: Optional[float]
    wetten: List[WetteEintrag]
    verpasste_chancen: List[VerpassteChance]
    race: Optional[RaceInfo] = None
    repricing: List[RepricingKurve] = []
    # Summe der Wetten-Tiefen (nur Wetten mit Snapshot): sofort sichtbares
    # Angebot am Trigger. Werte ueber 100% beim Einsatz-Verhaeltnis heissen:
    # der Sweep nahm nachrueckende Liquiditaet mit (Snapshot = Untergrenze).
    sichtbare_tiefe_usd: Optional[float] = None
    einsatz_zu_sichtbarer_tiefe_pct: Optional[float] = None
    # Wallet-Wahrheit je Event (kuratierter Abgleich; None ohne Eintrag).
    wallet_netto_usd: Optional[float] = None


class RunsAggregat(_Strict):
    n_runs: int
    n_wetten: int
    gewonnen: int
    verloren: int
    offen: int
    einsatz_usd: float
    aufgeloester_einsatz_usd: float
    realisierter_payout_usd: float
    realisierter_pnl_usd: float
    roi_realisiert_pct: Optional[float]
    offener_einsatz_usd: float
    sichtbare_tiefe_usd: Optional[float] = None
    einsatz_zu_sichtbarer_tiefe_pct: Optional[float] = None
    wallet_netto_usd: Optional[float] = None
    wallet_abgleich_stand: Optional[str] = None


class RunsPayload(_Strict):
    hinweis: str
    stand_utc: str
    kennzeichnung: str
    aggregat: RunsAggregat
    runs: List[RunEintrag]


class PostmortemEintrag(_Strict):
    """Ein kuratierter Vorfall aus dem Live-Betrieb samt verifiziertem Fix."""

    datum: str
    profil: str
    achse: str  # Kernachse (z.B. "Detection-Latenz", "Risiko-Disziplin")
    titel: str
    was_passierte: str
    auswirkung: str
    fix: str
    referenz: str  # Commit/PR/Log-Fundstelle


class PostmortemsPayload(_Strict):
    hinweis: str
    stand_utc: str
    kennzeichnung: str
    eintraege: List[PostmortemEintrag]


class PilotSignalKompakt(_Strict):
    ts_utc: str
    arm: str
    frage: str
    seite: str
    signal_preis: Optional[float]
    buchtiefe_usd: Optional[float]
    restlaufzeit_tage: Optional[float]
    status: str


class PilotProtokollInfo(_Strict):
    quelle: str
    budget_usdc: float
    einsatz_je_trade_usdc: float
    regel_freeze_datum: str
    handelsfenster_bis: str
    arm1_kurz: str
    arm2_kurz: str


class PilotPayload(_Strict):
    hinweis: str
    stand_utc: str
    kennzeichnung: str
    protokoll: PilotProtokollInfo
    watcher_lauf_ts_utc: Optional[str]
    watcher_parameter: Dict[str, Any]
    watcher_statistik: Dict[str, int]
    signal_zaehler: Dict[str, int]
    signale_neueste: List[PilotSignalKompakt]
    trades: List[Dict[str, Optional[str]]]


# ---------------------------------------------------------------------------
# Parser (reine Funktionen ueber den Log-Zeilen)
# ---------------------------------------------------------------------------


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def _ts(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _sekunden(spaeter: Any, frueher: Any) -> Optional[float]:
    t1, t0 = _ts(spaeter), _ts(frueher)
    if t1 is None or t0 is None:
        return None
    return round((t1 - t0).total_seconds(), 1)


def parse_events(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Drop-, Start- und Abschlussinfos aus ``bot_events.jsonl``."""

    info: Dict[str, Any] = {
        "modus": "",
        "n_maerkte": 0,
        "drop_quelle": "",
        "episode_titel": "",
        "pubdate_utc": None,
        "drop_erkannt_utc": None,
        "ausgegeben_usd": None,
    }
    for event in rows:
        art = str(event.get("art", ""))
        if art == "start":
            info["modus"] = str(event.get("modus", ""))
            info["n_maerkte"] = int(event.get("aktive_maerkte", 0) or 0)
        elif art == "drop_erkannt" and info["drop_erkannt_utc"] is None:
            # Bot-Restarts loggen den Drop erneut -- die ECHTE
            # Erkennungslatenz ist die erste Erkennung.
            info["drop_quelle"] = str(event.get("quelle", ""))
            # Feed-Titel enthalten teils HTML-Entities (&amp;) -- decodieren.
            info["episode_titel"] = html.unescape(str(event.get("titel", "")))
            info["pubdate_utc"] = event.get("pubdate_utc")
            info["drop_erkannt_utc"] = event.get("wall_ts_utc")
        elif art == "fertig":
            info["ausgegeben_usd"] = event.get("ausgegeben_usd")
    return info


#: Kaufobergrenze aus dem Entscheidungs-Grund ("ask 0.68 <= 0.9").
_DECKEL_RE = re.compile(r"<=\s*(0\.\d+)")


def _deckel_aus_reason(reason: str) -> Optional[float]:
    treffer = _DECKEL_RE.search(reason or "")
    return float(treffer.group(1)) if treffer else None


def _sweep_clips(detail: str) -> int:
    """Anzahl Sweep-Clips aus dem Fill-Detail (``Sweep: N Clips, ...``)."""

    text = str(detail or "")
    if not text.startswith("Sweep:"):
        return 1
    try:
        return int(text.split("Sweep:", 1)[1].strip().split(" ", 1)[0])
    except (ValueError, IndexError):
        return 1


def klassifiziere_grund(reason: str) -> str:
    """No-Action-Grund in eine kleine Anzeige-Kategorie uebersetzen."""

    text = str(reason or "")
    if "_ask" in text and ">" in text:
        return "bereits_eingepreist"
    if text.startswith("kein_"):
        return "kein_angebot"
    return "regel_nicht_erfuellt"


def race_fuer_wette(
    tape_rows: List[Dict[str, Any]],
    drop_ts: Any,
    fill_ts: Any,
) -> Dict[str, Optional[float]]:
    """Drop-Rennen einer Wette gegen das anonymisierte Markt-Tape.

    ``tape_rows``: Taker-Trades eines Markts (``ts_utc``, ``preis``, ``size``,
    ``eigen``), zeitlich unsortiert erlaubt. Gezaehlt wird zwischen Drop und
    der geloggten Fill-Zeit des Bots; eigene Clips zaehlen nie als fremd.
    ``verfolger_s`` ist der Abstand vom eigenen Fill zum ersten fremden
    Trade danach (None, wenn keiner folgt).
    """

    leer: Dict[str, Optional[float]] = {
        "tape_rang": None,
        "fremde_davor": None,
        "fremdvolumen_davor_usd": None,
        "verfolger_s": None,
    }
    t_drop, t_fill = _ts(drop_ts), _ts(fill_ts)
    if not tape_rows or t_drop is None or t_fill is None:
        return leer

    fremde_davor = 0
    fremdvolumen = 0.0
    verfolger: Optional[datetime] = None
    for row in sorted(tape_rows, key=lambda r: str(r.get("ts_utc", ""))):
        t = _ts(row.get("ts_utc"))
        if t is None or t < t_drop or bool(row.get("eigen")):
            continue
        if t < t_fill:
            fremde_davor += 1
            fremdvolumen += float(row.get("preis") or 0.0) * float(
                row.get("size") or 0.0
            )
        elif verfolger is None:
            verfolger = t
    return {
        "tape_rang": fremde_davor + 1,
        "fremde_davor": fremde_davor,
        "fremdvolumen_davor_usd": round(fremdvolumen, 2),
        "verfolger_s": (
            None
            if verfolger is None
            else round((verfolger - t_fill).total_seconds(), 1)
        ),
    }


#: Bot-Kaufgrenze -- Preis darueber gilt als "eingepreist" (kein Entry mehr).
PRICED_ASK_CAP = 0.90
#: Mentions-Maerkte preisen waehrend der laufenden Episode ein -- die
#: Fremd-Kaeufe kommen oft erst Stunden nach dem Drop, daher 24h Fenster.
REPRICING_WINDOW_S = 24 * 3600
COUNTERFACTUAL_DELTAS_S = (0, 30, 60, 120, 300, 900)


def tape_price_series(
    tape_rows: List[Dict[str, Any]], seite: str
) -> List[tuple[datetime, float]]:
    """FREMDE Kauf-Preise der Wett-Seite aus dem Taker-Tape, sortiert.

    Nur Taker-BUYs derselben Outcome-Seite zaehlen: sie sind Ask-seitig und
    beantworten "was haette ein spaeterer Kaeufer gezahlt". SELLs und
    Gegenseiten-Trades sind Bid-seitig und wuerden faelschlich fallende
    Einstiegspreise suggerieren; eigene Clips fliegen raus, weil sie im
    Counterfactual "wir kommen spaeter" nicht existieren wuerden.
    Grundlage ist das Tape, weil der Bot sein Orderbuch-Log waehrend der
    heissen Phase pausiert -- im Repricing-Fenster gibt es keine Quotes.
    """

    wanted = "Yes" if str(seite).upper() == "YES" else "No"
    series: List[tuple[datetime, float]] = []
    for row in tape_rows or []:
        if bool(row.get("eigen")):
            continue
        if str(row.get("outcome") or "") != wanted:
            continue
        if str(row.get("side") or "").upper() != "BUY":
            continue
        preis = row.get("preis")
        t = _ts(row.get("ts_utc"))
        if t is None or preis is None:
            continue
        preis = float(preis)
        if 0.0 < preis < 1.0:
            series.append((t, preis))
    series.sort(key=lambda item: item[0])
    return series


def _price_at(
    series: List[tuple[datetime, float]], moment: datetime
) -> Optional[float]:
    """Letzter gehandelter Preis vor oder auf ``moment`` (None ohne Trade)."""

    preis = None
    for t, value in series:
        if t > moment:
            break
        preis = value
    return preis


def counterfactual_prices(
    series: List[tuple[datetime, float]], fill_ts: Any, drop_ts: Any = None
) -> Dict[str, Optional[float]]:
    """Letzter fremder Kauf-Preis der Wett-Seite N Sekunden nach dem Fill.

    Nur Kaeufe AB dem Drop zaehlen -- Preise aus der Zeit davor beschreiben
    den alten, uninformierten Markt und taugen nicht als Einstiegs-Proxy.
    None heisst: bis zu diesem Zeitpunkt hat seit dem Drop niemand sonst
    unsere Seite gekauft.
    """

    t_fill = _ts(fill_ts)
    if t_fill is None or not series:
        return {}
    t_drop = _ts(drop_ts)
    if t_drop is not None:
        series = [(t, preis) for t, preis in series if t >= t_drop]
    return {
        str(delta): _price_at(series, t_fill + timedelta(seconds=delta))
        for delta in COUNTERFACTUAL_DELTAS_S
    }


def repricing_kurve(
    series: List[tuple[datetime, float]],
    drop_ts: Any,
    fill_ts: Any,
    *,
    frage: str,
    seite: str,
) -> Optional[RepricingKurve]:
    """Trade-Preis-Kurve ab Drop (jeder Trade ein Punkt, 1h Fenster)."""

    t_drop = _ts(drop_ts)
    if t_drop is None or not series:
        return None
    punkte: List[List[float]] = []
    time_to_priced: Optional[float] = None
    for t, preis in series:
        s = (t - t_drop).total_seconds()
        if s < 0 or s > REPRICING_WINDOW_S:
            continue
        if time_to_priced is None and preis > PRICED_ASK_CAP:
            time_to_priced = round(s, 1)
        punkte.append([round(s, 1), preis])
    if not punkte:
        return None
    return RepricingKurve(
        frage=frage,
        seite=seite,
        time_to_priced_s=time_to_priced,
        fill_nach_s=_sekunden(fill_ts, drop_ts),
        punkte=punkte,
    )


def build_race_info(wetten: List[WetteEintrag]) -> Optional[RaceInfo]:
    """Run-Zusammenfassung aus den Wetten-Race-Feldern (None ohne Tape)."""

    mit_tape = [w for w in wetten if w.tape_rang is not None]
    if not mit_tape:
        return None
    verfolger = sorted(
        w.verfolger_s for w in mit_tape if w.verfolger_s is not None
    )
    median = (
        None
        if not verfolger
        else round(
            (
                verfolger[len(verfolger) // 2]
                if len(verfolger) % 2
                else (verfolger[len(verfolger) // 2 - 1] + verfolger[len(verfolger) // 2]) / 2.0
            ),
            1,
        )
    )
    return RaceInfo(
        quelle=TAPE_QUELLE,
        wetten_mit_tape=len(mit_tape),
        first_on=sum(1 for w in mit_tape if w.tape_rang == 1),
        fremde_trades_vor_uns=sum(w.fremde_davor or 0 for w in mit_tape),
        median_verfolger_s=median,
    )


def build_run(
    *,
    profil: str,
    events: List[Dict[str, Any]],
    decisions: List[Dict[str, Any]],
    snapshot: Dict[str, Any],
    resolutions: Dict[str, Any],
    tape: Optional[Dict[str, Any]] = None,
) -> RunEintrag:
    """Einen Run aus Logs, Markt-Snapshot und Aufloesungs-Cache bauen.

    ``tape``: optionaler anonymisierter Trade-Tape-Cache
    (``maerkte`` -> market_id -> Taker-Trades) fuer Race-Felder,
    Repricing-Kurven und das Latenz-Counterfactual.
    """

    info = parse_events(events)
    tape_maerkte: Dict[str, Any] = (tape or {}).get("maerkte") or {}
    series_cache: Dict[tuple[str, str], List[tuple[datetime, float]]] = {}

    def _series(mid: str, seite: str) -> List[tuple[datetime, float]]:
        key = (mid, str(seite).upper())
        if key not in series_cache:
            series_cache[key] = tape_price_series(
                tape_maerkte.get(mid) or [], seite
            )
        return series_cache[key]
    fragen = {
        str(m.get("id")): str(m.get("question") or m.get("slug") or "")
        for m in snapshot.get("markets", [])
    }
    aufloesung = {
        str(k): v for k, v in (resolutions.get("maerkte") or {}).items()
    }

    zaehler: Dict[str, int] = {}
    eingepreist = 0
    wetten: List[WetteEintrag] = []
    verpasst: List[VerpassteChance] = []
    einsatz = 0.0
    realisiert: Optional[float] = None
    erster_fill_ts: Optional[str] = None

    for record in decisions:
        decision = record.get("decision", {}) or {}
        result = record.get("result", {}) or {}
        status = str(result.get("status", ""))
        zaehler[status] = zaehler.get(status, 0) + 1

        mid = str(result.get("market_id") or decision.get("market_id") or "")
        frage = fragen.get(mid, mid)

        if status == "no_action":
            if klassifiziere_grund(decision.get("reason", "")) in (
                "bereits_eingepreist",
                "kein_angebot",
            ):
                eingepreist += 1
            continue

        if status == "skipped_budget":
            markt_skip = aufloesung.get(mid) or {}
            waere_gewonnen: Optional[bool] = None
            if bool(markt_skip.get("closed")) and markt_skip.get("outcome_yes") is not None:
                waere_gewonnen = (
                    str(decision.get("action", "")) == "YES"
                ) == bool(markt_skip["outcome_yes"])
            verpasst.append(
                VerpassteChance(
                    frage=frage,
                    seite=str(decision.get("action", "")),
                    limit_preis=(
                        None
                        if decision.get("limit_price") is None
                        else float(decision["limit_price"])
                    ),
                    grund="budget_exhausted",
                    waere_gewonnen=waere_gewonnen,
                )
            )
            continue

        if status not in FILL_STATUS:
            continue

        seite = str(result.get("action", decision.get("action", "")))
        shares = float(result.get("size_shares", 0.0) or 0.0)
        size_usd = float(result.get("size_usd", 0.0) or 0.0)
        einsatz += size_usd
        avg_fill = round(size_usd / shares, 4) if shares > 0 else None

        markt = aufloesung.get(mid) or {}
        aufgeloest = bool(markt.get("closed"))
        gewonnen: Optional[bool] = None
        payout: Optional[float] = None
        pnl: Optional[float] = None
        roi: Optional[float] = None
        if aufgeloest and markt.get("outcome_yes") is not None:
            gewonnen = (seite == "YES") == bool(markt["outcome_yes"])
            payout = round(shares if gewonnen else 0.0, 2)
            pnl = round(payout - size_usd, 2)
            roi = round(pnl / size_usd * 100.0, 1) if size_usd > 0 else None
            realisiert = round((realisiert or 0.0) + pnl, 2)
        if erster_fill_ts is None:
            erster_fill_ts = str(record.get("wall_ts_utc", ""))

        race = race_fuer_wette(
            tape_maerkte.get(mid) or [],
            info["drop_erkannt_utc"],
            record.get("wall_ts_utc"),
        )
        deckel = _deckel_aus_reason(str(decision.get("reason", "")))
        buch = record.get("book_snapshot") or {}
        tiefe_bis_deckel = (
            ausfuehrbare_tiefe_usd(buch, deckel)
            if deckel is not None and buch.get("asks")
            else None
        )
        wetten_series = _series(mid, seite)
        wetten.append(
            WetteEintrag(
                frage=frage,
                seite="YES" if seite == "YES" else "NO",
                entscheidungs_preis=(
                    None
                    if decision.get("limit_price") is None
                    else float(decision["limit_price"])
                ),
                avg_fill_preis=avg_fill,
                shares=round(shares, 2),
                einsatz_usd=round(size_usd, 2),
                sweep_clips=_sweep_clips(result.get("detail", "")),
                fill_status=status,
                fill_ts_utc=str(record.get("wall_ts_utc", "")),
                aufgeloest=aufgeloest,
                gewonnen=gewonnen,
                payout_usd=payout,
                pnl_usd=pnl,
                roi_pct=roi,
                aktueller_yes_preis=(
                    None if aufgeloest else markt.get("aktueller_yes_preis")
                ),
                tape_rang=race["tape_rang"],
                fremde_davor=race["fremde_davor"],
                fremdvolumen_davor_usd=race["fremdvolumen_davor_usd"],
                verfolger_s=race["verfolger_s"],
                preis_nach_fill=counterfactual_prices(
                    wetten_series,
                    record.get("wall_ts_utc"),
                    info["drop_erkannt_utc"],
                ),
                tiefe_usd_bis_deckel=tiefe_bis_deckel,
            )
        )

    tiefen_wetten = [
        w for w in wetten if w.tiefe_usd_bis_deckel is not None
    ]
    kapazitaet: Optional[float] = None
    auslastung: Optional[float] = None
    if tiefen_wetten:
        kapazitaet = round(
            sum(w.tiefe_usd_bis_deckel or 0.0 for w in tiefen_wetten), 2
        )
        einsatz_mit_tiefe = sum(w.einsatz_usd for w in tiefen_wetten)
        if kapazitaet > 0:
            auslastung = round(einsatz_mit_tiefe / kapazitaet * 100.0, 1)

    drop_ts = info["drop_erkannt_utc"]
    erste_entscheidung = (
        _sekunden(decisions[0].get("wall_ts_utc"), drop_ts) if decisions else None
    )
    repricing: List[RepricingKurve] = []
    gesehen: set[tuple[str, str]] = set()
    for record in decisions:
        result = record.get("result", {}) or {}
        if str(result.get("status", "")) not in FILL_STATUS:
            continue
        mid = str(
            result.get("market_id")
            or (record.get("decision", {}) or {}).get("market_id")
            or ""
        )
        seite = str(result.get("action", "")) or "YES"
        if (mid, seite) in gesehen:
            continue
        gesehen.add((mid, seite))
        kurve = repricing_kurve(
            _series(mid, seite),
            drop_ts,
            record.get("wall_ts_utc"),
            frage=fragen.get(mid, mid),
            seite="YES" if seite == "YES" else "NO",
        )
        if kurve is not None:
            repricing.append(kurve)
    return RunEintrag(
        profil=profil,
        event_slug=str(snapshot.get("slug") or resolutions.get("event_slug") or ""),
        episode_titel=info["episode_titel"],
        modus=info["modus"],
        drop_quelle=info["drop_quelle"],
        pubdate_utc=info["pubdate_utc"],
        drop_erkannt_utc=drop_ts,
        erkennungslatenz_s=_sekunden(drop_ts, info["pubdate_utc"]),
        erste_entscheidung_s=erste_entscheidung,
        erster_fill_s=_sekunden(erster_fill_ts, drop_ts),
        n_maerkte=info["n_maerkte"],
        n_entscheidungen=len(decisions),
        zaehler=zaehler,
        eingepreist=eingepreist,
        einsatz_usd=round(einsatz, 2),
        realisierter_pnl_usd=realisiert,
        wetten=wetten,
        verpasste_chancen=verpasst,
        race=build_race_info(wetten),
        repricing=repricing,
        sichtbare_tiefe_usd=kapazitaet,
        einsatz_zu_sichtbarer_tiefe_pct=auslastung,
    )


def build_aggregat(runs: List[RunEintrag]) -> RunsAggregat:
    alle_wetten = [w for run in runs for w in run.wetten]
    aufgeloeste = [w for w in alle_wetten if w.aufgeloest and w.gewonnen is not None]
    aufgeloester_einsatz = round(sum(w.einsatz_usd for w in aufgeloeste), 2)
    payout = round(sum(w.payout_usd or 0.0 for w in aufgeloeste), 2)
    pnl = round(sum(w.pnl_usd or 0.0 for w in aufgeloeste), 2)
    offene = [w for w in alle_wetten if not w.aufgeloest]
    tiefen_wetten = [w for w in alle_wetten if w.tiefe_usd_bis_deckel is not None]
    kapazitaet: Optional[float] = None
    auslastung: Optional[float] = None
    if tiefen_wetten:
        kapazitaet = round(
            sum(w.tiefe_usd_bis_deckel or 0.0 for w in tiefen_wetten), 2
        )
        if kapazitaet > 0:
            auslastung = round(
                sum(w.einsatz_usd for w in tiefen_wetten) / kapazitaet * 100.0, 1
            )
    return RunsAggregat(
        n_runs=len(runs),
        n_wetten=len(alle_wetten),
        gewonnen=sum(1 for w in aufgeloeste if w.gewonnen),
        verloren=sum(1 for w in aufgeloeste if not w.gewonnen),
        offen=len(offene),
        einsatz_usd=round(sum(w.einsatz_usd for w in alle_wetten), 2),
        aufgeloester_einsatz_usd=aufgeloester_einsatz,
        realisierter_payout_usd=payout,
        realisierter_pnl_usd=pnl,
        roi_realisiert_pct=(
            round(pnl / aufgeloester_einsatz * 100.0, 1)
            if aufgeloester_einsatz > 0
            else None
        ),
        offener_einsatz_usd=round(sum(w.einsatz_usd for w in offene), 2),
        sichtbare_tiefe_usd=kapazitaet,
        einsatz_zu_sichtbarer_tiefe_pct=auslastung,
    )


def discover_runs(live_root: Path) -> List[Path]:
    """Run-Verzeichnisse unter ``live_root`` (haben ein decisions_log.jsonl)."""

    if not live_root.exists():
        return []
    return sorted(
        p for p in live_root.iterdir()
        if p.is_dir() and (p / "decisions_log.jsonl").exists()
    )


def lade_wallet_abgleich(
    quelle: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Kuratierter Wallet-Abgleich (None, wenn die Quelldatei fehlt).

    Der Default wird zur Laufzeit aus dem Modul-Attribut gelesen
    (test-/monkeypatch-freundlich).
    """

    quelle = quelle if quelle is not None else WALLET_ABGLEICH_QUELLE
    if not quelle.exists():
        return None
    try:
        return json.loads(quelle.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def build_runs_payload(
    *,
    live_root: Path,
    resolutions_dir: Path = RESOLUTIONS_DIR_DEFAULT,
    now_utc: Optional[str] = None,
) -> RunsPayload:
    now = now_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    runs: List[RunEintrag] = []
    for run_dir in discover_runs(live_root):
        profil = run_dir.name
        snapshot_path = run_dir / "gamma_event_snapshot.json"
        snapshot = (
            json.loads(snapshot_path.read_text(encoding="utf-8"))
            if snapshot_path.exists()
            else {}
        )
        resolutions_path = resolutions_dir / f"resolutions_{profil}.json"
        resolutions = (
            json.loads(resolutions_path.read_text(encoding="utf-8"))
            if resolutions_path.exists()
            else {}
        )
        tape_path = resolutions_dir / f"tape_{profil}.json"
        tape = (
            json.loads(tape_path.read_text(encoding="utf-8"))
            if tape_path.exists()
            else None
        )
        runs.append(
            build_run(
                profil=profil,
                events=_read_jsonl(run_dir / "bot_events.jsonl"),
                decisions=_read_jsonl(run_dir / "decisions_log.jsonl"),
                snapshot=snapshot,
                resolutions=resolutions,
                tape=tape,
            )
        )
    runs.sort(key=lambda r: r.drop_erkannt_utc or "")
    abgleich = lade_wallet_abgleich()
    if abgleich:
        events = abgleich.get("events", {}) or {}
        runs = [
            r.model_copy(
                update={"wallet_netto_usd": (events.get(r.profil) or {}).get("netto_usd")}
            )
            for r in runs
        ]
    aggregat = build_aggregat(runs)
    if abgleich:
        aggregat = aggregat.model_copy(update={
            "wallet_netto_usd": abgleich.get("gesamt_netto_usd"),
            "wallet_abgleich_stand": abgleich.get("stand"),
        })
    return RunsPayload(
        hinweis=HINWEIS,
        stand_utc=now,
        kennzeichnung="live/descriptive",
        aggregat=aggregat,
        runs=runs,
    )


# ---------------------------------------------------------------------------
# Optionaler read-only Netzpfad: Aufloesungs-Cache auffrischen
# ---------------------------------------------------------------------------


def fetch_resolutions(
    live_root: Path, resolutions_dir: Path = RESOLUTIONS_DIR_DEFAULT
) -> List[Path]:
    """Aufloesungs-Cache je Run via Gamma auffrischen (read-only)."""

    import httpx

    written: List[Path] = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    resolutions_dir.mkdir(parents=True, exist_ok=True)
    for run_dir in discover_runs(live_root):
        snapshot_path = run_dir / "gamma_event_snapshot.json"
        if not snapshot_path.exists():
            continue
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        ids = {str(m.get("id")) for m in snapshot.get("markets", []) if m.get("id")}
        event_slug = str(snapshot.get("slug") or "")
        if not ids or not event_slug:
            continue
        # Gamma beantwortet /markets?id=... fuer diese Maerkte inzwischen leer;
        # /events?slug=... traegt dieselben Maerkte inkl. closed/outcomePrices.
        response = httpx.get(
            GAMMA_EVENTS_URL,
            params={"slug": event_slug},
            headers=HTTP_HEADERS,
            timeout=60,
        )
        response.raise_for_status()
        events = response.json() or []
        event_markets = events[0].get("markets", []) if events else []
        maerkte: Dict[str, Any] = {}
        for markt in event_markets:
            if str(markt.get("id")) not in ids:
                continue
            prices = markt.get("outcomePrices")
            prices = (
                json.loads(prices) if isinstance(prices, str) else (prices or [])
            )
            closed = bool(markt.get("closed"))
            maerkte[str(markt.get("id"))] = {
                "frage": str(markt.get("question") or ""),
                "closed": closed,
                "outcome_yes": (
                    (float(prices[0]) > 0.99) if (closed and prices) else None
                ),
                "aktueller_yes_preis": (
                    None if closed or not prices else float(prices[0])
                ),
            }
        payload = {
            "profil": run_dir.name,
            "event_slug": event_slug,
            "event_titel": str(events[0].get("title") or "") if events else "",
            "abgerufen_utc": now,
            "quelle": "gamma-api.polymarket.com/events (oeffentlich, read-only)",
            "maerkte": maerkte,
        }
        target = resolutions_dir / f"resolutions_{run_dir.name}.json"
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        written.append(target)
    return written


def _load_own_wallets(live_root: Path) -> set[str]:
    """Eigene Wallet-Adressen (lowercase) NUR fuer das interne Tape-Matching.

    Die Adressen verlassen diese Funktion nicht: der Cache und alle
    publizierten Artefakte tragen nur ein ``eigen``-Flag.
    """

    wallet_path = live_root / "deposit_wallet.json"
    if not wallet_path.exists():
        return set()
    data = json.loads(wallet_path.read_text(encoding="utf-8"))
    own = set()
    for key in ("deposit_wallet", "owner_eoa"):
        value = str(data.get(key) or "").strip().lower()
        if value.startswith("0x") and len(value) == 42:
            own.add(value)
    return own


def fetch_trade_tape(
    live_root: Path, tape_dir: Path = RESOLUTIONS_DIR_DEFAULT
) -> List[Path]:
    """Oeffentliches Taker-Trade-Tape je Run-Markt cachen (read-only).

    Ein GET je Markt gegen die Data-API; jede Zeile wird beim Schreiben
    anonymisiert (Zeit, Seite, Preis, Groesse, ``eigen``-Flag) -- keine
    Wallets, keine Namen, keine Tx-Hashes im Cache.
    """

    import httpx

    own_wallets = _load_own_wallets(live_root)
    written: List[Path] = []
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    tape_dir.mkdir(parents=True, exist_ok=True)
    for run_dir in discover_runs(live_root):
        snapshot_path = run_dir / "gamma_event_snapshot.json"
        if not snapshot_path.exists():
            continue
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        maerkte: Dict[str, List[Dict[str, Any]]] = {}
        for markt in snapshot.get("markets", []):
            mid = str(markt.get("id") or "")
            condition_id = str(markt.get("conditionId") or "")
            if not mid or not condition_id:
                continue
            rows: List[Dict[str, Any]] = []
            offset = 0
            while True:
                response = httpx.get(
                    DATA_API_TRADES_URL,
                    params={
                        "market": condition_id,
                        "limit": 500,
                        "offset": offset,
                    },
                    headers=HTTP_HEADERS,
                    timeout=60,
                )
                response.raise_for_status()
                batch = response.json() or []
                for trade in batch:
                    ts = datetime.fromtimestamp(
                        int(trade.get("timestamp") or 0), timezone.utc
                    )
                    rows.append(
                        {
                            "ts_utc": ts.isoformat().replace("+00:00", "Z"),
                            "side": str(trade.get("side") or ""),
                            "outcome": str(trade.get("outcome") or ""),
                            "preis": float(trade.get("price") or 0.0),
                            "size": float(trade.get("size") or 0.0),
                            "eigen": (
                                str(trade.get("proxyWallet") or "").lower()
                                in own_wallets
                            ),
                        }
                    )
                if len(batch) < 500:
                    break
                offset += 500
            rows.sort(key=lambda r: r["ts_utc"])
            maerkte[mid] = rows
        payload = {
            "profil": run_dir.name,
            "event_slug": str(snapshot.get("slug") or ""),
            "abgerufen_utc": now,
            "quelle": TAPE_QUELLE,
            "maerkte": maerkte,
        }
        target = tape_dir / f"tape_{run_dir.name}.json"
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
        )
        written.append(target)
    return written


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------


def publish_runs(
    payload: RunsPayload,
    *,
    publish_dir: Path = PUBLISH_DIR_DEFAULT,
    extra_publish_dir: Optional[Path] = None,
) -> List[Path]:
    """runs.json validiert + Gate-geprueft in die Zielordner schreiben."""

    serialized = payload.model_dump_json(indent=1)
    run_redaction_gate({RUNS_FILE: serialized})
    written: List[Path] = []
    for target_dir in [publish_dir] + (
        [extra_publish_dir] if extra_publish_dir else []
    ):
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / RUNS_FILE
        target.write_text(serialized + "\n", encoding="utf-8")
        written.append(target)
    return written


def build_postmortems_payload(
    quelle: Path = POSTMORTEMS_QUELLE, now_utc: Optional[str] = None
) -> Optional[PostmortemsPayload]:
    """Kuratierte Vorfall-Liste validieren (None, wenn Quelldatei fehlt)."""

    if not quelle.exists():
        return None
    roh = json.loads(quelle.read_text(encoding="utf-8"))
    now = now_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return PostmortemsPayload(
        hinweis=str(roh.get("hinweis") or ""),
        stand_utc=now,
        kennzeichnung="curated/postmortem",
        eintraege=[PostmortemEintrag(**e) for e in roh.get("eintraege", [])],
    )


#: Protokoll-Eckdaten (Version 2, bestaetigt 18.07.2026 — Quelle unten).
_PILOT_PROTOKOLL = PilotProtokollInfo(
    quelle="docs/project/PILOT_PROTOKOLL_ECHTGELD_2026-07-11.md (Version 2)",
    budget_usdc=100.0,
    einsatz_je_trade_usdc=10.0,
    regel_freeze_datum="2026-07-18",
    handelsfenster_bis="2026-08-01",
    arm1_kurz=(
        "Referenz-entschieden-Fade: bereits irreversibel entschiedene Seite "
        "handelt noch <= 0.97; Kandidaten werden manuell verifiziert."
    ),
    arm2_kurz=(
        "Favoriten-Seite (Tail-Fade): 0.90-0.97 bei <= 21 Tagen Restlaufzeit, "
        "Exit nur ueber die Aufloesung."
    ),
)


def build_pilot_payload(
    pilot_dir: Path = PILOT_DIR_DEFAULT,
    now_utc: Optional[str] = None,
    max_neueste: int = 15,
) -> Optional[PilotPayload]:
    """pilot.json aus den read-only Watcher-/Trade-Artefakten bauen."""

    metadata_path = pilot_dir / "watcher_metadata.json"
    signals_path = pilot_dir / "signals.csv"
    if not metadata_path.exists() or not signals_path.exists():
        return None
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))

    def _f(wert: Any) -> Optional[float]:
        try:
            return float(wert)
        except (TypeError, ValueError):
            return None

    signale: List[PilotSignalKompakt] = []
    zaehler: Dict[str, int] = {}
    with open(signals_path, encoding="utf-8", newline="") as handle:
        for zeile in csv.DictReader(handle):
            schluessel = f"{zeile.get('arm', '?')}:{zeile.get('status', '?')}"
            zaehler[schluessel] = zaehler.get(schluessel, 0) + 1
            signale.append(
                PilotSignalKompakt(
                    ts_utc=str(zeile.get("ts_utc") or ""),
                    arm=str(zeile.get("arm") or ""),
                    frage=str(zeile.get("frage") or "")[:120],
                    seite=str(zeile.get("seite") or ""),
                    signal_preis=_f(zeile.get("signal_preis")),
                    buchtiefe_usd=_f(zeile.get("buchtiefe_usd")),
                    restlaufzeit_tage=_f(zeile.get("restlaufzeit_tage")),
                    status=str(zeile.get("status") or ""),
                )
            )

    trades: List[Dict[str, Optional[str]]] = []
    trades_path = pilot_dir / "trades.csv"
    if trades_path.exists():
        with open(trades_path, encoding="utf-8", newline="") as handle:
            trades = [dict(z) for z in csv.DictReader(handle)]

    now = now_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return PilotPayload(
        hinweis=(
            "Read-only candidate scanner of the pre-registered small-stake "
            "field test. Signals are rule matches, not recommendations; all "
            "trading decisions are made manually by the author."
        ),
        stand_utc=now,
        kennzeichnung="pilot/preregistered",
        protokoll=_PILOT_PROTOKOLL,
        watcher_lauf_ts_utc=meta.get("lauf_ts_utc"),
        watcher_parameter=dict(meta.get("parameter") or {}),
        watcher_statistik={
            k: int(v) for k, v in (meta.get("statistik") or {}).items()
        },
        signal_zaehler=zaehler,
        signale_neueste=sorted(
            signale, key=lambda s: s.ts_utc, reverse=True
        )[:max_neueste],
        trades=trades,
    )


def publish_payloads(
    payloads: Dict[str, str],
    *,
    publish_dir: Path = PUBLISH_DIR_DEFAULT,
    extra_publish_dir: Optional[Path] = None,
) -> List[Path]:
    """Beliebige JSON-Payloads Gate-geprueft in die Zielordner schreiben."""

    run_redaction_gate(payloads)
    written: List[Path] = []
    for target_dir in [publish_dir] + (
        [extra_publish_dir] if extra_publish_dir else []
    ):
        target_dir.mkdir(parents=True, exist_ok=True)
        for name, serialized in payloads.items():
            target = target_dir / name
            target.write_text(serialized + "\n", encoding="utf-8")
            written.append(target)
    return written


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Live-Run-Dashboard (runs.json) aus den Run-Logs bauen."
    )
    parser.add_argument(
        "--live-root",
        type=Path,
        default=LIVE_BASE_DIR,
        help="Wurzel der Run-Verzeichnisse (Default: data/live im Repo).",
    )
    parser.add_argument(
        "--publish-dir",
        type=Path,
        default=None,
        help="Zusaetzlicher Zielordner (z.B. public/data der Website).",
    )
    parser.add_argument(
        "--fetch-resolutions",
        action="store_true",
        help="Aufloesungs-Cache vor dem Bauen read-only via Gamma auffrischen.",
    )
    parser.add_argument(
        "--fetch-tape",
        action="store_true",
        help=(
            "Anonymisiertes Taker-Trade-Tape je Run-Markt read-only via "
            "Data-API auffrischen (fuer die Race-Felder)."
        ),
    )
    args = parser.parse_args(argv)

    if not args.live_root.exists():
        print(
            f"ABBRUCH: live-root {args.live_root} nicht vorhanden -- "
            "bestehendes runs.json bleibt unveraendert.",
            file=sys.stderr,
        )
        return 2

    try:
        if args.fetch_resolutions:
            for path in fetch_resolutions(args.live_root):
                print(f"Aufloesungs-Cache: {path}")
        if args.fetch_tape:
            for path in fetch_trade_tape(args.live_root):
                print(f"Tape-Cache: {path}")
        payload = build_runs_payload(live_root=args.live_root)
        written = publish_runs(payload, extra_publish_dir=args.publish_dir)
        extra_payloads: Dict[str, str] = {}
        postmortems = build_postmortems_payload()
        if postmortems is not None:
            extra_payloads[POSTMORTEMS_FILE] = postmortems.model_dump_json(indent=1)
        pilot = build_pilot_payload()
        if pilot is not None:
            extra_payloads[PILOT_FILE] = pilot.model_dump_json(indent=1)
        if extra_payloads:
            written += publish_payloads(
                extra_payloads, extra_publish_dir=args.publish_dir
            )
    except (RedactionGateError, ValueError, RuntimeError) as exc:
        print(f"ABBRUCH: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "written": [str(p) for p in written],
                "n_runs": payload.aggregat.n_runs,
                "n_wetten": payload.aggregat.n_wetten,
                "einsatz_usd": payload.aggregat.einsatz_usd,
                "realisierter_pnl_usd": payload.aggregat.realisierter_pnl_usd,
            },
            ensure_ascii=False,
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
