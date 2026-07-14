"""Step 2: Normalize the dataset into a clean analytical view.

Builds a tidy DataFrame with canonical columns, parsed dates, a computed MTTR,
and a combined text field used for classification. Original data is not mutated.
"""

from __future__ import annotations

import re

import pandas as pd

from . import util
from .schema import col

_PRIORITY_MAP = {
    "1": "P1", "p1": "P1", "critical": "P1", "highest": "P1", "sev1": "P1", "urgent": "P1",
    "2": "P2", "p2": "P2", "high": "P2", "sev2": "P2",
    "3": "P3", "p3": "P3", "moderate": "P3", "medium": "P3", "normal": "P3", "sev3": "P3",
    "4": "P4", "p4": "P4", "low": "P4", "minor": "P4", "sev4": "P4",
    "5": "P5", "p5": "P5", "planning": "P5", "lowest": "P5",
}

_STATUS_MAP = {
    "closed": "Resolved", "resolved": "Resolved", "done": "Resolved", "complete": "Resolved",
    "completed": "Resolved", "cancelled": "Cancelled", "canceled": "Cancelled",
    "open": "Open", "new": "Open", "in progress": "In Progress", "work in progress": "In Progress",
    "pending": "Pending", "on hold": "Pending", "waiting": "Pending", "assigned": "Open",
}


def normalize(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)

    out["ticket_id"] = _get(df, schema, "ticket_id", default_index=True)
    out["created"] = util.to_datetime(col(df, schema, "created"))
    out["resolved"] = util.to_datetime(col(df, schema, "resolved"))
    out["mttr_hours"] = util.compute_mttr_hours(
        col(df, schema, "created"), col(df, schema, "resolved"), col(df, schema, "mttr_hours"))

    out["status"] = _map_values(_get(df, schema, "status"), _STATUS_MAP)
    out["priority"] = _map_values(_get(df, schema, "priority"), _PRIORITY_MAP)
    out["type"] = _clean_text(_get(df, schema, "type"))
    out["category"] = _clean_text(_get(df, schema, "category"))
    out["subcategory"] = _clean_text(_get(df, schema, "subcategory"))
    out["assignment_group"] = _clean_text(_get(df, schema, "assignment_group"))
    out["requester"] = _clean_text(_get(df, schema, "requester"))
    out["department"] = _clean_text(_get(df, schema, "department"))
    out["application"] = _clean_text(_get(df, schema, "application"))

    short = _get(df, schema, "short_description")
    long = _get(df, schema, "description")
    out["short_description"] = _clean_text(short)

    # Combined lowercase text for classification: category + subcategory +
    # application + description. This is what the theme rules score against.
    parts = []
    for series in (out["category"], out["subcategory"], out["application"],
                   out["short_description"], _clean_text(long)):
        parts.append(series.fillna("").astype(str))
    out["_text"] = (parts[0].str.cat(parts[1:], sep=" ")).str.lower().str.strip()
    out["_text"] = out["_text"].map(lambda s: re.sub(r"\s+", " ", s))

    return out


def _get(df, schema, field, default_index: bool = False):
    c = col(df, schema, field)
    if c is not None:
        return c.reset_index(drop=True)
    if default_index:
        return pd.Series([f"row-{i+1}" for i in range(len(df))])
    return pd.Series([None] * len(df))


def _clean_text(series: pd.Series | None) -> pd.Series:
    if series is None:
        return pd.Series([None] * 0).reindex(range(0))
    s = series.astype("string")
    s = s.str.strip()
    s = s.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "null": pd.NA})
    return s


def _map_values(series: pd.Series | None, mapping: dict) -> pd.Series:
    if series is None:
        return pd.Series([None] * 0).reindex(range(0))
    s = series.astype("string").str.strip()

    def m(v):
        if v is pd.NA or v is None:
            return pd.NA
        key = str(v).strip().lower()
        return mapping.get(key, str(v).strip())

    return s.map(m)
