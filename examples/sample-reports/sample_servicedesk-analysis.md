# Service Desk Analysis: examples/sample_servicedesk.csv

_Generated 2026-07-14T17:02:18 by servicedesk-analyzer v0.1.0. Deterministic, offline, no model used._

## A. Executive Summary

- 600 tickets analyzed over 2026-01-01 to 2026-06-24 (174 days).
- Data quality: Strong (100/100).
- Largest theme: Access & Authentication at 23.2% of volume.
- Overall median MTTR: 11.4h.
- Estimated deflectable volume: 28.3% to 50.7% (planning estimate).

**Top findings**

- (High) 7 themes drive ~80% of ticket volume (led by Access & Authentication at 23.2%).
- (Medium) Slowest theme by MTTR: Hardware & Devices at 42.2h median.
- (High) Highest deflection upside: Access & Authentication (56-97 tickets, Workflow Automation).

## B. Data Quality Assessment

- Records: 600
- Quality: Strong (100/100)
- Fields detected: ticket_id, created, resolved, status, priority, type, category, subcategory, assignment_group, requester, department, short_description, description, application
- Fields missing: assignee, mttr_hours
- Duplicates: 0 (by ticket id (Number))
- Date range: 2026-01-01 to 2026-06-24 (174 days)
- MTTR: available (derived from created/resolved timestamps)

## C. Ticket Volume Analysis

- Total: 600
- Resolved/closed: 387; open backlog: 213
- By type: Incident 320 (53.3%), Request 280 (46.7%)
- By priority: 4 - Low 157 (26.2%), 3 - Moderate 156 (26.0%), 1 - Critical 148 (24.7%), 2 - High 139 (23.2%)
- By status: Resolved 387 (64.5%), Open 117 (19.5%), In Progress 96 (16.0%)

## D. MTTR Analysis

- Overall: median 11.4h, mean 15.8h, p90 35.0h (n=387)
- Slowest themes: Hardware & Devices 42.2h, Attendance & Leave 22.0h, HR & Payroll 20.9h, Data / Reporting 18.2h, Approval / Workflow 16.5h
- Fastest themes: Access & Authentication 3.3h, Email & Collaboration 5.9h, Network & Connectivity 6.8h, Device Management / MDM 9.6h, Application & Software 13.1h

## E. Theme and Category Breakdown

| Theme | Count | % | MTTR med (h) | Confidence |
| --- | ---: | ---: | ---: | --- |
| Access & Authentication | 139 | 23.2 | 3.3 | High |
| Application & Software | 108 | 18.0 | 13.1 | High |
| Salesforce / CRM | 51 | 8.5 | 13.1 | High |
| Hardware & Devices | 50 | 8.3 | 42.2 | High |
| Device Management / MDM | 49 | 8.2 | 9.6 | High |
| Email & Collaboration | 48 | 8.0 | 5.9 | High |
| Network & Connectivity | 45 | 7.5 | 6.8 | High |
| Attendance & Leave | 33 | 5.5 | 22.0 | Medium |
| Approval / Workflow | 31 | 5.2 | 16.5 | Medium |
| Data / Reporting | 26 | 4.3 | 18.2 | Medium |
| HR & Payroll | 20 | 3.3 | 20.9 | Medium |

## F. Application Landscape

- Distinct applications: 20
  - Okta: 57 (9.5%)
  - Salesforce: 51 (8.5%)
  - Intune: 49 (8.2%)
  - Microsoft Entra ID: 36 (6.0%)
  - SAP SuccessFactors: 33 (5.5%)
  - ServiceNow: 31 (5.2%)
  - Company Portal: 30 (5.0%)
  - Outlook: 29 (4.8%)
  - Field Sales App: 28 (4.7%)
  - SAP: 27 (4.5%)

## G. Top Operational Friction Points

- Hardware & Devices: 50 tickets, median 42.2h, est effort 2108.1h (high total effort (volume x resolution time))
- Application & Software: 108 tickets, median 13.1h, est effort 1411.7h (high total effort (volume x resolution time))
- Attendance & Leave: 33 tickets, median 22.0h, est effort 725.8h (high total effort (volume x resolution time))
- Salesforce / CRM: 51 tickets, median 13.1h, est effort 666.4h (high total effort (volume x resolution time))
- Approval / Workflow: 31 tickets, median 16.5h, est effort 512.7h (high total effort (volume x resolution time))

## H. AI Automation Opportunity Backlog

