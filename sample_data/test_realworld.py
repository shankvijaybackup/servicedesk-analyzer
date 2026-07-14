"""Regression test replicating the real-world failure patterns:
- 'Resolved By' column (person names) must NOT map to resolved_date
- CASB/GTB/SentinelOne tickets -> Security & Compliance, not Attendance/SAP
- 'HDMI not working' / 'headphone not charging' -> Hardware, not Knowledge
- 'GitHub Copilot access' / 'add user' -> Access & Authentication with confidence
- Status friction (On Hold, Transfer to...) must appear in the report
- Short period (5 days) must produce a loud warning
- No opportunities from <5 ticket themes
"""

import csv
import sys

sys.path.insert(0, "..")

ROWS = [
    ("REQ-1", "Laptop replacement", "User laptop is 4 years old, please help", "Closed", "Alice T"),
    ("REQ-2", "Laptop preparation", "Prepare laptop for new joinee", "On Hold", "Bob R"),
    ("REQ-3", "Dell Tech Direct request", "Raise warranty request with Dell", "Closed", "Alice T"),
    ("REQ-4", "Laptops HDMI not working", "How do I connect? The HDMI port seems dead", "Closed", "Bob R"),
    ("REQ-5", "Headphone not charging", "Please guide me, my headphone won't charge", "On Hold", "Alice T"),
    ("REQ-6", "GitHub Copilot access", "I need copilot access for my project please", "Closed", "Carol M"),
    ("REQ-7", "Need Copilot access", "requesting access to github copilot", "Closed", "Carol M"),
    ("REQ-8", "Access removal 1 September 2025", "remove access for departed user", "Closed", "Carol M"),
    ("REQ-9", "Requesting to add the user in to the DL", "please add user to distribution list", "On Hold", "Dan K"),
    ("REQ-10", "CASB compliance 25August to 31August2025 India", "weekly CASB compliance report India location", "Closed", "Eve S"),
    ("REQ-11", "GTB compliance 25August2025 to 31August2025 India location", "weekly GTB compliance", "Closed", "Eve S"),
    ("REQ-12", "CASB compliance 25August to 31August2025 US EMEA", "weekly report", "Closed", "Eve S"),
    ("REQ-13", "High SentinelOne upgradation of SAP GUI for Windows", "upgrade SentinelOne agent on SAP GUI machines", "Closed", "Eve S"),
    ("REQ-14", "Email id and system setup for new joinees", "create email and setup system", "Transfer to Cloud Infra", "Dan K"),
    ("REQ-15", "Emails are not loading into High Radius email", "user reports emails not loading", "On Hold", "Dan K"),
    ("REQ-16", "Memcache low storage", "memcache server low on storage", "Transfer to Cloud Infra", "Frank P"),
    ("REQ-17", "AD DNS creation", "create DNS entry in AD", "Closed", "Frank P"),
    ("REQ-18", "Install Tailscale VPN", "need tailscale vpn installed", "Closed", "Frank P"),
    ("REQ-19", "Requirement of MS Excel", "please install microsoft excel", "Closed", "Bob R"),
    ("REQ-20", "Export VDI usage report 20MayTo18Aug", "need VDI usage report exported", "On Hold", "Frank P"),
]

with open("realworld_tickets.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["RequestID", "Requester", "Requester Email", "Department",
                "Created Time", "Request Status", "Technician", "Subject",
                "Description", "Has Attachments", "Resolved By"])
    for i, (rid, subj, desc, status, resolver) in enumerate(ROWS):
        w.writerow([rid, f"User {i}", f"user{i}@corp.com", "G&A IT",
                    f"2025-09-0{(i % 5) + 1} 10:{i:02d}:00", status,
                    "Tech A", subj, desc, "No", resolver])

print(f"Wrote {len(ROWS)} rows to realworld_tickets.csv")
