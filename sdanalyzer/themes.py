"""Enterprise theme categorization (methodology step 3).

Rule-based keyword classification into 15 business themes. Rules are ordered:
more specific themes (SAP, Salesforce, Security, MDM) are checked before
generic ones (Application & Software).

Scoring is summary-first: the ticket subject (plus raw category/application
fields) carries full weight; the free-text description carries half weight.
Long polite descriptions ("please help", "how do I raise this") otherwise
drown out the subject and produce absurd classifications.

Each ticket gets a theme and a confidence:
- high: strong evidence in the summary
- medium: single keyword or description-driven match
- low: weak/no evidence (Other / Unclear)
"""

import re
from collections import Counter

import pandas as pd

# (theme, strong_keywords, weak_keywords)
# Order matters: first match wins for equal strength.
THEME_RULES = [
    ("Security & Compliance", [
        r"\bcasb\b", r"\bgtb\b", r"\bdlp\b", r"\bsentinel\s?one\b", r"\bcrowdstrike\b",
        r"\bdefender\b", r"\bantivirus\b", r"\bmalware\b", r"\bphishing\b", r"\bvirus\b",
        r"\bsecurity (incident|alert|patch|vulnerabilit)", r"\bvulnerabilit",
        r"\bcompliance report\b", r"\bcompliance\b.*\b(weekly|monthly|location|india|emea|us)\b",
        r"\binfosec\b", r"\bsoc\b.*\balert\b", r"\bsiem\b", r"\bencryption\b.*\b(disk|drive)\b",
        r"\bbitlocker\b", r"\bfilevault\b", r"\bzscaler\b", r"\bnetskope\b",
    ], [r"\bcompliance\b", r"\bsecurity\b", r"\baudit\b.*\b(log|report)\b"]),
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
        r"\b(need|request|requesting|provide|grant|give|remove|revoke|enable|disable)\b.{0,30}\baccess\b",
        r"\baccess\b.{0,20}\b(removal|request|issue|required|needed)\b",
        r"\badd\b.{0,25}\buser\b", r"\bremove\b.{0,25}\buser\b", r"\bcopilot access\b",
        r"\blicense\b.{0,20}\b(assign|allocat|remov)", r"\bonboard\b.{0,20}\baccess\b",
        r"\boffboard", r"\baccess removal\b", r"\bgroup membership\b",
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
        r"\bemail id\b", r"\bemail\b.{0,20}\b(creation|create|setup|new)\b", r"\bdl\b.{0,15}\b(add|remove)\b",
    ], [r"\bemail\b", r"\bmeeting\b"]),
    ("Network & Connectivity", [
        r"\bvpn\b(?!.*access request)", r"\bwi-?fi\b", r"\bwireless\b", r"\blan\b", r"\bethernet\b",
        r"\bnetwork\b.*\b(down|slow|issue|drop|outage)\b", r"\bconnectivity\b", r"\bdns\b",
        r"\bproxy\b", r"\bfirewall\b", r"\bip address\b", r"\bbandwidth\b", r"\binternet\b.*\b(slow|down|not)\b",
    ], [r"\bnetwork\b", r"\brouter\b", r"\bswitch port\b"]),
    ("Hardware & Devices", [
        r"\blaptop\b.*\b(broken|damage|repair|replace|replacement|not (turning|booting|charging)|slow|crash|prepar|setup|issue)\b",
        r"\bkeyboard\b", r"\bmouse\b", r"\bmonitor\b", r"\bdocking station\b", r"\bheadset\b",
        r"\bheadphone", r"\bearphone", r"\bwebcam\b", r"\bhdmi\b", r"\bdisplay port\b",
        r"\bprinter\b", r"\bscanner\b", r"\bbattery\b", r"\bscreen\b.*\b(crack|broken|flicker)\b",
        r"\bhard disk\b", r"\bssd\b", r"\bram\b.*\bupgrade\b", r"\bcharger\b", r"\badapter\b",
        r"\bnew laptop\b", r"\blaptop request\b", r"\basset (return|allocation|recovery)\b",
        r"\bdesktop\b.*\b(issue|not)\b", r"\bsystem setup\b", r"\bmachine\b.*\b(replace|slow|issue)\b",
        r"\btech direct\b", r"\bwarranty\b", r"\bnot charging\b", r"\bnot working\b.*\b(port|cable|dock)\b",
    ], [r"\blaptop\b", r"\bhardware\b", r"\bdevice\b.*\b(broken|physical|damage)\b", r"\bmacbook\b",
        r"\bdell\b", r"\blenovo\b", r"\bthinkpad\b"]),
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