| Theme | Type | Addressable | Est. deflectable | MTTR impact | Complexity | Risk | Confidence |
| --- | --- | ---: | --- | --- | --- | --- | --- |
| Access & Authentication | Workflow Automation | 139 | 56-97 (40-70%) | High | Medium | Medium | High |
| Application & Software | Knowledge AI | 108 | 27-49 (25-45%) | Medium | Medium | Low | High |
| Email & Collaboration | Knowledge AI | 48 | 14-26 (30-55%) | Medium | Medium | Low | High |
| Device Management / MDM | Integration Automation | 49 | 12-22 (25-45%) | Medium | Medium | Medium | Medium |
| Salesforce / CRM | Integration Automation | 51 | 10-20 (20-40%) | Medium | High | Medium | Medium |
| Attendance & Leave | Workflow Automation | 33 | 13-20 (40-60%) | High | Medium | Low | Medium |
| Approval / Workflow | Workflow Automation | 31 | 12-19 (40-60%) | Medium | Medium | Low | Medium |
| Network & Connectivity | Knowledge AI | 45 | 7-16 (15-35%) | Medium | Medium | Medium | High |
| Hardware & Devices | Workflow Automation | 50 | 8-15 (15-30%) | Low | Low | Low | High |
| Data / Reporting | Integration Automation | 26 | 5-10 (20-40%) | Medium | Medium | Medium | Medium |
| HR & Payroll | Knowledge AI | 20 | 6-10 (30-50%) | Medium | Medium | Medium | Medium |

**ROI (planning estimate):** 170-304 tickets (28.3-50.7% of total).

- Assumption: Deflection ranges assume the resolution path is API-accessible and knowledge quality is good.
- Assumption: Ranges are planning estimates, not commitments; validate with SMEs before quoting.
- Assumption: Physical fulfilment (hardware) and ambiguous 'Other' tickets are excluded from deflection upside.

## I. Agentic AI Use Case Backlog

### Access & Authentication (139 tickets, confidence High)
- Trigger: Password reset, account unlock, or access request ticket created
- System of action: Identity provider (Entra ID / Okta / AD)
- Permissions: Scoped identity admin for reset/unlock/group membership
- Steps: Verify requester identity, Check policy and entitlements, Execute reset or group change, Confirm and close
- Feasibility: High where IdP API is available
- Risk: Medium (identity actions; privileged changes need approval)
- Fallback: Route to IAM team with a prepared action packet
- Human approval: Required for privileged or role escalations
- Expected impact: Large share of L1 access load handled without an agent

### Application & Software (108 tickets, confidence High)
- Trigger: Repeated application error or configuration request
- System of action: Application admin console or config API
- Permissions: App-scoped admin (read plus limited config)
- Steps: Match to known issue, Apply guided fix or config, Verify, Document
- Feasibility: Medium; depends on app API maturity
- Risk: Low to Medium
- Fallback: Escalate to app owner with diagnosis
- Human approval: For production config changes
- Expected impact: Deflect how-to and known-error tickets, shorten diagnosis

### Salesforce / CRM (51 tickets, confidence Medium)
- Trigger: CRM data/metadata sync issue or record correction
- System of action: Salesforce (API / metadata / admin)
- Permissions: Scoped Salesforce admin
- Steps: Diagnose the sync/record issue, Prepare metadata or data fix, Validate in sandbox if available, Apply, Verify
- Feasibility: Medium to High via API
- Risk: Medium to High
- Fallback: Escalate to Salesforce admin/ops
- Human approval: For metadata/schema changes
- Expected impact: Resolve recurring CRM sync/data tickets faster

### Device Management / MDM (49 tickets, confidence Medium)
- Trigger: Device enrolment, compliance, or remote action request
- System of action: MDM (Intune / Jamf)
- Permissions: Scoped MDM admin
- Steps: Confirm device and policy, Trigger enrol/sync/lock/wipe as requested, Verify compliance state
- Feasibility: High; MDM APIs are mature
- Risk: Medium (wipe/lock are destructive)
- Fallback: Route to endpoint team
- Human approval: Required for wipe/lock
- Expected impact: Deflect enrolment/compliance tickets; act on devices safely

### Email & Collaboration (48 tickets, confidence High)
- Trigger: Distribution list, mailbox, or calendar access request
- System of action: Microsoft 365 / Google Workspace admin
- Permissions: Scoped collaboration admin
- Steps: Validate request, Apply membership/mailbox change, Confirm
- Feasibility: High; mature APIs
- Risk: Low
- Fallback: Route to messaging team
- Human approval: For shared/privileged mailboxes
- Expected impact: Deflect routine mailbox/DL requests

