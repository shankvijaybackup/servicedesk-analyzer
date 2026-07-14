"""Step 12: Implementation and UAT package.

Turns the analyzed ticket data into the artifacts a project manager needs to
test and go live on a new ITSM/PM tool: a UAT test plan derived from the real
workflows found in the data, a role and permission matrix built from the
detected assignment groups, an implementation RACI, a go-live readiness
checklist, and a 15-day testing phase plan.

Like everything else in this tool it is deterministic and traceable: every
test case cites the data signal that generated it (a theme, a priority, an
assignment group, a data-quality gap). Nothing is invented; if the data does
not show approvals, no approval test is emitted. Test cases reference themes
and aggregate values only, never raw ticket rows.
"""

from __future__ import annotations

import pandas as pd

from .themes import OTHER

_MIN_THEME_COUNT = 5     # do not build a test case on fewer tickets than this
_MAX_THEME_CASES = 8     # cap lifecycle cases so the plan stays executable
_MAX_GROUPS = 6          # cap role rows derived from assignment groups

_CANONICAL_STATUSES = ["Open", "In Progress", "Pending", "Resolved"]


def build(classified: pd.DataFrame, integ: dict, theme_summaries: list[dict],
          mttr_res: dict) -> dict:
    themes = [t for t in theme_summaries
              if t["theme"] != OTHER and t["count"] >= _MIN_THEME_COUNT]
    groups = _detected(classified, "assignment_group", _MAX_GROUPS)
    priorities = _detected(classified, "priority", 5)
    types = _detected(classified, "type", 5)
    statuses = [s for s in _CANONICAL_STATUSES
                if s in set(classified["status"].dropna().astype(str))]

    counter = _Counter()
    cases: list[dict] = []
    cases += _lifecycle_cases(counter, themes, statuses)
    cases += _priority_cases(counter, priorities, mttr_res)
    cases += _role_cases(counter, groups)
    cases += _notification_cases(counter)
    cases += _approval_cases(counter, themes)
    cases += _reporting_cases(counter, integ)
    cases += _migration_cases(counter, integ)

    must = sum(1 for c in cases if c["priority"] == "Must")
    return {
        "test_plan": {
            "cases": cases,
            "total_cases": len(cases),
            "must_count": must,
            "should_count": sum(1 for c in cases if c["priority"] == "Should"),
            "could_count": sum(1 for c in cases if c["priority"] == "Could"),
            "coverage_note": (
                f"Cases are generated from the {len(themes)} themes, "
                f"{len(groups)} assignment groups, and {len(priorities)} priority levels "
                f"observed in the data. Test how the team actually works, not every feature."),
        },
        "role_matrix": _role_matrix(groups),
        "raci": _raci(),
        "readiness_checklist": _readiness(integ, theme_summaries, types),
        "phase_plan_15_day": _phase_plan(themes, groups),
        "assumptions": [
            "Test in a sandbox if available. If not, disable outbound email/notifications "
            "or redirect them to internal test recipients before any test run, so no "
            "customer or end user is notified by accident.",
            "Use dedicated test accounts per role, never personal or customer accounts.",
            "Test cases reflect workflows observed in the historical data; new processes "
            "introduced by the tool need cases added by the process owner.",
            "Every Must case needs a pass and a named sign-off before go-live.",
        ],
    }


class _Counter:
    def __init__(self) -> None:
        self.n = 0

    def next(self) -> str:
        self.n += 1
        return f"TC-{self.n:03d}"


def _case(counter: _Counter, area: str, title: str, role: str, steps: list[str],
          expected: str, priority: str, source: str) -> dict:
    return {"id": counter.next(), "area": area, "title": title, "role": role,
            "steps": steps, "expected": expected, "priority": priority,
            "source": source}


