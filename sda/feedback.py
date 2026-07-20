"""Strict parsing for optional pilot-feedback fields.

Invalid or missing values remain unavailable. In particular, they are never
coerced to ``False`` or zero, because that would fabricate outcome evidence.
"""

from __future__ import annotations

import pandas as pd

from .schema import col

BOOLEAN_FIELDS = (
    "first_contact_resolved", "sla_breached", "escalated", "ai_attempted",
    "ai_accepted", "human_override", "user_confirmed_resolved",
)
INTEGER_FIELDS = ("reopen_count",)
TEXT_FIELDS = ("pilot_id", "treatment_group")

_TRUE_VALUES = {"true", "yes", "y", "1"}
_FALSE_VALUES = {"false", "no", "n", "0"}
_MISSING_VALUES = {"", "nan", "none", "null", "na", "n/a"}


def normalize_feedback(df: pd.DataFrame, schema: dict) -> dict[str, pd.Series]:
    """Return typed, index-aligned optional feedback columns."""
    result: dict[str, pd.Series] = {}
    for field in BOOLEAN_FIELDS:
        result[field] = _parse_boolean(col(df, schema, field), df.index)
    for field in INTEGER_FIELDS:
        result[field] = _parse_nonnegative_integer(col(df, schema, field), df.index)
    for field in TEXT_FIELDS:
        result[field] = _parse_text(col(df, schema, field), df.index)
    return result


def feedback_parse_quality(df: pd.DataFrame, schema: dict) -> dict[str, dict]:
    """Report source availability and invalid-value counts for each field."""
    parsed = normalize_feedback(df, schema)
    quality = {}
    for field, values in parsed.items():
        source = col(df, schema, field)
        supplied = _supplied_mask(source, df.index)
        quality[field] = {
            "available": source is not None,
            "source_column": schema["mapping"].get(field),
            "supplied_count": int(supplied.sum()),
            "parsed_count": int(values.notna().sum()),
            "invalid_count": int((supplied & values.isna()).sum()),
        }
    return quality


def _parse_boolean(series: pd.Series | None, index: pd.Index) -> pd.Series:
    source = _as_strings(series, index)

    def parse(value):
        if pd.isna(value):
            return pd.NA
        key = str(value).strip().lower()
        if key in _TRUE_VALUES:
            return True
        if key in _FALSE_VALUES:
            return False
        return pd.NA

    return source.map(parse).astype("boolean")


def _parse_nonnegative_integer(series: pd.Series | None, index: pd.Index) -> pd.Series:
    source = _as_strings(series, index)
    numeric = pd.to_numeric(source, errors="coerce")
    valid = numeric.notna() & (numeric >= 0) & (numeric.mod(1) == 0)
    return numeric.where(valid).astype("Int64")


def _parse_text(series: pd.Series | None, index: pd.Index) -> pd.Series:
    source = _as_strings(series, index).str.strip()
    return source.mask(source.str.lower().isin(_MISSING_VALUES)).astype("string")


def _as_strings(series: pd.Series | None, index: pd.Index) -> pd.Series:
    if series is None:
        return pd.Series(pd.NA, index=index, dtype="string")
    return series.reset_index(drop=True).set_axis(index).astype("string")


def _supplied_mask(series: pd.Series | None, index: pd.Index) -> pd.Series:
    values = _as_strings(series, index)
    return values.notna() & ~values.str.strip().str.lower().isin(_MISSING_VALUES)
