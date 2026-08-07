"""Erzeugt die Abbildung zur Waehrungsmigration fuer die On-Chain-Fallstudie.

Zeigt, warum ein reiner USDC-Ledger Mitte 2026 verstummt: das monatliche
USDC-Transfervolumen bricht Ende April 2026 ein, waehrend pUSD den Handel
uebernimmt. Die kumulierte PnL-Kurve laeuft ungebrochen weiter. Die Daten sind
Monatsaggregate aus dem vollstaendigen On-Chain-Ledger der Wallet W und aus der
Polymarket-PnL-Kurve; sie sind hier eingebettet, damit die Abbildung ohne die
mehrere Millionen Zeilen grossen Rohdaten reproduzierbar bleibt.

Ausfuehren: python thesis/figures/make_onchain_currency_migration.py
Ausgabe:   thesis/figures/onchain_currency_migration.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

MONATE = [
    "2025-08", "2025-09", "2025-10", "2025-11", "2025-12",
    "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07",
]

# Monatliches Brutto-Transfervolumen je Waehrung (in Mio. USD), aus
# data/ledger_monthly.csv und data/ledger_monthly_pusd.csv (Summe in + out).
USDC_VOL = [1.38, 9.41, 39.58, 61.19, 79.96, 136.04, 133.54, 166.85, 100.84, 2.55, 10.24, 32.31]
PUSD_VOL = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.92, 138.91, 553.31, 521.08]

# Kumulierte PnL zum Monatsende (in Mio. USD), aus der Polymarket-PnL-Kurve.
PNL_KUM = [-0.02, -0.14, 0.04, 1.55, 3.14, 3.90, 4.50, 5.64, 6.76, 9.16, 14.25, 21.91]

MIGRATION_INDEX = 8  # 2026-04, Ende April erfolgt die Umstellung


def main() -> None:
    x = list(range(len(MONATE)))
    fig, ax = plt.subplots(figsize=(10, 5.2))

    breite = 0.42
    ax.bar([i - breite / 2 for i in x], USDC_VOL, breite, label="USDC-Volumen",
           color="#3b6ea5")
    ax.bar([i + breite / 2 for i in x], PUSD_VOL, breite, label="pUSD-Volumen",
           color="#c17d3c")
    ax.set_ylabel("Monatliches Transfervolumen (Mio. USD)")
    ax.set_xticks(x)
    ax.set_xticklabels(MONATE, rotation=45, ha="right")
    ax.set_ylim(0, 600)

    ax.axvline(MIGRATION_INDEX + 0.5, color="#555555", linestyle="--", linewidth=1.2)
    ax.text(MIGRATION_INDEX + 0.6, 560, "Währungsmigration\nUSDC nach pUSD",
            fontsize=8.5, color="#333333", va="top")

    ax2 = ax.twinx()
    ax2.plot(x, PNL_KUM, color="#222222", marker="o", markersize=4, linewidth=1.8,
             label="Kumulierte PnL")
    ax2.set_ylabel("Kumulierte PnL (Mio. USD)")
    ax2.set_ylim(-2, 24)

    linien1, label1 = ax.get_legend_handles_labels()
    linien2, label2 = ax2.get_legend_handles_labels()
    ax.legend(linien1 + linien2, label1 + label2, loc="upper left", fontsize=9)

    ax.set_title("Währungsmigration und ungebrochene PnL der Swisstony-Wallet", fontsize=12)
    fig.tight_layout()

    out = Path(__file__).resolve().parent / "onchain_currency_migration.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"gespeichert -> {out}")


if __name__ == "__main__":
    main()
