"""AI opportunity mapping, Atomicwork solution mapping, agentic use cases,
and ROI estimation (methodology steps 6-9).

All estimates are ranges derived from ticket volume and MTTR in the data.
Nothing is invented: themes with no evidence get "No Automation Recommended".
"""

import pandas as pd

# Per-theme playbook: solution type (A-F), Atomicwork capabilities,
# deflection range (min%, max%), mttr reduction range, complexity, risk.
# Deflection ranges are conservative industry-typical bands, applied only
# when the theme has enough volume; confidence is downgraded otherwise.
THEME_PLAYBOOK = {
    "Access & Authentication": {
        "solution_type": "B. Workflow Automation + C. Integration Automation",
        "capabilities": [
            "AI coworker in Slack or Microsoft Teams", "Employee self-service",
            "Access provisioning", "Identity automation", "MCP/API orchestration",
            "Approval automation",
        ],
        "ai_coworkers": [
            "Atom (front door in Slack/Teams: password reset and unlock, ~90s zero-touch)",
            "Access Guardian (agentic IGA: Okta/Entra provisioning, group membership, "
            "deprovisioning with approval matrix)",
        ],
        "deflection": (40, 60), "mttr_reduction": (50, 80),
        "complexity": "Medium", "risk": "Medium",
        "dependencies": ["Okta / Entra ID API access", "Approval policy definition"],
        "rationale": "Password resets, unlocks, and access requests follow deterministic, "
                     "API-accessible flows via Okta/Entra. Approval steps stay human-in-the-loop.",
    },
    "Knowledge / How-to": {
        "solution_type": "A. Knowledge AI",
        "capabilities": [
            "AI coworker in Slack or Microsoft Teams", "Knowledge ingestion",
            "Ticket deflection", "Employee self-service",
        ],
        "ai_coworkers": [
            "Atom (answers policy/how-to questions from ingested knowledge, cites sources)",
        ],
        "deflection": (50, 70), "mttr_reduction": (60, 90),
        "complexity": "Low", "risk": "Low",
        "dependencies": ["Knowledge article quality and coverage"],
        "rationale": "Repetitive how-to and policy questions are the classic deflection case, "
                     "if knowledge quality is good.",
    },
    "HR & Payroll": {
        "solution_type": "A. Knowledge AI + C. Integration Automation",
        "capabilities": [
            "HR service automation", "AI coworker in Slack or Microsoft Teams",
            "Knowledge ingestion", "MCP/API orchestration", "Human approval loop",
        ],
        "ai_coworkers": [
            "People Ops Assistant (payslips on demand via Workday/SuccessFactors MCP, "
            "benefits and leave policy answers)",
        ],
        "deflection": (30, 50), "mttr_reduction": (30, 50),
        "complexity": "Medium", "risk": "Medium",
        "dependencies": ["Workday / HRMS API access", "HR policy knowledge base"],
        "rationale": "Payslip, tax, and policy queries deflect via knowledge; "
                     "data changes need HRMS integration with human checkpoints.",
    },
    "Attendance & Leave": {
        "solution_type": "C. Integration Automation + E. Human-in-the-loop AI",
        "capabilities": [
            "HR service automation", "Workflow execution", "Approval automation",
            "MCP/API orchestration",
        ],
        "ai_coworkers": [
            "People Ops Assistant (leave balance, regularization requests with manager "
            "approval loop)",
        ],
        "deflection": (35, 55), "mttr_reduction": (40, 60),
        "complexity": "Medium", "risk": "Medium",
        "dependencies": ["HRMS / SAP time-management API or agentic access"],
        "rationale": "Regularization and unlock requests are deterministic once "
                     "manager approval is captured.",
    },
    "Email & Collaboration": {
        "solution_type": "A. Knowledge AI + B. Workflow Automation",
        "capabilities": [
            "Guided troubleshooting", "Employee self-service", "Ticket deflection",
            "Workflow execution",
        ],
        "ai_coworkers": [
            "Collaboration Concierge (DL creation/membership, shared mailboxes, "
            "Entra/Exchange groups via Graph)",
        ],
        "deflection": (30, 50), "mttr_reduction": (30, 50),
        "complexity": "Low", "risk": "Low",
        "dependencies": ["M365 / Google admin API for mailbox and DL actions"],
        "rationale": "DL membership, shared mailbox, and common Teams/Outlook issues are "
                     "scriptable; how-to volume deflects to knowledge.",
    },
    "Application & Software": {
        "solution_type": "B. Workflow Automation + A. Knowledge AI",
        "capabilities": [
            "Employee self-service", "Guided troubleshooting", "Workflow execution",
            "Approval automation", "Ticket deflection",
        ],
        "ai_coworkers": [
            "Atom (software catalog requests with approval chain, license reclaim)",
            "Device Doctor (app push/install via Intune, guided troubleshooting)",
        ],
        "deflection": (25, 45), "mttr_reduction": (30, 50),
        "complexity": "Medium", "risk": "Low",
        "dependencies": ["Software catalog definition", "License pool visibility"],
        "rationale": "Install/license requests are catalog + approval workflows. "
                     "Error/bug reports deflect less; guided troubleshooting helps triage.",
    },
    "Device Management / MDM": {
        "solution_type": "C. Integration Automation + D. Agentic AI",
        "capabilities": [
            "Agentic backend action", "MCP/API orchestration", "IT service automation",
            "Guided troubleshooting",
        ],
        "ai_coworkers": [
            "Device Health Coworker (reads linked asset, runs Intune Endpoint Analytics "
            "diagnostics, proposes remediation for approval; sync/restart auto, "
            "wipe/retire gated)",
        ],
        "deflection": (30, 50), "mttr_reduction": (40, 70),
        "complexity": "Medium", "risk": "Medium",
        "dependencies": ["Intune / Jamf API permissions", "Device compliance policy clarity"],
        "rationale": "Sync, enrollment, and compliance actions are Graph-API accessible; "
                     "console-only actions suit agentic execution with approval.",
    },
    "Security & Compliance": {
        "solution_type": "C. Integration Automation + E. Human-in-the-loop AI",
        "capabilities": [
            "Workflow execution", "MCP/API orchestration", "Human approval loop",
            "Analytics and operational insights",
        ],
        "ai_coworkers": [
            "Phishing Triage Coworker (SPF/DKIM/DMARC forensics, blast radius, verdict "
            "for analyst approval)",
            "SecOps Coworker (device posture + risk reasoning; isolate/scan gated by "
            "approval)",
        ],
        "deflection": (25, 45), "mttr_reduction": (30, 50),
        "complexity": "Medium", "risk": "Medium",
        "dependencies": ["Security tooling API access (EDR, CASB, SIEM)",
                         "InfoSec sign-off on automation scope"],
        "rationale": "Recurring compliance reports, agent-version upgrades, and standard "
                     "security checks are schedulable and API-driven; alerts and "
                     "exceptions stay with the security team.",
    },
    "SAP / ERP": {
        "solution_type": "D. Agentic AI + E. Human-in-the-loop AI",
        "capabilities": [
            "Agentic backend action", "Human approval loop", "Workflow execution",
            "MCP/API orchestration",
        ],
        "ai_coworkers": [
            "Custom ERP Coworker (built in the AI Coworker builder with scoped skills; "
            "unlock/posting actions always behind human approval)",
        ],
        "deflection": (20, 40), "mttr_reduction": (30, 60),
        "complexity": "High", "risk": "High",
        "dependencies": ["SAP BAPI/OData availability or GUI-level agentic access",
                         "Change-control alignment"],
        "rationale": "SAP tasks (unlocks, postings, master-data fixes) often lack clean APIs; "
                     "agentic execution with mandatory human approval is the realistic path.",
    },
    "Salesforce / CRM": {
        "solution_type": "C. Integration Automation + D. Agentic AI",
        "capabilities": [
            "Agentic backend action", "MCP/API orchestration", "Workflow execution",
        ],
        "ai_coworkers": [
            "Custom CRM Coworker (record fixes and content sync via Salesforce MCP/API; "
            "production metadata changes gated by approval)",
        ],
        "deflection": (25, 45), "mttr_reduction": (30, 60),
        "complexity": "Medium", "risk": "Medium",
        "dependencies": ["Salesforce API scopes", "Sandbox for validation"],
        "rationale": "Record fixes, sync retries, and content pushes are API-accessible; "
                     "metadata/admin-console work suits agentic AI.",
    },
    "Approval / Workflow": {
        "solution_type": "B. Workflow Automation",
        "capabilities": [
            "Approval automation", "Workflow execution", "AI coworker in Slack or Microsoft Teams",
        ],
        "ai_coworkers": [
            "Atom (approval chains in Slack/Teams: remind, delegate per matrix, escalate)",
        ],
        "deflection": (40, 60), "mttr_reduction": (50, 80),
        "complexity": "Low", "risk": "Low",
        "dependencies": ["Approval matrix definition"],
        "rationale": "Stuck approvals are solved by reminders, delegation, and escalation "
                     "automation, all deterministic.",
    },
    "Data / Reporting": {
        "solution_type": "C. Integration Automation + D. Agentic AI",
        "capabilities": [
            "Analytics and operational insights", "Agentic backend action",
            "MCP/API orchestration",
        ],
        "ai_coworkers": [
            "Reporting Coworker (builds and refreshes dashboards/reports via Power BI MCP, "
            "distributes on schedule)",
        ],
        "deflection": (20, 40), "mttr_reduction": (30, 50),
        "complexity": "Medium", "risk": "Medium",
        "dependencies": ["BI platform API access", "Report catalog"],
        "rationale": "Recurring report generation and data pulls can be automated; "
                     "ad-hoc analysis stays human.",
    },
    "Network & Connectivity": {
        "solution_type": "A. Knowledge AI + E. Human-in-the-loop AI",
        "capabilities": [
            "Guided troubleshooting", "Knowledge ingestion", "Ticket deflection",
        ],
        "ai_coworkers": [
            "Atom (guided VPN/Wi-Fi triage)",
            "Infrastructure Coworker (guardrailed infra diagnosis: correlate alerts, "
            "root cause, propose remediation with approval)",
        ],
        "deflection": (15, 30), "mttr_reduction": (10, 30),
        "complexity": "Medium", "risk": "Medium",
        "dependencies": ["Network monitoring integration for context"],
        "rationale": "Guided VPN/Wi-Fi triage deflects simple cases; infrastructure issues "
                     "need human engineers.",
    },
    "Hardware & Devices": {
        "solution_type": "F. No Automation Recommended (logistics workflow only)",
        "capabilities": [
            "Employee self-service", "Approval automation", "IT service automation",
        ],
        "ai_coworkers": [
            "Atom (request-approval-dispatch workflow around physical work)",
        ],
        "deflection": (10, 25), "mttr_reduction": (10, 20),
        "complexity": "Low", "risk": "Low",
        "dependencies": ["Asset management integration"],
        "rationale": "Physical repair/replacement needs hands. Only the request-approval-"
                     "dispatch workflow around it can be automated.",
    },
    "Other / Unclear": {
        "solution_type": "F. No Automation Recommended",
        "capabilities": ["Analytics and operational insights"],
        "ai_coworkers": [
            "Ticket Attribute Coworker (categorizes, prioritizes, and routes every ticket "
            "at intake; directly shrinks this bucket)",
        ],
        "deflection": (0, 10), "mttr_reduction": (0, 10),
        "complexity": "n/a", "risk": "n/a",
        "dependencies": ["Better categorization at intake"],
        "rationale": "Too ambiguous to automate. Fix intake quality first, then re-analyze.",
    },
}

