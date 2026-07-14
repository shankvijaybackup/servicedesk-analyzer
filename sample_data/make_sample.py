"""Generate a realistic ServiceNow-style sample CSV for testing."""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

TEMPLATES = [
    # (weight, summary, category, subcategory, app, group, mttr_lo, mttr_hi)
    (14, "Password reset required for {app}", "Access", "Password", "Okta", "IT Service Desk", 0.2, 2),
    (8, "Account locked out - unable to login to {app}", "Access", "Account Lock", "Microsoft Entra ID", "IT Service Desk", 0.3, 3),
    (6, "Access request for {app} for new joiner", "Access", "Provisioning", "Salesforce", "IAM Team", 4, 48),
    (7, "How do I apply for leave in Workday", "HR", "Query", "Workday", "HR Helpdesk", 1, 8),
    (5, "Payslip not visible for last month", "HR", "Payroll", "Workday", "HR Helpdesk", 4, 24),
    (6, "SAP attendance period locked - unable to submit timesheet", "ERP", "Attendance", "SAP", "SAP Basis", 8, 72),
    (4, "SAP GUI error when posting invoice", "ERP", "Error", "SAP", "SAP Basis", 12, 96),
    (7, "Salesforce opportunity not syncing to dashboard", "Application", "Sync", "Salesforce", "CRM Support", 8, 60),
    (5, "iPad slide content not updated in field sales app", "Hardware", "Tablet", "Salesforce Field App", "CRM Support", 12, 80),
    (8, "Outlook not receiving emails", "Email", "Outlook", "Microsoft 365", "IT Service Desk", 1, 12),
    (5, "Need to be added to distribution list", "Email", "DL", "Exchange", "IT Service Desk", 2, 24),
    (6, "Teams call audio not working during meetings", "Collaboration", "Teams", "Microsoft Teams", "IT Service Desk", 1, 10),
    (6, "VPN keeps disconnecting when working from home", "Network", "VPN", "GlobalProtect", "Network Team", 2, 36),
    (4, "WiFi not working on 3rd floor", "Network", "WiFi", "Corporate WiFi", "Network Team", 4, 48),
    (7, "Laptop running very slow, needs replacement", "Hardware", "Laptop", "Dell Latitude", "IT Service Desk", 24, 168),
    (4, "Keyboard keys not working", "Hardware", "Peripheral", "Dell Latitude", "IT Service Desk", 8, 72),
    (5, "Software install request - {sw}", "Software", "Install", "{sw}", "IT Service Desk", 2, 24),
    (4, "License required for {sw}", "Software", "License", "{sw}", "IT Service Desk", 4, 48),
    (5, "Device not compliant in Intune - cannot access email", "MDM", "Compliance", "Microsoft Intune", "Endpoint Team", 4, 36),
    (3, "iPhone enrollment failing in company portal", "MDM", "Enrollment", "Microsoft Intune", "Endpoint Team", 6, 48),
    (4, "Approval pending for laptop request over a week", "Workflow", "Approval", "ServiceNow", "IT Service Desk", 24, 240),
    (4, "Monthly sales report not generated", "Reporting", "Report", "Power BI", "Analytics Team", 8, 72),
    (3, "How to connect to office printer", "Knowledge", "How-to", "Print Server", "IT Service Desk", 0.5, 4),
    (3, "What is the policy for personal device usage", "Knowledge", "Policy", "", "IT Service Desk", 0.5, 6),
    (3, "Leave balance showing incorrectly", "HR", "Leave", "Workday", "HR Helpdesk", 4, 30),
    (2, "Misc issue reported by user", "Other", "", "", "IT Service Desk", 2, 48),
]

SW = ["Visio", "Adobe Acrobat", "Zoom", "Slack", "AutoCAD"]
PRIORITIES = [("3 - Medium", 55), ("2 - High", 25), ("4 - Low", 15), ("1 - Critical", 5)]
DEPTS = ["Sales", "Finance", "Engineering", "HR", "Operations", "Marketing"]
NAMES = ["A Kumar", "B Singh", "C Sharma", "D Patel", "E Reddy", "F Nair", "G Rao", "H Iyer"]


def pick_priority():
    r = random.uniform(0, 100)
    cum = 0
    for p, w in PRIORITIES:
        cum += w
        if r <= cum:
            return p
    return "3 - Medium"


rows = []
start = datetime(2026, 1, 5)
n = 0
for weight, summary, cat, subcat, app_, group, lo, hi in TEMPLATES:
    for _ in range(weight * 3):
        n += 1
        sw = random.choice(SW)
        created = start + timedelta(hours=random.uniform(0, 24 * 150))
        mttr = random.uniform(lo, hi)
        resolved = created + timedelta(hours=mttr)
        status = random.choices(["Closed", "Resolved", "In Progress", "Open"],
                                weights=[60, 20, 12, 8])[0]
        rows.append({
            "Number": f"INC{100000 + n}",
            "Short description": summary.format(app=app_ or "system", sw=sw),
            "Category": cat,
            "Subcategory": subcat,
            "Priority": pick_priority(),
            "State": status,
            "Opened": created.strftime("%Y-%m-%d %H:%M:%S"),
            "Resolved": resolved.strftime("%Y-%m-%d %H:%M:%S") if status in ("Closed", "Resolved") else "",
            "Assignment group": group,
            "Configuration item": (app_ or "").format(sw=sw),
            "Caller": random.choice(NAMES),
            "Department": random.choice(DEPTS),
        })

# A few duplicates and dirty rows to exercise quality checks
rows.append(dict(rows[10]))
rows.append(dict(rows[20]))
bad = dict(rows[5])
bad["Opened"] = "not-a-date"
rows.append(bad)

random.shuffle(rows)
with open("sample_tickets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"Wrote {len(rows)} rows to sample_tickets.csv")
