"""CSV/XLSX import and column detection.

Maps vendor-specific column names (ServiceNow, Jira SM, Freshservice,
Zendesk, ManageEngine, Atomicwork) to a canonical schema. Never invents
fields: if a canonical field cannot be mapped, it is reported as missing.
"""

import io
import re

import pandas as pd

from .textclean import STATUS_LIKE, plausible_label

NA_VALUES = ["", "null", "NULL", "None", "N/A", "n/a"]

# Canonical field -> candidate source column names (lowercased, punctuation stripped)
FIELD_CANDIDATES = {
    "ticket_id": [
        "number", "ticket id", "ticketid", "id", "key", "issue key", "request id",
        "ticket", "case number", "incident number", "display id", "ref",
    ],
    "summary": [
        "short description", "summary", "subject", "title", "description summary",
        "issue summary", "request subject",
    ],
    "description": [
        "description", "details", "long description", "issue description", "body",
    ],
    "category": [
        "category", "issue type", "request type", "ticket type category", "type",
    ],
    "subcategory": [
        "subcategory", "sub category", "sub-category", "item", "issue subtype",
    ],
    "ticket_type": [
        "ticket type", "record type", "issuetype", "issue type name", "request category",
    ],
    "priority": ["priority", "urgency", "priority level", "severity"],
    "status": ["status", "state", "ticket status", "current status"],
    "created_date": [
        "created", "created date", "created at", "opened", "opened at", "open time",
        "created time", "creation date", "reported date", "submit date", "createdon",
    ],
    "resolved_date": [
        "resolved", "resolved date", "resolved at", "resolution date", "closed",
        "closed at", "close time", "closed date", "completed date", "resolution time stamp",
    ],
    "assignment_group": [
        "assignment group", "team", "group", "assigned group", "queue", "support group",
        "assigned team", "resolver group",
    ],
    "assignee": ["assigned to", "assignee", "agent", "owner", "resolver", "technician"],
    "requester": [
        "requester", "requested by", "caller", "reporter", "opened by", "created by",
        "requestor", "customer",
    ],
    "department": [
        "department", "requester department", "business unit", "org", "division",
        "dept", "team department", "requester group",
    ],
    "application": [
        "application", "app", "configuration item", "ci", "affected application",
        "system", "service", "affected ci", "business service", "product",
    ],
    "resolution_notes": [
        "resolution notes", "resolution", "close notes", "resolution description",
        "work notes", "resolution summary",
    ],
    "mttr_hours": [
        "mttr", "mttr hours", "resolution time hours", "time to resolve",
        "resolution time", "mttr hrs",
    ],
    "sla_met": [
        "sla met", "sla", "sla status", "made sla", "sla breached", "within sla",
        "sla achieved",
    ],
}


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", str(name).lower()).strip()


# Tokens that disqualify a column from mapping to a field, even on substring
# match. Prevents "Resolved By" (a person) from becoming resolved_date.
NEGATIVE_TOKENS = {
    "resolved_date": {"by", "notes"},
    "created_date": {"by"},
}


def detect_columns(columns) -> dict:
    """Return {canonical_field: source_column} for fields that can be mapped."""
    normed = {_norm(c): c for c in columns}
    mapping = {}
    for field, candidates in FIELD_CANDIDATES.items():
        neg = NEGATIVE_TOKENS.get(field, set())
        for cand in candidates:
            if cand in normed and normed[cand] not in mapping.values() \
                    and not (neg & set(cand.split())):
                mapping[field] = normed[cand]
                break
        if field in mapping:
            continue
        # fallback: substring match
        for n, orig in normed.items():
            if orig in mapping.values():
                continue
            if neg & set(n.split()):
                continue
            if any(cand in n for cand in candidates):
                mapping[field] = orig
                break
    return mapping


