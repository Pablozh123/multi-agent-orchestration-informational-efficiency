"""Bet-Sizing-Analyse fuer duenne Maerkte (REIN LESEND, kein Trading).

Zeigt je Markt aus dem echten Live-Orderbuch:
- die EV-optimale Stopp-Grenze (kaufe Level, solange der Grenzgewinn je
  Share ueber der Mindestschwelle liegt) gegen den aktuellen flachen
  Deckel des Bots (ASK_OBERGRENZE, z.B. 0.90),
- wie viel der Deckel-Einsatz im duennen/negativen Edge-Bereich landet
  (das vermeidbare Risiko),
- die Slippage-Kurve (Einsatz -> Payout-bei-Gewinn -> Grenz-Payout je
  zusaetzlichem Dollar) — genau der Effekt "100 USD -> ~600 gewinnen,
  200 USD -> nur ~700".

Modell (post-Trigger): nach dem Ausloeser ist YES ~sicher (Fair Value
p_win = 1 - Fehlerrate); jede Share unter p_win ist Edge, darueber
negativ. EV je Share bei Preis p = p_win - p. Worst Case (Fehltrigger,
YES loest 0 auf) = voller Einsatz verloren.

KEIN Import von execution.py, KEINE Orders. Nur Orderbuch-Abrufe.

Aufruf:
  BOT_PROFIL=elon_july13 python -m operations.pipeline.sizing_analyse
  ... --fehlerrate 0.01 --min-edge 0.03 --budget 170 --seite yes
  ... --markt tesla         (Detail: Level-Aufschluesselung + Slippage)
"""

from __future__ import annotations

import argparse
import json

from operations.pipeline import config
from operations.pipeline.market_rules import _token_ids
from operations.pipeline.orderbook import fetch_book, now_utc_iso


def asks_aufsteigend(book: dict) -> list[tuple[float, float]]:
    """(Preis, Groesse)-Level der Ask-Seite, aufsteigend nach Preis."""
    roh = book.get("asks") or []
    level = []
    for a in roh:
        try:
            p, s = float(a["price"]), float(a["size"])
        except (KeyError, TypeError, ValueError):
            continue
        if p > 0 and s > 0:
            level.append((p, s))
    level.sort(key=lambda x: x[0])
    return level


def kauf_walk(
    asks: list[tuple[float, float]], max_preis: float, budget: float
) -> dict:
    """Kaufe Level aufsteigend, solange Preis <= max_preis und Budget da.

    Teil-Level werden anteilig genommen. Liefert Kennzahlen des Kaufs.
    """
    usd = 0.0
    shares = 0.0
    n_level = 0
    for preis, groesse in asks:
        if preis > max_preis + 1e-9:
            break
        rest = budget - usd
        if rest <= 1e-9:
            break
        max_usd_level = preis * groesse
        nimm_usd = min(max_usd_level, rest)
        usd += nimm_usd
        shares += nimm_usd / preis
        n_level += 1
    avg = (usd / shares) if shares > 0 else 0.0
    return {"usd": round(usd, 2), "shares": round(shares, 2),
            "avg": round(avg, 4), "n_level": n_level}


def kennzahlen(kauf: dict, p_win: float) -> dict:
    """EV, Payout-bei-Gewinn und Worst Case zu einem Kauf-Ergebnis."""
    shares, usd = kauf["shares"], kauf["usd"]
    payout_gewinn = round(shares, 2)          # jede Share zahlt 1 bei YES
    ev = round(p_win * shares - usd, 2)        # Erwartungswert
    worst = round(-usd, 2)                     # Fehltrigger: alles weg
    rendite = round(ev / usd, 3) if usd > 0 else 0.0
    return {**kauf, "payout_gewinn": payout_gewinn, "ev": ev,
            "worst": worst, "ev_rendite": rendite}


