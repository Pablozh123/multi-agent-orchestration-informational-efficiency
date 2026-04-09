"""Validierungs-Report fuer die bestehende thesis.db.

Liest jede Core-Tabelle als DataFrame, wirft sie durch das passende Pandera-
Schema und gibt einen strukturierten Bericht ueber Verletzungen aus.

Aufruf:
    python -m operations.validation.report
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
from pandera.errors import SchemaError, SchemaErrors

from operations.validation.pandera_schemas import TABLE_TO_SCHEMA


DB_PATH = Path("data/thesis.db")


def _format_violation(table: str, error: Exception) -> str:
    """Formats a Pandera SchemaError into a multi-line report entry."""
    if isinstance(error, SchemaError):
        return (
            f"  [FAIL] {table}: {error.check} on column "
            f"{getattr(error, 'schema', None) and error.schema.name!r}\n"
            f"      reason: {error}\n"
            f"      failing rows (first 5): "
            f"{error.failure_cases.head(5).to_dict(orient='records') if hasattr(error, 'failure_cases') and error.failure_cases is not None else 'n/a'}"
        )
    return f"  [FAIL] {table}: {type(error).__name__}: {error}"


def main() -> int:
    """Run the validation report. Returns process exit code (0 = clean)."""
    if not DB_PATH.exists():
        print(f"FATAL: {DB_PATH} not found")
        return 2

    conn = sqlite3.connect(str(DB_PATH))
    print(f"Validating {DB_PATH} against pandera schemas\n")

    total_violations = 0
    for table, schema in TABLE_TO_SCHEMA.items():
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
        n = len(df)
        if n == 0:
            print(f"  [SKIP] {table}: 0 rows")
            continue

        try:
            schema.validate(df, lazy=True)
            print(f"  [OK]   {table}: {n} rows pass")
        except (SchemaError, SchemaErrors) as exc:
            total_violations += 1
            # SchemaErrors (lazy=True) collects all failures; SchemaError is one
            if isinstance(exc, SchemaErrors):
                print(f"  [FAIL] {table}: {n} rows -- {len(exc.failure_cases)} failing cases")
                # Print up to 10 distinct failure entries
                cases = exc.failure_cases.head(10)
                for _, row in cases.iterrows():
                    print(
                        f"      column={row.get('column', '?')} "
                        f"check={row.get('check', '?')} "
                        f"failure={row.get('failure_case', '?')!r} "
                        f"index={row.get('index', '?')}"
                    )
            else:
                print(_format_violation(table, exc))

    conn.close()
    print(f"\n{'-' * 60}")
    print(f"Tables with violations: {total_violations}/{len(TABLE_TO_SCHEMA)}")
    return 0 if total_violations == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