def _validate_mapping(df: pd.DataFrame, mapping: dict) -> list[str]:
    """Sanity-check field mappings against actual content. Drops mappings
    that do not hold up (e.g. a 'date' column that contains names, an
    'application' column that contains approval statuses or free text) and
    returns human-readable notes about what was rejected."""
    notes = []
    for field in ("created_date", "resolved_date"):
        col = mapping.get(field)
        if not col:
            continue
        sample = df[col].dropna().astype(str)
        sample = sample[sample.str.strip() != ""].head(300)
        if not len(sample):
            continue
        parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
        if parsed.notna().mean() < 0.2:
            notes.append(
                f"Column '{col}' looked like {field} by name but its values are not "
                "dates; mapping rejected so downstream metrics are not corrupted.")
            del mapping[field]
    if "mttr_hours" in mapping:
        sample = pd.to_numeric(df[mapping["mttr_hours"]], errors="coerce")
        if sample.notna().mean() < 0.2:
            notes.append(
                f"Column '{mapping['mttr_hours']}' looked like an MTTR column but is "
                "not numeric; mapping rejected.")
            del mapping["mttr_hours"]

    # Categorical fields: reject columns whose content is approval-status
    # vocabulary or mostly free text / URLs / log lines.
    for field in ("application", "category", "subcategory", "assignment_group",
                  "department", "ticket_type"):
        col = mapping.get(field)
        if not col:
            continue
        sample = df[col].dropna().astype(str)
        sample = sample[sample.str.strip() != ""].head(500)
        if not len(sample):
            continue
        lowered = sample.str.strip().str.lower()
        status_share = lowered.isin(STATUS_LIKE).mean()
        implausible_share = 1 - sample.map(plausible_label).mean()
        if status_share > 0.5:
            notes.append(
                f"Column '{col}' looked like {field} by name but contains approval/"
                f"status values ({round(status_share * 100)}% match status vocabulary); "
                "mapping rejected.")
            del mapping[field]
        elif implausible_share > 0.5:
            notes.append(
                f"Column '{col}' looked like {field} by name but over half its values "
                "are free text, URLs, or log fragments; mapping rejected.")
            del mapping[field]
    return notes


_XLSX_MAGIC = b"PK\x03\x04"  # xlsx is a zip container
_XLS_MAGIC = b"\xd0\xcf\x11\xe0"  # legacy OLE2 .xls


def _is_excel(source, filename: str | None) -> bool:
    if filename and filename.lower().endswith((".xlsx", ".xlsm", ".xls")):
        return True
    head = None
    if isinstance(source, str):
        if source.lower().endswith((".xlsx", ".xlsm", ".xls")):
            return True
        try:
            with open(source, "rb") as f:
                head = f.read(4)
        except OSError:
            return False
    elif hasattr(source, "read") and hasattr(source, "seek"):
        head = source.read(4)
        source.seek(0)
    return head in (_XLSX_MAGIC, _XLS_MAGIC)


def _read_excel(source) -> pd.DataFrame:
    """Read the first non-empty sheet as strings."""
    sheets = pd.read_excel(source, sheet_name=None, dtype=str,
                           keep_default_na=False, na_values=NA_VALUES)
    for name, df in sheets.items():
        if len(df) and len(df.columns):
            return df
    # all empty: return the first anyway
    return next(iter(sheets.values()))


def load_csv(source, filename: str | None = None) -> tuple[pd.DataFrame, dict, list[str]]:
    """Load a CSV or Excel file from a path, file-like object, or raw bytes.

    Returns (raw_dataframe, column_mapping, mapping_notes).
    """
    if isinstance(source, bytes):
        source = io.BytesIO(source)

    if _is_excel(source, filename):
        df = _read_excel(source)
    else:
        try:
            df = pd.read_csv(source, dtype=str, keep_default_na=False, na_values=NA_VALUES)
        except UnicodeDecodeError:
            if hasattr(source, "seek"):
                source.seek(0)
            df = pd.read_csv(source, dtype=str, keep_default_na=False,
                             na_values=NA_VALUES, encoding="latin-1")
    df.columns = [str(c).strip() for c in df.columns]
    mapping = detect_columns(df.columns)
    notes = _validate_mapping(df, mapping)
    return df, mapping, notes
