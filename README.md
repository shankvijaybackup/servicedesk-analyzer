# Service Desk Analyzer

Import a service desk export (CSV or XLSX) from any tool and get an executive-ready analysis, one transparent pilot recommendation, and an evidence-based way to compare the pilot with its baseline. Outputs to HTML, PowerPoint, Markdown, Excel, and JSON.

It is deterministic and offline. No LLM, no model training, no data retention. Every number is computed by explicit, inspectable Python rules and is traceable to your input. The same file always produces the same result.

## Why it exists

Teams on ServiceNow, Jira Service Management, Freshservice, Zendesk, ManageEngine and others sit on rich ticket data but rarely turn it into a clear operational picture. This tool reads what you already export and gives you an honest current-state analysis plus where automation could realistically help, without sending your data to a model or making anything up.

## What "no AI BS" means here

- Core analysis never calls a language model.
- No training, no fine-tuning, no embeddings, no external API.
- Classification is a transparent keyword rule set (`sda/rules/themes.yaml`) you can read and edit.
- Nothing is persisted: files are analyzed in memory and forgotten. Reports contain aggregated analysis only, never raw ticket rows, so no PII is written to disk.
- If a field is missing, the tool says it is missing rather than inventing it. ROI is always a range with stated assumptions, never a fabricated single number.
- The output is written for humans reading it under deadline: no emojis, no filler, no marketing tone. Plain statements of what the data shows, what is assumed, and what to do next.

## Install

```bash
git clone <your-fork-url>
cd servicedesk-analyzer
pip install -e .            # core (CLI + report generation)
pip install -e ".[ui]"      # add the Streamlit web UI
pip install -e ".[dev]"     # add pytest
```

Python 3.9+.

## Use it: command line

```bash
sda examples/sample_servicedesk.csv --out reports
# or a subset of formats
sda tickets.xlsx --out reports --formats html,pptx
```

This writes `reports/<name>-analysis.{html,md,json,xlsx,pptx}`.

Compare a follow-up export with the baseline:

```bash
sda baseline.csv --compare-with follow-up.csv \
  --theme "Access & Authentication" \
  --assignment-group "L1" \
  --primary-metric median_mttr_hours \
  --minimum-improvement 10 \
  --out reports
```

The comparison reports one of four deterministic decisions: `widen`, `correct`,
`continue_measuring`, or `stop`. Before-and-after results are labeled as
associations and never presented as proof that the intervention caused a change.

## Use it: web UI

```bash
streamlit run sda/app.py
```

Drag and drop a CSV or XLSX, see the analysis, download any format. The file stays in memory on your machine.

## Use it: as a library

```python
from sda import analyze_file
from sda.report import write_all

analysis = analyze_file("tickets.csv")     # returns a plain dict
write_all(analysis, "reports")             # writes all five formats
```

## What it produces (deliverables)

A. Executive summary B. Data quality assessment C. Ticket volume D. MTTR analysis E. Theme and category breakdown F. Application landscape G. Top operational friction points H. AI automation opportunity backlog I. Agentic AI use case backlog J. Solution mapping K. 30-60-90 day roadmap L. Workshop questions M. Slide deck N. Final recommendations.

Plus an implementation and UAT package derived from the same data, for teams rolling out or migrating to a new ITSM/PM tool: O. UAT test plan (cases generated from the themes, priorities, and assignment groups observed in your tickets, each traceable to its data signal) P. Role and permission test matrix Q. Implementation RACI R. Go-live readiness checklist (including outbound-email safety when there is no test environment) S. 15-day testing phase plan with exit criteria. The Excel output includes execution columns (status, tester, date, defect ref) so the test plan works as a live tracking sheet.

## The implementation and UAT package: what it answers

This package exists for a situation that comes up constantly: a team (often led by someone new to project management) has to test and roll out an ITSM or project management tool on a short deadline, replacing an email/excel workflow, with no test environment and no service desk coordinator. The generator turns the questions that situation raises into concrete artifacts:

