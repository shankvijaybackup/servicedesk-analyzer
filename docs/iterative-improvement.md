# Iterative Improvement Workflow

This workflow implements a small-change, measure, decide, repeat operating
model for service-desk improvement.

## 1. Establish the baseline

Upload the pre-pilot export. Confirm data quality before selecting a metric.
Resolution-time outcomes require valid resolution data. Reopen, FCR, SLA, and
AI-assistance outcomes require their corresponding optional fields.

## 2. Select one cohort

Limit the pilot to one useful operational slice, such as:

- Access and authentication tickets
- The L1 queue
- One application
- One department
- One priority group

The same cohort definition is applied to baseline and follow-up exports.

## 3. Define the pilot charter

The charter records:

- Pilot ID and name
- Intervention
- Cohort
- Primary metric
- Minimum improvement percentage
- Required guardrails
- Minimum cohort size
- Human-approval requirement
- Rollback condition

## 4. Run the pilot

Run the intervention only inside the selected cohort. Where automation can
change systems or user access, preserve the configured human-approval gate.

## 5. Measure the follow-up

Upload the post-pilot export. Each metric includes:

- Availability status
- Value
- Numerator where applicable
- Denominator
- Coverage percentage
- Reason when unavailable

Missing data never becomes a successful zero value.

## 6. Review comparability

The analyzer checks:

- Minimum sample size
- Ticket IDs appearing in both periods
- Priority-mix distance
- MTTR-coverage difference

A before-and-after comparison is observational. Staffing, seasonality, ticket
mix, and unrelated process changes may influence the result.

## 7. Apply the decision

Decision precedence is deterministic:

1. Insufficient evidence means `continue_measuring`.
2. A failed required guardrail means `stop`.
3. An unavailable required guardrail means `continue_measuring`.
4. A passed primary threshold with passing guardrails means `widen`.
5. Otherwise the result is `correct`.

The decision engine never calls local AI.

## CLI example

```bash
sda baseline.csv --compare-with follow-up.csv \
  --theme "Access & Authentication" \
  --assignment-group "L1" \
  --primary-metric median_mttr_hours \
  --minimum-improvement 10 \
  --minimum-cohort-size 20 \
  --out reports
```