# Agentic AI use case templates, triggered when matching themes have volume.
AGENTIC_TEMPLATES = [
    {
        "theme": "SAP / ERP",
        "name": "SAP attendance / account unlock",
        "trigger": "Employee reports locked SAP attendance period or user account",
        "system_of_action": "SAP (GUI or BAPI)",
        "permissions": "SAP service account with unlock authorization, scoped to specific t-codes",
        "steps": ["Validate requester identity", "Confirm lock state in SAP",
                  "Obtain manager/HR approval", "Execute unlock", "Verify and notify"],
        "feasibility": "Medium (depends on BAPI availability; GUI-level agentic if not)",
        "risk": "High", "human_approval": "Required",
        "fallback": "Route to SAP basis team with full context attached",
    },
    {
        "theme": "Salesforce / CRM",
        "name": "CRM content / metadata sync push",
        "trigger": "Field team reports outdated content or failed sync in CRM app",
        "system_of_action": "Salesforce (Metadata/Tooling API or admin console)",
        "permissions": "Integration user with deploy + content management scopes",
        "steps": ["Identify stale content package", "Diff against source of truth",
                  "Push update via API", "Trigger device-side refresh", "Confirm with reporter"],
        "feasibility": "High if API-accessible, Medium for console-only steps",
        "risk": "Medium", "human_approval": "Required for production metadata changes",
        "fallback": "Create change task for CRM admin with prepared diff",
    },
    {
        "theme": "Device Management / MDM",
        "name": "MDM device remediation",
        "trigger": "Device out of compliance, stuck enrollment, or app push failure",
        "system_of_action": "Intune / Jamf (Graph API or console)",
        "permissions": "Graph DeviceManagementManagedDevices.ReadWrite scoped app registration",
        "steps": ["Pull device state", "Run compliance diagnosis", "Execute sync/retire/re-enroll action",
                  "Verify state change", "Update ticket"],
        "feasibility": "High (Graph API covers most actions)",
        "risk": "Medium", "human_approval": "Required for wipe/retire; auto for sync/restart",
        "fallback": "Escalate to endpoint team with diagnostic bundle",
    },
    {
        "theme": "Access & Authentication",
        "name": "Bulk / individual access change execution",
        "trigger": "Approved access request or offboarding event",
        "system_of_action": "Okta / Entra ID",
        "permissions": "Group membership + lifecycle management API scopes",
        "steps": ["Validate approval", "Execute group/role change", "Verify effective access",
                  "Log evidence for audit", "Notify requester"],
        "feasibility": "High",
        "risk": "Medium", "human_approval": "Pre-approved matrix: auto; else approval loop",
        "fallback": "Route to IAM team",
    },
    {
        "theme": "Data / Reporting",
        "name": "Recurring report generation",
        "trigger": "Scheduled or on-demand request for a known report",
        "system_of_action": "BI platform (Power BI / Tableau) or source system",
        "permissions": "Read scopes on datasets, write to distribution channel",
        "steps": ["Identify report template", "Refresh dataset", "Export and distribute",
                  "Log completion"],
        "feasibility": "High for cataloged reports",
        "risk": "Low", "human_approval": "Not required for standard reports",
        "fallback": "Route to analytics team",
    },
    {
        "theme": "Approval / Workflow",
        "name": "Workflow unstick and reassignment",
        "trigger": "Approval pending beyond SLA or approver unavailable",
        "system_of_action": "ITSM / HRMS workflow engine",
        "permissions": "Workflow admin API scope",
        "steps": ["Detect stale approval", "Check approver availability/OOO",
                  "Remind, then delegate per matrix", "Log audit trail"],
        "feasibility": "High",
        "risk": "Low", "human_approval": "Delegation rules pre-approved by process owner",
        "fallback": "Escalate to process owner",
    },
]