def lade_maerkte() -> list[dict]:
    """(label, yes_token, no_token, frage) je offenem Markt aus dem Snapshot.

    Bewusst unabhaengig von build_rule (dessen Ausnahme-Skip wuerde die
    Elon-Maerkte verwerfen): fuer die Buch-Analyse reichen die Token-IDs.
    """
    with open(config.GAMMA_SNAPSHOT, encoding="utf-8") as f:
        snap = json.load(f)
    out = []
    for m in snap["markets"]:
        frage = (m.get("question") or "")
        if m.get("closed"):
            continue
        q = frage.lower()
        if "no episode" in q or "no qualifying" in q or "will no " in q:
            continue
        yes_id, no_id = _token_ids(m)
        if not yes_id:
            continue
        label = (m.get("slug") or frage)[:60]
        out.append({"label": label, "yes": yes_id, "no": no_id,
                    "frage": frage})
    return out


def analysiere(p_win: float, min_edge: float, budget: float,
               deckel: float, seite: str) -> None:
    opt_max = p_win - min_edge
    print(f"\nSizing-Analyse ({now_utc_iso()}) | Profil {config.PROFIL} | "
          f"Seite {seite.upper()}")
    print(f"Fair Value p_win={p_win:.3f} (Fehlerrate {1 - p_win:.3f}) | "
          f"Mindest-Edge {min_edge:.3f} -> EV-Deckel {opt_max:.3f} | "
          f"Bot-Deckel {deckel:.2f} | Budget {budget:.0f}\n")
    kopf = (f"{'Markt':<40}{'bestAsk':>8}{'Opt$':>7}{'Opt-EV':>8}"
            f"{'Deck$':>7}{'Deck-EV':>8}{'dEV':>7}  Deckel-Urteil")
    print(kopf)
    print("-" * 92)

    summe_opt_ev = summe_deck_ev = 0.0
    for mk in lade_maerkte():
        token = mk["yes"] if seite == "yes" else mk["no"]
        if not token:
            continue
        try:
            asks = asks_aufsteigend(fetch_book(token))
        except Exception as ex:  # noqa: BLE001
            print(f"{mk['label']:<40} Buchfehler: {str(ex)[:20]}")
            continue
        if not asks:
            continue
        best = asks[0][0]
        opt = kennzahlen(kauf_walk(asks, opt_max, budget), p_win)
        deck = kennzahlen(kauf_walk(asks, deckel, budget), p_win)
        # dEV = EV, den der flache Deckel gegenueber dem EV-Optimum liegen
        # laesst. Positiv -> Deckel zu eng (verpasste Edge), da opt_max
        # ueber dem Deckel liegt; negativ -> Deckel zu locker (kauft in
        # duennen/negativen Edge-Bereich, Ueberrisiko).
        d_ev = round(opt["ev"] - deck["ev"], 2)
        if opt_max > deckel + 1e-9 and d_ev > 0.5:
            urteil = "zu eng (Edge verpasst)"
        elif opt_max < deckel - 1e-9 and d_ev > 0.5:
            urteil = "zu locker (Ueberrisiko)"
        else:
            urteil = "ok"
        summe_opt_ev += opt["ev"]
        summe_deck_ev += deck["ev"]
        kurz = mk["label"].replace("will-elon-post-", "").replace(
            "-on-x-this-week", "").replace(
            "-be-said-during-the-next-episode-of-the", "")[:39]
        print(f"{kurz:<40}{best:>8.3f}{opt['usd']:>7.0f}{opt['ev']:>8.1f}"
              f"{deck['usd']:>7.0f}{deck['ev']:>8.1f}{d_ev:>7.1f}  {urteil}")

    print("-" * 92)
    print(f"{'SUMME EV':<40}{'':>8}{'':>7}{summe_opt_ev:>8.1f}"
          f"{'':>7}{summe_deck_ev:>8.1f}"
          f"{summe_opt_ev - summe_deck_ev:>7.1f}")
    print(f"\nOpt$ = EV-optimaler Einsatz (Deckel {opt_max:.3f}) | "
          f"Deck$ = Einsatz beim flachen {deckel:.2f}-Bot-Deckel")
    print("dEV = entgangener Erwartungswert des flachen Deckels je Markt. "
          "Vorzeichen des Urteils haengt an p_win: bei zuverlaessiger "
          "Erkennung (Elon-Text) liegt die EV-Grenze UEBER 0.90 -> Deckel "
          "zu eng.")


