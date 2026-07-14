"""Enterprise theme categorization (methodology step 3).

Rule-based keyword classification into 14 business themes. Rules are ordered:
more specific themes (SAP, Salesforce, MDM) are checked before generic ones
(Application & Software) so that "iPad managed by Intune" lands in MDM, not
Hardware, and "Salesforce content not syncing" lands in CRM, not Hardware.

Each ticket gets a theme and a confidence:
- high: matched 2+ keywords or a strong keyword
- medium: matched 1 keyword
- low: fell through to Other / Unclear
"""

import re

import pandas as pd

# (theme, strong_keywords, weak_keywords)
# Order matters: first match wins for equal strength.
THEME_RULES = [
    ("SAP / ERP", [
        r"\bsap\b", r"\berp\b", r"\bs/4\s?hana\b", r"\bfiori\b", r"attendance unlock",
        r"\bcats\b", r"\bsap gui\b",
    ], [r"\binvoice posting\b", r"\bpurchase order\b", r"\bmaterial master\b"]),
    ("Salesforce / CRM", [
        r"\bsalesforce\b", r"\bsfdc\b", r"\bcrm\b", r"\bopportunity\b.*\bsync\b",
        r"\blead assignment\b", r"\bsales cloud\b", r"\bservice cloud\b",
    ], [r"\baccount record\b", r"\bcontact record\b", r"\bcampaign\b"]),
    ("HR & Payroll", [
        r"\bpayroll\b", r"\bpayslip\b", r"\bsalary\b", r"\bworkday\b", r"\bsuccessfactors\b",
        r"\bpay slip\b", r"\btax declaration\b", r"\bform 16\b", r"\breimbursement\b",
        r"\bonboarding\b", r"\boffboarding\b", r"\bexit process\b",
    ], [r"\bhr\b", r"\bemployee record\b", r"\bbenefits\b", r"\bcompensation\b"]),
    ("Attendance & Leave", [
        r"\battendance\b", r"\bleave balance\b", r"\bleave request\b", r"\btimesheet\b",
        r"\btime sheet\b", r"\bregulari[sz]ation\b", r"\bshift\b.*\broster\b", r"\bswipe\b",
        r"\bclock in\b", r"\bclock out\b", r"\bpunch\b",
    ], [r"\bleave\b", r"\bholiday calendar\b", r"\bwfh request\b"]),
    ("Access & Authentication", [
        r"\bpassword reset\b", r"\baccount lock", r"\blocked out\b", r"\bmfa\b", r"\b2fa\b",
        r"\bokta\b", r"\bentra\b", r"\bazure ad\b", r"\bsso\b", r"\bsingle sign", r"\botp\b",
        r"\baccess request\b", r"\bpermission\b.*\b(denied|request)\b", r"\bunauthori[sz]ed\b",
        r"\bvpn access\b", r"\brole assignment\b", r"\bprovision\b", r"\bdeprovision\b",
        r"\bauthenticat", r"\blogin\b.*\b(fail|issue|problem|error|unable)\b",
        r"\bunable to log ?in\b", r"\bcannot log ?in\b", r"\bcan'?t log ?in\b", r"\bsign[- ]?in\b",
    ], [r"\baccess\b", r"\bpassword\b", r"\bcredential", r"\baccount\b.*\bdisabled\b"]),
    ("Device Management / MDM", [
        r"\bintune\b", r"\bmdm\b", r"\bjamf\b", r"\bworkspace one\b", r"\bairwatch\b",
        r"\bdevice enrol", r"\bdevice compliance\b", r"\bcompany portal\b", r"\bkiosk mode\b",
        r"\bdevice wipe\b", r"\bremote wipe\b", r"\bdevice policy\b", r"\bmanaged device\b",
        r"\bautopilot\b", r"\bdep\b.*\benrol",
    ], [r"\bprofile\b.*\bdevice\b"]),
    ("Email & Collaboration", [
        r"\boutlook\b", r"\bexchange\b", r"\bmailbox\b", r"\bemail\b.*\b(not|issue|problem|delay|bounce)\b",
        r"\bteams\b.*\b(call|meeting|channel|chat|not)\b", r"\bmicrosoft teams\b", r"\bslack\b",
        r"\bzoom\b", r"\bwebex\b", r"\bsharepoint\b", r"\bonedrive\b", r"\bcalendar\b",
        r"\bdistribution list\b", r"\bshared mailbox\b", r"\bgoogle workspace\b", r"\bgmail\b",
    ], [r"\bemail\b", r"\bmeeting\b"]),
    ("Network & Connectivity", [
        r"\bvpn\b(?!.*access request)", r"\bwi-?fi\b", r"\bwireless\b", r"\blan\b", r"\bethernet\b",
        r"\bnetwork\b.*\b(down|slow|issue|drop|outage)\b", r"\bconnectivity\b", r"\bdns\b",
        r"\bproxy\b", r"\bfirewall\b", r"\bip address\b", r"\bbandwidth\b", r"\binternet\b.*\b(slow|down|not)\b",
    ], [r"\bnetwork\b", r"\brouter\b", r"\bswitch port\b"]),
    ("Hardware & Devices", [
        r"\blaptop\b.*\b(broken|damage|repair|replace|not (turning|booting|charging)|slow|crash)\b",
        r"\bkeyboard\b", r"\bmouse\b", r"\bmonitor\b", r"\bdocking station\b", r"\bheadset\b",
        r"\bprinter\b", r"\bscanner\b", r"\bbattery\b", r"\bscreen\b.*\b(crack|broken|flicker)\b",
        r"\bhard disk\b", r"\bssd\b", r"\bram\b.*\bupgrade\b", r"\bcharger\b", r"\badapter\b",
        r"\bnew laptop\b", r"\blaptop request\b", r"\basset return\b", r"\bdesktop\b.*\b(issue|not)\b",
    ], [r"\blaptop\b", r"\bhardware\b", r"\bdevice\b.*\b(broken|physical|damage)\b", r"\bmacbook\b"]),
    ("Approval / Workflow", [
        r"\bapproval\b.*\b(pending|stuck|delay|not)\b", r"\bapprove\b.*\brequest\b",
        r"\bworkflow\b.*\b(stuck|error|fail|broken)\b", r"\bpending approval\b",
        r"\breminder\b.*\bapprover\b", r"\bescalat", r"\breassign\b.*\bapproval\b",
    ], [r"\bapproval\b", r"\bworkflow\b"]),
    ("Data / Reporting", [
        r"\breport\b.*\b(generate|not|missing|wrong|incorrect|fail|request)\b", r"\bdashboard\b",
        r"\bpower ?bi\b", r"\btableau\b", r"\bexport\b.*\b(data|csv|excel)\b", r"\bdata extract\b",
        r"\bdata reconcil", r"\bmis report\b", r"\banalytics\b", r"\bdata mismatch\b",
        r"\bdata (sync|discrepanc)",
    ], [r"\breport\b", r"\bdata\b.*\bincorrect\b"]),
    ("Knowledge / How-to", [
        r"\bhow (do|to|can) i\b", r"\bhow to\b", r"\bwhere (do|can) i\b", r"\bguide\b",
        r"\binstruction", r"\bdocumentation\b", r"\bpolicy\b.*\b(question|clarif)\b",
        r"\bwhat is the (process|policy|procedure)\b", r"\bhelp with\b", r"\bquery regarding\b",
        r"\bclarification\b", r"\bquestion about\b",
    ], [r"\bpolicy\b", r"\bprocess question\b"]),
    ("Application & Software", [
        r"\binstall\b", r"\buninstall\b", r"\bsoftware request\b", r"\blicense\b", r"\blicence\b",
        r"\bupgrade\b.*\b(version|software|app)\b", r"\bapplication\b.*\b(error|crash|slow|not (working|loading|responding))\b",
        r"\bapp\b.*\b(crash|error|not working|freez)\b", r"\bbug\b", r"\berror message\b",
        r"\bexception\b", r"\bpatch\b", r"\bversion update\b", r"\bactivation\b",
        r"\bcontent\b.*\b(not|missing|sync|update|push)\b", r"\bslide\b.*\b(not|missing|old|outdated)\b",
    ], [r"\bsoftware\b", r"\bapplication\b", r"\bapp\b", r"\bcrash", r"\bnot working\b"]),
]