def _lifecycle_cases(counter: _Counter, themes: list[dict], statuses: list[str]) -> list[dict]:
    cases = []
    flow = " -> ".join(statuses) if statuses else "Open -> Resolved"
    for t in themes[:_MAX_THEME_CASES]:
        top_type = t["top_types"][0]["value"] if t["top_types"] else "request"
        cases.append(_case(
            counter, "End-to-end lifecycle",
            f"Full lifecycle for a {t['theme']} ticket",
            "Requester + Agent",
            [f"As a requester, raise a {top_type.lower()} representative of the "
             f"'{t['theme']}' theme",
             "Verify it is categorized and routed to the right queue",
             "As an agent, assign it, work it, and add a resolution note",
             f"Move it through the status flow ({flow}) and close it",
             "Verify the requester can see the state at each step"],
            "Ticket completes the full flow; every transition is recorded and visible "
            "to the requester",
            "Must",
            f"theme '{t['theme']}': {t['count']} tickets ({t['pct']}% of volume)"))
    return cases


def _priority_cases(counter: _Counter, priorities: list[str], mttr_res: dict) -> list[dict]:
    cases = []
    for p in priorities[:4]:
        cases.append(_case(
            counter, "Priority and SLA",
            f"SLA behavior for priority {p}",
            "Agent",
            [f"Create a test ticket at priority {p}",
             "Verify the SLA clock, target, and any escalation timer start correctly",
             "Let the ticket approach breach in the test window if feasible",
             "Verify breach warnings fire to the right people"],
            f"Priority {p} applies the configured SLA and escalation path",
            "Must" if p in {"P1", "P2"} else "Should",
            f"priority '{p}' present in the data"))
    if mttr_res.get("available") and mttr_res.get("slowest"):
        sl = mttr_res["slowest"][0]
        cases.append(_case(
            counter, "Priority and SLA",
            f"Escalation path for the historically slowest area ({sl['value']})",
            "Agent + Manager",
            [f"Create a ticket in the '{sl['value']}' area",
             "Leave it unactioned past the escalation threshold",
             "Verify it escalates to the manager or next tier automatically"],
            "Stale tickets escalate instead of sitting idle",
            "Should",
            f"slowest theme by MTTR: {sl['value']} at {sl['median_hours']}h median"))
    return cases


def _role_cases(counter: _Counter, groups: list[str]) -> list[dict]:
    cases = [_case(
        counter, "Roles and permissions",
        "Requester sees only their own tickets",
        "Requester",
        ["Log in as a plain requester test account",
         "Verify they can raise and view their own tickets",
         "Verify they cannot see other users' tickets, admin settings, or queues"],
        "Requester access is limited to their own records",
        "Must",
        "baseline role separation")]
    for g in groups:
        cases.append(_case(
            counter, "Roles and permissions",
            f"Queue visibility and assignment for group '{g}'",
            f"Agent ({g})",
            [f"Log in as a test agent in '{g}'",
             f"Verify the agent sees the '{g}' queue and can pick up and reassign within it",
             "Verify the agent cannot edit tickets owned exclusively by other groups "
             "unless that is intended"],
            f"'{g}' agents work their queue; cross-queue access matches the agreed design",
            "Must",
            f"assignment group '{g}' present in the data"))
    return cases


def _notification_cases(counter: _Counter) -> list[dict]:
    steps_guard = ("Before running: confirm outbound email is disabled or redirected "
                   "to internal test recipients")
    return [
        _case(counter, "Notifications",
              "Acknowledgement on ticket creation",
              "Requester",
              [steps_guard,
               "Raise a test ticket",
               "Verify the requester receives (or would receive) a creation acknowledgement",
               "Verify the notification goes only to the intended recipient"],
              "Creation acknowledgement is sent to the requester only",
              "Must", "standard notification flow; email-safety guard applied"),
        _case(counter, "Notifications",
              "Assignment and resolution notifications",
              "Agent",
              [steps_guard,
               "Assign a test ticket to an agent and verify the agent is notified",
               "Resolve it and verify the requester is notified with the resolution"],
              "Assignment notifies the agent; resolution notifies the requester",
              "Must", "standard notification flow; email-safety guard applied"),
        _case(counter, "Notifications",
              "No notifications leak outside the test group",
              "Project Manager",
              ["Review the notification/audit log after a full test day",
               "Verify no notification was sent to a real end user or external address"],
              "Zero notifications reached anyone outside the test group",
              "Must", "risk raised for go-lives without a test environment"),
    ]