### Attendance & Leave (33 tickets, confidence Medium)
- Trigger: Attendance correction or leave-balance/unlock request
- System of action: HR / attendance system (e.g. SAP)
- Permissions: Scoped attendance admin
- Steps: Validate request against policy, Apply correction or unlock, Confirm balance, Notify
- Feasibility: High where attendance API/UI is reachable
- Risk: Low to Medium
- Fallback: Route to HR ops
- Human approval: For exceptions beyond policy
- Expected impact: Deflect routine attendance/leave tickets end to end

### Data / Reporting (26 tickets, confidence Medium)
- Trigger: Recurring report request or data reconciliation
- System of action: BI / data platform
- Permissions: Read plus scoped write for reconciliation
- Steps: Interpret the request, Run the query/report, Reconcile if needed, Deliver, Log
- Feasibility: Medium to High
- Risk: Medium
- Fallback: Route to data team
- Human approval: For data writes
- Expected impact: Deflect standard report requests; speed reconciliation

### HR & Payroll (20 tickets, confidence Medium)
- Trigger: Payroll or benefits query or correction request
- System of action: HRIS (Workday / SAP HR)
- Permissions: Read plus scoped correction with approval
- Steps: Answer from policy knowledge, If correction needed prepare change, Route for HR approval, Apply
- Feasibility: Medium; sensitive data
- Risk: Medium to High (compliance)
- Fallback: Route to HR shared services
- Human approval: Required
- Expected impact: Deflect policy questions; speed corrections with a human checkpoint

## J. Atomicwork Solution Mapping

- Access & Authentication (139): Access provisioning, Identity automation, Employee self-service, Ticket deflection, AI coworker in Slack or Microsoft Teams
- Application & Software (108): Guided troubleshooting, Knowledge ingestion, Ticket deflection, Employee self-service
- Salesforce / CRM (51): MCP/API orchestration, Agentic backend action, Analytics and operational insights
- Hardware & Devices (50): Employee self-service, Workflow execution, Approval automation, Analytics and operational insights
- Device Management / MDM (49): MCP/API orchestration, Agentic backend action, IT service automation
- Email & Collaboration (48): Knowledge ingestion, Workflow execution, Access provisioning, Employee self-service
- Network & Connectivity (45): Guided troubleshooting, Knowledge ingestion, Ticket deflection
- Attendance & Leave (33): Workflow execution, HR service automation, Approval automation, Employee self-service
- Approval / Workflow (31): Approval automation, Workflow execution, Human approval loop
- Data / Reporting (26): Analytics and operational insights, MCP/API orchestration, Agentic backend action, Human approval loop
- HR & Payroll (20): HR service automation, Knowledge ingestion, Approval automation, Employee self-service

## K. 30-60-90 Day Roadmap

**Days 0-30: Deflect the deterministic, low-risk load**
- Themes: Application & Software, Email & Collaboration, Network & Connectivity
- Ingest existing knowledge
- Stand up the AI coworker in Slack/Teams
- Deflect top how-to and password/access requests

**Days 30-60: Automate deterministic workflows**
- Themes: Access & Authentication, Attendance & Leave, Approval / Workflow
- Wire approval and provisioning workflows
- Connect the primary ITSM read/write
- Measure deflection vs baseline

**Days 60-90: Integration and agentic use cases with guardrails**
- Themes: Device Management / MDM, Salesforce / CRM, Data / Reporting
- Pilot one agentic backend use case with human approval
- Expand MCP/API integrations
- Review ROI against the baseline

## L. Workshop Questions for Customer

- Which of the top themes are already partially automated today?
- For the highest-volume theme, is the resolution path API-accessible or admin-UI only?
- What is the knowledge-base quality and coverage for the top deflection candidates?
- Which actions require a human approval step for compliance or risk reasons?
- For Access & Authentication, who owns the system of action and what permissions can be granted?

## M. PowerPoint Slide Outline

1. Title: Service Desk Analysis, examples/sample_servicedesk.csv
2. Executive summary and headline numbers
3. Data quality and confidence
4. Ticket volume and mix
5. MTTR: slowest and fastest areas
6. Theme breakdown (Pareto: the vital few)
7. Application landscape
8. Top operational friction points
9. AI automation opportunity backlog
10. Agentic AI use cases (with guardrails)
11. Atomicwork solution mapping
12. 30-60-90 day roadmap
13. ROI ranges and assumptions
14. Risks, assumptions, and workshop questions

## N. Final Recommendations

- Start with quick wins: Access & Authentication, Application & Software, Email & Collaboration. These are deterministic and low risk.
- Prioritize Access & Authentication for the largest deflection upside (56-97 tickets).
- Pilot one agentic use case (Access & Authentication) behind a human approval checkpoint before scaling.
- Treat all deflection figures as ranges to validate with SMEs, not commitments.

## O. UAT Test Plan

