"""Dreistufige Validierungs-Pipeline (CLAUDE.md v2.1 §6.1).

Stufe 1: Pydantic — Schema-Validierung pro Zeile.
Stufe 2: Pandera — DataFrame-Schema und Wertebereiche.
Stufe 3: Tenacity — Retry mit exponentiellem Backoff bei transienten Fehlern.

Die Funktionen sind unabhaengig nutzbar; `run_pipeline()` verkettet alle drei.
"""
from __future__ import annotations

from typing import Any, Callable, TypeVar

import pandas as pd
import pandera.pandas as pa
from pydantic import BaseModel, ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)


T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")


# --- Stufe 1: Pydantic ---------------------------------------------------


def validate_row(model_cls: type[T], data: dict[str, Any]) -> T:
    """Validiert eine einzelne Zeile gegen ein Pydantic-Modell.

    Args:
        model_cls: Pydantic-Modellklasse (z. B. PolymarketPriceRow).
        data: Dictionary mit Spalten => Werten.

    Returns:
        Instanziiertes Modell.

    Raises:
        pydantic.ValidationError: Wenn Felder fehlen oder Typen nicht passen.
    """
    return model_cls.model_validate(data)


# --- Stufe 2: Pandera ----------------------------------------------------


def validate_dataframe(schema: pa.DataFrameSchema, df: pd.DataFrame) -> pd.DataFrame:
    """Validiert einen DataFrame gegen ein Pandera-Schema.

    Args:
        schema: Pandera DataFrameSchema.
        df: Pandas DataFrame mit den zu validierenden Zeilen.

    Returns:
        Den (ggf. gecasteten) DataFrame, wenn die Validierung erfolgreich war.

    Raises:
        pandera.errors.SchemaError: Wenn ein Constraint verletzt ist.
    """
    return schema.validate(df, lazy=False)


# --- Stufe 3: Tenacity ---------------------------------------------------


def with_retry(
    fn: Callable[..., R],
    max_attempts: int = 3,
    retry_exceptions: tuple[type[Exception], ...] = (ConnectionError, TimeoutError),
) -> Callable[..., R]:
    """Wrapped `fn` mit exponentiellem Backoff fuer transiente Fehler.

    Args:
        fn: Synchrone Funktion, die retried werden soll.
        max_attempts: Maximale Anzahl Versuche (default 3).
        retry_exceptions: Exception-Typen, die einen Retry ausloesen.

    Returns:
        Decorated function.
    """
    decorator = retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(multiplier=1, max=10),
        retry=retry_if_exception_type(retry_exceptions),
        reraise=True,
    )
    return decorator(fn)


# --- Top-level pipeline --------------------------------------------------


def run_pipeline(
    model_cls: type[T],
    schema: pa.DataFrameSchema,
    rows: list[dict[str, Any]],
) -> pd.DataFrame:
    """Verkettet Stufe 1 + 2 fuer eine Sammlung von Zeilen.

    Stufe 3 (retry) wird nur fuer I/O-bound Functions benoetigt und ist
    deshalb nicht Teil dieser pipeline — der API-Client oben drauf wickelt
    den retry-Decorator selbst ein.

    Args:
        model_cls: Pydantic-Modell fuer Stufe 1.
        schema: Pandera-Schema fuer Stufe 2.
        rows: Roh-Zeilen aus der API oder einem CSV-Parser.

    Returns:
        Validierter DataFrame.

    Raises:
        ValidationError oder SchemaError je nach Stufe.
    """
    # Stage 1 — per-row Pydantic validation, surfaces field-level errors
    validated_models = [validate_row(model_cls, row) for row in rows]
    df = pd.DataFrame([m.model_dump() for m in validated_models])

    # Stage 2 — DataFrame schema, surfaces value-range and uniqueness errors
    return validate_dataframe(schema, df)
