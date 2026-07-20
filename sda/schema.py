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
    # Optional pilot-feedback fields are exact-match only. Their aliases are
    # deliberately specific so ordinary columns such as "AI category" cannot
    # silently become outcome evidence.
    "reopen_count": ["reopen count", "number of reopens", "reopens"],
    "first_contact_resolved": [
        "first contact resolved", "resolved on first contact",
    ],
    "sla_breached": ["sla breached", "sla breach"],
    "escalated": ["escalated", "is escalated"],
    "ai_attempted": ["ai attempted", "ai assistance attempted"],
    "ai_accepted": ["ai accepted", "ai answer accepted", "ai assistance accepted"],
    "human_override": ["human override", "human overridden"],
    "user_confirmed_resolved": [
        "user confirmed resolved", "user confirmed resolution", "confirmed resolved by user",
    ],
    "pilot_id": ["pilot id", "experiment id"],
    "treatment_group": ["treatment group", "experiment group", "control or treatment"],
}

EXACT_ONLY_FIELDS = {
    "reopen_count", "first_contact_resolved", "sla_breached", "escalated",
    "ai_attempted", "ai_accepted", "human_override", "user_confirmed_resolved",
    "pilot_id", "treatment_group",
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

    # Reserve exact-only feedback columns before fuzzy matching legacy fields.
    # Otherwise broad aliases such as "id", "resolved", or "group" can steal
    # a precise header such as "Pilot ID" or "First Contact Resolved".
    used: set[str] = set()
    for field in FIELD_ALIASES:
        if field not in EXACT_ONLY_FIELDS:
            continue
        chosen = next(
            (norm_to_actual[_norm(alias)] for alias in FIELD_ALIASES[field]
             if _norm(alias) in norm_to_actual and norm_to_actual[_norm(alias)] not in used),
            None,
        )
        mapping[field] = chosen
        if chosen is not None:
            used.add(chosen)

    # Exact normalized match first, then substring, longest alias wins.
    for field, aliases in FIELD_ALIASES.items():
        if field in EXACT_ONLY_FIELDS:
            continue
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

    # Preserve canonical declaration order in public output.
    ordered_mapping = {field: mapping[field] for field in FIELD_ALIASES}
    present = [f for f, c in ordered_mapping.items() if c is not None]
    missing = [f for f, c in ordered_mapping.items()
               if c is None and f not in EXACT_ONLY_FIELDS]
    optional_missing = [f for f in EXACT_ONLY_FIELDS if ordered_mapping[f] is None]
    return {
        "mapping": ordered_mapping,
        "present": present,
        "missing": missing,
        "optional_missing": sorted(optional_missing),
    }


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