_Cases are generated from the 11 themes, 6 assignment groups, and 4 priority levels observed in the data. Test how the team actually works, not every feature._

- Total cases: 29 (Must 20, Should 9, Could 0)

| ID | Area | Test case | Role | Priority | Derived from |
| --- | --- | --- | --- | --- | --- |
| TC-001 | End-to-end lifecycle | Full lifecycle for a Access & Authentication ticket | Requester + Agent | Must | theme 'Access & Authentication': 139 tickets (23.2% of volume) |
| TC-002 | End-to-end lifecycle | Full lifecycle for a Application & Software ticket | Requester + Agent | Must | theme 'Application & Software': 108 tickets (18.0% of volume) |
| TC-003 | End-to-end lifecycle | Full lifecycle for a Salesforce / CRM ticket | Requester + Agent | Must | theme 'Salesforce / CRM': 51 tickets (8.5% of volume) |
| TC-004 | End-to-end lifecycle | Full lifecycle for a Hardware & Devices ticket | Requester + Agent | Must | theme 'Hardware & Devices': 50 tickets (8.3% of volume) |
| TC-005 | End-to-end lifecycle | Full lifecycle for a Device Management / MDM ticket | Requester + Agent | Must | theme 'Device Management / MDM': 49 tickets (8.2% of volume) |
| TC-006 | End-to-end lifecycle | Full lifecycle for a Email & Collaboration ticket | Requester + Agent | Must | theme 'Email & Collaboration': 48 tickets (8.0% of volume) |
| TC-007 | End-to-end lifecycle | Full lifecycle for a Network & Connectivity ticket | Requester + Agent | Must | theme 'Network & Connectivity': 45 tickets (7.5% of volume) |
| TC-008 | End-to-end lifecycle | Full lifecycle for a Attendance & Leave ticket | Requester + Agent | Must | theme 'Attendance & Leave': 33 tickets (5.5% of volume) |
| TC-009 | Priority and SLA | SLA behavior for priority 4 - Low | Agent | Should | priority '4 - Low' present in the data |
| TC-010 | Priority and SLA | SLA behavior for priority 3 - Moderate | Agent | Should | priority '3 - Moderate' present in the data |
| TC-011 | Priority and SLA | SLA behavior for priority 1 - Critical | Agent | Should | priority '1 - Critical' present in the data |
| TC-012 | Priority and SLA | SLA behavior for priority 2 - High | Agent | Should | priority '2 - High' present in the data |
| TC-013 | Priority and SLA | Escalation path for the historically slowest area (Hardware & Devices) | Agent + Manager | Should | slowest theme by MTTR: Hardware & Devices at 42.2h median |
| TC-014 | Roles and permissions | Requester sees only their own tickets | Requester | Must | baseline role separation |
| TC-015 | Roles and permissions | Queue visibility and assignment for group 'Endpoint Team' | Agent (Endpoint Team) | Must | assignment group 'Endpoint Team' present in the data |
| TC-016 | Roles and permissions | Queue visibility and assignment for group 'HR Ops' | Agent (HR Ops) | Must | assignment group 'HR Ops' present in the data |
| TC-017 | Roles and permissions | Queue visibility and assignment for group 'CRM Support' | Agent (CRM Support) | Must | assignment group 'CRM Support' present in the data |
| TC-018 | Roles and permissions | Queue visibility and assignment for group 'Network Team' | Agent (Network Team) | Must | assignment group 'Network Team' present in the data |
| TC-019 | Roles and permissions | Queue visibility and assignment for group 'Service Desk L1' | Agent (Service Desk L1) | Must | assignment group 'Service Desk L1' present in the data |
| TC-020 | Roles and permissions | Queue visibility and assignment for group 'ERP Support' | Agent (ERP Support) | Must | assignment group 'ERP Support' present in the data |
| TC-021 | Notifications | Acknowledgement on ticket creation | Requester | Must | standard notification flow; email-safety guard applied |
| TC-022 | Notifications | Assignment and resolution notifications | Agent | Must | standard notification flow; email-safety guard applied |
| TC-023 | Notifications | No notifications leak outside the test group | Project Manager | Must | risk raised for go-lives without a test environment |
| TC-024 | Approvals | Approval flow for a Approval / Workflow request | Requester + Approver | Must | theme 'Approval / Workflow' present in the data |
| TC-025 | Approvals | Approval cannot be bypassed | Agent | Should | control test for the approval flow |
| TC-026 | Reporting | Operational report matches known baseline | Manager | Should | baseline: 600 records analyzed |
| TC-027 | Reporting | MTTR/resolution-time report is computable | Manager | Should | MTTR available in the historical data |
| TC-028 | Data migration | Migrated record counts reconcile | Technical Resource | Must | migration from the current email/excel workflow |
| TC-029 | Data migration | Missing fields are captured going forward | Project Manager | Should | fields missing in the source data: assignee, mttr_hours |

