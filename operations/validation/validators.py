"""Small deterministic validation helpers for thesis data rows."""
from __future__ import annotations

from typing import Any, Callable, TypeVar

import pandas as pd
import pandera.pandas as pa
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from operations.validation.pandera_schemas import TABLE_TO_SCHEMA
from operations.validation.schemas import TABLE_TO_MODEL


T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")


def validate_row(model_cls: type[T], data: dict[str, Any]) -> T:
    """Validate one row against a Pydantic model.

    Pydantic raises clear field-level errors for missing critical fields,
    unparseable dates, and value-range violations.
    """
    return model_cls.model_validate(data)


def validate_dataframe(schema: pa.DataFrameSchema, df: pd.DataFrame) -> pd.DataFrame:
    """Validate a DataFrame against a Pandera schema."""
    return schema.validate(df, lazy=False)


def validate_table_row(table_name: str, data: dict[str, Any]) -> BaseModel:
    """Validate one row using the registered model for `table_name`."""
    try:
        model_cls = TABLE_TO_MODEL[table_name]
    except KeyError as exc:
        raise ValueError(f"no Pydantic validation model registered for {table_name!r}") from exc
    return validate_row(model_cls, data)


def validate_table_rows(table_name: str, rows: list[dict[str, Any]]) -> pd.DataFrame:
    """Validate rows with the registered Pydantic and Pandera schemas."""
    try:
        model_cls = TABLE_TO_MODEL[table_name]
        schema = TABLE_TO_SCHEMA[table_name]
    except KeyError as exc:
        raise ValueError(f"no validation schema registered for {table_name!r}") from exc
    return run_pipeline(model_cls, schema, rows)


def with_retry(
    fn: Callable[..., R],
    max_attempts: int = 3,
    retry_exceptions: tuple[type[Exception], ...] = (ConnectionError, TimeoutError),
) -> Callable[..., R]:
    """Wrap `fn` with retry behavior for transient I/O failures."""
    decorator = retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(multiplier=1, max=10),
        retry=retry_if_exception_type(retry_exceptions),
        reraise=True,
    )
    return decorator(fn)


def run_pipeline(
    model_cls: type[T],
    schema: pa.DataFrameSchema,
    rows: list[dict[str, Any]],
) -> pd.DataFrame:
    """Run row-level Pydantic validation followed by DataFrame validation."""
    if not rows:
        return pd.DataFrame(columns=list(schema.columns.keys()))

    validated_models = [validate_row(model_cls, row) for row in rows]
    df = pd.DataFrame([model.model_dump(exclude_none=True) for model in validated_models])
    return validate_dataframe(schema, df)
