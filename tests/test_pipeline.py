"""Unit tests for the deterministic pipeline."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from sda import analyze_dataframe
from sda.integrity import assess
from sda.feedback import feedback_parse_quality
from sda.mttr import build as mttr_build
from sda.normalize import normalize
from sda.pareto import pareto
from sda.report.json_out import write as write_json
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


def test_feedback_fields_use_exact_aliases_and_typed_normalization():
    df = pd.DataFrame({
        "Reopen_Count": [0, "2", None],
        "First Contact Resolved": ["yes", "false", None],
        "AI Attempted": [1, "no", ""],
        "Pilot ID": ["pilot-1", "pilot-1", None],
        "Treatment Group": ["treatment", "control", None],
    })
    schema = detect_schema(df)
    norm = normalize(df, schema)

    assert schema["mapping"]["reopen_count"] == "Reopen_Count"
    assert str(norm["reopen_count"].dtype) == "Int64"
    assert norm["reopen_count"].tolist() == [0, 2, pd.NA]
    assert str(norm["first_contact_resolved"].dtype) == "boolean"
    assert norm["first_contact_resolved"].iloc[:2].tolist() == [True, False]
    assert pd.isna(norm["first_contact_resolved"].iloc[2])
    assert norm["ai_attempted"].iloc[:2].tolist() == [True, False]
    assert pd.isna(norm["ai_attempted"].iloc[2])
    assert str(norm["pilot_id"].dtype) == "string"


def test_feedback_invalid_values_are_unavailable_not_false():
    df = pd.DataFrame({"SLA Breached": ["yes", "unknown", "", None, "no"]})
    schema = detect_schema(df)
    norm = normalize(df, schema)
    quality = feedback_parse_quality(df, schema)["sla_breached"]

    assert norm["sla_breached"].iloc[[0, 4]].tolist() == [True, False]
    assert norm["sla_breached"].iloc[1:4].isna().all()
    assert quality == {
        "available": True,
        "source_column": "SLA Breached",
        "supplied_count": 3,
        "parsed_count": 2,
        "invalid_count": 1,
    }


def test_feedback_detection_does_not_fuzzily_map_unrelated_columns():
    schema = detect_schema(pd.DataFrame({
        "AI category": ["automation"],
        "Escalated owner": ["team-a"],
        "Pilot identifier notes": ["draft"],
    }))

    assert schema["mapping"]["ai_attempted"] is None
    assert schema["mapping"]["ai_accepted"] is None
    assert schema["mapping"]["escalated"] is None
    assert schema["mapping"]["pilot_id"] is None
    assert "ai_attempted" not in schema["missing"]
    assert "ai_attempted" in schema["optional_missing"]


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


def test_analysis_and_json_never_emit_raw_ticket_descriptions(tmp_path):
    descriptions = [
        "PRIVATE-CANARY-ALPHA password reset for person@example.test",
        "PRIVATE-CANARY-BRAVO laptop assigned to employee 555-0102",
    ]
    df = pd.DataFrame({
        "Number": ["PRIVATE-ID-001", "PRIVATE-ID-002"],
        "Opened": ["2026-01-01 09:00:00"] * 2,
        "Resolved": ["2026-01-01 11:00:00"] * 2,
        "Category": ["Access", "Hardware"],
        "Short description": descriptions,
    })

    analysis = analyze_dataframe(df, source_name="privacy-test.csv")
    serialized_analysis = json.dumps(analysis, default=str)

    output = tmp_path / "analysis.json"
    write_json(analysis, output)
    serialized_report = output.read_text(encoding="utf-8")

    for private_value in [*descriptions, "PRIVATE-ID-001", "PRIVATE-ID-002"]:
        assert private_value not in serialized_analysis
        assert private_value not in serialized_report

    assert all("examples" not in theme for theme in analysis["themes"])
    assert sum(theme["count"] for theme in analysis["themes"]) == len(df)


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