### TC-001: Full lifecycle for a Access & Authentication ticket (Must)
- Role: Requester + Agent
- Step 1: As a requester, raise a incident representative of the 'Access & Authentication' theme
- Step 2: Verify it is categorized and routed to the right queue
- Step 3: As an agent, assign it, work it, and add a resolution note
- Step 4: Move it through the status flow (Open -> In Progress -> Resolved) and close it
- Step 5: Verify the requester can see the state at each step
- Expected: Ticket completes the full flow; every transition is recorded and visible to the requester

### TC-002: Full lifecycle for a Application & Software ticket (Must)
- Role: Requester + Agent
- Step 1: As a requester, raise a request representative of the 'Application & Software' theme
- Step 2: Verify it is categorized and routed to the right queue
- Step 3: As an agent, assign it, work it, and add a resolution note
- Step 4: Move it through the status flow (Open -> In Progress -> Resolved) and close it
- Step 5: Verify the requester can see the state at each step
- Expected: Ticket completes the full flow; every transition is recorded and visible to the requester

### TC-003: Full lifecycle for a Salesforce / CRM ticket (Must)
- Role: Requester + Agent
- Step 1: As a requester, raise a request representative of the 'Salesforce / CRM' theme
- Step 2: Verify it is categorized and routed to the right queue
- Step 3: As an agent, assign it, work it, and add a resolution note
- Step 4: Move it through the status flow (Open -> In Progress -> Resolved) and close it
- Step 5: Verify the requester can see the state at each step
- Expected: Ticket completes the full flow; every transition is recorded and visible to the requester

### TC-004: Full lifecycle for a Hardware & Devices ticket (Must)
- Role: Requester + Agent
- Step 1: As a requester, raise a request representative of the 'Hardware & Devices' theme
- Step 2: Verify it is categorized and routed to the right queue
- Step 3: As an agent, assign it, work it, and add a resolution note
- Step 4: Move it through the status flow (Open -> In Progress -> Resolved) and close it
- Step 5: Verify the requester can see the state at each step
- Expected: Ticket completes the full flow; every transition is recorded and visible to the requester

### TC-005: Full lifecycle for a Device Management / MDM ticket (Must)
- Role: Requester + Agent
- Step 1: As a requester, raise a request representative of the 'Device Management / MDM' theme
- Step 2: Verify it is categorized and routed to the right queue
- Step 3: As an agent, assign it, work it, and add a resolution note
- Step 4: Move it through the status flow (Open -> In Progress -> Resolved) and close it
- Step 5: Verify the requester can see the state at each step
- Expected: Ticket completes the full flow; every transition is recorded and visible to the requester

### TC-006: Full lifecycle for a Email & Collaboration ticket (Must)
- Role: Requester + Agent
- Step 1: As a requester, raise a incident representative of the 'Email & Collaboration' theme
- Step 2: Verify it is categorized and routed to the right queue
- Step 3: As an agent, assign it, work it, and add a resolution note
- Step 4: Move it through the status flow (Open -> In Progress -> Resolved) and close it
- Step 5: Verify the requester can see the state at each step
- Expected: Ticket completes the full flow; every transition is recorded and visible to the requester

### TC-007: Full lifecycle for a Network & Connectivity ticket (Must)
- Role: Requester + Agent
- Step 1: As a requester, raise a incident representative of the 'Network & Connectivity' theme
- Step 2: Verify it is categorized and routed to the right queue
- Step 3: As an agent, assign it, work it, and add a resolution note
- Step 4: Move it through the status flow (Open -> In Progress -> Resolved) and close it
- Step 5: Verify the requester can see the state at each step
- Expected: Ticket completes the full flow; every transition is recorded and visible to the requester

### TC-008: Full lifecycle for a Attendance & Leave ticket (Must)
- Role: Requester + Agent
- Step 1: As a requester, raise a incident representative of the 'Attendance & Leave' theme
- Step 2: Verify it is categorized and routed to the right queue
- Step 3: As an agent, assign it, work it, and add a resolution note
- Step 4: Move it through the status flow (Open -> In Progress -> Resolved) and close it
- Step 5: Verify the requester can see the state at each step
- Expected: Ticket completes the full flow; every transition is recorded and visible to the requester

### TC-009: SLA behavior for priority 4 - Low (Should)
- Role: Agent
- Step 1: Create a test ticket at priority 4 - Low
- Step 2: Verify the SLA clock, target, and any escalation timer start correctly
- Step 3: Let the ticket approach breach in the test window if feasible
- Step 4: Verify breach warnings fire to the right people
- Expected: Priority 4 - Low applies the configured SLA and escalation path

