# Service Desk Intelligence Analyzer

Analyze service desk exports (CSV or Excel) from ServiceNow, Jira Service Management,
Freshservice, Zendesk, ManageEngine, or Atomicwork, and produce an executive-ready
operational assessment: theme breakdown, Pareto and MTTR analysis, an AI automation
opportunity backlog, an Agentic AI use case backlog, a 30-60-90 roadmap, and a
PowerPoint deck.

## Privacy: no AI, no cloud, no retention

This tool is fully offline and deterministic. Verifiable in the source:

- **No LLM, no AI service, no telemetry.** There are no API clients, no SDKs, no keys.
  The only dependencies are pandas, Flask, python-pptx, and openpyxl. Analysis is
  rule-based (keyword classification and aggregation) - grep the code for `http` and
  you will find no outbound calls.
- **Your data never leaves your machine.** Everything runs locally (or on whatever
  host you deploy it to). Nothing is sent anywhere.
- **No training, no learning.** The tool has no model and stores nothing between runs.
- **No retention.** Uploads are processed in memory and never written to disk. The
  web app keeps only the aggregated report (no raw rows) in memory for 30 minutes so
  you can download formats, then purges it. A "Forget now" button purges immediately.
  The CLI writes only the report files you ask for.

Do not take these claims on faith. Run the audit yourself:

```bash
.venv/bin/python audit.py
```

It verifies, on your machine: no network/AI imports anywhere in the source, the
dependency list is exactly pandas/flask/python-pptx/openpyxl, the web app has no
disk writes, raw data is deleted at every pipeline stage, "Forget now" and the
30-minute TTL actually purge, and generated reports contain no emojis, no
marketing filler, and no invented figures. Exits non-zero on any violation.

## Quick start (local)

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

Upload a CSV/XLSX, view the report in the browser, download Markdown / HTML / PPTX /
slide outline, then "Forget now".

### CLI

```bash
.venv/bin/python cli.py tickets.csv                              # HTML report
.venv/bin/python cli.py tickets.xlsx -f html md pptx ppt-outline -o output
```

### Try it with sample data

```bash
cd sample_data && ../.venv/bin/python make_sample.py && cd ..
.venv/bin/python cli.py sample_data/sample_tickets.csv -f html -o output
```

## Hosting it (optional)

The default bind is 127.0.0.1 (local only). To expose it, set `HOST` and `PORT`:

```bash
HOST=0.0.0.0 PORT=8080 .venv/bin/python web_app.py
```

Or with Docker:

```bash
docker build -t servicedesk-analyzer .
docker run --rm -p 5080:5080 servicedesk-analyzer
```

The container runs as a non-root user and keeps a single worker process because the
report store is in-process memory. If you host it for a team, put it behind your own
TLS/auth (reverse proxy); the app itself has no accounts and no database by design.

## What the report contains (deliverables A-N)

A. Executive Summary - B. Data Quality Assessment - C. Ticket Volume Analysis -
D. MTTR Analysis - E. Theme and Category Breakdown - F. Application Landscape -
G. Top Operational Friction Points - H. AI Automation Opportunity Backlog -
I. Agentic AI Use Case Backlog - J. Atomicwork Solution Mapping -
K. 30-60-90 Day Roadmap - L. Workshop Questions - M. PowerPoint Slide Outline -
N. Final Recommendations (with a self-challenge section separating facts from
assumptions).

## Methodology

1. Data integrity first: columns, missing fields, duplicates, parse rates. Missing
   fields are reported, never invented.
2. Normalization: canonical schema, standardized priority/status, MTTR from an
   explicit column or computed from timestamps.
3. Theme categorization: 14 enterprise themes via ordered keyword rules. Specific
   systems (SAP, Salesforce, MDM) are matched before generic buckets, so "iPad slide
   content not updated" is classified as application content, not hardware.
4. Pareto: top 20% of categories driving 80% of load; high-volume vs high-pain split.
5. MTTR by theme, priority, application, and assignment group with coverage caveats.
6. AI opportunity types A-F per theme: Knowledge AI, Workflow Automation, Integration
   Automation, Agentic AI, Human-in-the-loop, or No Automation Recommended.
7. Atomicwork capability mapping per opportunity.
8. Agentic use cases with trigger, system of action, permissions, steps, risk,
   approval requirement, and fallback path.
9. ROI as conservative ranges tied to observed volume and MTTR - never fake precision.
10. Every insight carries a confidence tag (High / Medium / Low).

## Project structure

- `sdanalyzer/loader.py` - CSV/XLSX import, vendor column detection
- `sdanalyzer/quality.py` - data integrity assessment
- `sdanalyzer/normalize.py` - canonical analytical view
- `sdanalyzer/themes.py` - theme classification rules
- `sdanalyzer/analysis.py` - Pareto + MTTR
- `sdanalyzer/opportunities.py` - opportunity / agentic / ROI playbooks
- `sdanalyzer/report.py` - pipeline + deliverable assembly
- `sdanalyzer/render_md.py` / `render_html.py` / `render_pptx.py` - output formats
- `cli.py` / `web_app.py` - entry points
- `sample_data/make_sample.py` - synthetic test data generator

## Extending

Theme rules live in `sdanalyzer/themes.py` (`THEME_RULES`), and the per-theme
automation playbook in `sdanalyzer/opportunities.py` (`THEME_PLAYBOOK`,
`AGENTIC_TEMPLATES`). Both are plain data structures - adjust keywords, deflection
ranges, or add new agentic scenarios without touching the pipeline.

## License

MIT