def _approval_cases(counter: _Counter, themes: list[dict]) -> list[dict]:
    names = {t["theme"] for t in themes}
    cases = []
    if "Approval / Workflow" in names or "Access & Authentication" in names:
        target = ("Approval / Workflow" if "Approval / Workflow" in names
                  else "Access & Authentication")
        cases.append(_case(
            counter, "Approvals",
            f"Approval flow for a {target} request",
            "Requester + Approver",
            [f"Raise a request in the '{target}' area that requires approval",
             "Verify the approver is notified and can approve or reject",
             "Verify rejection returns the request with a reason",
             "Verify approval releases the request for fulfilment"],
            "Approve and reject paths both work and are recorded",
            "Must",
            f"theme '{target}' present in the data"))
        cases.append(_case(
            counter, "Approvals",
            "Approval cannot be bypassed",
            "Agent",
            ["As an agent, attempt to fulfil an approval-gated request before approval",
             "Verify the tool blocks fulfilment until the approval is recorded"],
            "Approval gate cannot be skipped",
            "Should",
            "control test for the approval flow"))
    return cases


def _reporting_cases(counter: _Counter, integ: dict) -> list[dict]:
    return [
        _case(counter, "Reporting",
              "Operational report matches known baseline",
              "Manager",
              ["Run the volume-by-category and open-backlog reports on the test data",
               "Compare against the counts from this analysis as the baseline"],
              "Report figures reconcile with the baseline counts",
              "Should",
              f"baseline: {integ['total_records']} records analyzed"),
        _case(counter, "Reporting",
              "MTTR/resolution-time report is computable",
              "Manager",
              ["Resolve at least two test tickets with known timestamps",
               "Run the resolution-time report and verify the durations are correct"],
              "Resolution time is computed from the correct timestamps",
              "Should",
              "MTTR " + ("available in the historical data"
                         if integ["mttr_available"] else
                         "was NOT computable in the historical data; make sure the new "
                         "tool captures created and resolved timestamps")),
    ]


def _migration_cases(counter: _Counter, integ: dict) -> list[dict]:
    cases = [_case(
        counter, "Data migration",
        "Migrated record counts reconcile",
        "Technical Resource",
        [f"Export the source data (baseline: {integ['total_records']} records)",
         "Import into the new tool",
         "Verify counts match by status and by category; investigate any delta"],
        "Source and target record counts reconcile exactly",
        "Must",
        "migration from the current email/excel workflow")]
    if integ["duplicate_records"] > 0:
        cases.append(_case(
            counter, "Data migration",
            "Duplicates handled before import",
            "Technical Resource",
            [f"Resolve the {integ['duplicate_records']} duplicate records found "
             f"(by {integ['duplicate_basis']}) in the source data",
             "Verify the import contains no duplicates"],
            "No duplicate records in the new tool",
            "Must",
            f"{integ['duplicate_records']} duplicates found in the source data"))
    if integ["fields_missing"]:
        cases.append(_case(
            counter, "Data migration",
            "Missing fields are captured going forward",
            "Project Manager",
            ["Verify the new tool makes these fields mandatory or defaulted at creation: "
             + ", ".join(integ["fields_missing"][:6]),
             "Raise a test ticket and confirm the fields are populated"],
            "Fields absent in the historical data are captured by the new tool",
            "Should",
            "fields missing in the source data: " + ", ".join(integ["fields_missing"][:6])))
    return cases