### TC-010: SLA behavior for priority 3 - Moderate (Should)
- Role: Agent
- Step 1: Create a test ticket at priority 3 - Moderate
- Step 2: Verify the SLA clock, target, and any escalation timer start correctly
- Step 3: Let the ticket approach breach in the test window if feasible
- Step 4: Verify breach warnings fire to the right people
- Expected: Priority 3 - Moderate applies the configured SLA and escalation path

### TC-011: SLA behavior for priority 1 - Critical (Should)
- Role: Agent
- Step 1: Create a test ticket at priority 1 - Critical
- Step 2: Verify the SLA clock, target, and any escalation timer start correctly
- Step 3: Let the ticket approach breach in the test window if feasible
- Step 4: Verify breach warnings fire to the right people
- Expected: Priority 1 - Critical applies the configured SLA and escalation path

### TC-012: SLA behavior for priority 2 - High (Should)
- Role: Agent
- Step 1: Create a test ticket at priority 2 - High
- Step 2: Verify the SLA clock, target, and any escalation timer start correctly
- Step 3: Let the ticket approach breach in the test window if feasible
- Step 4: Verify breach warnings fire to the right people
- Expected: Priority 2 - High applies the configured SLA and escalation path

### TC-013: Escalation path for the historically slowest area (Hardware & Devices) (Should)
- Role: Agent + Manager
- Step 1: Create a ticket in the 'Hardware & Devices' area
- Step 2: Leave it unactioned past the escalation threshold
- Step 3: Verify it escalates to the manager or next tier automatically
- Expected: Stale tickets escalate instead of sitting idle

### TC-014: Requester sees only their own tickets (Must)
- Role: Requester
- Step 1: Log in as a plain requester test account
- Step 2: Verify they can raise and view their own tickets
- Step 3: Verify they cannot see other users' tickets, admin settings, or queues
- Expected: Requester access is limited to their own records

### TC-015: Queue visibility and assignment for group 'Endpoint Team' (Must)
- Role: Agent (Endpoint Team)
- Step 1: Log in as a test agent in 'Endpoint Team'
- Step 2: Verify the agent sees the 'Endpoint Team' queue and can pick up and reassign within it
- Step 3: Verify the agent cannot edit tickets owned exclusively by other groups unless that is intended
- Expected: 'Endpoint Team' agents work their queue; cross-queue access matches the agreed design

### TC-016: Queue visibility and assignment for group 'HR Ops' (Must)
- Role: Agent (HR Ops)
- Step 1: Log in as a test agent in 'HR Ops'
- Step 2: Verify the agent sees the 'HR Ops' queue and can pick up and reassign within it
- Step 3: Verify the agent cannot edit tickets owned exclusively by other groups unless that is intended
- Expected: 'HR Ops' agents work their queue; cross-queue access matches the agreed design

### TC-017: Queue visibility and assignment for group 'CRM Support' (Must)
- Role: Agent (CRM Support)
- Step 1: Log in as a test agent in 'CRM Support'
- Step 2: Verify the agent sees the 'CRM Support' queue and can pick up and reassign within it
- Step 3: Verify the agent cannot edit tickets owned exclusively by other groups unless that is intended
- Expected: 'CRM Support' agents work their queue; cross-queue access matches the agreed design

### TC-018: Queue visibility and assignment for group 'Network Team' (Must)
- Role: Agent (Network Team)
- Step 1: Log in as a test agent in 'Network Team'
- Step 2: Verify the agent sees the 'Network Team' queue and can pick up and reassign within it
- Step 3: Verify the agent cannot edit tickets owned exclusively by other groups unless that is intended
- Expected: 'Network Team' agents work their queue; cross-queue access matches the agreed design

### TC-019: Queue visibility and assignment for group 'Service Desk L1' (Must)
- Role: Agent (Service Desk L1)
- Step 1: Log in as a test agent in 'Service Desk L1'
- Step 2: Verify the agent sees the 'Service Desk L1' queue and can pick up and reassign within it
- Step 3: Verify the agent cannot edit tickets owned exclusively by other groups unless that is intended
- Expected: 'Service Desk L1' agents work their queue; cross-queue access matches the agreed design

### TC-020: Queue visibility and assignment for group 'ERP Support' (Must)
- Role: Agent (ERP Support)
- Step 1: Log in as a test agent in 'ERP Support'
- Step 2: Verify the agent sees the 'ERP Support' queue and can pick up and reassign within it
- Step 3: Verify the agent cannot edit tickets owned exclusively by other groups unless that is intended
- Expected: 'ERP Support' agents work their queue; cross-queue access matches the agreed design