FALLBACK_THEME = "Other / Unclear"

ALL_THEMES = [t[0] for t in THEME_RULES] + [FALLBACK_THEME]

_COMPILED = [
    (theme,
     [re.compile(p) for p in strong],
     [re.compile(p) for p in weak])
    for theme, strong, weak in THEME_RULES
]


def classify_text(text: str) -> tuple[str, str, list]:
    """Return (theme, confidence, matched_keywords)."""
    if not text or not text.strip():
        return FALLBACK_THEME, "low", []
    best = None  # (score, theme, matches)
    for theme, strong, weak in _COMPILED:
        matches = []
        score = 0
        for pat in strong:
            m = pat.search(text)
            if m:
                score += 2
                matches.append(m.group(0).strip())
        for pat in weak:
            m = pat.search(text)
            if m:
                score += 1
                matches.append(m.group(0).strip())
        if score > 0 and (best is None or score > best[0]):
            best = (score, theme, matches)
    if best is None:
        return FALLBACK_THEME, "low", []
    score, theme, matches = best
    confidence = "high" if score >= 3 else ("medium" if score == 2 else "low")
    return theme, confidence, matches[:5]


def classify(view: pd.DataFrame) -> pd.DataFrame:
    """Add theme, theme_confidence, theme_keywords columns to the view."""
    results = view["_text"].map(classify_text)
    view = view.copy()
    view["theme"] = results.map(lambda r: r[0])
    view["theme_confidence"] = results.map(lambda r: r[1])
    view["theme_keywords"] = results.map(lambda r: ", ".join(r[2]))
    return view