| If you are asking | The package gives you |
| --- | --- |
| What should I test? Where do I even start? | A UAT test plan generated from the request patterns actually observed in your data: lifecycle, SLA and escalation, roles, notifications, approvals, reporting, and migration cases, each with steps, expected result, and a Must/Should/Could gate (section O, `UATTestPlan` sheet) |
| Who can do what? Are the roles right? | A role and permission test matrix seeded from the assignment groups detected in your tickets, plus per-group queue-visibility test cases (section P, `RoleMatrix` sheet) |
| Who owns which activity during the rollout? | An implementation RACI covering configuration, test execution, defect fixing, migration, go/no-go, training, and hypercare (section Q, `RACI` sheet) |
| How do I know we are ready to go live? | A readiness checklist with hard Must gates, including sign-off on every Must test case and a rollback plan (section R, `Readiness` sheet) |
| There is no test environment. What if I email a client by mistake? | A Must gate to disable or redirect outbound email before any test run, a dedicated "no notifications leak outside the test group" test case, and a guard step prefixed to every notification case (sections O and R) |
| I have 15 days. How do I sequence this? | A 15-day phase plan: setup and smoke test, core workflows, roles and notifications, migration dry run, go/no-go, go-live preparation, each with exit criteria (section S, `PhasePlan` sheet) |
| The old data is messy. What about migration? | Migration test cases that reconcile record counts against the analyzed baseline, flag the duplicates found in your source data, and require fields that were missing historically to be captured going forward (section O) |

Two principles, both taken from how experienced practitioners actually run these projects:

1. Test whether the tool supports how the team actually works, not every feature. Cases are generated only from themes, priorities, statuses, and groups observed in your data, and every case cites the data signal that produced it.
2. Be overly careful with notifications when there is no sandbox. The email-safety gate is not optional; it is a Must item on the readiness checklist.

If your export is thin (no assignment groups, no timestamps), the package degrades honestly: you still get the baseline role cases, the notification safety cases, the RACI, and the phase plan, and the readiness checklist tells you which fields the new tool must start capturing.

## Supported inputs

Any CSV, TSV, or XLSX. Column headers are auto-detected against a large alias list, so exports from ServiceNow, Jira Service Management, Freshservice, Zendesk, ManageEngine and similar tools generally map without configuration. The detected and missing fields are listed in every report so you always know what the analysis is based on.

## How classification works

Each ticket's text (category, subcategory, application, description) is scored against keyword rules per theme. Highest score wins; no match goes to "Other / Unclear". Word-boundary matching avoids false hits. It is a bag-of-keywords classifier: fast, reproducible, and fully auditable. Edit `sda/rules/themes.yaml` to tune it for your environment, and `sda/rules/atomicwork.yaml` to tune the solution mapping and deflection ranges.

## Privacy and statelessness

- Core analysis runs entirely on your machine with no network calls.
- The uploaded/opened file is read into memory and discarded after analysis.
- Generated reports contain aggregates (theme counts, metrics, opportunity backlog), not raw ticket records.
- `.gitignore` excludes `data/`, `reports/`, and generated report files so customer data and outputs are never committed.

## Optional local AI assistance

The deterministic analyzer does not require or bundle a language model. The
optional `sda.ai` package can draft pilot wording through a user-managed
llama.cpp server on `localhost`. It sends only an explicit allowlist of
aggregate metrics. Raw ticket text, requester data, ticket identifiers, and
filenames remain outside the AI boundary. Metrics and decisions remain
deterministic and cannot be changed by AI output.

```python
from sda.ai import draft_pilot
from sda.ai.llamacpp import LlamaCppHTTPProvider

provider = LlamaCppHTTPProvider(
    "http://127.0.0.1:8080",
    model="Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M",
)
draft = draft_pilot(provider, analysis)
```

