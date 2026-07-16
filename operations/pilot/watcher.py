"""Pilot-Watcher: read-only Kandidaten-Scanner fuer den Echtgeld-Mini-Piloten.

Quelle der Regeln: docs/project/PILOT_PROTOKOLL_ECHTGELD_2026-07-11.md
(Version 2 vom 16.07.2026). Die Konstanten unten sind die dort ex ante
festgelegten Parameter; Aenderungen laufen nur ueber eine neue
Protokoll-Version, nicht ueber diesen Code.

Der Watcher hat bewusst keinen Order-Pfad: Er liest ausschliesslich
oeffentliche Gamma-/CLOB-Endpunkte, schreibt begrenzte CSV-Ausgaben und
ueberlaesst jede Handelsentscheidung dem Menschen (Protokoll: "gehandelt
wird manuell durch die Studentin").

Arm 1 liefert ausdruecklich nur Kandidaten (`kandidat_referenz_pruefen`):
Ob die dokumentierte Referenzquelle den Ausgang wirklich irreversibel
entschieden hat, prueft die Studentin manuell. Automatisch erkannt wird
nur, was ohne Referenz-Feed erkennbar ist (Stichtag verstrichen oder
"ever/reaches"-Formulierung plus fuehrende Seite im Preisfenster).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from operations.pipeline.orderbook import (
    ausfuehrbare_tiefe_usd,
    best_ask,
    fetch_book,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PILOT_DIR = REPO_ROOT / "pilot"

PROTOKOLL_QUELLE = (
    "docs/project/PILOT_PROTOKOLL_ECHTGELD_2026-07-11.md (Version 2, 2026-07-16)"
)

# --- Eingefrorene Parameter aus dem Pilot-Protokoll V2 ---------------------
# Arm 1: Referenz-entschieden-Fade
ARM1_MAX_ENTRY_PREIS = 0.97  # Kauf nur, solange Briefkurs hoechstens 0.97
# Arm 2: Favoriten-Seite (Tail-Fade)
ARM2_MIN_PREIS = 0.90  # Favorit handelt zwischen 0.90 ...
ARM2_MAX_PREIS = 0.97  # ... und 0.97
ARM2_MAX_RESTLAUFZEIT_TAGE = 21.0
ARM2_SPAETESTE_AUFLOESUNG = datetime(2026, 8, 2, 23, 59, 59, tzinfo=timezone.utc)
# Beide Arme
MIN_BUCHTIEFE_USDC = 20.0  # Orderbuchtiefe auf der Kaufseite
MAX_TRADES_PRO_MARKT = 1
# Repo-Guardrail (begrenzte Outputs), nicht Teil des Protokolls:
MAX_SIGNALE_PRO_LAUF = 50

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"
HTTP_HEADERS = {"User-Agent": "ba-thesis-pilot-watcher/1.0 (read-only)"}

TRADES_CSV_FELDER = [
    "zeitstempel_utc", "markt_id", "markt_frage", "arm", "signal_regel",
    "signal_ausloesewert", "seite", "signalpreis", "ausfuehrungspreis",
    "groesse_usd", "gebuehren_usd", "slippage",
    "orderbuchtiefe_einstieg_usd", "exit_zeit_utc", "exit_preis",
    "exit_grund", "bemerkung",
]

SIGNAL_CSV_FELDER = [
    "ts_utc", "arm", "market_id", "frage", "seite", "token_id",
    "signal_preis", "buchtiefe_usd", "restlaufzeit_tage", "end_date",
    "regel", "ausloesewert", "status", "hinweis",
]

_KRYPTO = re.compile(
    r"\b(bitcoin|btc|ethereum|eth|solana|sol|xrp|ripple|doge(coin)?|"
    r"cardano|ada|crypto)\b",
    re.IGNORECASE,
)
_NUMERISCHE_REFERENZ = re.compile(
    r"\$\s?\d[\d,\.]*|\b\d[\d,]*(\.\d+)?\s*(usd|usdc|dollars?)\b",
    re.IGNORECASE,
)
_REFERENZQUELLE = re.compile(
    r"\b(binance|coinbase|chainlink|coingecko|coinmarketcap|kraken|"
    r"bitstamp|pyth|uma)\b",
    re.IGNORECASE,
)
_AUSNAHMEBEDINGUNG = re.compile(r"\bunless\b|\bexcept\b|\bonly if\b", re.IGNORECASE)
_IRREVERSIBEL_STIL = re.compile(
    r"\b(ever|at any point|at any time|touch(es)?|reach(es)?|hit(s)?)\b",
    re.IGNORECASE,
)


@dataclass
class PilotSignal:
    ts_utc: str
    arm: str  # "arm1" oder "arm2"
    market_id: str
    frage: str
    seite: str
    token_id: str
    signal_preis: float
    buchtiefe_usd: float
    restlaufzeit_tage: float | None
    end_date: str
    regel: str
    ausloesewert: str
    status: str  # "signal" oder "kandidat_referenz_pruefen"
    hinweis: str = ""


# ------------------------------------------------------------ Parsen


def _json_liste(market: dict, feld: str) -> list:
    roh = market.get(feld)
    if roh is None:
        return []
    if isinstance(roh, str):
        try:
            return list(json.loads(roh))
        except (ValueError, TypeError):
            return []
    return list(roh)


def parse_end_date(market: dict) -> datetime | None:
    roh = market.get("endDate") or market.get("end_date_iso") or ""
    if not roh:
        return None
    try:
        dt = datetime.fromisoformat(str(roh).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def restlaufzeit_tage(end_date: datetime, now: datetime) -> float:
    return (end_date - now).total_seconds() / 86400.0


def hat_ausnahmebedingung(description: str) -> bool:
    """Auffaellige Aufloesungsregeln (unless/except/only if) -> unklar."""
    return bool(_AUSNAHMEBEDINGUNG.search(description or ""))


def hat_laufenden_streit(market: dict) -> bool:
    status = str(market.get("umaResolutionStatus") or "").lower()
    return bool(market.get("disputed")) or status in {"disputed", "challenged"}


def ist_krypto_referenzmarkt(market: dict) -> bool:
    """Arm-1-Universum: Krypto mit numerischer, dokumentierter Referenz."""
    frage = market.get("question", "") or ""
    beschreibung = market.get("description", "") or ""
    return bool(
        _KRYPTO.search(frage)
        and _NUMERISCHE_REFERENZ.search(frage + " " + beschreibung)
        and _REFERENZQUELLE.search(beschreibung)
    )


def _seiten(market: dict) -> list[tuple[str, str, float]]:
    """(Outcome-Name, Token-ID, Gamma-Preis) je Seite; [] wenn nicht binaer."""
    outcomes = [str(o) for o in _json_liste(market, "outcomes")]
    tokens = [str(t) for t in _json_liste(market, "clobTokenIds")]
    preise_roh = _json_liste(market, "outcomePrices")
    if len(outcomes) != 2 or len(tokens) != 2 or len(preise_roh) != 2:
        return []
    try:
        preise = [float(p) for p in preise_roh]
    except (TypeError, ValueError):
        return []
    return list(zip(outcomes, tokens, preise))


# ------------------------------------------------------------ Arme


def pruefe_arm1(market: dict, now: datetime) -> tuple[str, str] | None:
    """Arm-1-Vorfilter ohne Orderbuch; (grund_regel, hinweis) oder None."""
    if not ist_krypto_referenzmarkt(market):
        return None
    end_date = parse_end_date(market)
    stichtag_verstrichen = end_date is not None and end_date <= now
    irreversibel_moeglich = bool(
        _IRREVERSIBEL_STIL.search(market.get("question", "") or "")
    )
    if not (stichtag_verstrichen or irreversibel_moeglich):
        return None
    if stichtag_verstrichen:
        return (
            "arm1_stichtag_verstrichen",
            "Stichtag verstrichen, Markt unaufgeloest: Referenzquelle "
            "manuell pruefen, ob der Ausgang irreversibel entschieden ist.",
        )
    return (
        "arm1_schwelle_moeglich",
        "Formulierung erlaubt irreversible Entscheidung vor Stichtag: "
        "Referenzquelle manuell pruefen (Schwelle erreicht?).",
    )


def pruefe_arm2_vorfilter(market: dict, now: datetime) -> str | None:
    """Arm-2-Vorfilter ohne Orderbuch; Skip-Grund oder None (= weiter)."""
    end_date = parse_end_date(market)
    if end_date is None:
        return "end_date_fehlt"
    if end_date > ARM2_SPAETESTE_AUFLOESUNG:
        return "aufloesung_nach_stichtag"
    rest = restlaufzeit_tage(end_date, now)
    if rest < 0:
        return "bereits_abgelaufen"
    if rest > ARM2_MAX_RESTLAUFZEIT_TAGE:
        return "restlaufzeit_ueber_21_tagen"
    if hat_ausnahmebedingung(market.get("description", "") or ""):
        return "aufloesungsregel_unklar"
    if hat_laufenden_streit(market):
        return "laufender_streit"
    return None


# ------------------------------------------------------------ Scan


def scan(
    markets: list[dict],
    now: datetime,
    fetch_book_fn=fetch_book,
    gehandelte_maerkte: set[str] | None = None,
    signalisierte: set[tuple[str, str]] | None = None,
) -> tuple[list[PilotSignal], dict]:
    """Prueft Maerkte gegen beide Arme; Arm 1 hat Vorrang (Protokoll).

    Orderbuecher werden nur fuer Vorfilter-Treffer geladen. Ergebnis ist
    deterministisch fuer gleiche Eingaben (now wird injiziert).
    """
    gehandelte_maerkte = gehandelte_maerkte or set()
    signalisierte = signalisierte or set()
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    signale: list[PilotSignal] = []
    statistik: dict[str, int] = {"maerkte": len(markets), "gekappt": 0}

    def zaehle(grund: str) -> None:
        statistik[grund] = statistik.get(grund, 0) + 1

    for market in markets:
        if len(signale) >= MAX_SIGNALE_PRO_LAUF:
            statistik["gekappt"] += 1
            continue
        mid = str(market.get("id"))
        if mid in gehandelte_maerkte:
            zaehle("bereits_gehandelt")  # max. ein Trade pro Markt
            continue
        seiten = _seiten(market)
        if not seiten:
            zaehle("nicht_binaer")
            continue
        end_date = parse_end_date(market)
        end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%SZ") if end_date else ""
        frage = market.get("question", "") or ""

        arm1 = pruefe_arm1(market, now)
        if arm1 is not None:
            if ("arm1", mid) in signalisierte:
                zaehle("arm1_bereits_signalisiert")
                continue
            regel, hinweis = arm1
            seite, token, _ = max(seiten, key=lambda s: s[2])
            try:
                book = fetch_book_fn(token)
            except Exception:  # noqa: BLE001 - Buchabruf darf den Lauf nicht stoppen
                zaehle("arm1_buch_nicht_ladbar")
                continue
            ask = best_ask(book)
            if ask is None or ask > ARM1_MAX_ENTRY_PREIS:
                zaehle("arm1_preis_ueber_097")
                continue
            tiefe = ausfuehrbare_tiefe_usd(book, ARM1_MAX_ENTRY_PREIS)
            if tiefe < MIN_BUCHTIEFE_USDC:
                zaehle("arm1_tiefe_unter_20")
                continue
            rest = restlaufzeit_tage(end_date, now) if end_date else None
            signale.append(PilotSignal(
                ts_utc=ts, arm="arm1", market_id=mid, frage=frage,
                seite=seite, token_id=token, signal_preis=ask,
                buchtiefe_usd=tiefe,
                restlaufzeit_tage=round(rest, 2) if rest is not None else None,
                end_date=end_iso, regel=regel,
                ausloesewert=f"ask={ask}",
                status="kandidat_referenz_pruefen", hinweis=hinweis,
            ))
            continue  # Arm 1 hat Vorrang; kein Arm-2-Signal fuer den Markt

        grund = pruefe_arm2_vorfilter(market, now)
        if grund is not None:
            zaehle(f"arm2_{grund}")
            continue
        if ("arm2", mid) in signalisierte:
            zaehle("arm2_bereits_signalisiert")
            continue
        seite, token, _ = max(seiten, key=lambda s: s[2])
        try:
            book = fetch_book_fn(token)
        except Exception:  # noqa: BLE001
            zaehle("arm2_buch_nicht_ladbar")
            continue
        ask = best_ask(book)
        if ask is None or not (ARM2_MIN_PREIS <= ask <= ARM2_MAX_PREIS):
            zaehle("arm2_preis_ausserhalb_090_097")
            continue
        tiefe = ausfuehrbare_tiefe_usd(book, ARM2_MAX_PREIS)
        if tiefe < MIN_BUCHTIEFE_USDC:
            zaehle("arm2_tiefe_unter_20")
            continue
        rest = restlaufzeit_tage(end_date, now) if end_date else None
        signale.append(PilotSignal(
            ts_utc=ts, arm="arm2", market_id=mid, frage=frage,
            seite=seite, token_id=token, signal_preis=ask,
            buchtiefe_usd=tiefe,
            restlaufzeit_tage=round(rest, 2) if rest is not None else None,
            end_date=end_iso, regel="arm2_favorit_090_097_max21d",
            ausloesewert=f"ask={ask}", status="signal",
        ))

    return signale, statistik


# ------------------------------------------------------------ Ablage


def ensure_trades_template(pfad: Path | None = None) -> Path:
    """Legt pilot/trades.csv mit den Pflichtfeldern an, falls sie fehlt."""
    pfad = pfad or (PILOT_DIR / "trades.csv")
    pfad.parent.mkdir(parents=True, exist_ok=True)
    if not pfad.exists():
        with open(pfad, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=TRADES_CSV_FELDER).writeheader()
    return pfad


def lade_gehandelte_maerkte(pfad: Path | None = None) -> set[str]:
    """Markt-IDs aus pilot/trades.csv (Regel: max. ein Trade pro Markt)."""
    pfad = pfad or (PILOT_DIR / "trades.csv")
    if not pfad.exists():
        return set()
    with open(pfad, newline="", encoding="utf-8") as f:
        return {
            str(zeile.get("markt_id", "")).strip()
            for zeile in csv.DictReader(f)
            if str(zeile.get("markt_id", "")).strip()
        }


def lade_signalisierte(pfad: Path | None = None) -> set[tuple[str, str]]:
    """(arm, market_id)-Paare, die schon in pilot/signals.csv stehen."""
    pfad = pfad or (PILOT_DIR / "signals.csv")
    if not pfad.exists():
        return set()
    with open(pfad, newline="", encoding="utf-8") as f:
        return {
            (str(z.get("arm", "")), str(z.get("market_id", "")))
            for z in csv.DictReader(f)
        }


def schreibe_signale(signale: list[PilotSignal], pfad: Path | None = None) -> Path:
    pfad = pfad or (PILOT_DIR / "signals.csv")
    pfad.parent.mkdir(parents=True, exist_ok=True)
    neu = not pfad.exists()
    with open(pfad, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SIGNAL_CSV_FELDER)
        if neu:
            writer.writeheader()
        for s in signale:
            writer.writerow({k: asdict(s).get(k) for k in SIGNAL_CSV_FELDER})
    return pfad


def schreibe_metadata(
    statistik: dict, anzahl_signale: int, now: datetime, pfad: Path | None = None
) -> Path:
    pfad = pfad or (PILOT_DIR / "watcher_metadata.json")
    pfad.parent.mkdir(parents=True, exist_ok=True)
    inhalt = {
        "lauf_ts_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "protokoll": PROTOKOLL_QUELLE,
        "parameter": {
            "arm1_max_entry_preis": ARM1_MAX_ENTRY_PREIS,
            "arm2_min_preis": ARM2_MIN_PREIS,
            "arm2_max_preis": ARM2_MAX_PREIS,
            "arm2_max_restlaufzeit_tage": ARM2_MAX_RESTLAUFZEIT_TAGE,
            "arm2_spaeteste_aufloesung": ARM2_SPAETESTE_AUFLOESUNG.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "min_buchtiefe_usdc": MIN_BUCHTIEFE_USDC,
            "max_trades_pro_markt": MAX_TRADES_PRO_MARKT,
            "max_signale_pro_lauf": MAX_SIGNALE_PRO_LAUF,
        },
        "tiefen_definition": (
            "ausfuehrbare Ask-Tiefe in USD bis einschliesslich der "
            "Arm-Preisobergrenze"
        ),
        "signale": anzahl_signale,
        "statistik": statistik,
        "order_pfad": "keiner (read-only Watcher, manueller Handel)",
    }
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(inhalt, f, ensure_ascii=False, indent=2)
    return pfad


# ------------------------------------------------------------ Live-Abruf


def fetch_gamma_maerkte(max_seiten: int = 4, seitengroesse: int = 500) -> list[dict]:
    """Aktive, ungeschlossene Maerkte mit Aufloesung bis zum Pilot-Stichtag."""
    import httpx

    maerkte: list[dict] = []
    for seite in range(max_seiten):
        resp = httpx.get(
            GAMMA_MARKETS_URL,
            params={
                "active": "true",
                "closed": "false",
                "limit": seitengroesse,
                "offset": seite * seitengroesse,
                "end_date_max": ARM2_SPAETESTE_AUFLOESUNG.strftime("%Y-%m-%d"),
            },
            headers=HTTP_HEADERS,
            timeout=30.0,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        maerkte.extend(batch)
        if len(batch) < seitengroesse:
            break
    return maerkte


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only Pilot-Watcher (kein Order-Pfad). Regeln: "
            + PROTOKOLL_QUELLE
        )
    )
    parser.add_argument(
        "--snapshot",
        help="JSON-Datei {markets: [...], books: {token_id: book}} statt Live-Abruf",
    )
    parser.add_argument(
        "--out-dir", default=str(PILOT_DIR), help="Ausgabeverzeichnis (Default pilot/)"
    )
    args = parser.parse_args(argv)
    out_dir = Path(args.out_dir)
    now = datetime.now(timezone.utc)

    if args.snapshot:
        with open(args.snapshot, encoding="utf-8") as f:
            snap = json.load(f)
        maerkte = snap.get("markets", [])
        buecher = snap.get("books", {})

        def fetch_book_fn(token_id: str) -> dict:
            return buecher.get(token_id, {})
    else:
        maerkte = fetch_gamma_maerkte()
        fetch_book_fn = fetch_book

    trades_pfad = ensure_trades_template(out_dir / "trades.csv")
    signale, statistik = scan(
        maerkte,
        now,
        fetch_book_fn=fetch_book_fn,
        gehandelte_maerkte=lade_gehandelte_maerkte(trades_pfad),
        signalisierte=lade_signalisierte(out_dir / "signals.csv"),
    )
    schreibe_signale(signale, out_dir / "signals.csv")
    schreibe_metadata(statistik, len(signale), now, out_dir / "watcher_metadata.json")

    for s in signale:
        print(
            f"[{s.arm}] {s.status} {s.market_id} {s.seite} "
            f"ask={s.signal_preis} tiefe={s.buchtiefe_usd} USD "
            f"rest={s.restlaufzeit_tage}d :: {s.frage[:80]}"
        )
    print(
        f"Lauf {now:%Y-%m-%dT%H:%M:%SZ}: {len(maerkte)} Maerkte, "
        f"{len(signale)} Signale/Kandidaten. Details: {out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
