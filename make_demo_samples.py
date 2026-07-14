"""Generate five anonymized demo exports modeling real enterprise shapes.

All data is synthetic. No customer names, no person names (Employee NNNN /
Agent NN only), no customer-identifiable application names. Patterns are
modeled on real service desk exports: column layouts from ServiceNow,
ManageEngine SDP, HR dumps, and Jira; subject phrasing, volume mixes, email
noise, and data-quality defects as found in the wild.

Run: python make_demo_samples.py
Produces, in this directory:
  1. demo1_pharma_fieldforce.csv   ServiceNow-style, field-force heavy
  2. demo2_it_helpdesk.csv         ManageEngine SDP-style, general IT
  3. demo3_hr_servicedesk.csv      HR service desk dump
  4. demo4_devops_jira.csv         Jira Service Management export
  5. demo5_messy_export.csv        Degraded export (shows honesty guards)
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(7)

DEPTS = ["Field Sales", "Manufacturing", "Quality", "Finance", "HR",
         "Supply Chain", "R&D", "IT", "Regulatory Affairs", "Marketing"]
LOCS = ["Plant A", "Plant B", "HQ", "Region North", "Region South", "Region West"]

EMAIL_NOISE = (
    " [External] EXTERNAL SENDER: do not click links unless you recognize the "
    "sender. Regards, Employee {emp} Emp Code {emp} Mobile 98xxxxxx{d2} HQ {loc}. "
    "Get Outlook for iOS. Disclaimer: This email and any files transmitted with "
    "it are confidential and intended solely for the use of the individual.")


def emp():
    return f"Employee {random.randint(1000, 9999)}"


def noise(text):
    e = random.randint(1000, 9999)
    return text + EMAIL_NOISE.format(emp=e, d2=random.randint(10, 99),
                                     loc=random.choice(LOCS))


def dt(base, days_range):
    return base + timedelta(hours=random.uniform(0, 24 * days_range))


def fmt(d):
    return d.strftime("%d-%m-%Y %I:%M:%S %p")


# ---------------------------------------------------------------- demo 1
# Pharma field force, ServiceNow-style. Modeled mix: attendance ~40%,
# devices ~10%, password/SSO, CLM sync, SAP, and a large Other mass.
def demo1():
    base = datetime(2025, 3, 1)
    templates = [
        # (weight, subject, category, subcategory, group, lo_h, hi_h)
        (28, "Kindly unlock my attendance in FieldHub", "Application & Software", "FieldHub - Attendance & Leave", "Field Support L1", 4, 72),
        (8, "FieldHub attendance reset request {day} March", "Application & Software", "FieldHub - Attendance & Leave", "Field Support L1", 4, 72),
        (6, "Forgot to submit my call, please backdate", "Application & Software", "SalesTrack CRM", "Field Support L1", 8, 96),
        (5, "Leave balance not reflecting in FieldHub", "Application & Software", "FieldHub - Reporting & Account", "Field Support L1", 8, 60),
        (7, "DetailPro slides not syncing on iPad", "Application & Software", "DetailPro CLM", "Field Support L2", 12, 120),
        (4, "Requesting for iPad slide is not working", "Hardware & Devices", "iPad", "Field Support L2", 12, 120),
        (5, "iPad enrollment for new joiner", "Hardware & Devices", "iPad", "Endpoint Team", 24, 168),
        (3, "Remove remote management from my old iPad", "Hardware & Devices", "iPad", "Endpoint Team", 24, 120),
        (3, "Laptop running very slow after update", "Hardware & Devices", "Laptop", "IT Service Desk", 24, 168),
        (6, "URGENT: password reset request and login issue", "Access & Authentication", "Login Issues", "IT Service Desk", 1, 8),
        (4, "Account locked out, unable to sign in to SSO", "Access & Authentication", "Login Issues", "IT Service Desk", 1, 8),
        (3, "Access rights request for SalesTrack dashboards", "Access & Authentication", "Access Rights", "IAM Team", 24, 96),
        (4, "Company portal not working on managed device", "Hardware & Devices", "Mobile", "Endpoint Team", 12, 96),
        (4, "SAP attendance period locked, cannot submit timesheet", "Application & Software", "SAP", "SAP Basis", 24, 120),
        (2, "SAP login error after password change", "Application & Software", "SAP", "SAP Basis", 8, 72),
        (3, "Unable to use my Outlook on laptop", "Communication Tools", "Email/Outlook", "IT Service Desk", 4, 48),
        (2, "Payslip not visible for last month", "HR & Payroll", "Payslip", "HR Helpdesk", 12, 96),
        (2, "VPN keeps disconnecting at plant network", "Network & Connectivity", "VPN", "Network Team", 8, 96),
        # the Other mass: vague subjects, as in real dumps
        (10, "New Ticket", "", "", "IT Service Desk", 8, 200),
        (5, "sales assist not working", "", "", "Field Support L1", 8, 160),
        (4, "showing error, please help", "", "", "IT Service Desk", 8, 160),
        (4, "unable to access, request to resolve", "", "", "IT Service Desk", 8, 160),
    ]
    rows = []
    n = 0
    for w, subj, cat, subcat, grp, lo, hi in templates:
        for _ in range(w * 6):
            n += 1
            created = dt(base, 120)
            status = random.choices(
                ["Closed", "Resolved", "On Hold", "Open", "Transfer to GXP Support"],
                weights=[62, 15, 12, 8, 3])[0]
            resolved = (created + timedelta(hours=random.uniform(lo, hi))
                        if status in ("Closed", "Resolved") else None)
            rows.append({
                "ID": f"FLD{190000 + n}",
                "Priority": random.choices(["low", "medium", "high", "urgent"],
                                           weights=[20, 60, 15, 5])[0],
                "Source": random.choices(["email", "portal", "chat"], weights=[55, 35, 10])[0],
                "Requester Name": emp(),
                "Subject": subj.format(day=random.randint(1, 28)),
                "Description": noise(subj.format(day=random.randint(1, 28))
                                     + ". Please resolve on priority."),
                "Status": status,
                "Agent Group Name": grp,
                "Agent Name": f"Agent {random.randint(1, 40):02d}",
                "Created Date": fmt(created),
                "Resolved Date": fmt(resolved) if resolved else "",
                "Requester Location": random.choice(LOCS),
                "Department Name": random.choice(["Field Sales"] * 6 + DEPTS),
                "Service Category": cat,
                "Sub Category": subcat,
                "SLA Met": random.choices(["Yes", "No"], weights=[85, 15])[0],
            })
    random.shuffle(rows)
    return "demo1_pharma_fieldforce.csv", rows


# ---------------------------------------------------------------- demo 2
# General IT helpdesk, ManageEngine SDP-style columns.
def demo2():
    base = datetime(2025, 6, 1)
    templates = [
        (10, "Password reset for domain account", "Identity & Access", 0.5, 4),
        (7, "New starter account creation", "User Lifecycle", 8, 72),
        (6, "Leaver access revocation", "User Lifecycle", 8, 48),
        (8, "Software install request", "Software", 4, 48),
        (5, "License required for design tool", "Software", 8, 72),
        (7, "Printer not printing on level 2", "Hardware", 4, 48),
        (6, "Laptop replacement request", "Hardware", 48, 240),
        (5, "Monitor flickering", "Hardware", 8, 72),
        (6, "Wi-Fi drops in meeting rooms", "Network", 8, 120),
        (5, "VPN setup for remote work", "Network", 4, 48),
        (7, "Shared mailbox access request", "Email & Collaboration", 4, 48),
        (5, "Distribution list update", "Email & Collaboration", 4, 48),
        (6, "How do I set up MFA on new phone", "How-to", 0.5, 8),
        (4, "Weekly sales report not generated", "Reporting", 8, 96),
        (3, "Approval stuck for laptop request", "Workflow", 24, 240),
    ]
    rows = []
    n = 0
    for w, subj, cat, lo, hi in templates:
        for _ in range(w * 4):
            n += 1
            created = dt(base, 90)
            status = random.choices(["Closed", "Resolved", "On Hold", "Open"],
                                    weights=[65, 15, 10, 10])[0]
            resolved = (created + timedelta(hours=random.uniform(lo, hi))
                        if status in ("Closed", "Resolved") else None)
            rows.append({
                "RequestID": str(70000 + n),
                "Subject": subj,
                "Description": subj + ". Raised via self-service portal.",
                "Category": cat,
                "Department": random.choice(DEPTS),
                "Requester": emp(),
                "Technician": f"Tech {random.randint(1, 12):02d}",
                "Request Mode": random.choice(["Web Form", "E-Mail", "Phone Call"]),
                "Created Time": created.strftime("%Y-%m-%d %H:%M:%S"),
                "Resolved Time": resolved.strftime("%Y-%m-%d %H:%M:%S") if resolved else "",
                "Request Status": status,
                "Priority": random.choice(["Low", "Medium", "High"]),
            })
    random.shuffle(rows)
    return "demo2_it_helpdesk.csv", rows


# ---------------------------------------------------------------- demo 3
# HR service desk dump.
def demo3():
    base = datetime(2025, 7, 1)
    templates = [
        (9, "Payslip not available for June", "Payroll & Compensation", 8, 72),
        (6, "Salary component query", "Payroll & Compensation", 8, 96),
        (8, "Leave balance incorrect after regularization", "Attendance & Leave", 8, 72),
        (7, "Attendance regularization pending manager approval", "Attendance & Leave", 24, 168),
        (5, "PF transfer status", "PF/Investment/Tax", 48, 336),
        (4, "Tax declaration window reopen request", "PF/Investment/Tax", 24, 120),
        (6, "Medical insurance card not received", "Benefits & Medical Insurance", 48, 240),
        (4, "Add dependent to insurance policy", "Benefits & Medical Insurance", 24, 168),
        (5, "Employment letter for visa application", "Letters & Certificates", 24, 96),
        (4, "Experience certificate request", "Letters & Certificates", 24, 120),
        (5, "Bank account update for salary credit", "Employee Data Updates", 8, 72),
        (4, "Name correction in HR system", "Employee Data Updates", 24, 168),
        (5, "Onboarding documents upload failing", "Onboarding & Offboarding", 8, 48),
        (3, "ID card reissue", "ID Cards & Access", 24, 120),
        (4, "HR app login not working", "HR App/Tech Support", 4, 48),
        (4, "Reimbursement claim rejected without reason", "Reimbursements & Expenses", 24, 168),
    ]
    rows = []
    n = 0
    for w, subj, cat, lo, hi in templates:
        for _ in range(w * 4):
            n += 1
            created = dt(base, 90)
            status = random.choices(["Closed", "Resolved", "On Hold", "Open"],
                                    weights=[60, 18, 14, 8])[0]
            resolved = (created + timedelta(hours=random.uniform(lo, hi))
                        if status in ("Closed", "Resolved") else None)
            rows.append({
                "Ticket Id": f"HR-{40000 + n}",
                "Subject": subj,
                "Description": subj + ". Employee raised via HR portal.",
                "Category": cat,
                "Sub Category": "",
                "Status": status,
                "Priority": random.choice(["P3 - Medium", "P2 - High", "P4 - Low"]),
                "Created Time": created.strftime("%d/%m/%Y %H:%M"),
                "Resolved Time": resolved.strftime("%d/%m/%Y %H:%M") if resolved else "",
                "Group": random.choice(["HR Helpdesk", "Payroll Team", "Benefits Team"]),
                "Requester Name": emp(),
                "Department": random.choice(DEPTS),
                "Location": random.choice(LOCS),
            })
    random.shuffle(rows)
    return "demo3_hr_servicedesk.csv", rows


# ---------------------------------------------------------------- demo 4
# DevOps queue, Jira Service Management export.
def demo4():
    base = datetime(2025, 1, 15)
    templates = [
        (6, "CI pipeline failing on main branch", "Bug", 4, 72),
        (5, "Deployment to staging stuck at approval", "Task", 8, 120),
        (5, "Access request: production logs read-only", "Access", 8, 72),
        (4, "New service onboarding to monitoring", "Task", 24, 240),
        (4, "Kibana dashboard not loading", "Bug", 4, 48),
        (4, "Increase disk on build agents", "Infrastructure", 8, 96),
        (3, "Rotate API keys for payment gateway", "Security", 8, 72),
        (3, "VPN access for new contractor", "Access", 8, 48),
        (3, "Terraform plan drift on network module", "Infrastructure", 24, 168),
        (3, "How to request a new namespace", "Question", 1, 24),
        (2, "Secrets manager permission denied", "Access", 4, 48),
        (2, "Alert fatigue: tune noisy monitor", "Task", 24, 240),
    ]
    rows = []
    n = 0
    for w, subj, itype, lo, hi in templates:
        for _ in range(w * 3):
            n += 1
            created = dt(base, 180)
            status = random.choices(["Done", "In Progress", "To Do", "Blocked"],
                                    weights=[64, 16, 12, 8])[0]
            resolved = (created + timedelta(hours=random.uniform(lo, hi))
                        if status == "Done" else None)
            rows.append({
                "Issue Key": f"DVO-{1000 + n}",
                "Project": "DevOps",
                "Issue Type": itype,
                "Summary": subj,
                "Description": subj + ". See runbook for context.",
                "Status": status,
                "Priority": random.choice(["Low", "Medium", "High", "Highest"]),
                "Assignee": f"Agent {random.randint(1, 8):02d}",
                "Reporter": emp(),
                "Created": created.strftime("%Y-%m-%dT%H:%M:%S"),
                "Resolved": resolved.strftime("%Y-%m-%dT%H:%M:%S") if resolved else "",
                "Resolution": "Done" if resolved else "",
            })
    random.shuffle(rows)
    return "demo4_devops_jira.csv", rows


# ---------------------------------------------------------------- demo 5
# Degraded export: 6-day window, no resolution timestamps, a "Resolved By"
# person column, an "Application" column full of approval statuses, and
# email-dump descriptions. Demonstrates the honesty guards end to end.
def demo5():
    base = datetime(2025, 9, 1)
    subjects = [
        "Laptop replacement", "Need code assistant access", "Access removal request",
        "Email id creation for new joinees", "Weekly compliance report India",
        "New Ticket", "VPN not connecting", "Printer offline level 3",
        "Add user to distribution list", "System slow after patch",
        "Requesting software install", "Password reset needed",
    ]
    long_dump = ("FYI, see thread below. <https://tracking.example-mailer.invalid/ls/click?upn="
                 + "A" * 220 + "> [image] follow us on social. "
                 "Service call returned an error: request channel timed out while waiting "
                 "for a reply after 00:03:59. Increase the SendTimeout value on the binding. "
                 "2025-09-03 11:26:17 Contacts {A5006D7F-4CBB-F011-A9EB-000D3AD09F7D}")
    rows = []
    for i in range(1, 121):
        created = base + timedelta(hours=random.uniform(0, 24 * 6))
        rows.append({
            "RequestID": f"REQ-{5000 + i}",
            "Subject": random.choice(subjects),
            "Description": (long_dump if i % 3 == 0 else "please look into this"),
            "Application": random.choices(["Not Requested", "Approved", "Cancelled"],
                                          weights=[75, 20, 5])[0],
            "Requester": emp(),
            "Department": random.choice(DEPTS),
            "Created Time": created.strftime("%Y-%m-%d %H:%M:%S"),
            "Request Status": random.choices(
                ["Closed", "On Hold", "Open", "Transfer to Infra"],
                weights=[55, 25, 15, 5])[0],
            "Technician": f"Tech {random.randint(1, 6):02d}",
            "Resolved By": f"Agent {random.randint(1, 6):02d}",
        })
    return "demo5_messy_export.csv", rows


if __name__ == "__main__":
    for build in (demo1, demo2, demo3, demo4, demo5):
        name, rows = build()
        with open(name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"{name}: {len(rows)} rows")
