# Service Desk Intelligence Analyzer

Turn a raw service desk export (CSV or Excel) into an executive decision memo,
built on ITIL 4 guiding principles: where we are today, where we want to be,
and how we get there.

Works with exports from ServiceNow, Jira Service Management, Freshservice,
Zendesk, ManageEngine, and Atomicwork. Produces a browser report, Markdown,
a PowerPoint deck, and a slide outline. Fully offline, deterministic, and
auditable: no AI, no cloud, no data retention.

## Why this exists

Service desk reporting is usually a metrics dump: ticket counts, SLA charts,
MTTR graphs. Numbers without a decision. ITIL 4 says value is co-created with
the consumer, and reporting should serve decisions, not dashboards. This tool
reads one export and answers the three questions an executive actually asks:

1. **Where are we today?** Measured from your data: volume concentration,
   median wait, work stuck on hold, tickets bouncing between teams.
2. **Where do we want to be?** A concrete, checkable target state: which share
   of requests should never need a human, what employee wait should become.
3. **How do we get there?** A 30-60-90 plan with named automations, an explicit
   ask, and this report as the baseline to measure progress against.

## ITIL 4 alignment

### Guiding principles, applied end to end

| ITIL 4 principle | How the report applies it |
| --- | --- |
| Focus on value | The report opens with outcomes per stakeholder (CIO, CFO, CHRO, service desk lead, employees), not metrics. Every number must serve a decision or it is cut. |
| Start where you are | The analysis is built only from your export. Missing fields are declared missing, never invented. The report itself becomes the day-0 baseline. |
| Progress iteratively with feedback | The roadmap is 30-60-90 with a re-run of this analysis after each phase. Scale only what the data shows is working. |
| Collaborate and promote visibility | Deliverable L is a workshop question set for SMEs; every finding carries a confidence tag (High / Medium / Low) so disagreement is invited, not hidden. |
| Think and work holistically | Themes span IT, HR, security, ERP, and CRM; workflow-state analysis (stuck, transferred) exposes cross-team friction, not just per-queue stats. |
| Keep it simple and practical | One page decision memo up front. Median wait in human units ("15 hours"), never absurd cumulative figures. No invented currency: hours x your rate. |
| Optimize and automate | Every theme is classified into solution types A-F, including "No Automation Recommended" where the honest answer is a human or a process fix. |

### Service Value Chain mapping

The deliverables map to ITIL 4 Service Value Chain activities:

| SVC activity | Deliverables |
| --- | --- |
| Plan | A. Executive Summary (decision memo), K. 30-60-90 Roadmap |
| Improve | G. Friction Points, H. Automation Backlog, I. Agentic AI Backlog, N. Recommendations |
| Engage | L. Workshop Questions, M. Slide Outline, stakeholder value table |
| Design and transition | J. Solution Mapping (AI Coworkers, capabilities, dependencies, risk, approval paths) |
| Obtain/build | Dependencies per opportunity: API access, credentials, knowledge quality |
| Deliver and support | C. Volume, D. MTTR, E. Themes, F. Application Landscape (the operational evidence base) |

### Continual improvement, built in

The report follows the ITIL continual improvement model: *What is the vision*
(target state) -> *Where are we now* (baseline, data quality verdict) ->
*Where do we want to be* (deflection ranges, wait-time targets) -> *How do we
get there* (roadmap) -> *Take action* (quick wins, pilots) -> *Did we get
there* (re-run the analysis; deltas against day-0). Because the tool is
deterministic, two runs on the same data always produce the same numbers:
your baseline is reproducible, not a screenshot.

### Metrics discipline (ITIL 4 measurement and reporting practice)

