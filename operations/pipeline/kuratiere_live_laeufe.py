"""Kuratierte, versionierbare Kopien abgeschlossener Live-Laeufe erzeugen.

Hintergrund: ``data/live/`` ist gitignored und existiert nur in dem Checkout,
in dem die Bots gelaufen sind. Die taegliche Kette laeuft aber in einer anderen
Arbeitskopie und publizierte darum ein leeres ``pipeline_forward.json``.

Dieses Modul schreibt je Lauf eine reduzierte Kopie nach
``data/live_curated/<profil>/``. Kopiert werden AUSSCHLIESSLICH die Felder, die
``daily_review_run.build_pipeline_forward`` ohnehin publiziert:

* ``decisions_log.jsonl``: ``wall_ts_utc`` (nur zur Sortierung der Laeufe, wird
  nicht publiziert), ``decision.{action,reason,limit_price}``,
  ``result.size_usd`` sowie ``book_snapshot.{asks,bids}`` auf ``price``/``size``
  reduziert (daraus werden bester Brief- und Geldkurs abgeleitet).
* ``bot_events.jsonl``: nur die Ereignisse mit Wortzaehler-Staenden
  (``chunk``/``staende`` und ``fertig``/``endstaende``), in Original-Reihenfolge,
  damit der Endstand identisch bleibt.

Bewusst NICHT kopiert: ``token_id``, ``market_id``,
``result.status``/``detail``/``size_shares`` (enthaelt gekuerzte Wallet-Ids),
Buch-Zeitstempel, Orderbuch-CSV, Bot-Logs, ``deposit_wallet.json``,
Audio- und Videodateien. ``decision.outcome`` und die Buch-Groessen
bleiben seit 27.07. erhalten — die Extraktionsquote des Publish-Schritts
braucht Seiten-Fallback und Ebenen-Tiefe (beides redaktionssicher). Vor dem Schreiben laeuft dasselbe Redaktions-Gate wie
im Publish-Schritt ueber jede erzeugte Datei; ein Fund bricht ab.

Aufruf::

    python -m operations.pipeline.kuratiere_live_laeufe \
        --live-root C:\\Users\\chole\\ba-thesis\\data\\live
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from operations.pipeline.daily_review_run import (
    LIVE_CURATED_DIR,
    RedactionGateError,
    live_roots,
    scan_payload_text,
)

#: Ereignisarten mit Wortzaehler-Staenden -> Feld mit den Zaehlern.
COUNTER_EVENTS = {"chunk": "staende", "fertig": "endstaende"}


def kuratiere_entscheidung(record: Dict[str, Any]) -> Dict[str, Any]:
    """Eine Zeile aus ``decisions_log.jsonl`` auf die Publish-Felder kuerzen."""

    decision = record.get("decision", {}) or {}
    result = record.get("result", {}) or {}
    book = record.get("book_snapshot", {}) or {}

    def _preise(seite: str) -> List[Dict[str, Any]]:
        # price UND size behalten: die Extraktionsquote des Publish-
        # Schritts braucht die Ebenen-Tiefe (verfuegbare USD unter dem
        # Deckel); beides ist redaktionssicher (keine Wallet-Daten).
        eintraege: List[Dict[str, Any]] = []
        for entry in book.get(seite, []) or []:
            if isinstance(entry, dict) and entry.get("price") is not None:
                schlank_entry: Dict[str, Any] = {"price": entry["price"]}
                if entry.get("size") is not None:
                    schlank_entry["size"] = entry["size"]
                eintraege.append(schlank_entry)
        return eintraege

    schlank: Dict[str, Any] = {
        "decision": {
            "action": decision.get("action", "NONE"),
            "reason": decision.get("reason", ""),
            "limit_price": decision.get("limit_price"),
            # Seiten-Fallback fuer den Deckel der Extraktionsquote.
            "outcome": decision.get("outcome"),
        },
        "result": {"size_usd": result.get("size_usd")},
        "book_snapshot": {"asks": _preise("asks"), "bids": _preise("bids")},
    }
    if record.get("wall_ts_utc"):
        schlank["wall_ts_utc"] = record["wall_ts_utc"]
    return schlank


def kuratiere_ereignis(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Nur Wortzaehler-Ereignisse behalten, alles andere verwerfen."""

    art = str(event.get("art", ""))
    feld = COUNTER_EVENTS.get(art)
    if feld is None or not isinstance(event.get(feld), dict):
        return None
    return {"art": art, feld: {str(k): int(v) for k, v in event[feld].items()}}


