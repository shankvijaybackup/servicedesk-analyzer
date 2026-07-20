# Methodology

This is the analysis the tool implements, deterministically and offline. It is a coded specification: each step maps to a module in `sda/`. Nothing is left to a model.

## 1. Data integrity first (sda/integrity.py)

Before any insight, inspect the dataset: total records, detected columns, missing fields, duplicates, date range, ticket types, priority, assignment groups, categories, resolution and MTTR availability, requester and application fields. Missing fields are reported as missing, never invented. A transparent 0-100 quality score is produced, and every deduction is listed.

## 2. Normalize (sda/normalize.py)

Build a clean analytical view with canonical columns, parsed dates, a computed MTTR, standardized priority and status, and a combined lowercase text field used for classification. Original data is not mutated.

## 3. Theme categorization (sda/themes.py, rules/themes.yaml)

Score each ticket's text against keyword rules per business theme (Access, Application, HR, Attendance, Hardware, Network, Email, SAP/ERP, CRM, MDM, Knowledge, Approval, Data, Other). Highest score wins; word-boundary matching prevents false hits; negatives reduce misclassification. Per theme: count, percentage, MTTR, top types, top applications, match strength, description coverage, and a confidence level. Raw example phrases are not included in exportable analysis.

## 4. Pareto (sda/pareto.py)

Identify the vital few categories driving most of the load. High-volume (count) is separated from high-pain (count x median MTTR) so they are not conflated.

## 5. MTTR (sda/mttr.py)

Overall and by theme, category, subcategory, application, priority, and assignment group. Slowest and fastest areas are flagged. Groups below a minimum size are not ranked. The module never claims a reduction is achievable; that is decided only where a clear automation path exists.

## 6-9. Opportunity, solution, agentic, ROI (sda/opportunities.py, rules/atomicwork.yaml)

Each theme maps to automation types (Knowledge, Workflow, Integration, Agentic, Human-in-the-loop, or None), to Atomicwork capabilities, and, where applicable, to an agentic use case with trigger, system of action, permissions, steps, feasibility, risk, fallback, human-approval requirement, and expected impact. ROI is expressed as ranges derived from actual counts and conservative deflection bands, always gated on stated assumptions.

## 10. Executive output (sda/executive.py)

Current-state summary, top findings, quick wins, 30-60-90 roadmap, risks and assumptions, workshop questions, and final recommendations, all derived from the computed numbers.

## 11. Validation and challenge

Confidence is marked High, Medium, or Low per theme and per opportunity, driven by volume, description coverage, and match strength. Low-confidence areas and "Other" volume are surfaced explicitly, with workshop questions prompting SME validation.

## 12. Implementation and UAT package (sda/uat.py)

When the analysis will feed a tool implementation or migration (for example replacing an email/excel workflow with an ITSM/PM platform), the same data drives a testing package: a UAT test plan whose cases come from the themes, priorities, statuses, and assignment groups actually observed; a role and permission test matrix seeded from the detected groups; an implementation RACI; a go-live readiness checklist (including disabling or redirecting outbound email when no test environment exists); and a 15-day testing phase plan with exit criteria. Every test case cites the data signal that generated it. The principle is: test whether the tool supports how the team actually works, not every feature.

## 13. Deliverables

A through N plus the implementation package O through S (UAT test plan, role matrix, RACI, readiness checklist, phase plan), rendered to HTML, PowerPoint, Markdown, Excel, and JSON by `sda/report/`. The Excel workbook includes execution columns (status, tester, date, defect ref) so the test plan is directly usable as a tracking sheet.

## 14. Iterative improvement and feedback

The tool can compare a baseline and follow-up export for one explicitly defined
cohort. The same deterministic rule pack is applied to both. Every metric states
whether it is measurable and includes its denominator and coverage. Missing
feedback fields remain unknown.

The comparison checks minimum sample size, overlapping ticket identifiers,
priority-mix differences, and MTTR-coverage differences. It then applies a pure
decision order: insufficient evidence means continue measuring; a failed required
guardrail means stop; a passed primary threshold with measurable guardrails means
widen; otherwise correct.

This is an observational before-and-after comparison. It reports association,
not causation. Ticket mix, staffing, seasonality, and unrelated process changes
can influence the result.

## Rules the tool follows

Do not hallucinate. Do not invent customer systems. Do not invent ROI. Do not overstate confidence. Do not classify a physical device issue as software (or vice versa) without keyword evidence. Separate facts, assumptions, and recommendations. Every insight is traceable to the data.