def _score_field(text: str, strong, weak, weight: float):
    matches, score = [], 0.0
    if not text:
        return score, matches
    for pat in strong:
        m = pat.search(text)
        if m:
            score += 2 * weight
            matches.append(m.group(0).strip())
    for pat in weak:
        m = pat.search(text)
        if m:
            score += 1 * weight
            matches.append(m.group(0).strip())
    return score, matches


def classify_fields(primary: str, secondary: str) -> tuple[str, str, list]:
    """Classify with summary-first weighting.

    primary: subject + raw category + application (weight 1.0)
    secondary: free-text description (weight 0.5)

    Confidence is high only when the primary field carries the evidence;
    a match that exists solely in the description caps at low/medium so
    boilerplate phrases in polite descriptions cannot outvote the subject.
    """
    primary = (primary or "").lower()
    secondary = (secondary or "").lower()
    if not primary.strip() and not secondary.strip():
        return FALLBACK_THEME, "low", []

    best = None  # (total, primary_score, theme, matches)
    for theme, strong, weak in _COMPILED:
        p_score, p_matches = _score_field(primary, strong, weak, 1.0)
        s_score, s_matches = _score_field(secondary, strong, weak, 0.5)
        total = p_score + s_score
        if total > 0 and (best is None or total > best[0]):
            best = (total, p_score, theme, p_matches + s_matches)
    if best is None:
        return FALLBACK_THEME, "low", []
    total, p_score, theme, matches = best
    if p_score >= 3:
        confidence = "high"
    elif p_score >= 2 or total >= 2.5:
        confidence = "medium"
    elif p_score > 0:
        confidence = "medium" if total >= 2 else "low"
    else:
        confidence = "low"  # description-only evidence
    return theme, confidence, matches[:5]


def classify(view: pd.DataFrame) -> pd.DataFrame:
    """Add theme, theme_confidence, theme_keywords columns to the view."""
    view = view.copy()
    primary = (view["summary"] + " " + view["category_raw"] + " " +
               view["subcategory_raw"] + " " + view["application"]).str.lower()
    secondary = view["description"].str.lower()
    results = [classify_fields(p, s) for p, s in zip(primary, secondary)]
    view["theme"] = [r[0] for r in results]
    view["theme_confidence"] = [r[1] for r in results]
    view["theme_keywords"] = [", ".join(r[2]) for r in results]
    return view


_STOPWORDS = frozenset("""
a an and are as at be been by can could do does for from get has have hi hello
how i if in is it its me my need needs new no not of on or our please pls
regarding request requesting required so team thank thanks the this to unable
us use user we with would you your kindly dear help issue am pm facing since
""".split())


def mine_other_terms(view: pd.DataFrame, top: int = 15) -> list[tuple[str, int]]:
    """Mine frequent meaningful terms from 'Other / Unclear' summaries so the
    report can show what the blind spot contains instead of hiding it."""
    other = view.loc[view["theme"] == FALLBACK_THEME, "summary"]
    if other.empty:
        return []
    words_counter, bigram_counter = Counter(), Counter()
    for s in other:
        tokens = [t for t in re.findall(r"[a-z0-9][a-z0-9\-\.]{2,}", s.lower())
                  if t not in _STOPWORDS and not t.isdigit()]
        words_counter.update(set(tokens))
        bigram_counter.update({f"{a} {b}" for a, b in zip(tokens, tokens[1:])})
    combined = [(t, n) for t, n in (bigram_counter + words_counter).most_common(top * 3) if n >= 2]
    kept, seen_words = [], set()
    for term, n in sorted(combined, key=lambda x: (-x[1], -len(x[0]))):
        if " " not in term and term in seen_words:
            continue
        if " " in term:
            seen_words.update(term.split())
        kept.append((term, n))
        if len(kept) >= top:
            break
    return kept


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
