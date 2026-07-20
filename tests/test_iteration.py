from __future__ import annotations

import pandas as pd

from sda import CohortSpec, Guardrail, PilotCharter, compare_dataframes
from sda.pilots import recommend_pilot
from sda import analyze_dataframe


def _cohort(mttr_hours, *, priorities=None, reopened=None):
    n = len(mttr_hours)
    data = {
        "Number": [f"T-{mttr_hours[0]}-{i}" for i in range(n)],
        "Opened": ["2026-01-01 09:00:00"] * n,
        "Resolution time hours": mttr_hours,
        "Status": ["Resolved"] * n,
        "Priority": priorities or ["P3"] * n,
        "Assignment group": ["L1"] * n,
        "Short description": ["password reset account locked"] * n,
    }
    if reopened is not None:
        data["Reopen count"] = reopened
    return pd.DataFrame(data)


def _charter(**kwargs):
    values = dict(
        pilot_id="P-1", name="Access pilot", intervention="Draft resolution",
        cohort=CohortSpec(themes=("Access & Authentication",), assignment_groups=("L1",)),
        primary_metric="median_mttr_hours", minimum_improvement_pct=20,
        minimum_cohort_size=5,
    )
    values.update(kwargs)
    return PilotCharter(**values)


def test_known_improvement_widens_and_preserves_evidence():
    result = compare_dataframes(_cohort([10] * 10), _cohort([6] * 10), _charter())
    assert result["decision"]["code"] == "widen"
    assert result["changes"]["median_mttr_hours"]["improvement_pct"] == 40.0
    assert result["baseline"]["metrics"]["median_mttr_hours"]["denominator"] == 10
    assert "does not prove causation" in result["causality_note"]


def test_identical_cohorts_do_not_fabricate_success():
    b = _cohort([10] * 10)
    f = _cohort([10] * 10)
    f["Number"] = [f"F-{i}" for i in range(10)]
    result = compare_dataframes(b, f, _charter())
    assert result["changes"]["median_mttr_hours"]["improvement_pct"] == 0
    assert result["decision"]["code"] == "correct"


def test_overlapping_ids_and_small_samples_continue_measuring():
    result = compare_dataframes(_cohort([10] * 3), _cohort([5] * 3), _charter())
    assert result["comparability"]["status"] == "insufficient"
    assert result["decision"]["code"] == "continue_measuring"


def test_missing_required_guardrail_blocks_widening():
    charter = _charter(guardrails=(Guardrail("reopen_rate", 0, True),))
    result = compare_dataframes(_cohort([10] * 10), _cohort([5] * 10), charter)
    assert result["decision"]["code"] == "continue_measuring"
    assert result["decision"]["guardrails"][0]["status"] == "not_measurable"


def test_failed_guardrail_stops_pilot():
    charter = _charter(guardrails=(Guardrail("reopen_rate", 0, True),))
    b = _cohort([10] * 10, reopened=[0] * 9 + [1])
    f = _cohort([5] * 10, reopened=[0] * 5 + [1] * 5)
    result = compare_dataframes(b, f, charter)
    assert result["decision"]["code"] == "stop"


def test_zero_baseline_percent_change_is_not_invented():
    charter = _charter(primary_metric="open_backlog_rate")
    b = _cohort([10] * 10)
    f = _cohort([5] * 10)
    f["Status"] = ["Open"] * 10
    result = compare_dataframes(b, f, charter)
    assert result["changes"]["open_backlog_rate"]["status"] == "partially_measurable"
    assert result["decision"]["code"] == "continue_measuring"


def test_recommendation_exposes_score_components():
    analysis = analyze_dataframe(_cohort([5] * 40))
    rec = recommend_pilot(analysis)
    assert rec is not None
    assert set(rec["score_components"]) == {"volume_share", "confidence", "feasibility", "safety"}