def _confidence_for(count: int, total: int, theme_conf: str) -> str:
    share = count / total if total else 0
    if count >= 30 and share >= 0.05 and theme_conf == "high":
        return "High confidence"
    if count >= 10 and theme_conf in ("high", "medium"):
        return "Medium confidence"
    return "Low confidence"


MIN_OPPORTUNITY_TICKETS = 5  # below this, an "opportunity" is statistical noise


def build_opportunities(view: pd.DataFrame, theme_stats: list[dict]) -> list[dict]:
    """One opportunity entry per theme with meaningful volume, mapped to
    playbook + ROI ranges. Themes below MIN_OPPORTUNITY_TICKETS are excluded:
    recommending automation on 2 tickets is noise, not insight."""
    total = len(view)
    out = []
    for ts in theme_stats:
        theme = ts["theme"]
        play = THEME_PLAYBOOK.get(theme)
        if play is None or ts["count"] < MIN_OPPORTUNITY_TICKETS:
            continue
        lo, hi = play["deflection"]
        mlo, mhi = play["mttr_reduction"]
        deflect_lo = int(ts["count"] * lo / 100)
        deflect_hi = int(ts["count"] * hi / 100)
        med = ts["mttr_median"]
        hours_saved = None
        if med is not None:
            hours_saved = (round(deflect_lo * med), round(deflect_hi * med))
        out.append({
            "theme": theme,
            "tickets_addressable": ts["count"],
            "pct_of_total": ts["pct"],
            "solution_type": play["solution_type"],
            "atomicwork_capabilities": play["capabilities"],
            "ai_coworkers": play.get("ai_coworkers", []),
            "deflection_range_pct": (lo, hi),
            "deflection_range_tickets": (deflect_lo, deflect_hi),
            "mttr_reduction_range_pct": (mlo, mhi),
            "est_hours_saved_range": hours_saved,
            "complexity": play["complexity"],
            "risk": play["risk"],
            "dependencies": play["dependencies"],
            "rationale": play["rationale"],
            "confidence": _confidence_for(ts["count"], total, ts["confidence"]),
        })
    # Rank: addressable volume x midpoint deflection, no-automation themes last
    def rank(o):
        no_auto = o["solution_type"].startswith("F.")
        mid = sum(o["deflection_range_tickets"]) / 2
        return (no_auto, -mid)
    out.sort(key=rank)
    return out


def build_agentic_backlog(view: pd.DataFrame) -> list[dict]:
    """Agentic use cases for themes present in the data with meaningful volume."""
    counts = view["theme"].value_counts().to_dict()
    total = len(view)
    out = []
    for tpl in AGENTIC_TEMPLATES:
        n = counts.get(tpl["theme"], 0)
        if n < MIN_OPPORTUNITY_TICKETS:
            continue
        entry = dict(tpl)
        entry["evidence_tickets"] = n
        entry["evidence_pct"] = round(n / total * 100, 1) if total else 0
        entry["expected_impact"] = (
            f"Addresses up to {n} tickets ({entry['evidence_pct']}% of volume) in this theme; "
            "actual impact depends on the share matching this exact scenario. Validate with SMEs."
        )
        entry["confidence"] = ("Medium confidence" if n >= 10 else "Low confidence")
        out.append(entry)
    out.sort(key=lambda e: e["evidence_tickets"], reverse=True)
    return out


def quick_wins(opps: list[dict]) -> list[dict]:
    return [o for o in opps
            if o["complexity"] == "Low" and o["risk"] == "Low"
            and not o["solution_type"].startswith("F.")][:5]
