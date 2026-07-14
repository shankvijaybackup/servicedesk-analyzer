"""Normalization (methodology step 2).

Builds a clean analytical view with canonical column names, parsed dates,
computed MTTR, and standardized priority/status values. Categorical labels
are scrubbed: values that look like free text, URLs, tracking blobs, or log
lines are blanked so they can never surface in rollup tables.
"""

import pandas as pd

from .textclean import scrub_labels, clean_text

PRIORITY_MAP = {
    "1": "P1 - Critical", "p1": "P1 - Critical", "critical": "P1 - Critical",
    "1 - critical": "P1 - Critical", "highest": "P1 - Critical", "urgent": "P1 - Critical",
    "2": "P2 - High", "p2": "P2 - High", "high": "P2 - High", "2 - high": "P2 - High",
    "3": "P3 - Medium", "p3": "P3 - Medium", "medium": "P3 - Medium", "moderate": "P3 - Medium",
    "3 - medium": "P3 - Medium", "normal": "P3 - Medium",
    "4": "P4 - Low", "p4": "P4 - Low", "low": "P4 - Low", "4 - low": "P4 - Low",
    "5": "P4 - Low", "planning": "P4 - Low", "lowest": "P4 - Low",
}

STATUS_MAP = {
    "closed": "Closed", "resolved": "Resolved", "closed complete": "Closed",
    "done": "Closed", "completed": "Closed", "closed successful": "Closed",
    "open": "Open", "new": "Open", "in progress": "In Progress", "active": "In Progress",
    "work in progress": "In Progress", "assigned": "In Progress", "pending": "Pending",
    "on hold": "Pending", "awaiting": "Pending", "waiting": "Pending",
    "cancelled": "Cancelled", "canceled": "Cancelled", "rejected": "Cancelled",
}

SLA_TRUE = {"yes", "true", "met", "achieved", "within sla", "1", "y"}
SLA_FALSE = {"no", "false", "breached", "missed", "0", "n"}


def _std_priority(v):
    if pd.isna(v):
        return "Unspecified"
    return PRIORITY_MAP.get(str(v).strip().lower(), str(v).strip())


def _std_status(v):
    if pd.isna(v):
        return "Unspecified"
    s = str(v).strip().lower()
    if s in STATUS_MAP:
        return STATUS_MAP[s]
    for k, out in STATUS_MAP.items():
        if k in s:
            return out
    return str(v).strip().title()


def _std_sla(v):
    if pd.isna(v):
        return None
    s = str(v).strip().lower()
    if s in SLA_TRUE:
        return True
    if s in SLA_FALSE:
        return False
    return None


def normalize(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    """Return the canonical analytical view. Original df is not modified."""
    out = pd.DataFrame(index=df.index)

    def col(field):
        return df[mapping[field]] if field in mapping else pd.Series(pd.NA, index=df.index)

    out["ticket_id"] = col("ticket_id")
    # Free text: strip URLs/blobs/markup, cap length (email dumps add noise)
    out["summary"] = col("summary").fillna("").map(clean_text)
    out["description"] = col("description").fillna("").map(clean_text)
    # Categorical labels are scrubbed: free text/URLs/log lines become ""
    out["category_raw"] = scrub_labels(col("category").fillna(""))
    out["subcategory_raw"] = scrub_labels(col("subcategory").fillna(""))
    out["ticket_type"] = scrub_labels(col("ticket_type").fillna(""))
    out["priority"] = col("priority").map(_std_priority)
    out["status"] = col("status").map(_std_status)
    out["assignment_group"] = scrub_labels(col("assignment_group").fillna(""))
    out["requester"] = col("requester").fillna("").astype(str).str.strip()
    out["department"] = scrub_labels(col("department").fillna(""))
    out["application"] = scrub_labels(col("application").fillna(""))
    out["resolution_notes"] = col("resolution_notes").fillna("").astype(str).str.strip()

    out["created_date"] = pd.to_datetime(col("created_date"), errors="coerce", format="mixed")
    out["resolved_date"] = pd.to_datetime(col("resolved_date"), errors="coerce", format="mixed")

    # MTTR: prefer explicit column; else compute from dates
    if "mttr_hours" in mapping:
        out["mttr_hours"] = pd.to_numeric(df[mapping["mttr_hours"]], errors="coerce")
        out["mttr_source"] = "column"
    else:
        delta = out["resolved_date"] - out["created_date"]
        out["mttr_hours"] = delta.dt.total_seconds() / 3600.0
        out["mttr_source"] = "computed"
    # Negative or absurd MTTR (> 1 year) treated as invalid
    out.loc[(out["mttr_hours"] < 0) | (out["mttr_hours"] > 24 * 365), "mttr_hours"] = pd.NA

    out["sla_met"] = col("sla_met").map(_std_sla) if "sla_met" in mapping else None

    # Combined searchable text for theme classification
    out["_text"] = (
        out["summary"] + " " + out["description"] + " " +
        out["category_raw"] + " " + out["subcategory_raw"] + " " + out["application"]
    ).str.lower()

    # Drop exact duplicate rows (keep first) - report handled in quality module
    out = out[~df.duplicated()].copy()
    return out