def _role_matrix(groups: list[str]) -> list[dict]:
    rows = [
        {"role": "Requester / End User", "derived_from": "baseline role",
         "can": ["Raise requests", "View and comment on own tickets",
                 "Approve items routed to them"],
         "cannot": ["View others' tickets", "Change configuration", "Access queues"]},
        {"role": "Service Desk Agent", "derived_from": "baseline role",
         "can": ["Work assigned queue", "Assign and reassign within group",
                 "Resolve and close", "Add worklog and resolution notes"],
         "cannot": ["Change workflow or SLA configuration", "Manage users"]},
    ]
    for g in groups:
        rows.append({
            "role": f"Agent: {g}", "derived_from": f"assignment group '{g}' in the data",
            "can": [f"Work the '{g}' queue", "Pick up, reassign, resolve within the group"],
            "cannot": ["Edit other groups' tickets (unless designed otherwise)",
                       "Change configuration"]})
    rows += [
        {"role": "Service Desk Manager", "derived_from": "baseline role",
         "can": ["View all queues and reports", "Reassign across groups",
                 "Approve escalations"],
         "cannot": ["Change system configuration (admin only)"]},
        {"role": "Administrator", "derived_from": "baseline role",
         "can": ["Configure workflows, SLAs, notifications, users, roles"],
         "cannot": ["Approve business requests (segregation of duties)"]},
    ]
    return rows


def _raci() -> list[dict]:
    pm, dl, tr, vendor, users = ("Project Manager", "Delivery Lead",
                                 "Technical Resources", "Vendor / Implementer",
                                 "Business Users")
    return [
        {"activity": "Map current workflows into test scenarios",
         "responsible": pm, "accountable": dl, "consulted": users, "informed": vendor},
        {"activity": "Configure the tool (queues, roles, SLAs, notifications)",
         "responsible": vendor, "accountable": pm, "consulted": tr, "informed": dl},
        {"activity": "Prepare test accounts and disable/redirect outbound email",
         "responsible": tr, "accountable": pm, "consulted": vendor, "informed": users},
        {"activity": "Execute UAT test cases and log defects",
         "responsible": tr, "accountable": pm, "consulted": users, "informed": dl},
        {"activity": "Fix defects and re-test",
         "responsible": vendor, "accountable": pm, "consulted": tr, "informed": dl},
        {"activity": "Data migration dry run and reconciliation",
         "responsible": tr, "accountable": dl, "consulted": vendor, "informed": pm},
        {"activity": "Go/no-go decision",
         "responsible": pm, "accountable": dl, "consulted": vendor, "informed": users},
        {"activity": "End-user training and comms",
         "responsible": pm, "accountable": dl, "consulted": users, "informed": vendor},
        {"activity": "Hypercare and post-go-live support",
         "responsible": vendor, "accountable": pm, "consulted": tr, "informed": users},
    ]