def theme_summary(view: pd.DataFrame) -> list[dict]:
    """Per-theme rollup used by the report (deliverable E)."""
    total = len(view)
    out = []
    for theme, grp in view.groupby("theme"):
        mttr = grp["mttr_hours"].dropna()
        # top issue types: most common summaries (first 8 words as a proxy)
        phrases = (
            grp["summary"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True)
            .str.split().str[:8].str.join(" ")
        )
        top_phrases = phrases[phrases != ""].value_counts().head(5).index.tolist()
        apps = grp.loc[grp["application"] != "", "application"].value_counts().head(5).to_dict()
        cats = grp.loc[grp["category_raw"] != "", "category_raw"].value_counts().head(5).to_dict()
        conf_share = grp["theme_confidence"].value_counts(normalize=True).to_dict()
        dominant_conf = ("high" if conf_share.get("high", 0) >= 0.5
                         else "medium" if conf_share.get("high", 0) + conf_share.get("medium", 0) >= 0.5
                         else "low")
        out.append({
            "theme": theme,
            "count": len(grp),
            "pct": round(len(grp) / total * 100, 1) if total else 0.0,
            "mttr_median": round(float(mttr.median()), 1) if len(mttr) else None,
            "mttr_mean": round(float(mttr.mean()), 1) if len(mttr) else None,
            "mttr_coverage_pct": round(len(mttr) / len(grp) * 100, 1),
            "top_issue_phrases": top_phrases,
            "top_applications": apps,
            "top_raw_categories": cats,
            "confidence": dominant_conf,
        })
    out.sort(key=lambda d: d["count"], reverse=True)
    return out
