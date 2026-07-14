"""Vendor-agnostic column detection.

Maps the messy headers exported by ServiceNow, Jira Service Management,
Freshservice, Zendesk, ManageEngine and others onto a small set of canonical
fields. Detection is pure string matching, fully deterministic and inspectable.
Nothing is guessed with a model.
"""

from __future__ import annotations

import re

import pandas as pd

# Canonical field -> list of accepted header aliases (matched case-insensitively
# after normalizing non-alphanumerics to single spaces).
FIELD_ALIASES: dict[str, list[str]] = {
    "ticket_id": [
        "number", "ticket", "ticket id", "issue key", "key", "id", "case number",
        "request id", "incident number", "reference", "display id",
    ],
    "created": [
        "opened", "opened at", "created", "created at", "created date",
        "created time", "open time", "reported date", "date created", "submitted",
    ],
    "resolved": [
        "resolved", "resolved at", "closed", "closed at", "resolved date",
        "closed date", "resolution date", "completed", "date resolved", "end time",
    ],
    "status": ["status", "state", "ticket status", "stage", "resolution status"],
    "priority": ["priority", "urgency", "severity", "impact priority", "p"],
    "type": [
        "type", "ticket type", "issue type", "request type", "record type",
        "task type", "category type",
    ],
    "category": ["category", "issue category", "classification", "topic", "service"],
    "subcategory": ["subcategory", "sub category", "sub-category", "subtype", "sub type"],
    "assignment_group": [
        "assignment group", "assigned group", "group", "support group", "team",
        "queue", "resolver group",
    ],
    "assignee": [
        "assigned to", "assignee", "owner", "agent", "resolved by", "handled by",
    ],
    "requester": [
        "requester", "requested by", "caller", "reporter", "opened by", "user",
        "employee", "affected user", "contact",
    ],
    "department": [
        "department", "dept", "business unit", "division", "cost center",
        "company", "location", "office",
    ],
    "short_description": [
        "short description", "summary", "subject", "title", "description",
        "issue", "problem", "details",
    ],
    "description": [
        "description", "details", "work notes", "comments", "body", "notes",
        "long description", "additional comments",
    ],
    "application": [
        "application", "app", "affected ci", "configuration item", "ci",
        "service offering", "product", "system", "software", "affected system",
    ],
    "mttr_hours": [
        "mttr", "resolution time", "time to resolve", "duration", "resolution time hours",
        "handle time", "elapsed time",
    ],
}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def detect_schema(df: pd.DataFrame) -> dict:
    """Return a mapping of canonical field -> actual column name (or None).

    Also returns which fields were found and which are missing, so the
    integrity step can be honest about gaps instead of inventing data.
    """
    norm_to_actual: dict[str, str] = {}
    for col in df.columns:
        norm_to_actual.setdefault(_norm(col), col)

    mapping: dict[str, str | None] = {}
    used: set[str] = set()

    # Exact normalized match first, then substring, longest alias wins.
    for field, aliases in FIELD_ALIASES.items():
        chosen: str | None = None
        for alias in sorted(aliases, key=len, reverse=True):
            na = _norm(alias)
            if na in norm_to_actual and norm_to_actual[na] not in used:
                chosen = norm_to_actual[na]
                break
        if chosen is None:
            for alias in sorted(aliases, key=len, reverse=True):
                na = _norm(alias)
                for norm_col, actual in norm_to_actual.items():
                    if actual in used:
                        continue
                    if norm_col == na or na in norm_col.split() or _phrase_in(na, norm_col):
                        chosen = actual
                        break
                if chosen:
                    break
        if chosen is not None:
            mapping[field] = chosen
            # description and short_description may legitimately share a source;
            # otherwise avoid double-assigning the same column.
            if field not in {"description", "short_description"}:
                used.add(chosen)
        else:
            mapping[field] = None

    present = [f for f, c in mapping.items() if c is not None]
    missing = [f for f, c in mapping.items() if c is None]
    return {"mapping": mapping, "present": present, "missing": missing}


def _phrase_in(needle: str, haystack: str) -> bool:
    """True if the multi-word needle appears as a contiguous phrase in haystack."""
    if " " not in needle:
        return False
    return needle in haystack


def col(df: pd.DataFrame, schema: dict, field: str) -> pd.Series | None:
    """Convenience accessor: the Series for a canonical field, or None."""
    name = schema["mapping"].get(field)
    if name is None or name not in df.columns:
        return None
    return df[name]
