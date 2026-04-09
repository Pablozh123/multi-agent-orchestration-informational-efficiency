"""Async API-Clients fuer Polymarket, Dune und GDELT.

Duenne Wrapper um die bestehenden Ingest-Module (ingest/polymarket.py,
ingest/dune.py, ingest/gdelt.py). Jede Methode ist mit tenacity-Retry
gewrappt und validiert Antworten gegen die Pydantic-Modelle aus
operations.validation.schemas.

Ziel: Ein einheitliches, typ-sicheres Interface fuer die Agent-Tools, ohne
die bestehenden Ingest-Skripte zu duplizieren. Nicht fuer den produktiven
Datenimport — das bleibt Aufgabe der ingest/-Skripte.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

# Side effect: load .env so subclasses can read API keys at init time.
load_dotenv()


# --- Retry decorator reused across clients -------------------------------

_RETRY_EXCEPTIONS = (httpx.TransportError, httpx.TimeoutException, httpx.HTTPStatusError)

_retry_http = retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=10),
    retry=retry_if_exception_type(_RETRY_EXCEPTIONS),
    reraise=True,
)


# --- Polymarket ----------------------------------------------------------


class PolymarketClient:
    """Thin async client fuer die Polymarket CLOB API."""

    _CLOB_BASE_URL = "https://clob.polymarket.com"

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    @_retry_http
    async def fetch_prices_history(
        self, token_id: str, fidelity: int = 1440
    ) -> dict[str, Any]:
        """Ruft die rohe Preishistorie fuer einen Token ab."""
        url = f"{self._CLOB_BASE_URL}/prices-history"
        params = {"market": token_id, "interval": "max", "fidelity": fidelity}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()

    @_retry_http
    async def fetch_market(self, condition_id: str) -> dict[str, Any]:
        """Liefert Market-Metadaten (Tokens, Outcomes) fuer eine condition_id."""
        url = f"{self._CLOB_BASE_URL}/markets/{condition_id}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()

    async def health_check(self) -> bool:
        """Smoke-Test: CLOB-API erreichbar?"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._CLOB_BASE_URL}/markets")
                return resp.status_code < 500
        except httpx.HTTPError:
            return False


# --- Dune ----------------------------------------------------------------


class DuneClient:
    """Thin sync client fuer die Dune Analytics REST API.

    Dune liefert Whale-Trade-Queries ueber vorkonfigurierte Query-IDs.
    API-Key muss ueber die Umgebungsvariable DUNE_API_KEY gesetzt sein.
    """

    _DUNE_API_BASE = "https://api.dune.com/api/v1"

    def __init__(self, api_key: str | None = None, timeout: float = 60.0) -> None:
        self._api_key = api_key or os.environ.get("DUNE_API_KEY")
        if not self._api_key:
            raise RuntimeError(
                "DUNE_API_KEY not set — configure in .env or pass api_key explicitly"
            )
        self._timeout = timeout

    @_retry_http
    def fetch_query_results(self, query_id: int) -> list[dict[str, Any]]:
        """Ruft die Ergebnisse einer bestehenden Dune-Query ab."""
        url = f"{self._DUNE_API_BASE}/query/{query_id}/results"
        headers = {"X-DUNE-API-KEY": self._api_key}
        resp = httpx.get(url, headers=headers, timeout=self._timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", {}).get("rows", [])


# --- GDELT ---------------------------------------------------------------


class GDELTClient:
    """Thin sync client fuer die GDELT DOC API 2.0.

    Kein API-Key. Aggregiert Tone-Werte fuer ein gegebenes Zeitfenster.
    """

    _GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout

    @_retry_http
    def fetch_articles(
        self,
        query: str,
        start_datetime: str,
        end_datetime: str,
        max_records: int = 250,
    ) -> dict[str, Any]:
        """Fragt das DOC-API-artlist-Endpoint fuer ein Zeitfenster ab.

        Args:
            query: Freitextquery (z.B. "election usa 2024").
            start_datetime: Format YYYYMMDDHHMMSS.
            end_datetime: Format YYYYMMDDHHMMSS.
            max_records: Maximale Anzahl Artikel (GDELT-Limit 250).
        """
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "STARTDATETIME": start_datetime,
            "ENDDATETIME": end_datetime,
            "maxrecords": str(max_records),
        }
        resp = httpx.get(self._GDELT_DOC_API, params=params, timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()


# --- Factory helpers -----------------------------------------------------


def default_polymarket_client() -> PolymarketClient:
    """Convenience-Konstruktor mit Default-Timeout."""
    return PolymarketClient()


def default_dune_client() -> DuneClient:
    """Liest DUNE_API_KEY aus .env."""
    return DuneClient()


def default_gdelt_client() -> GDELTClient:
    """Convenience-Konstruktor mit Default-Timeout."""
    return GDELTClient()