def detail(markt_muster: str, p_win: float, min_edge: float,
           budget: float, deckel: float, seite: str) -> None:
    ziel = None
    for mk in lade_maerkte():
        if markt_muster.lower() in mk["label"].lower() or (
                markt_muster.lower() in mk["frage"].lower()):
            ziel = mk
            break
    if ziel is None:
        print(f"Kein Markt passt zu '{markt_muster}'.")
        return
    token = ziel["yes"] if seite == "yes" else ziel["no"]
    asks = asks_aufsteigend(fetch_book(token))
    print(f"\nDetail: {ziel['frage']}  [Seite {seite.upper()}]")
    if not asks:
        print("Leeres Buch.")
        return

    opt_max = p_win - min_edge
    print(f"\nLevel-Aufschluesselung (p_win={p_win:.3f}, "
          f"EV-Grenze {opt_max:.3f}, Deckel {deckel:.2f}):")
    print(f"{'Preis':>7}{'Groesse':>9}{'kum$':>8}{'EV/Share':>9}  Zone")
    kum = 0.0
    for preis, groesse in asks:
        kum += preis * groesse
        ev_share = p_win - preis
        if preis <= opt_max + 1e-9:
            zone = "kaufen (Edge)"
        elif preis <= deckel + 1e-9:
            zone = "Deckel-Wall (duenn/neg)"
        else:
            zone = "ueber Deckel (aus)"
        print(f"{preis:>7.3f}{groesse:>9.1f}{kum:>8.1f}{ev_share:>+9.3f}  {zone}")

    print("\nSlippage-Kurve (kumulativer Kauf aufsteigend, Payout=Shares):")
    print(f"{'Einsatz$':>9}{'Shares':>9}{'avgPreis':>9}"
          f"{'Payout':>8}{'EV':>8}{'Grenz-Payout/$':>15}")
    gitter = [10, 25, 50, 75, 100, 125, 150, 200]
    gitter = [g for g in gitter if g <= budget] + [budget]
    prev_shares = 0.0
    prev_usd = 0.0
    for g in sorted(set(gitter)):
        k = kennzahlen(kauf_walk(asks, deckel, g), p_win)
        d_usd = k["usd"] - prev_usd
        grenz = ((k["shares"] - prev_shares) / d_usd) if d_usd > 1e-6 else 0.0
        print(f"{k['usd']:>9.0f}{k['shares']:>9.1f}{k['avg']:>9.3f}"
              f"{k['payout_gewinn']:>8.1f}{k['ev']:>8.1f}{grenz:>15.2f}")
        prev_shares, prev_usd = k["shares"], k["usd"]
    print("\nGrenz-Payout/$ faellt = jeder weitere Dollar kauft weniger "
          "Shares (Slippage). Faellt er unter ~1.0, kaufst du Shares teurer "
          "als ihr Maximalwert.")


def main() -> None:
    import sys

    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--fehlerrate", type=float, default=0.02,
                   help="P(Fehltrigger); p_win = 1 - Fehlerrate")
    p.add_argument("--p-win", type=float, default=None,
                   help="Fair Value direkt (ueberschreibt --fehlerrate)")
    p.add_argument("--min-edge", type=float, default=0.03,
                   help="Mindest-Grenzgewinn je Share")
    p.add_argument("--budget", type=float, default=config.MAX_USD_GESAMT)
    p.add_argument("--deckel", type=float, default=config.ASK_OBERGRENZE)
    p.add_argument("--seite", choices=["yes", "no"], default="yes")
    p.add_argument("--markt", default=None,
                   help="Detail-Analyse fuer den ersten passenden Markt")
    argv = p.parse_args()

    if not config.GAMMA_SNAPSHOT.exists():
        raise SystemExit(
            f"Kein Snapshot fuer Profil {config.PROFIL}. Zuerst den Bot mit "
            "--refresh-rules starten oder --status laufen lassen.")

    p_win = argv.p_win if argv.p_win is not None else (1.0 - argv.fehlerrate)
    p_win = max(0.0, min(1.0, p_win))

    if argv.markt:
        detail(argv.markt, p_win, argv.min_edge, argv.budget, argv.deckel,
               argv.seite)
    else:
        analysiere(p_win, argv.min_edge, argv.budget, argv.deckel, argv.seite)


if __name__ == "__main__":
    main()
