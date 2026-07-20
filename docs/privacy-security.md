# Privacy and Security

## Default data handling

- Analysis runs locally.
- Source files are read into memory.
- Raw ticket rows are not written to reports.
- Raw descriptions, requester values, and ticket IDs are excluded from outputs.
- Temporary report files are deleted immediately after download generation.
- No history is retained unless the user explicitly enables aggregate history.

## Export protection

HTML, Markdown, JSON, Excel, and PowerPoint reports contain aggregate analysis.
Regression tests use private canary values to verify that raw descriptions do
not appear in any format.

Excel cells beginning with `=`, `+`, `-`, or `@` are forced to literal text to
prevent formula injection. Numeric negative values remain numeric.

## Local AI isolation

The llama.cpp adapter accepts only loopback HTTP endpoints. The model receives
an explicit aggregate allowlist rather than a recursively redacted copy of the
analysis. New analysis fields cannot reach the model until deliberately added
to that allowlist.

AI responses must be schema-valid and cite approved evidence paths. Failure is
reported as unavailable and never changes deterministic output.

## Optional history

SQLite history is disabled by default. When enabled it stores:

- Pilot charter
- Aggregate baseline metrics
- Aggregate follow-up metrics
- Comparability result
- Decision and reasons

It does not store source ticket rows or descriptions. `delete_all()` removes
all locally retained scorecards.

## Known boundary

Aggregated labels such as application, category, assignment group, and source
filename may still be operationally sensitive. Treat generated reports as
internal artifacts unless reviewed for external sharing.
