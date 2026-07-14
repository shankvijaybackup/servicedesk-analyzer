"""Unit tests for the deterministic pipeline."""

from __future__ import annotations

import pandas as pd
import pytest

from sda import analyze_dataframe
from sda.integrity import assess
from sda.mttr import build as mttr_build
from sda.normalize import normalize
from sda.pareto import pareto
from sda.schema import detect_schema
from sda.themes import OTHER, classify


def _df():
    return pd.DataFrame({
        "Number": [f"INC{i}" for i in range(10)],
        "Opened": ["2026-01-01 09:00:00"] * 10,
        "Resolved": ["2026-01-01 11:00:00"] * 10,
        "Priority": ["1 - Critical", "3 - Moderate"] * 5,
        "Category": ["Access", "Hardware"] * 5,
        "Assignment group": ["L1", "Endpoint"] * 5,
        "Short description": [
            "Password reset for the portal", "Laptop screen flickering",
            "Cannot log in, account locked", "Need a new monitor",
            "MFA not working", "Docking station broken",
            "Reset my password please", "Keyboard not working",
            "VPN access request", "Monitor replacement",
        ],
    })


def test_schema_detection_maps_vendor_headers():
    schema = detect_schema(_df())
    m = schema["mapping"]
    assert m["ticket_id"] == "Number"
    assert m["created"] == "Opened"
    assert m["resolved"] == "Resolved"
    assert m["priority"] == "Priority"
    assert m["assignment_group"] == "Assignment group"


def test_missing_fields_are_reported_not_invented():
    df = pd.DataFrame({"foo": [1, 2], "bar": [3, 4]})
    schema = detect_schema(df)
    integ = assess(df, schema)
    assert "created" in integ["fields_missing"]
    assert integ["mttr_available"] is False
    assert integ["quality_grade"] in {"Weak", "Poor", "Adequate"}


def test_mttr_derived_from_timestamps():
    df = _df()
    schema = detect_schema(df)
    norm = normalize(df, schema)
    assert norm["mttr_hours"].dropna().iloc[0] == pytest.approx(2.0, abs=0.01)
    res = mttr_build(classify(norm))
    assert res["available"] is True
    assert res["overall"]["median_hours"] == pytest.approx(2.0, abs=0.01)


def test_classification_is_deterministic_and_traceable():
    df = _df()
    schema = detect_schema(df)
    classified = classify(normalize(df, schema))
    themes = set(classified["_theme"])
    assert "Access & Authentication" in themes
    assert "Hardware & Devices" in themes
    # same input, same output
    again = classify(normalize(df, schema))
    assert list(classified["_theme"]) == list(again["_theme"])


def test_pareto_cumulative_reaches_100():
    s = pd.Series(["a", "a", "a", "b", "b", "c"])
    p = pareto(s)
    assert p["rows"][-1]["cumulative_pct"] == pytest.approx(100.0, abs=0.1)
    assert p["total"] == 6


def test_full_analysis_shape_and_no_data_retained():
    a = analyze_dataframe(_df(), source_name="unit")
    for key in ("meta", "data_quality", "volume", "mttr", "themes", "pareto",
                "opportunities", "executive"):
        assert key in a
    # ROI expressed as a range, never a single fabricated number
    rng = a["opportunities"]["roi_summary"]["est_total_deflectable_range"]
    assert len(rng) == 2 and rng[0] <= rng[1]
    # analysis dict carries no raw ticket text column
    assert "_text" not in a["themes"][0]


def test_unknown_text_goes_to_other():
    df = pd.DataFrame({
        "Number": ["1", "2"],
        "Short description": ["zxcvbnm qwerty", "asdf gibberish token"],
    })
    schema = detect_schema(df)
    classified = classify(normalize(df, schema))
    assert set(classified["_theme"]) == {OTHER}


def test_implementation_package_is_generated_and_traceable():
    a = analyze_dataframe(_df(), source_name="unit")
    impl = a["implementation"]
    tp = impl["test_plan"]
    assert tp["total_cases"] == len(tp["cases"]) > 0
    # every case has an id, steps, an expected result, and a data source
    for c in tp["cases"]:
        assert c["id"].startswith("TC-")
        assert c["steps"] and c["expected"] and c["source"]
        assert c["priority"] in {"Must", "Should", "Could"}
    # ids are unique and sequential
    ids = [c["id"] for c in tp["cases"]]
    assert len(ids) == len(set(ids))
    # detected assignment groups appear in the role matrix
    roles = {r["role"] for r in impl["role_matrix"]}
    assert "Agent: L1" in roles and "Agent: Endpoint" in roles
    # readiness always includes the email-safety gate
    assert any("Outbound email" in r["item"] for r in impl["readiness_checklist"])
    # phase plan covers 15 days ending in go-live prep
    assert impl["phase_plan_15_day"][-1]["days"] == "15"


def test_implementation_reflects_data_gaps():
    # no timestamps -> readiness must demand timestamp capture
    df = pd.DataFrame({
        "Number": [f"T{i}" for i in range(20)],
        "Short description": ["password reset request"] * 20,
    })
    a = analyze_dataframe(df, source_name="unit")
    items = [r["item"] for r in a["implementation"]["readiness_checklist"]]
    assert any("created and resolved timestamps" in i for i in items)


def test_implementation_is_deterministic():
    a1 = analyze_dataframe(_df(), source_name="unit")
    a2 = analyze_dataframe(_df(), source_name="unit")
    assert a1["implementation"] == a2["implementation"]
