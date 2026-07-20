"""Evidence-grounded executive narrative with no generative model."""

from __future__ import annotations


def build_executive_narrative(analysis: dict) -> dict:
    dq = analysis["data_quality"]
    mttr = analysis["mttr"]
    themes = analysis["themes"][:3]
    roi = analysis["opportunities"]["roi_summary"]

    observed = (f"The analysis covers {dq['total_records']} tickets. Data quality is "
                f"{dq['quality_grade']} ({dq['quality_score']}/100).")
    if mttr.get("available"):
        overall = mttr["overall"]
        observed += (f" Median resolution time is {overall['median_hours']} hours and the "
                     f"90th percentile is {overall['p90_hours']} hours, based on "
                     f"{overall['n']} tickets with valid resolution data.")
    else:
        observed += " Resolution-time metrics are not measurable from the supplied fields."

    if themes:
        theme_text = ", ".join(
            f"{item['theme']} ({item['count']} tickets, {item['pct']}%)" for item in themes
        )
        priorities = f"The largest observed themes are {theme_text}."
    else:
        priorities = "No classified themes were available."
    low, high = roi["est_total_deflectable_range"]
    low_pct, high_pct = roi["est_total_deflectable_pct_range"]
    priorities += (f" Rule-based planning estimates identify {low} to {high} potentially "
                   f"deflectable tickets ({low_pct}% to {high_pct}%). These are estimates "
                   f"to validate through a scoped pilot, not measured savings.")

    return {
        "status": "available",
        "label": "Deterministic evidence narrative. No model generated or changed these facts.",
        "generation_method": "deterministic",
        "content": {
            "title": "Service Desk Executive Summary",
            "paragraphs": [observed, priorities],
            "citations": ["data_quality", "mttr", "themes", "opportunities"],
        },
    }
