"""Label plausibility checks.

Real-world exports carry email bodies, tracking URLs, base64 blobs, and
error logs inside categorical fields. Anything that is not a plausible
short label must never surface in a rollup table.
"""

import re

# Workflow/approval vocabulary: a column dominated by these is an approval
# or status column, regardless of what its header says.
STATUS_LIKE = {
    "approved", "rejected", "cancelled", "canceled", "not requested",
    "pending", "denied", "requested", "yes", "no", "true", "false",
    "n/a", "na", "none", "completed", "in progress", "on hold",
}

_URL_RE = re.compile(r"https?://|www\.|sendgrid|\.ct\.|click\?upn|mailto:")
_BLOB_RE = re.compile(r"[A-Za-z0-9+/\-_%]{40,}")   # base64/tracking blobs
_LOG_RE = re.compile(r"error type|timed out|exception|stack trace|:\d\d:\d\d")


def plausible_label(v) -> bool:
    """True if v looks like a short categorical label (app name, category,
    team name), not free text, a URL, a log line, or an encoded blob."""
    if v is None:
        return False
    s = str(v).strip()
    if not s or len(s) > 60:
        return False
    if "\n" in s or "\t" in s:
        return False
    if s.isdigit():           # bare record IDs are not categories
        return False
    lo = s.lower()
    if _URL_RE.search(lo) or _LOG_RE.search(lo):
        return False
    if len(s.split()) > 8:
        return False
    if _BLOB_RE.search(s):
        return False
    return True


def scrub_labels(series):
    """Blank out implausible values in a pandas Series of labels."""
    return series.map(lambda v: str(v).strip() if plausible_label(v) else "")


# Free-text cleaning: applied to summary/description before classification
# and display. Strips content that carries no analytical signal and pollutes
# phrase mining (tracking URLs, base64 blobs, angle-bracket link dumps,
# [image] markers, HTML entities).
_STRIP_PATTERNS = [
    re.compile(r"<https?://[^>]*>"),          # angle-bracket link dumps
    re.compile(r"https?://\S+"),               # bare URLs
    re.compile(r"\[image\]", re.IGNORECASE),
    re.compile(r"\[cid:[^\]]*\]", re.IGNORECASE),
    re.compile(r"&[a-z]+;|&#\d+;"),            # HTML entities
    re.compile(r"[A-Za-z0-9+/\-_%]{40,}"),     # base64 / tracking blobs
    # Email signature/footer noise: must not influence classification
    # ("Get Outlook for iOS" would otherwise pull tickets into Email theme)
    re.compile(r"get outlook for (ios|android)", re.IGNORECASE),
    re.compile(r"sent from my (iphone|ipad|android|samsung|galaxy)[^.]*", re.IGNORECASE),
    re.compile(r"\[external\]", re.IGNORECASE),
    re.compile(r"external sender[:.][^.]*\.", re.IGNORECASE),
    re.compile(r"disclaimer:.*", re.IGNORECASE | re.DOTALL),
    re.compile(r"this email and any files transmitted.*", re.IGNORECASE | re.DOTALL),
    re.compile(r"(warm |kind |best )?regards,.*", re.IGNORECASE | re.DOTALL),
]
_WS_RE = re.compile(r"\s+")

MAX_FREETEXT_CHARS = 1500  # email-thread dumps beyond this add noise, not signal


def clean_text(v) -> str:
    """Strip URLs, blobs, and markup from free text; collapse whitespace;
    cap length so pasted email threads cannot dominate analysis."""
    if v is None:
        return ""
    s = str(v)
    for pat in _STRIP_PATTERNS:
        s = pat.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s[:MAX_FREETEXT_CHARS]