No model weights are included or downloaded. If the local server is absent,
the function returns an explicit `unavailable` result and deterministic
analysis continues unchanged. AI responses are labeled as advisory drafts and
must cite fields in the safe aggregate evidence packet.

### Model packaging decision

The default distribution does not bundle a TinyLM or other model weights. Model
artifacts are large, hardware-dependent, updated independently, and carry their
own provenance and redistribution obligations. Users explicitly choose and run
a local model instead.

The initial recommended CPU tier is Qwen2.5-1.5B-Instruct in an audited,
checksummed Q4 GGUF build through llama.cpp. The official Qwen model is Apache
2.0 licensed and has 1.54 billion parameters. The GGUF artifact must be pinned
and audited separately because community quantizations are separate artifacts.
SmolLM2-1.7B-Instruct is an Apache 2.0 alternative, but its official model card
describes it as primarily English and warns that its output may be inaccurate.
No performance claim is made because target-hardware benchmarks have not yet
been run.

Primary references:

- Qwen model card: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct
- SmolLM2 model card: https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct
- llama.cpp: https://github.com/ggml-org/llama.cpp

Executive summaries are deterministic because live testing showed that a 1.5B
model could confuse median and p90 values or turn planning estimates into
claims. AI is limited to human-reviewed pilot wording from an aggregate
allowlist. It cannot compute metrics, classify tickets, select the final pilot,
write the grounded executive summary, or issue the pilot decision.

See [Local AI](docs/local-ai.md) for setup, trust boundaries, and limitations.

## Iterative improvement workflow

1. Analyze one export and verify its data quality.
2. Use the transparent recommendation score to select one theme and team.
3. Record a pilot charter, primary metric, threshold, and required guardrails.
4. Run the pilot with human approval where required.
5. Upload the baseline and follow-up exports.
6. Review comparability, metric coverage, absolute change, and percentage change.
7. Widen, correct, continue measuring, or stop based on the configured evidence.

Optional feedback fields are detected through conservative exact header aliases:
reopen count, first-contact resolution, SLA breach, escalation, AI attempted,
AI accepted, human override, user-confirmed resolution, pilot id, and treatment
group. Missing or invalid values remain unknown and are never converted to false
or zero.

Aggregate scorecard history is opt-in. When enabled in the UI it uses a local
SQLite file and stores the pilot charter and aggregate comparison only. Source
ticket rows are never stored, and history can be deleted through the history API.

Detailed documentation:

- [Feature guide](docs/features.md)
- [Iterative improvement workflow](docs/iterative-improvement.md)
- [Local AI setup and boundaries](docs/local-ai.md)
- [Privacy and security](docs/privacy-security.md)
- [Analysis methodology](docs/methodology.md)

## Project layout

```
sda/
  ingest.py       load CSV/XLSX (in memory)
  schema.py       vendor-agnostic column detection
  integrity.py    step 1: data integrity
  normalize.py    step 2: clean analytical view
  themes.py       step 3: theme classification (rules)
  pareto.py       step 4: Pareto
  mttr.py         step 5: MTTR
  opportunities.py steps 6-9, 11: opportunity + Atomicwork map + agentic + ROI + confidence
  executive.py    step 10: exec summary, roadmap, questions
  uat.py          step 12: UAT test plan, role matrix, RACI, readiness, phase plan
  pilots.py       cohort, guardrail, charter, and deterministic recommendation
  metrics.py      measured outcome registry with numerator/denominator coverage
  iteration.py    baseline/follow-up comparison and decision engine
  history.py      optional aggregate-only SQLite iteration history
  analyze.py      orchestrator -> analysis dict
  cli.py          command line
  app.py          Streamlit UI
  ai/             optional aggregate-only local AI advisory layer
  rules/          editable YAML rule files
  report/         html, markdown, json, excel, pptx writers
tests/            pytest suite
examples/         deterministic sample data + generator
docs/methodology.md   the analysis methodology this implements
```

## Tests

```bash
python -m pytest -q
```

## License

MIT. See `LICENSE`.