### TC-021: Acknowledgement on ticket creation (Must)
- Role: Requester
- Step 1: Before running: confirm outbound email is disabled or redirected to internal test recipients
- Step 2: Raise a test ticket
- Step 3: Verify the requester receives (or would receive) a creation acknowledgement
- Step 4: Verify the notification goes only to the intended recipient
- Expected: Creation acknowledgement is sent to the requester only

### TC-022: Assignment and resolution notifications (Must)
- Role: Agent
- Step 1: Before running: confirm outbound email is disabled or redirected to internal test recipients
- Step 2: Assign a test ticket to an agent and verify the agent is notified
- Step 3: Resolve it and verify the requester is notified with the resolution
- Expected: Assignment notifies the agent; resolution notifies the requester

### TC-023: No notifications leak outside the test group (Must)
- Role: Project Manager
- Step 1: Review the notification/audit log after a full test day
- Step 2: Verify no notification was sent to a real end user or external address
- Expected: Zero notifications reached anyone outside the test group

### TC-024: Approval flow for a Approval / Workflow request (Must)
- Role: Requester + Approver
- Step 1: Raise a request in the 'Approval / Workflow' area that requires approval
- Step 2: Verify the approver is notified and can approve or reject
- Step 3: Verify rejection returns the request with a reason
- Step 4: Verify approval releases the request for fulfilment
- Expected: Approve and reject paths both work and are recorded

### TC-025: Approval cannot be bypassed (Should)
- Role: Agent
- Step 1: As an agent, attempt to fulfil an approval-gated request before approval
- Step 2: Verify the tool blocks fulfilment until the approval is recorded
- Expected: Approval gate cannot be skipped

### TC-026: Operational report matches known baseline (Should)
- Role: Manager
- Step 1: Run the volume-by-category and open-backlog reports on the test data
- Step 2: Compare against the counts from this analysis as the baseline
- Expected: Report figures reconcile with the baseline counts

### TC-027: MTTR/resolution-time report is computable (Should)
- Role: Manager
- Step 1: Resolve at least two test tickets with known timestamps
- Step 2: Run the resolution-time report and verify the durations are correct
- Expected: Resolution time is computed from the correct timestamps

### TC-028: Migrated record counts reconcile (Must)
- Role: Technical Resource
- Step 1: Export the source data (baseline: 600 records)
- Step 2: Import into the new tool
- Step 3: Verify counts match by status and by category; investigate any delta
- Expected: Source and target record counts reconcile exactly

### TC-029: Missing fields are captured going forward (Should)
- Role: Project Manager
- Step 1: Verify the new tool makes these fields mandatory or defaulted at creation: assignee, mttr_hours
- Step 2: Raise a test ticket and confirm the fields are populated
- Expected: Fields absent in the historical data are captured by the new tool

## P. Role and Permission Test Matrix

| Role | Can | Cannot | Derived from |
| --- | --- | --- | --- |
| Requester / End User | Raise requests; View and comment on own tickets; Approve items routed to them | View others' tickets; Change configuration; Access queues | baseline role |
| Service Desk Agent | Work assigned queue; Assign and reassign within group; Resolve and close; Add worklog and resolution notes | Change workflow or SLA configuration; Manage users | baseline role |
| Agent: Endpoint Team | Work the 'Endpoint Team' queue; Pick up, reassign, resolve within the group | Edit other groups' tickets (unless designed otherwise); Change configuration | assignment group 'Endpoint Team' in the data |
| Agent: HR Ops | Work the 'HR Ops' queue; Pick up, reassign, resolve within the group | Edit other groups' tickets (unless designed otherwise); Change configuration | assignment group 'HR Ops' in the data |
| Agent: CRM Support | Work the 'CRM Support' queue; Pick up, reassign, resolve within the group | Edit other groups' tickets (unless designed otherwise); Change configuration | assignment group 'CRM Support' in the data |
| Agent: Network Team | Work the 'Network Team' queue; Pick up, reassign, resolve within the group | Edit other groups' tickets (unless designed otherwise); Change configuration | assignment group 'Network Team' in the data |
| Agent: Service Desk L1 | Work the 'Service Desk L1' queue; Pick up, reassign, resolve within the group | Edit other groups' tickets (unless designed otherwise); Change configuration | assignment group 'Service Desk L1' in the data |
| Agent: ERP Support | Work the 'ERP Support' queue; Pick up, reassign, resolve within the group | Edit other groups' tickets (unless designed otherwise); Change configuration | assignment group 'ERP Support' in the data |
| Service Desk Manager | View all queues and reports; Reassign across groups; Approve escalations | Change system configuration (admin only) | baseline role |
| Administrator | Configure workflows, SLAs, notifications, users, roles | Approve business requests (segregation of duties) | baseline role |