- Facts, assumptions, and recommendations are separated and labeled. Measured
  figures cite their source (e.g. "median elapsed time from your timestamps");
  assumption-based figures state the band used (e.g. "15-45 min handle time,
  replace with yours").
- Ranges, never fake precision. Deflection is "40-60% if API-accessible", not
  "52.3%".
- No invented currency. The report gives hours; you bring your loaded rate.
- Confidence tags on every insight, and a self-challenge section that attacks
  the analysis before you present it (misclassification rate, blind spots,
  duplicate distortion, one-time spikes, MTTR reliability).

## Privacy: no AI, no cloud, no retention

- **No LLM, no AI service, no telemetry.** No API clients, no SDKs, no keys.
  Dependencies are exactly pandas, Flask, python-pptx, openpyxl. Analysis is
  rule-based: keyword classification and aggregation.
- **Data never leaves the machine.** Local execution only.
- **No training, no learning.** No model, no state between runs.
- **Forgets immediately.** Uploads are processed in memory, never written to
  disk. Raw data is deleted at each pipeline stage. The web app keeps only the
  aggregate report for 30 minutes (or until "Forget now"), then purges.

Do not take these claims on faith. Run the audit:

```bash
.venv/bin/python audit.py
```

Fourteen checks, exits non-zero on any violation: no network/AI imports, exact
dependency list, no disk writes in the web app, deletion at every pipeline
stage, forget and TTL purge verified live, and generated reports free of
emojis, marketing filler, and invented figures.

## Quick start

Requires Python 3.10+.

```bash
git clone https://github.com/<you>/servicedesk-analyzer.git
cd servicedesk-analyzer
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Web app

```bash
.venv/bin/python web_app.py
# open http://127.0.0.1:5080
```

Upload a CSV/XLSX, read the memo, download Markdown / HTML / PPTX / slide
outline, then "Forget now".

### CLI

```bash
.venv/bin/python cli.py tickets.csv                              # HTML report
.venv/bin/python cli.py tickets.xlsx -f html md pptx ppt-outline -o output
```

### Sample data

```bash
cd sample_data && ../.venv/bin/python make_sample.py && cd ..
.venv/bin/python cli.py sample_data/sample_tickets.csv -f html -o output
```

## Hosting (optional)

Default bind is 127.0.0.1. To expose it:

```bash
HOST=0.0.0.0 PORT=8080 .venv/bin/python web_app.py
```

Or Docker:

```bash
docker build -t servicedesk-analyzer .
docker run --rm -p 5080:5080 servicedesk-analyzer
```

Non-root container, single worker (the report store is in-process memory).
For team use, put your own TLS/auth in front; the app has no accounts and no
database by design.

## What you get (deliverables A-N)

A. Executive Summary (the three-question decision memo) - B. Data Quality
Assessment - C. Ticket Volume Analysis - D. MTTR and Workflow-State Analysis -
E. Theme and Category Breakdown (with blind-spot term mining) - F. Application
Landscape - G. Operational Friction Points - H. AI Automation Opportunity
Backlog - I. Agentic AI Use Case Backlog - J. Atomicwork Solution Mapping
(AI Coworkers per theme) - K. 30-60-90 Roadmap - L. Workshop Questions -
M. PowerPoint Slide Outline - N. Final Recommendations with self-challenge.

## How the analysis works

1. **Data integrity first.** Columns, missing fields, duplicates, parse rates.
   Column mappings are content-validated: a "Resolved By" column of names will
   not be mistaken for a date; an "Application" column full of approval
   statuses is rejected with a note.
2. **Pollution defense.** Email dumps, tracking URLs, base64 blobs, and error
   logs inside fields are scrubbed before they can reach any table.
3. **Normalization.** Canonical schema, standardized priority/status, MTTR
   from explicit column or timestamps.
4. **Theme classification.** 15 enterprise themes via ordered keyword rules,
   summary-first weighting (the subject line outvotes boilerplate in the
   description). Unclassified tickets get term-mined so the blind spot is
   visible, not hidden.
5. **Pareto and pain.** 80% volume drivers; high-volume vs high-MTTR split;
   stuck and transferred work as friction signals when MTTR is absent.
6. **Opportunity mapping.** Solution types A-F per theme, AI Coworker
   assignments, deflection ranges gated by evidence volume (below 5 tickets,
   no recommendation).
7. **Honesty guards.** Short observation windows produce a loud snapshot
   warning; sub-0.3 FTE claims are suppressed; every estimate declares its
   basis.

## Extending

- Theme rules: `THEME_RULES` in [sdanalyzer/themes.py](sdanalyzer/themes.py)
- Automation playbook and AI Coworker mapping: `THEME_PLAYBOOK` and
  `AGENTIC_TEMPLATES` in [sdanalyzer/opportunities.py](sdanalyzer/opportunities.py)
- Deliverable assembly: [sdanalyzer/report.py](sdanalyzer/report.py)

All plain data structures; adjust without touching the pipeline. Run
`audit.py` after changes.

## License

MIT