def _lies_jsonl(path: Path) -> List[Dict[str, Any]]:
    zeilen: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            zeilen.append(record)
    return zeilen


def _schreibe_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    text = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    treffer = scan_payload_text(path.name, text)
    if treffer:
        raise RedactionGateError(
            f"Redaktions-Gate: {path} enthaelt {', '.join(sorted(set(treffer)))}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@dataclass
class LaufKuration:
    profil: str
    n_entscheidungen: int
    n_zaehler_ereignisse: int


def kuratiere_lauf(quell_dir: Path, ziel_dir: Path) -> LaufKuration:
    """Einen Lauf kuratieren; schreibt nach ``ziel_dir``."""

    entscheidungen = [
        kuratiere_entscheidung(record)
        for record in _lies_jsonl(quell_dir / "decisions_log.jsonl")
    ]
    _schreibe_jsonl(ziel_dir / "decisions_log.jsonl", entscheidungen)

    ereignisse: List[Dict[str, Any]] = []
    events_path = quell_dir / "bot_events.jsonl"
    if events_path.exists():
        for event in _lies_jsonl(events_path):
            kuratiert = kuratiere_ereignis(event)
            if kuratiert is not None:
                ereignisse.append(kuratiert)
    if ereignisse:
        _schreibe_jsonl(ziel_dir / "bot_events.jsonl", ereignisse)

    return LaufKuration(
        profil=ziel_dir.name,
        n_entscheidungen=len(entscheidungen),
        n_zaehler_ereignisse=len(ereignisse),
    )


def kuratiere_alle(live_root: Path, ziel_root: Path) -> List[LaufKuration]:
    """Alle Laeufe unter ``live_root`` mit ``decisions_log.jsonl`` kuratieren."""

    ergebnisse: List[LaufKuration] = []
    for quell_dir in sorted(p for p in live_root.iterdir() if p.is_dir()):
        if not (quell_dir / "decisions_log.jsonl").exists():
            continue
        ergebnisse.append(kuratiere_lauf(quell_dir, ziel_root / quell_dir.name))
    return ergebnisse


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--live-root",
        type=Path,
        default=None,
        help="Wurzel der Lauf-Verzeichnisse; ohne Angabe die uebliche Suchreihenfolge.",
    )
    parser.add_argument("--ziel", type=Path, default=LIVE_CURATED_DIR)
    args = parser.parse_args(argv)

    roots = [args.live_root] if args.live_root else live_roots()
    roots = [root for root in roots if root and Path(root).is_dir()]
    # Das Ziel darf nie zugleich Quelle sein (sonst kuratiert man sich selbst).
    roots = [root for root in roots if Path(root).resolve() != args.ziel.resolve()]
    if not roots:
        print("ABBRUCH: keine Live-Wurzel gefunden", file=sys.stderr)
        return 2

    try:
        ergebnisse = kuratiere_alle(Path(roots[0]), args.ziel)
    except RedactionGateError as exc:
        print(f"ABBRUCH: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "quelle": str(roots[0]),
                "ziel": str(args.ziel),
                "laeufe": [
                    {
                        "profil": e.profil,
                        "entscheidungen": e.n_entscheidungen,
                        "zaehler_ereignisse": e.n_zaehler_ereignisse,
                    }
                    for e in ergebnisse
                ],
            },
            ensure_ascii=False,
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