def _readiness(integ: dict, theme_summaries: list[dict], types: list[str]) -> list[dict]:
    items = [
        {"item": "Outbound email/notifications disabled or redirected to internal "
                 "test recipients for the whole test window",
         "category": "Safety", "gate": "Must",
         "source": "no test environment: prevent accidental customer emails"},
        {"item": "Dedicated test accounts exist for every role in the role matrix",
         "category": "Safety", "gate": "Must", "source": "role matrix"},
        {"item": "All Must test cases passed and signed off by a named owner",
         "category": "Quality", "gate": "Must", "source": "UAT test plan"},
        {"item": "Rollback plan agreed (keep the old email/excel channel warm for "
                 "the first two weeks)",
         "category": "Safety", "gate": "Must", "source": "standard go-live control"},
        {"item": "Support model for launch week defined (who triages, who escalates)",
         "category": "Operations", "gate": "Must", "source": "standard go-live control"},
        {"item": "End users trained on raising and tracking requests",
         "category": "Adoption", "gate": "Should", "source": "standard go-live control"},
    ]
    top = [t for t in theme_summaries if t["theme"] != OTHER][:5]
    if top:
        items.append({
            "item": "Category scheme in the new tool covers the top observed themes: "
                    + ", ".join(t["theme"] for t in top),
            "category": "Configuration", "gate": "Must",
            "source": "theme breakdown of the historical data"})
    other = next((t for t in theme_summaries if t["theme"] == OTHER), None)
    if other and other["pct"] >= 15:
        items.append({
            "item": f"Plan to reduce unclassified tickets ({other['pct']}% were "
                    f"unclassifiable in the historical data): mandatory category at creation",
            "category": "Configuration", "gate": "Should",
            "source": f"{other['pct']}% of historical tickets unclassified"})
    if not integ["mttr_available"]:
        items.append({
            "item": "New tool captures created and resolved timestamps so resolution "
                    "time is measurable from day one",
            "category": "Configuration", "gate": "Must",
            "source": "MTTR was not computable in the historical data"})
    if integ["duplicate_records"] > 0:
        items.append({
            "item": f"Source duplicates resolved before migration "
                    f"({integ['duplicate_records']} found)",
            "category": "Data", "gate": "Must",
            "source": "duplicate check on the source data"})
    if types:
        items.append({
            "item": "Request types configured to match observed intake: " + ", ".join(types),
            "category": "Configuration", "gate": "Should",
            "source": "type field in the historical data"})
    items.append({
        "item": "Baseline metrics from this analysis saved to compare after go-live "
                "(volume, MTTR, theme mix)",
        "category": "Measurement", "gate": "Should",
        "source": "this analysis"})
    return items


def _phase_plan(themes: list[dict], groups: list[str]) -> list[dict]:
    theme_names = ", ".join(t["theme"] for t in themes[:4]) or "top request areas"
    return [
        {"days": "1-3", "phase": "Setup and smoke test",
         "activities": [
             "Confirm configuration: queues, categories, roles, SLAs",
             "Create test accounts per role; disable or redirect outbound email",
             "Smoke test: one ticket end to end per request type"],
         "exit_criteria": "One ticket completes the full lifecycle with no blocker"},
        {"days": "4-8", "phase": "Core workflow testing",
         "activities": [
             f"Run lifecycle cases for the top themes ({theme_names})",
             "Run priority/SLA and escalation cases",
             "Log every defect with steps to reproduce; retest fixes daily"],
         "exit_criteria": "All Must lifecycle and SLA cases pass"},
        {"days": "9-11", "phase": "Roles, notifications, approvals",
         "activities": [
             f"Verify queue visibility for each group ({', '.join(groups) or 'agent groups'})",
             "Run all notification cases; audit that nothing leaked externally",
             "Run approval flow and bypass-prevention cases"],
         "exit_criteria": "Role matrix verified; zero external notification leaks"},
        {"days": "12-13", "phase": "Migration dry run and regression",
         "activities": [
             "Dry-run data migration; reconcile counts against the baseline",
             "Regression pass on all previously failed cases",
             "Freeze configuration"],
         "exit_criteria": "Migration reconciles; no open Must defects"},
        {"days": "14", "phase": "Go/no-go",
         "activities": [
             "Walk the readiness checklist with the delivery lead",
             "Named sign-off on every Must item",
             "Decide go/no-go; if no-go, agree the gap plan"],
         "exit_criteria": "Documented go decision with sign-offs"},
        {"days": "15", "phase": "Go-live preparation",
         "activities": [
             "Re-enable outbound notifications for production recipients",
             "Final comms to end users; hypercare rota confirmed",
             "Keep the old intake channel open as fallback"],
         "exit_criteria": "Tool live; fallback and support rota in place"},
    ]


def _detected(classified: pd.DataFrame, column: str, n: int) -> list[str]:
    s = classified[column].dropna()
    if not len(s):
        return []
    return [str(v) for v in s.value_counts().head(n).index]
