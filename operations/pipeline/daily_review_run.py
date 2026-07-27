"""Taeglicher Review-Lauf mit Publish-Schritt fuer die Website.

Ablauf (deterministisch und offline, einzige Ausnahme ist --llm):

0. Optional ``--collect``: der bestehende read-only Polymarket-Collector
   (``polymarket_rolling_history``, source=live) sammelt frische
   Markt-Buckets und schreibt neue Alert-Rows -- die Anomalie-Erkennung
   arbeitet damit auf aktuellen Daten und die Baseline waechst mit jedem
   Tageslauf. Fail-soft: bei Netzfehlern laeuft der Rest mit den
   vorhandenen Alert-Rows weiter.
1. Monitor-Kandidaten-Refresh ueber die bestehenden Module:
   ``monitor_reference_candidates`` -> ``monitor_candidate_review_report``
   -> ``monitor_anomaly_review_queue``. Das ist eine reine Datei-Pipeline
   auf den (ggf. frisch gesammelten) Alert-Rows.
2. ``build_review_queue`` aus ``operations/agents/review_queue``.
   Default ist das deterministische Mock-Backend (kein Netz, kein Key).
   Erst das Flag ``--llm`` aktiviert den produktiven LLM-Betrieb; der Key
   kommt dann aus ``ANTHROPIC_API_KEY`` in ``.env`` (python-dotenv) und
   wird nie geloggt oder publiziert.
   Die Agenten lesen ausschliesslich ueber die MCP-Lesescheibe (vier
   Read-only-Tools, maximal 50 Zeilen pro Antwort, Wallet-Adressen
   maskiert). Der Skeptiker kann die Prioritaet nur SENKEN
   (``confidence_adjustment`` in [-0.3, 0.0]), nie anheben.
3. Snapshot-Rechner: ``category_efficiency_snapshot`` (offline),
   ``mentions_latency`` (nur wenn jede nicht ausgeschlossene Seed-Zeile
   einen Preis-Cache hat -- sonst Skip mit Vermerk, damit garantiert kein
   Netzzugriff passiert) und ``category_latency_examples`` (offline).
4. Export nach ``data/publish/`` als statische JSONs mit
   pydantic-Validierung (fail-closed: Validierungsfehler oder
   Redaktions-Fund => es wird NICHTS geschrieben).
5. Redaktions-Gate vor dem Schreiben: alle Payloads werden auf
   Wallet-Adressmuster (``0x`` + 40 Hex; Token-/Condition-Ids mit 64 Hex
   bleiben erlaubt) und Key-artige Strings geprueft. Fund => Abbruch.
6. ``--publish-dir`` kopiert ``data/publish/`` zusaetzlich in einen
   angegebenen Ordner (z.B. das ``public/data`` der Website).

Die publizierten Inhalte sind deskriptiv (beobachtend/paper). Sie
enthalten keine Handlungsempfehlung zum Handel, keine Finanzberatung,
keine Wallet-Daten und keine PnL-Aussage.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from operations.pipeline.publish_io import schreibe_atomar

REPO_ROOT = Path(__file__).resolve().parents[2]

PUBLISH_DIR_DEFAULT = REPO_ROOT / "data" / "publish"
RESULTS_DIR = REPO_ROOT / "data" / "results"
SEED_PATH = REPO_ROOT / "data" / "events" / "mentions_latency_seed.csv"
MENTIONS_CACHE_DIR = REPO_ROOT / "data" / "raw" / "mentions_latency"
LIVE_BASE_DIR = REPO_ROOT / "data" / "live"
#: Kuratierte, versionierte Kopien der abgeschlossenen Laeufe (nur die
#: publizierbaren Felder, siehe ``scripts/kuratiere_live_laeufe.py``). Sie sind
#: der Fallback, wenn die Arbeitskopie kein ``data/live`` hat -- so publiziert
#: die Kette auf jeder Maschine dieselben Eintraege.
LIVE_CURATED_DIR = REPO_ROOT / "data" / "live_curated"
#: Umgebungsvariable fuer eine abweichende Live-Wurzel (z.B. das Checkout mit
#: den Rohdaten). Explizites ``--live-root`` gewinnt gegen die Variable.
LIVE_ROOT_ENV = "THESIS_LIVE_ROOT"

QUEUE_CSV_PATH = RESULTS_DIR / "monitor_anomaly_review_queue.csv"
SUMMARY_V2_PATH = RESULTS_DIR / "category_efficiency_summary_v2.csv"
LATENCY_EXAMPLES_PATH = RESULTS_DIR / "category_latency_examples.csv"
MENTIONS_CSV_PATH = RESULTS_DIR / "mentions_latency.csv"
DAILY_LLM_AUDIT_PATH = RESULTS_DIR / "daily_review_llm_audit_log.jsonl"

LIVE_PROFILE_CANDIDATES = ("allin_july3", "jre_july6")

PUBLISH_FILES = (
    "queue.json",
    "kategorie_karte.json",
    "mentions_latenz.json",
    "pipeline_forward.json",
    "audit.json",
    "meta.json",
)

#: Publizierte Empfehlungs-Whitelist (Pruef-Empfehlungen, keine
#: Handelsanweisungen). Werte 1:1 aus der Agenten-Schicht.
EMPFEHLUNG_WHITELIST = ("watch", "check_source", "escalate_human")

#: Deskriptiver ``hinweis`` je publizierter Datei (englisch, Website-facing).
DATEI_HINWEISE = {
    "queue.json": (
        "Read-only result of a daily run. Recommendations are verification "
        "steps (watch, check_source, escalate_human), not trades."
    ),
    "kategorie_karte.json": (
        "Brier scores and pricing-speed examples per market category; sport/"
        "pop-culture convergence times are documented upper bounds."
    ),
    "mentions_latenz.json": (
        "Reaction and convergence times of mentions markets after the "
        "content drop; exclusions listed separately."
    ),
    "pipeline_forward.json": (
        "Observing paper run: decision fields and best book prices only, "
        "no wallet data, no return claim."
    ),
    "audit.json": (
        "Transparency about the agent run: counters and hashes only, no "
        "prompts, no vendor or version details."
    ),
    "meta.json": (
        "Run timestamp, backend mode, and principles of the daily "
        "analysis run."
    ),
}

DISCLAIMER = {
    "zweck": (
        "Descriptive research artifacts from a daily, deterministic "
        "review run over public market data."
    ),
    "keine_handlungsempfehlung": (
        "Recommendations are verification steps (watch, check the source, "
        "escalate to a human), not buy or sell signals."
    ),
    "keine_finanzberatung": (
        "No financial or investment advice. No return claim. Pipeline "
        "entries are observing/paper."
    ),
    "datenschutz": (
        "No wallet addresses, no keys, no prompts. Audit as hashes and "
        "counters only."
    ),
}


# ---------------------------------------------------------------------------
# Redaktions-Gate
# ---------------------------------------------------------------------------

#: Wallet-Adressen: ``0x``/``0X`` + exakt 40 Hex ODER eine nackte
#: 40-Hex-Sequenz. Die Lookarounds lassen laengere Hex-Ids
#: (Condition-/Token-Ids mit 64 Hex, sha256-Hashes) unangetastet.
WALLET_RE = re.compile(
    r"0[xX][0-9a-fA-F]{40}(?![0-9a-fA-F])"
    r"|(?<![0-9a-fA-FxX])[0-9a-fA-F]{40}(?![0-9a-fA-F])"
)

#: Key-artige Strings: bekannte Secret-Praefixe, PEM-Marker und
#: ``NAME=WERT``-Paare, deren Name nach einem Secret klingt.
SECRET_PATTERNS = (
    ("anthropic_key", re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{32,}")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("aws_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}")),
    ("pem_marker", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "env_assignment",
        # Quotes/Backslashes sind auf BEIDEN Seiten des Separators erlaubt,
        # damit auch JSON-serialisierte Paare ("api_key": "...") anschlagen.
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret|token|password|private[_-]?key)\b"
            r"[\\'\"]{0,3}\s*[=:]\s*[\\'\"]{0,3}[A-Za-z0-9+/_\-]{16,}"
        ),
    ),
)


class RedactionGateError(RuntimeError):
    """Redaktions-Gate hat ein verbotenes Muster gefunden -- kein Publish."""


def scan_payload_text(name: str, text: str) -> List[str]:
    """Alle Gate-Treffer in ``text``; Fundwerte werden NICHT zurueckgegeben."""

    hits: List[str] = []
    if WALLET_RE.search(text):
        hits.append(f"{name}: wallet_adressmuster (0x + 40 hex)")
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            hits.append(f"{name}: key_muster ({label})")
    return hits


def run_redaction_gate(payloads: Dict[str, str]) -> None:
    """Abbruch, falls irgendein serialisiertes Payload das Gate verletzt."""

    hits: List[str] = []
    for name, text in payloads.items():
        hits.extend(scan_payload_text(name, text))
    if hits:
        raise RedactionGateError(
            "Redaktions-Gate: verbotene Muster gefunden, kein Publish: "
            + "; ".join(hits)
        )


# ---------------------------------------------------------------------------
# pydantic-Schemas (fail-closed: extra='forbid', Literals fuer Whitelists)
# ---------------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QueueFall(_Strict):
    id: str
    markt_slug: str
    zeitfenster: str
    score_band: Literal["high", "medium", "low"]
    empfehlung: Literal["watch", "check_source", "escalate_human"]
    empfehlung_grund: str
    begruendung: str
    skeptic_begruendung: str
    skeptic_abschlag: Optional[float] = Field(default=None, ge=-0.3, le=0.0)
    signale: Dict[str, str]
    ts: str


class QueuePayload(_Strict):
    hinweis: str
    stand_utc: str
    faelle: List[QueueFall]


class KategorieEintrag(_Strict):
    kategorie: str
    brier_t7: Optional[float]
    trefferquote_t7: Optional[float]
    brier_t1: Optional[float]
    trefferquote_t1: Optional[float]
    n_maerkte: int
    n_t7: int
    median_volumen_usd: Optional[float]


class LatenzBeispiel(_Strict):
    kategorie: str
    ereignis: str
    markt_frage: str
    minuten_bis_konvergenz: Optional[float]
    minuten_bis_erste_reaktion: Optional[float]
    t0_utc: str
    praezisions_hinweis: str


class KategorieKartePayload(_Strict):
    hinweis: str
    stand_utc: str
    kategorien: List[KategorieEintrag]
    beispiele: List[LatenzBeispiel]


class MentionsFall(_Strict):
    event: str
    minuten_bis_erste_reaktion: Optional[float]
    minuten_bis_konvergenz: Optional[float]
    stunden_im_handelbaren_fenster: Optional[float]
    korrekt_aufgeloestes_outcome: Literal["YES", "NO"]
    status: Literal["ok"]


class MentionsAusschluss(_Strict):
    event: str
    status: str


class MentionsLatenzPayload(_Strict):
    hinweis: str
    stand_utc: str
    faelle: List[MentionsFall]
    ausschluesse: List[MentionsAusschluss]


class PipelineEintrag(_Strict):
    action: Literal["YES", "NO", "NONE"]
    reason: str
    limit_price: Optional[float]
    bestes_angebot: Optional[float]
    bestes_gebot: Optional[float]
    size_usd: Optional[float]
    #: Extraktionsquote je Kauf: wieviel der im Kaufmoment unter dem
    #: Preisdeckel verfuegbaren Buch-Tiefe (USD) der Sweep tatsaechlich
    #: gekauft hat. Reine Ausfuehrungsguete aus dem Buch-Snapshot des
    #: decisions_log — keine PnL-Aussage. None fuer Nicht-Kaeufe.
    verfuegbar_usd: Optional[float] = None
    extraktionsquote: Optional[float] = None


class PipelineLauf(_Strict):
    """Ein abgeschlossener Lauf. Gleiche Whitelist wie auf oberster Ebene."""

    profil: str
    n_eintraege: int = Field(ge=0)
    n_kaeufe: int = Field(ge=0)
    eintraege: List[PipelineEintrag]
    wortzaehler_endstaende: Dict[str, int]
    #: Aggregierte Extraktionsquote des Laufs ueber alle Kauf-Eintraege
    #: mit Buch-Snapshot: Summe gekauft / Summe verfuegbar (unter dem
    #: jeweiligen Seiten-Deckel). None, wenn keine Kaeufe.
    extraktion_gekauft_usd: Optional[float] = None
    extraktion_verfuegbar_usd: Optional[float] = None
    extraktionsquote: Optional[float] = None


class PipelineForwardPayload(_Strict):
    hinweis: str
    stand_utc: str
    kennzeichnung: Literal["observed/paper"]
    #: Rueckwaertskompatibel: der Lauf, den ``hinweis`` als Profil nennt
    #: (juengster Lauf mit Kaeufen). Bestehende Leser bleiben unveraendert.
    eintraege: List[PipelineEintrag]
    wortzaehler_endstaende: Dict[str, int]
    #: Alle Laeufe, juengster zuerst.
    laeufe: List[PipelineLauf] = Field(default_factory=list)


class AuditPayload(_Strict):
    hinweis: str
    stand_utc: str
    n_eintraege: int = Field(ge=0)
    rollen_zaehler: Dict[str, int]
    backend_zaehler: Dict[str, int]
    prompt_hashes: List[str]
    output_hashes: List[str]


class MetaPayload(_Strict):
    hinweis: str
    stand_utc: str
    backend: str
    schritte: Dict[str, str]
    disclaimer: List[str]


# ---------------------------------------------------------------------------
# Payload-Builder (reine Funktionen, testbar mit Fixtures)
# ---------------------------------------------------------------------------

_BAND_ORDER = {"high": 0, "medium": 1, "low": 2}

#: Uebersetzung der deterministischen Signal-Tokens in Klartext (englisch).
_TRIGGER_TEXT = {
    "active_wallet_activity": "active wallet activity",
    "wallet_tier_activity": "wallet tier activity",
    "concentration": "concentration",
    "market_move": "price move",
    "volume": "volume",
}
_REFERENZ_TEXT = {
    "reference_hit": "Reference pattern: hit",
    "partial_reference_overlap": "Reference pattern: partial overlap",
    "no_reference_overlap": "Reference pattern: no overlap",
    "not_evaluated": "Reference pattern: not evaluated",
}
_EREIGNIS_TEXT = {
    "nearest_event_only": "nearest event in time only, no confirmed link",
    "event_hit": "confirmed event link",
    "not_evaluated": "event context not evaluated",
}
_STATUS_TEXT = {
    "source_check_pending": "source check pending",
    "needs_human_review": "human review pending",
    "reviewed_false_context": "reviewed: harmless context",
    "reviewed_keep_candidate": "reviewed: candidate stays",
    "thesis_excluded": "excluded from the analysis",
}
_EMPFEHLUNG_GRUND_TEXT = {
    "escalate_human": "Band high -- the case goes fully to a human.",
    "check_source": (
        "Band medium and the source check is pending -- please verify whether "
        "a public event explains the flow."
    ),
    "watch": (
        "Low band or review completed -- keep watching only, no action "
        "needed."
    ),
}


def _parse_kv(text: str) -> Dict[str, str]:
    """``'a=b; c=d'`` -> ``{'a': 'b', 'c': 'd'}`` (tolerant gegen Freitext)."""

    result: Dict[str, str] = {}
    for part in str(text or "").split(";"):
        part = part.strip()
        if "=" in part:
            key, value = part.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def _fmt_zahl(value: str, *, dezimal: int = 0) -> str:
    try:
        return f"{float(value):,.{dezimal}f}"
    except (TypeError, ValueError):
        return str(value)


def queue_signale(row: Dict[str, str]) -> Dict[str, str]:
    """Kompakte Signal-Chips aus einer Queue-CSV-Zeile (deterministisch)."""

    signale: Dict[str, str] = {}
    trigger = [t.strip() for t in str(row.get("trigger_family", "")).split(",") if t.strip()]
    if trigger:
        signale["trigger"] = ", ".join(_TRIGGER_TEXT.get(t, t.replace("_", " ")) for t in trigger)
    basis = _parse_kv(row.get("priority_basis", ""))
    if basis.get("max_severity"):
        signale["severity"] = basis["max_severity"]
    if basis.get("max_percentile_rank"):
        try:
            signale["percentile"] = f"{float(basis['max_percentile_rank']) * 100:.0f}th"
        except ValueError:
            pass
    flow = _parse_kv(row.get("wallet_flow_context", ""))
    try:
        flow_usd = float(flow.get("total_observed_amount_usd", "0") or 0)
    except ValueError:
        flow_usd = 0.0
    if flow_usd > 0:
        wallets = _fmt_zahl(flow.get("active_wallets", ""), dezimal=0)
        signale["flow"] = f"${_fmt_zahl(flow['total_observed_amount_usd'])} / {wallets} wallet(s)"
    konz = _parse_kv(row.get("concentration_context", ""))
    if konz.get("concentration_context") == "present":
        signale["concentration"] = "present"
    referenz = str(row.get("reference_overlap_status", ""))
    if referenz:
        signale["reference"] = _REFERENZ_TEXT.get(referenz, referenz).replace("Reference pattern: ", "")
    return signale


def case_reasoning(row: Dict[str, str]) -> str:
    """Deterministische Klartext-Begruendung (englisch) aus den Signalfeldern.

    Kein LLM: alle Aussagen kommen woertlich aus den vorberechneten
    Monitor-Feldern. Bewusst beschreibend, keine Schlussfolgerung.
    """

    teile: List[str] = []
    frage = str(row.get("question", "")).strip()
    if frage:
        teile.append(f"Market: '{frage}'")
    trigger = [t.strip() for t in str(row.get("trigger_family", "")).split(",") if t.strip()]
    if trigger:
        teile.append(
            "Trigger: " + ", ".join(_TRIGGER_TEXT.get(t, t.replace("_", " ")) for t in trigger)
        )
    basis = _parse_kv(row.get("priority_basis", ""))
    basis_teile: List[str] = []
    if basis.get("max_severity"):
        basis_teile.append(f"severity {basis['max_severity']}")
    if basis.get("max_percentile_rank"):
        try:
            basis_teile.append(f"{float(basis['max_percentile_rank']) * 100:.0f}th percentile")
        except ValueError:
            pass
    if basis.get("family_count"):
        basis_teile.append(f"{basis['family_count']} signal family(ies)")
    if basis_teile:
        teile.append("Classification: " + ", ".join(basis_teile))
    flow = _parse_kv(row.get("wallet_flow_context", ""))
    try:
        _flow_usd = float(flow.get("total_observed_amount_usd", "0") or 0)
    except ValueError:
        _flow_usd = 0.0
    if _flow_usd > 0:
        flow_satz = (
            f"Observed flow ${_fmt_zahl(flow['total_observed_amount_usd'])} "
            f"from {_fmt_zahl(flow.get('active_wallets', '0'))} wallet(s) "
            f"({_fmt_zahl(flow.get('trade_count', '0'))} trade(s))"
        )
        if flow.get("materiality") == "below_one_percent_of_reference":
            flow_satz += ", materiality below 1% of the reference"
        teile.append(flow_satz)
    konz = _parse_kv(row.get("concentration_context", ""))
    muster = konz.get("triggered_patterns", "")
    if muster and muster != "none":
        teile.append(
            "Concentration patterns: " + muster.replace("_", " ").replace(",", ", ")
        )
    ereignis = str(row.get("event_context_status", ""))
    if ereignis:
        teile.append(_EREIGNIS_TEXT.get(ereignis, ereignis.replace("_", " ")))
    referenz = str(row.get("reference_overlap_status", ""))
    if referenz:
        teile.append(_REFERENZ_TEXT.get(referenz, referenz.replace("_", " ")))
    status = str(row.get("human_review_status", ""))
    if status:
        teile.append("Status: " + _STATUS_TEXT.get(status, status.replace("_", " ")))
    offene = [p.strip() for p in str(row.get("missing_evidence", "")).split(";") if p.strip()]
    if offene:
        teile.append(f"{len(offene)} verification steps open")
    teile.append(
        "Statistical anomaly, not a finding -- no claim about private information"
    )
    return ". ".join(teile) + "."


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _num(value: Any) -> Optional[float]:
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    return float(text)


def _int(value: Any) -> int:
    text = str(value if value is not None else "").strip()
    return int(float(text)) if text else 0


def build_queue_payload(
    queue_result: Dict[str, Any],
    *,
    queue_csv_rows: List[Dict[str, str]],
    now_utc: str,
    backend_name: str,
) -> QueuePayload:
    """Fallkarten aus dem ``build_review_queue``-Ergebnis, sortiert nach Band."""

    row_by_case = {str(row.get("case_id", "")): row for row in queue_csv_rows}
    faelle: List[QueueFall] = []
    for case in queue_result.get("ranked_cases", []):
        recommendation = str(case.get("recommendation", ""))
        if recommendation not in EMPFEHLUNG_WHITELIST:
            raise ValueError(
                f"Empfehlung ausserhalb der Whitelist: {recommendation!r}"
            )
        case_id = str(case.get("case_id", ""))
        row = row_by_case.get(case_id, {})
        begruendung = (
            case_reasoning(row) if row else str(case.get("narrative", ""))
        )
        faelle.append(
            QueueFall(
                id=case_id,
                markt_slug=str(case.get("market_slug", "")),
                zeitfenster=str(row.get("timestamp_utc", "")),
                score_band=str(case.get("priority", "")),
                empfehlung=recommendation,
                empfehlung_grund=_EMPFEHLUNG_GRUND_TEXT[recommendation],
                begruendung=begruendung,
                skeptic_begruendung=str(case.get("skeptic_note", "")),
                skeptic_abschlag=(
                    None
                    if case.get("confidence_adjustment") is None
                    else float(case["confidence_adjustment"])
                ),
                signale=queue_signale(row),
                ts=now_utc,
            )
        )
    # ranked_cases ist bereits score-sortiert; hier nur stabil nach Band ordnen.
    faelle.sort(key=lambda f: _BAND_ORDER[f.score_band])
    return QueuePayload(
        hinweis=DATEI_HINWEISE["queue.json"] + f" Backend: {backend_name}.",
        stand_utc=now_utc,
        faelle=faelle,
    )


def build_kategorie_karte(
    *,
    summary_rows: List[Dict[str, str]],
    beispiel_rows: List[Dict[str, str]],
    now_utc: str,
) -> KategorieKartePayload:
    kategorien = [
        KategorieEintrag(
            kategorie=row["kategorie"],
            brier_t7=_num(row["brier_t7"]),
            trefferquote_t7=_num(row["trefferquote_t7"]),
            brier_t1=_num(row["brier_t1"]),
            trefferquote_t1=_num(row["trefferquote_t1"]),
            n_maerkte=_int(row["n_maerkte"]),
            n_t7=_int(row["n_t7"]),
            median_volumen_usd=_num(row["median_volumen_usd"]),
        )
        for row in summary_rows
    ]
    beispiele = [
        LatenzBeispiel(
            kategorie=row["kategorie"],
            ereignis=row["ereignis"],
            markt_frage=row["markt_frage"],
            minuten_bis_konvergenz=_num(row["minuten_bis_konvergenz"]),
            minuten_bis_erste_reaktion=_num(row["minuten_bis_erste_reaktion"]),
            t0_utc=str(row.get("t0_utc", "")),
            praezisions_hinweis=row["praezisions_hinweis"],
        )
        for row in beispiel_rows
    ]
    return KategorieKartePayload(
        hinweis=DATEI_HINWEISE["kategorie_karte.json"],
        stand_utc=now_utc,
        kategorien=kategorien,
        beispiele=beispiele,
    )


def build_mentions_latenz(
    *,
    mentions_rows: List[Dict[str, str]],
    now_utc: str,
) -> MentionsLatenzPayload:
    """Nur Zeilen mit ``status == 'ok'`` (exakter Match) plus Ausschluesse.

    Ausschluesse tragen (event, status); der Status selbst dokumentiert den
    Grund (z.B. ``ausgeschlossen_zuordnungsambiguitaet``).
    """

    faelle: List[MentionsFall] = []
    ausschluesse: List[MentionsAusschluss] = []
    for row in mentions_rows:
        status = str(row.get("status", ""))
        if status == "ok":
            faelle.append(
                MentionsFall(
                    event=row["event"],
                    minuten_bis_erste_reaktion=_num(row["minuten_bis_erste_reaktion"]),
                    minuten_bis_konvergenz=_num(row["minuten_bis_konvergenz"]),
                    stunden_im_handelbaren_fenster=_num(
                        row["stunden_im_handelbaren_fenster"]
                    ),
                    korrekt_aufgeloestes_outcome=str(
                        row.get("korrekt_aufgeloestes_outcome", "")
                    ).upper(),
                    status="ok",
                )
            )
        else:
            ausschluesse.append(
                MentionsAusschluss(event=str(row.get("event", "")), status=status)
            )
    return MentionsLatenzPayload(
        hinweis=DATEI_HINWEISE["mentions_latenz.json"],
        stand_utc=now_utc,
        faelle=faelle,
        ausschluesse=ausschluesse,
    )


def _best_prices(book_snapshot: Dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
    def _prices(side: str) -> List[float]:
        values: List[float] = []
        for entry in book_snapshot.get(side, []) or []:
            try:
                values.append(float(entry.get("price")))
            except (TypeError, ValueError):
                continue
        return values

    asks = _prices("asks")
    bids = _prices("bids")
    return (min(asks) if asks else None, max(bids) if bids else None)


def _lies_lauf(
    live_dir: Optional[Path],
) -> tuple[List[PipelineEintrag], Dict[str, int], str]:
    """Einen Lauf einlesen: Eintraege, Wortzaehler-Endstand, letzter Zeitstempel.

    Gelesen werden AUSSCHLIESSLICH: ``action``, ``reason``, ``limit_price``,
    ``size_usd`` (aus ``decisions_log.jsonl``), abgeleitete Buch-Bestpreise
    (min ask / max bid aus dem ``book_snapshot``) sowie die Wortzaehler-Staende
    (aus ``bot_events.jsonl``). ``wall_ts_utc`` dient nur der Sortierung der
    Laeufe und wird nicht publiziert.
    """

    eintraege: List[PipelineEintrag] = []
    endstaende: Dict[str, int] = {}
    letzter_ts = ""
    decisions_path = live_dir / "decisions_log.jsonl" if live_dir else None
    events_path = live_dir / "bot_events.jsonl" if live_dir else None

    if decisions_path is not None and decisions_path.exists():
        for line in decisions_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            decision = record.get("decision", {}) or {}
            result = record.get("result", {}) or {}
            book = record.get("book_snapshot", {}) or {}
            bestes_angebot, bestes_gebot = _best_prices(book)
            letzter_ts = max(letzter_ts, str(record.get("wall_ts_utc", "")))
            # Extraktionsquote nur fuer echte Kaeufe: gekaufte USD gegen
            # die im Kaufmoment unter dem Seiten-Deckel verfuegbare
            # Ask-Tiefe (Clamp auf 1.0 gegen Rundungs-/Mittelkurs-Drift).
            verfuegbar_usd: Optional[float] = None
            quote: Optional[float] = None
            gekauft = result.get("size_usd")
            if str(decision.get("action", "NONE")) != "NONE" and gekauft:
                deckel = _deckel_aus_reason(
                    str(decision.get("reason", "")), decision.get("outcome")
                )
                verfuegbar_usd = _verfuegbar_unter_deckel(book, deckel)
                if verfuegbar_usd:
                    quote = round(
                        min(1.0, float(gekauft) / verfuegbar_usd), 4
                    )
            eintraege.append(
                PipelineEintrag(
                    action=str(decision.get("action", "NONE")),
                    reason=str(decision.get("reason", "")),
                    limit_price=(
                        None
                        if decision.get("limit_price") is None
                        else float(decision["limit_price"])
                    ),
                    bestes_angebot=bestes_angebot,
                    bestes_gebot=bestes_gebot,
                    size_usd=(
                        None
                        if result.get("size_usd") is None
                        else float(result["size_usd"])
                    ),
                    verfuegbar_usd=verfuegbar_usd,
                    extraktionsquote=quote,
                )
            )

    if events_path is not None and events_path.exists():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            art = str(event.get("art", ""))
            if art == "fertig" and isinstance(event.get("endstaende"), dict):
                endstaende = {
                    str(k): int(v) for k, v in event["endstaende"].items()
                }
            elif art == "chunk" and isinstance(event.get("staende"), dict):
                endstaende = {str(k): int(v) for k, v in event["staende"].items()}

    return eintraege, endstaende, letzter_ts


_DECKEL_MUSTER = re.compile(r"<=\s*([01](?:\.\d+)?)")


def _deckel_aus_reason(reason: str, outcome: Optional[str]) -> float:
    """Preisdeckel des Kaufs aus dem Entscheidungs-Grund.

    Der Bot schreibt den wirksamen Deckel in den reason ("ask 0.29 <=
    0.9" bzw. "no_ask 0.8 <= 0.8"); der LETZTE "<= x"-Treffer ist die
    Preisgrenze (davor kann die Zaehler-Grenze stehen). Fallback auf die
    Seiten-Defaults 0.9 (Yes) / 0.8 (No).
    """

    treffer = _DECKEL_MUSTER.findall(reason or "")
    if treffer:
        return float(treffer[-1])
    return 0.8 if str(outcome or "").strip().lower() == "no" else 0.9


def _verfuegbar_unter_deckel(
    book_snapshot: Dict[str, Any], deckel: float
) -> Optional[float]:
    """Ausfuehrbare Ask-Tiefe (USD) bis einschliesslich Preisdeckel."""

    total = 0.0
    for stufe in book_snapshot.get("asks") or []:
        try:
            preis = float(stufe.get("price"))
            groesse = float(stufe.get("size"))
        except (TypeError, ValueError):
            continue
        if preis <= deckel + 1e-9:
            total += preis * groesse
    return round(total, 2) if total > 0 else None


def entdecke_laeufe(roots: List[Path]) -> List[tuple[str, Path]]:
    """Alle Lauf-Verzeichnisse mit ``decisions_log.jsonl`` ueber alle Wurzeln.

    Je Profil gewinnt die erste Wurzel der Suchreihenfolge, damit Rohdaten die
    kuratierten Kopien schlagen. Sortiert wird spaeter nach Lauf-Zeit.
    """

    gefunden: Dict[str, Path] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for kandidat in sorted(p for p in root.iterdir() if p.is_dir()):
            if kandidat.name in gefunden:
                continue
            if (kandidat / "decisions_log.jsonl").exists():
                gefunden[kandidat.name] = kandidat
    return list(gefunden.items())


def build_pipeline_forward(
    *,
    live_dir: Optional[Path] = None,
    profil: str,
    now_utc: str,
    laeufe: Optional[List[tuple[str, Path]]] = None,
) -> PipelineForwardPayload:
    """Beobachtende Paper-Zeitleiste, ein Eintrag je Lauf.

    ``laeufe`` publiziert alle uebergebenen Laeufe, juengster zuerst. Die
    obersten Felder ``eintraege``/``wortzaehler_endstaende`` spiegeln weiterhin
    genau einen Lauf -- den juengsten mit Kaeufen, sonst den juengsten
    ueberhaupt -- damit bestehende Leser unveraendert funktionieren. ``profil``
    ist der Fallback-Name, wenn gar kein Lauf gefunden wurde.

    Keine Wallet-Daten, keine PnL-Aussage. Fehlt die Quelle (``data/live`` ist
    bewusst nicht im Repo), wird ein leeres, klar gekennzeichnetes Artefakt
    geschrieben.
    """

    if laeufe is None:
        laeufe = [(profil, live_dir)] if live_dir is not None else []

    gelesen: List[tuple[str, PipelineLauf]] = []
    for lauf_profil, lauf_dir in laeufe:
        eintraege, endstaende, letzter_ts = _lies_lauf(lauf_dir)
        if not eintraege:
            continue
        kaeufe_mit_buch = [
            e for e in eintraege
            if e.action != "NONE" and e.size_usd and e.verfuegbar_usd
        ]
        gekauft_summe = (
            round(sum(e.size_usd for e in kaeufe_mit_buch), 2)
            if kaeufe_mit_buch else None
        )
        verfuegbar_summe = (
            round(sum(e.verfuegbar_usd for e in kaeufe_mit_buch), 2)
            if kaeufe_mit_buch else None
        )
        lauf_quote = (
            round(min(1.0, gekauft_summe / verfuegbar_summe), 4)
            if gekauft_summe and verfuegbar_summe else None
        )
        gelesen.append(
            (
                letzter_ts,
                PipelineLauf(
                    profil=lauf_profil,
                    n_eintraege=len(eintraege),
                    n_kaeufe=sum(1 for e in eintraege if e.action != "NONE"),
                    eintraege=eintraege,
                    wortzaehler_endstaende=endstaende,
                    extraktion_gekauft_usd=gekauft_summe,
                    extraktion_verfuegbar_usd=verfuegbar_summe,
                    extraktionsquote=lauf_quote,
                ),
            )
        )

    # Juengster Lauf zuerst; ohne Zeitstempel ans Ende.
    gelesen.sort(key=lambda paar: paar[0], reverse=True)
    sortierte = [lauf for _, lauf in gelesen]

    # Oberste Ebene: juengster Lauf MIT Kaeufen, sonst juengster ueberhaupt.
    spiegel = next((lauf for lauf in sortierte if lauf.n_kaeufe), None)
    if spiegel is None and sortierte:
        spiegel = sortierte[0]

    hinweis = DATEI_HINWEISE["pipeline_forward.json"]
    hinweis += f" Profil: {spiegel.profil if spiegel else profil}."
    if spiegel is None:
        hinweis += (
            " Source decisions_log.jsonl not present on this machine -- "
            "empty artifact."
        )
    elif len(sortierte) > 1:
        hinweis += (
            f" Top-level fields mirror this run; all {len(sortierte)} runs are"
            " listed under laeufe, newest first."
        )

    return PipelineForwardPayload(
        hinweis=hinweis,
        stand_utc=now_utc,
        kennzeichnung="observed/paper",
        eintraege=spiegel.eintraege if spiegel else [],
        wortzaehler_endstaende=spiegel.wortzaehler_endstaende if spiegel else {},
        laeufe=sortierte,
    )


def build_audit(
    *,
    llm_sink: List[Dict[str, Any]],
    now_utc: str,
) -> AuditPayload:
    """Nur Hashes und Zaehler -- keine Prompts, Args, Modelle oder Kosten."""

    rollen: Dict[str, int] = {}
    backends: Dict[str, int] = {}
    for record in llm_sink:
        rolle = str(record.get("role", ""))
        backend = str(record.get("backend", ""))
        rollen[rolle] = rollen.get(rolle, 0) + 1
        backends[backend] = backends.get(backend, 0) + 1
    return AuditPayload(
        hinweis=DATEI_HINWEISE["audit.json"],
        stand_utc=now_utc,
        n_eintraege=len(llm_sink),
        rollen_zaehler=rollen,
        backend_zaehler=backends,
        prompt_hashes=[str(r.get("prompt_hash", "")) for r in llm_sink],
        output_hashes=[str(r.get("output_hash", "")) for r in llm_sink],
    )


def build_meta(
    *, now_utc: str, backend_name: str, schritte: Dict[str, str]
) -> MetaPayload:
    return MetaPayload(
        hinweis=DATEI_HINWEISE["meta.json"],
        stand_utc=now_utc,
        backend=backend_name,
        schritte=schritte,
        disclaimer=list(DISCLAIMER.values()),
    )


# ---------------------------------------------------------------------------
# Schritt-Ausfuehrung
# ---------------------------------------------------------------------------


def mentions_cache_complete(
    seed_path: Path = SEED_PATH, cache_dir: Path = MENTIONS_CACHE_DIR
) -> bool:
    """True, wenn jede nicht ausgeschlossene Seed-Zeile einen Cache hat.

    Nur dann ist ``mentions_latency`` garantiert offline (eine neue Zeile
    ohne ``prices_<event>.json`` wuerde einen Live-CLOB-Abruf ausloesen).
    """

    import csv

    if not seed_path.exists():
        return False
    with seed_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if (row.get("ausschluss") or "").strip():
                continue
            if not (cache_dir / f"prices_{row['event']}.json").exists():
                return False
    return True


def _run_collector(samples: int = 2, delay_seconds: float = 30.0) -> str:
    """Frische Marktdaten sammeln (Polymarket read-only, --collect).

    Fail-soft: Netz-/Validierungsfehler brechen den Tageslauf nicht ab --
    der Refresh nutzt dann die vorhandenen Alert-Rows und der Fehler steht
    im Schritt-Status von meta.json.
    """

    import httpx
    from pydantic import ValidationError as PydanticValidationError

    from operations.collectors.polymarket_rolling_history import (
        collect_polymarket_rolling_history,
    )

    try:
        result = collect_polymarket_rolling_history(
            source="live", samples=samples, delay_seconds=delay_seconds
        )
    except (httpx.HTTPError, PydanticValidationError, ValueError, FileNotFoundError) as exc:
        return f"fehlgeschlagen ({type(exc).__name__}) -- vorhandene Alert-Rows werden weiterverwendet"
    return (
        f"ok (samples={result.samples_completed}/{result.samples_requested}, "
        f"alerts={result.alert_count}, baseline={result.baseline_readiness})"
    )


def _filter_curation_csv(source: Path, target: Path, known_ids: set) -> Path:
    """Kurations-CSV auf bekannte case_ids filtern (Original bleibt unberuehrt).

    Nach einem frischen Collect existieren alte Fall-Ids nicht mehr in der
    Queue; der strikte Queue-Builder wuerde sonst abbrechen. Die Historie in
    ``data/`` wird NICHT veraendert -- der Tageslauf nutzt eine gefilterte
    Arbeitskopie.
    """

    import csv

    if not source.exists():
        return source
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = [r for r in reader if str(r.get("case_id", "")) in known_ids]
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return target


def _run_monitor_refresh() -> str:
    """Deterministischer Kandidaten-Refresh aus vorhandenen Artefakten."""

    import csv

    from operations.analysis.monitor_reference_candidates import (
        generate_monitor_reference_candidates,
    )
    from operations.analysis.monitor_candidate_review_report import (
        generate_monitor_candidate_human_review_report,
        REVIEW_REPORT_OUTPUT,
    )
    from operations.analysis.monitor_anomaly_review_queue import (
        generate_monitor_anomaly_review_queue,
        REVIEW_UPDATES_INPUT,
        REVIEW_DECISIONS_INPUT,
    )

    generate_monitor_reference_candidates()
    generate_monitor_candidate_human_review_report()

    with Path(REVIEW_REPORT_OUTPUT).open(encoding="utf-8", newline="") as handle:
        known_ids = {
            str(row.get("candidate_id", "")) for row in csv.DictReader(handle)
        }
    updates_path = _filter_curation_csv(
        Path(REVIEW_UPDATES_INPUT),
        RESULTS_DIR / "daily_review_filtered_status_updates.csv",
        known_ids,
    )
    decisions_path = _filter_curation_csv(
        Path(REVIEW_DECISIONS_INPUT),
        RESULTS_DIR / "daily_review_filtered_decisions.csv",
        known_ids,
    )
    result = generate_monitor_anomaly_review_queue(
        review_updates_path=updates_path,
        review_decisions_path=decisions_path,
    )
    return f"ok (queue_rows={result.queue_row_count})"


def _call_main_isolated(module_main: Callable[[], Any]) -> None:
    """Fremde ``main()`` ohne die eigene argv aufrufen.

    ``mentions_latency.main()`` parst ``sys.argv`` selbst; die Runner-Flags
    (z.B. ``--publish-dir``) wuerden dort als unbekannte Argumente einen
    ``SystemExit`` ausloesen.
    """

    old_argv = sys.argv
    sys.argv = [old_argv[0]]
    try:
        module_main()
    finally:
        sys.argv = old_argv


def _run_snapshots() -> Dict[str, str]:
    status: Dict[str, str] = {}

    from operations.analysis import category_efficiency_snapshot

    _call_main_isolated(category_efficiency_snapshot.main)
    status["category_efficiency_snapshot"] = "ok"

    if mentions_cache_complete():
        from operations.analysis import mentions_latency

        _call_main_isolated(mentions_latency.main)
        status["mentions_latency"] = "ok"
    else:
        status["mentions_latency"] = (
            "uebersprungen: Seed-Zeile ohne Preis-Cache -- Lauf ohne --refresh "
            "waere nicht offline"
        )

    from operations.analysis import category_latency_examples

    _call_main_isolated(category_latency_examples.main)
    status["category_latency_examples"] = "ok"
    return status


def _make_llm_backend() -> Callable[[str, str], str]:
    """Anthropic-Backend fuer --llm; Key aus .env, wird nie ausgegeben."""

    from dotenv import load_dotenv
    import os

    load_dotenv(REPO_ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError("--llm gesetzt, aber ANTHROPIC_API_KEY fehlt in .env")

    import anthropic

    client = anthropic.Anthropic()

    def backend(system: str, user: str) -> str:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=800,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text
            for block in response.content
            if getattr(block, "type", "") == "text"
        )

    return backend


def live_roots(explicit: Optional[Path] = None) -> List[Path]:
    """Suchreihenfolge fuer die Live-Wurzel, erste Treffer zuerst.

    ``--live-root`` schlaegt ``THESIS_LIVE_ROOT`` schlaegt das (gitignorierte)
    ``data/live`` der Arbeitskopie schlaegt die versionierten, kuratierten
    Kopien unter ``data/live_curated``. Zurueckgegeben werden nur existierende
    Verzeichnisse; ist keines vorhanden, ist die Liste leer und die Kette
    schreibt ein valides, gekennzeichnetes Leer-Artefakt.
    """

    candidates: List[Path] = []
    if explicit is not None:
        candidates.append(Path(explicit))
    from_env = os.environ.get(LIVE_ROOT_ENV, "").strip()
    if from_env:
        candidates.append(Path(from_env))
    candidates.extend((LIVE_BASE_DIR, LIVE_CURATED_DIR))

    roots: List[Path] = []
    for candidate in candidates:
        resolved = candidate.expanduser()
        if resolved.is_dir() and resolved not in roots:
            roots.append(resolved)
    return roots


def _resolve_live_dir(
    profil: Optional[str], roots: Optional[List[Path]] = None
) -> tuple[Optional[Path], str]:
    """Verzeichnis eines Laufs ueber die Wurzel-Suchreihenfolge finden."""

    roots = live_roots() if roots is None else roots
    wanted = (profil,) if profil else LIVE_PROFILE_CANDIDATES
    for candidate in wanted:
        for root in roots:
            candidate_dir = root / candidate
            if (candidate_dir / "decisions_log.jsonl").exists():
                return candidate_dir, candidate
    fallback = profil or LIVE_PROFILE_CANDIDATES[0]
    return None, fallback


@dataclass
class DailyReviewResult:
    publish_dir: Path
    written: List[Path] = field(default_factory=list)
    copied_to: Optional[Path] = None
    schritte: Dict[str, str] = field(default_factory=dict)


def run_daily_review(
    *,
    publish_dir: Path = PUBLISH_DIR_DEFAULT,
    extra_publish_dir: Optional[Path] = None,
    use_llm: bool = False,
    collect: bool = False,
    live_profile: Optional[str] = None,
    live_root: Optional[Path] = None,
    max_cases: int = 50,
    collect_fn: Callable[[], str] = _run_collector,
    refresh_fn: Callable[[], str] = _run_monitor_refresh,
    snapshots_fn: Callable[[], Dict[str, str]] = _run_snapshots,
    build_review_queue_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> DailyReviewResult:
    """Kompletter Tageslauf; schreibt erst nach Validierung UND Gate."""

    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    schritte: Dict[str, str] = {}

    # 0) Optional: frische Marktdaten sammeln (einziger Netzpfad neben --llm)
    if collect:
        schritte["collector"] = collect_fn()
    else:
        schritte["collector"] = "uebersprungen (--collect nicht gesetzt)"

    # 1) Monitor-Kandidaten-Refresh (offline, bestehende Module)
    schritte["monitor_refresh"] = refresh_fn()

    # 2) Agenten-Review-Queue (Mock default; --llm ist der einzige Netzpfad)
    if build_review_queue_fn is None:
        from operations.agents.review_queue.orchestrator import build_review_queue

        build_review_queue_fn = build_review_queue
    backend = _make_llm_backend() if use_llm else None
    # Publiziert wird nur die generische Betriebsart -- die konkrete
    # Modell-Id bleibt im internen (gitignorierten) LLM-Audit-Log.
    backend_name = "llm" if use_llm else "mock"
    llm_sink: List[Dict[str, Any]] = []
    queue_result = build_review_queue_fn(
        backend=backend,
        llm_audit_path=DAILY_LLM_AUDIT_PATH,
        llm_audit_sink=llm_sink,
        max_cases=max_cases,
    )
    schritte["review_queue"] = (
        f"ok (backend={backend_name}, cases={queue_result.get('count', 0)})"
    )

    # 3) Snapshot-Rechner (offline; mentions nur bei vollstaendigem Cache)
    schritte.update(snapshots_fn())

    # 4) Payloads bauen + pydantic-validieren (fail-closed)
    queue_payload = build_queue_payload(
        queue_result,
        queue_csv_rows=_read_csv_rows(QUEUE_CSV_PATH) if QUEUE_CSV_PATH.exists() else [],
        now_utc=now_utc,
        backend_name=backend_name,
    )
    karte_payload = build_kategorie_karte(
        summary_rows=_read_csv_rows(SUMMARY_V2_PATH),
        beispiel_rows=_read_csv_rows(LATENCY_EXAMPLES_PATH),
        now_utc=now_utc,
    )
    mentions_payload = build_mentions_latenz(
        mentions_rows=_read_csv_rows(MENTIONS_CSV_PATH) if MENTIONS_CSV_PATH.exists() else [],
        now_utc=now_utc,
    )
    roots = live_roots(live_root)
    if live_profile:
        # Explizites Profil: nur diesen einen Lauf publizieren.
        live_dir, profil = _resolve_live_dir(live_profile, roots)
        forward_laeufe = [(profil, live_dir)] if live_dir else []
    else:
        profil = LIVE_PROFILE_CANDIDATES[0]
        forward_laeufe = entdecke_laeufe(roots)
    forward_payload = build_pipeline_forward(
        profil=profil, now_utc=now_utc, laeufe=forward_laeufe
    )
    if forward_payload.laeufe:
        schritte["pipeline_forward"] = (
            f"ok ({len(forward_payload.laeufe)} laeufe, "
            f"{sum(lauf.n_eintraege for lauf in forward_payload.laeufe)} eintraege)"
        )
    else:
        schritte["pipeline_forward"] = (
            "quelle_fehlt (keine Live-Wurzel mit decisions_log.jsonl gefunden)"
        )
    audit_payload = build_audit(llm_sink=llm_sink, now_utc=now_utc)
    meta_payload = build_meta(
        now_utc=now_utc, backend_name=backend_name, schritte=schritte
    )

    serialized = {
        "queue.json": queue_payload.model_dump_json(indent=1),
        "kategorie_karte.json": karte_payload.model_dump_json(indent=1),
        "mentions_latenz.json": mentions_payload.model_dump_json(indent=1),
        "pipeline_forward.json": forward_payload.model_dump_json(indent=1),
        "audit.json": audit_payload.model_dump_json(indent=1),
        "meta.json": meta_payload.model_dump_json(indent=1),
    }

    # 5) Redaktions-Gate ueber ALLE Payloads, erst danach wird geschrieben.
    run_redaction_gate(serialized)

    publish_dir.mkdir(parents=True, exist_ok=True)
    result = DailyReviewResult(publish_dir=publish_dir, schritte=schritte)
    for name, text in serialized.items():
        result.written.append(schreibe_atomar(publish_dir / name, text + "\n"))

    # 6) Optionaler zusaetzlicher Publish-Ordner (z.B. Website public/data)
    if extra_publish_dir is not None:
        extra_publish_dir.mkdir(parents=True, exist_ok=True)
        for name in PUBLISH_FILES:
            # Atomar statt copy2: die Website liest diesen Ordner live.
            schreibe_atomar(
                extra_publish_dir / name,
                (publish_dir / name).read_text(encoding="utf-8"),
            )
        result.copied_to = extra_publish_dir

    return result


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Taeglicher Review-Lauf mit Publish nach data/publish/."
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Produktives LLM-Backend (ANTHROPIC_API_KEY aus .env); Default ist das netzfreie Mock-Backend.",
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Frische Marktdaten via read-only Polymarket-Collector sammeln (fail-soft).",
    )
    parser.add_argument(
        "--publish-dir",
        type=Path,
        default=None,
        help="Zusaetzlicher Zielordner (z.B. public/data der Website).",
    )
    parser.add_argument(
        "--live-profile",
        default=None,
        help="Live-Profil fuer pipeline_forward.json (z.B. allin_july3).",
    )
    parser.add_argument(
        "--live-root",
        type=Path,
        default=None,
        help=(
            "Wurzel der Lauf-Verzeichnisse (z.B. C:\\Users\\chole\\ba-thesis\\data\\live). "
            f"Alternativ ueber {LIVE_ROOT_ENV}. Ohne Angabe: data/live, sonst "
            "die kuratierten Kopien unter data/live_curated."
        ),
    )
    parser.add_argument("--max-cases", type=int, default=50)
    args = parser.parse_args(argv)

    try:
        result = run_daily_review(
            extra_publish_dir=args.publish_dir,
            use_llm=args.llm,
            collect=args.collect,
            live_profile=args.live_profile,
            live_root=args.live_root,
            max_cases=args.max_cases,
        )
    except (RedactionGateError, ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"ABBRUCH: {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "publish_dir": str(result.publish_dir),
                "written": [p.name for p in result.written],
                "copied_to": str(result.copied_to) if result.copied_to else None,
                "schritte": result.schritte,
            },
            ensure_ascii=False,
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