## Q. Implementation RACI

| Activity | Responsible | Accountable | Consulted | Informed |
| --- | --- | --- | --- | --- |
| Map current workflows into test scenarios | Project Manager | Delivery Lead | Business Users | Vendor / Implementer |
| Configure the tool (queues, roles, SLAs, notifications) | Vendor / Implementer | Project Manager | Technical Resources | Delivery Lead |
| Prepare test accounts and disable/redirect outbound email | Technical Resources | Project Manager | Vendor / Implementer | Business Users |
| Execute UAT test cases and log defects | Technical Resources | Project Manager | Business Users | Delivery Lead |
| Fix defects and re-test | Vendor / Implementer | Project Manager | Technical Resources | Delivery Lead |
| Data migration dry run and reconciliation | Technical Resources | Delivery Lead | Vendor / Implementer | Project Manager |
| Go/no-go decision | Project Manager | Delivery Lead | Vendor / Implementer | Business Users |
| End-user training and comms | Project Manager | Delivery Lead | Business Users | Vendor / Implementer |
| Hypercare and post-go-live support | Vendor / Implementer | Project Manager | Technical Resources | Business Users |

## R. Go-Live Readiness Checklist

| Gate | Category | Item | Derived from |
| --- | --- | --- | --- |
| Must | Safety | Outbound email/notifications disabled or redirected to internal test recipients for the whole test window | no test environment: prevent accidental customer emails |
| Must | Safety | Dedicated test accounts exist for every role in the role matrix | role matrix |
| Must | Quality | All Must test cases passed and signed off by a named owner | UAT test plan |
| Must | Safety | Rollback plan agreed (keep the old email/excel channel warm for the first two weeks) | standard go-live control |
| Must | Operations | Support model for launch week defined (who triages, who escalates) | standard go-live control |
| Should | Adoption | End users trained on raising and tracking requests | standard go-live control |
| Must | Configuration | Category scheme in the new tool covers the top observed themes: Access & Authentication, Application & Software, Salesforce / CRM, Hardware & Devices, Device Management / MDM | theme breakdown of the historical data |
| Should | Configuration | Request types configured to match observed intake: Incident, Request | type field in the historical data |
| Should | Measurement | Baseline metrics from this analysis saved to compare after go-live (volume, MTTR, theme mix) | this analysis |

## S. 15-Day Testing Phase Plan

**Days 1-3: Setup and smoke test**
- Confirm configuration: queues, categories, roles, SLAs
- Create test accounts per role; disable or redirect outbound email
- Smoke test: one ticket end to end per request type
- Exit criteria: One ticket completes the full lifecycle with no blocker

**Days 4-8: Core workflow testing**
- Run lifecycle cases for the top themes (Access & Authentication, Application & Software, Salesforce / CRM, Hardware & Devices)
- Run priority/SLA and escalation cases
- Log every defect with steps to reproduce; retest fixes daily
- Exit criteria: All Must lifecycle and SLA cases pass

**Days 9-11: Roles, notifications, approvals**
- Verify queue visibility for each group (Endpoint Team, HR Ops, CRM Support, Network Team, Service Desk L1, ERP Support)
- Run all notification cases; audit that nothing leaked externally
- Run approval flow and bypass-prevention cases
- Exit criteria: Role matrix verified; zero external notification leaks

**Days 12-13: Migration dry run and regression**
- Dry-run data migration; reconcile counts against the baseline
- Regression pass on all previously failed cases
- Freeze configuration
- Exit criteria: Migration reconciles; no open Must defects

**Days 14: Go/no-go**
- Walk the readiness checklist with the delivery lead
- Named sign-off on every Must item
- Decide go/no-go; if no-go, agree the gap plan
- Exit criteria: Documented go decision with sign-offs

**Days 15: Go-live preparation**
- Re-enable outbound notifications for production recipients
- Final comms to end users; hypercare rota confirmed
- Keep the old intake channel open as fallback
- Exit criteria: Tool live; fallback and support rota in place

**Testing assumptions**

- Test in a sandbox if available. If not, disable outbound email/notifications or redirect them to internal test recipients before any test run, so no customer or end user is notified by accident.
- Use dedicated test accounts per role, never personal or customer accounts.
- Test cases reflect workflows observed in the historical data; new processes introduced by the tool need cases added by the process owner.
- Every Must case needs a pass and a named sign-off before go-live.

---
_Analysis is deterministic and in-memory. No model was used, no data was retained, and no data left this machine._