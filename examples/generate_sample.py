"""Generate a deterministic sample service desk export for demos and tests.

Produces ServiceNow-style columns. Fixed seed, so output is reproducible.
Run:  python examples/generate_sample.py
"""

from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

# (short description template, category, subcategory, application, type, base MTTR hours)
TEMPLATES = [
    ("Password reset for {app}", "Access", "Password", "Active Directory", "Incident", 1.5),
    ("Cannot log in to {app}, account locked", "Access", "Account Lockout", "Okta", "Incident", 2.0),
    ("Need access to {app} shared drive", "Access", "Access Request", "Microsoft Entra ID", "Request", 20),
    ("MFA not working on {app}", "Access", "MFA", "Okta", "Incident", 3),
    ("How do I install {app}", "Software", "How-to", "Company Portal", "Request", 4),
    ("{app} keeps crashing on launch", "Software", "Application Error", "SAP GUI", "Incident", 12),
    ("Request license for {app}", "Software", "License", "Adobe Creative Cloud", "Request", 26),
    ("Payslip missing in {app}", "HR", "Payroll", "Workday", "Incident", 18),
    ("Leave balance incorrect in {app}", "HR", "Attendance", "SAP SuccessFactors", "Incident", 22),
    ("Attendance not captured, need unlock in {app}", "HR", "Attendance", "SAP", "Request", 30),
    ("Laptop screen flickering", "Hardware", "Laptop", "Dell Latitude", "Incident", 40),
    ("Need a new monitor", "Hardware", "Peripheral", "Monitor", "Request", 48),
    ("WiFi keeps dropping in office", "Network", "Connectivity", "Meraki WiFi", "Incident", 8),
    ("VPN not connecting", "Network", "VPN", "GlobalProtect", "Incident", 5),
    ("Outlook not receiving email", "Email", "Mailbox", "Outlook", "Incident", 6),
    ("Add me to the {app} distribution list", "Email", "Distribution List", "Exchange", "Request", 10),
    ("Salesforce report not syncing data", "CRM", "Sync", "Salesforce", "Incident", 28),
    ("Update opportunity stage in {app}", "CRM", "Data", "Salesforce", "Request", 9),
    ("Enroll my iPhone in {app}", "MDM", "Enrollment", "Intune", "Request", 7),
    ("Device shows non-compliant in {app}", "MDM", "Compliance", "Intune", "Incident", 11),
    ("Need the Q3 sales dashboard export", "Reporting", "Report", "Power BI", "Request", 14),
    ("Approve my software purchase in {app}", "Workflow", "Approval", "ServiceNow", "Request", 16),
    ("iPad slide deck not displaying in field app", "Software", "Content", "Field Sales App", "Incident", 15),
]
APPS = ["the portal", "the CRM", "the finance app", "email", "the HR system", "the VPN"]
GROUPS = ["Service Desk L1", "Identity Team", "Endpoint Team", "HR Ops", "Network Team",
          "ERP Support", "CRM Support"]
PRIORITIES = ["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"]
STATUSES = ["Closed", "Closed", "Closed", "Resolved", "In Progress", "Open"]


def generate(n: int = 600) -> list[dict]:
    rows = []
    start = datetime(2026, 1, 1, 9, 0, 0)
    for i in range(n):
        tmpl = random.choice(TEMPLATES)
        desc, cat, sub, app, ttype, base = tmpl
        created = start + timedelta(hours=random.randint(0, 24 * 175),
                                    minutes=random.randint(0, 59))
        status = random.choice(STATUSES)
        mttr = max(0.2, random.gauss(base, base * 0.4))
        resolved = created + timedelta(hours=mttr) if status in ("Closed", "Resolved") else ""
        rows.append({
            "Number": f"INC{100000 + i}",
            "Opened": created.strftime("%Y-%m-%d %H:%M:%S"),
            "Resolved": resolved.strftime("%Y-%m-%d %H:%M:%S") if resolved else "",
            "State": status,
            "Priority": random.choice(PRIORITIES),
            "Type": ttype,
            "Category": cat,
            "Subcategory": sub,
            "Assignment group": random.choice(GROUPS),
            "Configuration item": app,
            "Short description": desc.format(app=random.choice(APPS)),
            "Department": random.choice(["Sales", "Finance", "Engineering", "HR", "Operations"]),
            "Requested by": f"user{random.randint(1, 220)}",
        })
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    rows = generate(600)
    write_csv(rows, here / "sample_servicedesk.csv")
    write_csv(rows[:24], here.parent / "tests" / "data" / "sample_tickets.csv")
    print(f"Wrote {len(rows)} rows to examples/sample_servicedesk.csv and 24 to tests/data/.")
