"""Regression: polluted real-world export.

Replicates the garbage observed in real data:
- 'Application' column actually holds approval statuses (Not Requested/Approved)
- Category column holds junk: numeric IDs, city names, one giant sendgrid URL
- Description holds pasted email threads with tracking URLs, [image] markers,
  base64 blobs, and CRM timeout error logs
Verifies none of it surfaces in the report.
"""

import csv

SENDGRID = ("https://u56251250.ct.sendgrid.net/ls/click?upn=u001.Hk1qt-2B0Fz00lAWWIk9N4pw"
            "XqqD9yfGjbYXlJrMQM8LwEzRvANo01DY8CPl9MvX79" + "A" * 400 + "-3D-3D")
CRM_LOG = ("CRM service call returned an error: The request channel timed out while "
           "waiting for a reply after 00:03:59.9375047. Increase the timeout value passed "
           "to the call to Request or increase the SendTimeout value on the Binding. "
           "(Error Type / Reason: Timeout) 2025-11-10 17:26:17 Contacts "
           "{83006D7F-4CBB-F011-A9EB-000D3AD09F7D} ") * 5
EMAIL_DUMP = (f"Hi team, see below <{SENDGRID}> [image]<{SENDGRID}> follow us "
              f"[HobbyKing Facebook]<{SENDGRID}> * Price indicated may vary based on your location")

rows = []
for i in range(1, 41):
    if i <= 30:
        app_status = "Not Requested"
    elif i <= 38:
        app_status = "Approved"
    else:
        app_status = "Cancelled"
    if i % 7 == 0:
        cat = "Kowloon"
    elif i % 5 == 0:
        cat = str(240470 + i)
    elif i == 3:
        cat = SENDGRID
    elif i == 9:
        cat = "Datawarehouse"
    else:
        cat = ""
    if i % 3 == 0:
        desc = EMAIL_DUMP
    elif i % 4 == 0:
        desc = CRM_LOG
    else:
        desc = "please look into this issue"
    rows.append({
        "RequestID": f"REQ-{1000+i}",
        "Subject": ["Laptop replacement request", "Need GitHub Copilot access",
                    "Outlook not syncing emails", "VPN keeps disconnecting",
                    "Password reset needed"][i % 5],
        "Description": desc,
        "Category": cat,
        "Application": app_status,
        "Created Time": f"2025-11-{(i % 28) + 1:02d} 10:00:00",
        "Request Status": ["Closed", "On Hold", "Closed", "Open"][i % 4],
        "Technician": "Tech A",
    })

with open("polluted_tickets.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"Wrote {len(rows)} polluted rows")
