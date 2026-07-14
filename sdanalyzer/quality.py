"""Data integrity assessment (methodology step 1).

Inspects the dataset before any insight generation. Reports what exists,
what is missing, and how reliable the data is. Never invents fields.
"""

import pandas as pd

from .textclean import plausible_label

REQUIRED_FIELDS = [
    "ticket_id", "summary", "category", "priority", "status",
    "created_date", "resolved_date",
]
OPTIONAL_FIELDS = [
    "description", "subcategory", "ticket_type", "assignment_group", "assignee",
    "requester", "department", "application", "resolution_notes", "mttr_hours",
    "sla_met",
]


def assess(df: pd.DataFrame, mapping: dict) -> dict:
    total = len(df)
    mapped = set(mapping.keys())
    missing_required = [f for f in REQUIRED_FIELDS if f not in mapped]
    missing_optional = [f for f in OPTIONAL_FIELDS if f not in mapped]

    # Duplicates
    dup_full = int(df.duplicated().sum())
    dup_id = 0
    if "ticket_id" in mapping:
        dup_id = int(df[mapping["ticket_id"]].duplicated().sum())

    # Date range
    date_range = None
    created_parse_rate = None
    if "created_date" in mapping:
        created = pd.to_datetime(df[mapping["created_date"]], errors="coerce", format="mixed")
        valid = created.dropna()
        created_parse_rate = round(len(valid) / total * 100, 1) if total else 0.0
        if len(valid):
            date_range = (valid.min(), valid.max())

    resolved_parse_rate = None
    if "resolved_date" in mapping:
        resolved = pd.to_datetime(df[mapping["resolved_date"]], errors="coerce", format="mixed")
        resolved_parse_rate = round(resolved.notna().sum() / total * 100, 1) if total else 0.0

    # Field completeness for mapped fields
    completeness = {}
    for field, col in mapping.items():
        non_null = df[col].notna() & (df[col].astype(str).str.strip() != "")
        completeness[field] = round(non_null.sum() / total * 100, 1) if total else 0.0

    # Value inventories
    def _values(field, top=15):
        if field not in mapping:
            return None
        vc = df[mapping[field]].dropna().astype(str).str.strip()
        vc = vc[(vc != "") & vc.map(plausible_label)].value_counts()
        return vc.head(top).to_dict() or None

    inventories = {
        "ticket_types": _values("ticket_type"),
        "priorities": _values("priority"),
        "statuses": _values("status"),
        "assignment_groups": _values("assignment_group"),
        "categories": _values("category"),
        "subcategories": _values("subcategory"),
        "departments": _values("department"),
        "applications": _values("application"),
    }

    # Short-description check
    short_desc_pct = None
    if "summary" in mapping:
        lens = df[mapping["summary"]].fillna("").astype(str).str.len()
        short_desc_pct = round((lens < 15).sum() / total * 100, 1) if total else 0.0

    # Overall quality verdict
    issues = []
    if missing_required:
        issues.append(f"Missing required fields: {', '.join(missing_required)}")
    if dup_id:
        issues.append(f"{dup_id} duplicate ticket IDs")
    if dup_full:
        issues.append(f"{dup_full} fully duplicated rows")
    if created_parse_rate is not None and created_parse_rate < 90:
        issues.append(f"Only {created_parse_rate}% of created dates parse cleanly")
    if "resolved_date" not in mapping:
        issues.append("No resolution timestamp column found; MTTR cannot be computed. "
                      "Request an export with a resolved/closed date column")
    elif resolved_parse_rate is not None and resolved_parse_rate == 0:
        issues.append("Resolved-date column contains no parseable dates; MTTR cannot be computed")
    elif resolved_parse_rate is not None and resolved_parse_rate < 60:
        issues.append(f"Only {resolved_parse_rate}% of tickets have parseable resolved dates; MTTR coverage is partial")
    if short_desc_pct is not None and short_desc_pct > 25:
        issues.append(f"{short_desc_pct}% of ticket summaries are under 15 characters; theme classification confidence is reduced")
    for f in ("category", "application"):
        if f in completeness and completeness[f] < 60:
            issues.append(f"{f} is only {completeness[f]}% populated")

    if missing_required or (created_parse_rate is not None and created_parse_rate < 70):
        verdict = "WEAK"
    elif issues:
        verdict = "MODERATE"
    else:
        verdict = "GOOD"

    return {
        "total_records": total,
        "available_columns": list(df.columns),
        "column_mapping": mapping,
        "missing_required_fields": missing_required,
        "missing_optional_fields": missing_optional,
        "duplicate_rows": dup_full,
        "duplicate_ticket_ids": dup_id,
        "date_range": date_range,
        "created_parse_rate": created_parse_rate,
        "resolved_parse_rate": resolved_parse_rate,
        "completeness": completeness,
        "inventories": inventories,
        "short_summary_pct": short_desc_pct,
        "issues": issues,
        "verdict": verdict,
    }
