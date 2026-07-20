# Feature Guide

Service Desk Analyzer 0.2 turns a one-time ticket report into a deterministic
improvement loop. Core analysis remains offline, inspectable, and independent
of any language model.

## Current-state analysis

- CSV, TSV, and XLSX ingestion
- Vendor-neutral schema detection
- Data-quality scoring with explicit deductions
- Ticket volume and status analysis
- Median, mean, and p90 resolution time
- Theme classification using editable keyword rules
- Pareto and operational-pain analysis
- Application and assignment-group views
- Automation and agentic opportunity backlogs
- Planning ranges with assumptions and confidence labels

## Recommended pilot

The analyzer recommends one first pilot using an exposed score composed of:

- Volume share
- Evidence confidence
- Implementation feasibility
- Operational safety

The score is deterministic. Users can inspect every component and override the
recommendation.

## Iterative improvement

- Baseline and follow-up comparison
- Cohort filters for theme, assignment group, priority, application, and department
- Pilot charter with primary metric and minimum improvement threshold
- Required guardrails
- Sample-size and comparability checks
- Overlapping ticket-ID detection
- Priority-mix and MTTR-coverage warnings
- Explicit `widen`, `correct`, `continue_measuring`, or `stop` decision
- Observational-association warning instead of causal claims

## Optional feedback metrics

The following fields are supported through conservative exact header aliases:

- Reopen count
- First-contact resolution
- SLA breach
- Escalation
- AI attempted
- AI accepted
- Human override
- User-confirmed resolution
- Pilot ID
- Treatment group

Invalid or missing values remain unknown. They are never converted to false or
zero.

## Grounded executive narrative

The executive summary is generated deterministically from aggregate evidence.
It reports record count, data quality, median and p90 resolution time, the top
three themes, and clearly labeled planning estimates. No language model can
alter these facts.

## Implementation and UAT package

- Data-derived UAT test plan
- Role and permission matrix
- Implementation RACI
- Go-live readiness checklist
- Outbound-email safety gate
- 15-day rollout phase plan
- Execution columns in Excel

## Outputs

Every analysis can be exported to:

- HTML
- Markdown
- JSON
- Excel
- PowerPoint

Iteration comparisons add scorecard and decision sections without breaking the
original report structure.

## Local AI

Local AI is optional and advisory. It can draft pilot wording from a strict
aggregate allowlist. It cannot see raw tickets, compute metrics, classify
tickets, select a pilot, or decide whether to widen it.

## Local history

Iteration history is disabled by default. When enabled, SQLite stores only the
pilot charter and aggregate scorecard. Source rows are never stored.
