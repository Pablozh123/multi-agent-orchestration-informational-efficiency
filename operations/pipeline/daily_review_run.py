"""Taeglicher Review-Lauf mit Publish-Schritt fuer die Website.

Ablauf (deterministisch und offline, einzige Ausnahme ist --llm):

1. Monitor-Kandidaten-Refresh ueber die bestehenden Module:
   ``monitor_reference_candidates`` -> ``monitor_candidate_review_report``
   -> ``monitor_anomaly_review_queue``. Das ist eine reine Datei-Pipeline;
   der Netz-Collector ``polymarket_rolling_history`` wird bewusst NICHT
   aufgerufen, vorhandene Alert-Rows werden wiederverwendet.
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
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parents[2]

PUBLISH_DIR_DEFAULT = REPO_ROOT / "data" / "publish"
RESULTS_DIR = REPO_ROOT / "data" / "results"
SEED_PATH = REPO_ROOT / "data" / "events" / "mentions_latency_seed.csv"
MENTIONS_CACHE_DIR = REPO_ROOT / "data" / "raw" / "mentions_latency"
LIVE_BASE_DIR = REPO_ROOT / "data" / "live"

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

#: Deskriptiver ``hinweis`` je publizierter Datei.
DATEI_HINWEISE = {
    "queue.json": (
        "Read-only-Ergebnis eines taeglichen Laufs. Empfehlungen sind "
        "Pruef-Schritte (watch, check_source, escalate_human), keine Trades."
    ),
    "kategorie_karte.json": (
        "Brier-Scores und Einpreisungs-Beispiele je Marktkategorie; Sport/"
        "Popkultur-Konvergenzzeiten sind dokumentierte Obergrenzen."
    ),
    "mentions_latenz.json": (
        "Reaktions- und Konvergenzzeiten der Mentions-Maerkte nach dem "
        "Content-Drop; Ausschluesse separat gelistet."
    ),
    "pipeline_forward.json": (
        "Beobachtender Paper-Lauf: nur Entscheidungsfelder und Buch-Bestpreise, "
        "keine Wallet-Daten, keine Renditeaussage."
    ),
    "audit.json": (
        "Transparenz ueber den Agenten-Lauf: nur Zaehler und Hashes, keine "
        "Prompts, keine Modell-Details."
    ),
    "meta.json": (
        "Laufzeitpunkt, Backend-Betriebsart und Grundsaetze des taeglichen "
        "Analyse-Laufs."
    ),
}

DISCLAIMER = {
    "zweck": (
        "Deskriptive Forschungs-Artefakte eines taeglichen, deterministischen "
        "Review-Laufs ueber oeffentliche Marktdaten."
    ),
    "keine_handlungsempfehlung": (
        "Die Empfehlungen sind Pruef-Empfehlungen (beobachten, Quelle pruefen, "
        "an einen Menschen eskalieren) und keine Kauf- oder Verkaufssignale."
    ),
    "keine_finanzberatung": (
        "Keine Finanz- oder Anlageberatung. Keine Renditeaussage. "
        "Pipeline-Eintraege sind beobachtend/paper."
    ),
    "datenschutz": (
        "Keine Wallet-Adressen, keine Schluessel, keine Prompts. Audit nur "
        "als Hashes und Zaehler."
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
    begruendung: str
    skeptic_abschlag: Optional[float] = Field(default=None, ge=-0.3, le=0.0)
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


class PipelineForwardPayload(_Strict):
    hinweis: str
    stand_utc: str
    kennzeichnung: Literal["beobachtet/paper"]
    eintraege: List[PipelineEintrag]
    wortzaehler_endstaende: Dict[str, int]


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

    ts_by_case = {
        str(row.get("case_id", "")): str(row.get("timestamp_utc", ""))
        for row in queue_csv_rows
    }
    faelle: List[QueueFall] = []
    for case in queue_result.get("ranked_cases", []):
        recommendation = str(case.get("recommendation", ""))
        if recommendation not in EMPFEHLUNG_WHITELIST:
            raise ValueError(
                f"Empfehlung ausserhalb der Whitelist: {recommendation!r}"
            )
        case_id = str(case.get("case_id", ""))
        faelle.append(
            QueueFall(
                id=case_id,
                markt_slug=str(case.get("market_slug", "")),
                zeitfenster=ts_by_case.get(case_id, ""),
                score_band=str(case.get("priority", "")),
                empfehlung=recommendation,
                begruendung=str(case.get("narrative", "")),
                skeptic_abschlag=(
                    None
                    if case.get("confidence_adjustment") is None
                    else float(case["confidence_adjustment"])
                ),
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


def build_pipeline_forward(
    *,
    live_dir: Optional[Path],
    profil: str,
    now_utc: str,
) -> PipelineForwardPayload:
    """Beobachtende Paper-Zeitleiste aus dem Live-Verzeichnis.

    Publiziert werden AUSSCHLIESSLICH: Zeitstempel, ``action``, ``reason``,
    ``limit_price``, ``size_usd`` (aus ``decisions_log.jsonl``), abgeleitete
    Buch-Bestpreise (min ask / max bid aus dem ``book_snapshot``) sowie die
    Wortzaehler-Endstaende (aus ``bot_events.jsonl``). Keine Wallet-Daten,
    keine PnL-Aussage. Fehlt die Quelle (``data/live`` ist bewusst nicht im
    Repo), wird ein leeres, klar gekennzeichnetes Artefakt geschrieben.
    """

    eintraege: List[PipelineEintrag] = []
    endstaende: Dict[str, int] = {}
    hinweis = DATEI_HINWEISE["pipeline_forward.json"] + f" Profil: {profil}."
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
            bestes_angebot, bestes_gebot = _best_prices(
                record.get("book_snapshot", {}) or {}
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
                )
            )
    else:
        hinweis += (
            " Quelle decisions_log.jsonl auf dieser Maschine nicht vorhanden -- "
            "leeres Artefakt."
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

    return PipelineForwardPayload(
        hinweis=hinweis,
        stand_utc=now_utc,
        kennzeichnung="beobachtet/paper",
        eintraege=eintraege,
        wortzaehler_endstaende=endstaende,
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


def _run_monitor_refresh() -> str:
    """Deterministischer Kandidaten-Refresh aus vorhandenen Artefakten."""

    from operations.analysis.monitor_reference_candidates import (
        generate_monitor_reference_candidates,
    )
    from operations.analysis.monitor_candidate_review_report import (
        generate_monitor_candidate_human_review_report,
    )
    from operations.analysis.monitor_anomaly_review_queue import (
        generate_monitor_anomaly_review_queue,
    )

    generate_monitor_reference_candidates()
    generate_monitor_candidate_human_review_report()
    result = generate_monitor_anomaly_review_queue()
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


def _resolve_live_dir(profil: Optional[str]) -> tuple[Optional[Path], str]:
    if profil:
        return LIVE_BASE_DIR / profil, profil
    for candidate in LIVE_PROFILE_CANDIDATES:
        candidate_dir = LIVE_BASE_DIR / candidate
        if (candidate_dir / "decisions_log.jsonl").exists():
            return candidate_dir, candidate
    return None, LIVE_PROFILE_CANDIDATES[0]


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
    live_profile: Optional[str] = None,
    max_cases: int = 50,
    refresh_fn: Callable[[], str] = _run_monitor_refresh,
    snapshots_fn: Callable[[], Dict[str, str]] = _run_snapshots,
    build_review_queue_fn: Optional[Callable[..., Dict[str, Any]]] = None,
) -> DailyReviewResult:
    """Kompletter Tageslauf; schreibt erst nach Validierung UND Gate."""

    now_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    schritte: Dict[str, str] = {}

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
    live_dir, profil = _resolve_live_dir(live_profile)
    forward_payload = build_pipeline_forward(
        live_dir=live_dir, profil=profil, now_utc=now_utc
    )
    if forward_payload.eintraege:
        schritte["pipeline_forward"] = f"ok ({len(forward_payload.eintraege)} eintraege)"
    else:
        schritte["pipeline_forward"] = "quelle_fehlt (data/live nicht vorhanden)"
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
        target = publish_dir / name
        target.write_text(text + "\n", encoding="utf-8")
        result.written.append(target)

    # 6) Optionaler zusaetzlicher Publish-Ordner (z.B. Website public/data)
    if extra_publish_dir is not None:
        extra_publish_dir.mkdir(parents=True, exist_ok=True)
        for name in PUBLISH_FILES:
            shutil.copy2(publish_dir / name, extra_publish_dir / name)
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
    parser.add_argument("--max-cases", type=int, default=50)
    args = parser.parse_args(argv)

    try:
        result = run_daily_review(
            extra_publish_dir=args.publish_dir,
            use_llm=args.llm,
            live_profile=args.live_profile,
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
