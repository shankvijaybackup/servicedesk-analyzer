"""Streamlit UI: drag-drop a CSV/XLSX, view the analysis, download reports.

Run with:  streamlit run sda/app.py
Stateless: the uploaded file is analyzed in memory and never written to disk by
this app. Reports are offered as in-memory downloads only.
"""

from __future__ import annotations

import io

import streamlit as st

from .analyze import analyze_file
from .report.excel import write as _  # noqa: F401  (ensure optional dep present early)


def _to_bytes(analysis, kind: str) -> bytes:
    import tempfile
    from pathlib import Path
    from .report import write_all
    with tempfile.TemporaryDirectory() as tmp:
        paths = write_all(analysis, tmp, basename="analysis", formats=(kind,))
        return Path(paths[0]).read_bytes()


def main() -> None:
    st.set_page_config(page_title="Service Desk Analyzer", layout="wide")
    st.title("Service Desk Analyzer")
    st.caption("Deterministic and offline. No model, no training, no data retained. "
               "Your file is analyzed in memory and forgotten when you close the tab.")

    up = st.file_uploader("Drop a service desk export (CSV, TSV, or XLSX)",
                          type=["csv", "tsv", "xlsx", "xls"])
    if up is None:
        st.info("Export tickets from ServiceNow, Jira Service Management, Freshservice, "
                "Zendesk, or any tool, then drop the file here.")
        return

    with st.spinner("Analyzing (locally, no data leaves this machine)..."):
        analysis = analyze_file(io.BytesIO(up.getvalue()), filename=up.name)

    dq = analysis["data_quality"]
    roi = analysis["opportunities"]["roi_summary"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tickets", dq["total_records"])
    c2.metric("Data quality", f"{dq['quality_score']}/100", dq["quality_grade"])
    if analysis["mttr"].get("available"):
        c3.metric("Median MTTR", f"{analysis['mttr']['overall']['median_hours']}h")
    c4.metric("Est. deflectable",
              f"{roi['est_total_deflectable_pct_range'][0]}-{roi['est_total_deflectable_pct_range'][1]}%")

    if dq["fields_missing"]:
        st.warning("Missing fields (not invented): " + ", ".join(dq["fields_missing"]))

    st.subheader("Themes")
    st.dataframe([{k: t[k] for k in ("theme", "count", "pct", "mttr_median_hours", "confidence")}
                  for t in analysis["themes"]], use_container_width=True)

    st.subheader("Automation opportunity backlog")
    st.dataframe([{
        "theme": b["theme"], "type": b["primary_type"],
        "addressable": b["tickets_addressable"],
        "deflectable": f"{b['est_deflectable_tickets_range'][0]}-{b['est_deflectable_tickets_range'][1]}",
        "risk": b["risk_level"], "confidence": b["confidence"],
    } for b in analysis["opportunities"]["backlog"]], use_container_width=True)

    impl = analysis.get("implementation")
    if impl:
        tp = impl["test_plan"]
        st.subheader("UAT test plan")
        st.caption(f"{tp['total_cases']} cases (Must {tp['must_count']}, "
                   f"Should {tp['should_count']}, Could {tp['could_count']}). "
                   + tp["coverage_note"])
        st.dataframe([{k: c[k] for k in ("id", "area", "title", "role", "priority", "source")}
                      for c in tp["cases"]], use_container_width=True)
        with st.expander("Go-live readiness checklist"):
            st.dataframe([{k: r[k] for k in ("gate", "category", "item", "source")}
                          for r in impl["readiness_checklist"]], use_container_width=True)
        with st.expander("15-day testing phase plan"):
            st.dataframe([{"days": p["days"], "phase": p["phase"],
                           "exit_criteria": p["exit_criteria"]}
                          for p in impl["phase_plan_15_day"]], use_container_width=True)

    st.subheader("Download reports")
    d1, d2, d3, d4, d5 = st.columns(5)
    base = up.name.rsplit(".", 1)[0] + "-analysis"
    d1.download_button("HTML", _to_bytes(analysis, "html"), f"{base}.html", "text/html")
    d2.download_button("Markdown", _to_bytes(analysis, "md"), f"{base}.md", "text/markdown")
    d3.download_button("JSON", _to_bytes(analysis, "json"), f"{base}.json", "application/json")
    d4.download_button("Excel", _to_bytes(analysis, "xlsx"), f"{base}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    d5.download_button("PowerPoint", _to_bytes(analysis, "pptx"), f"{base}.pptx",
                       "application/vnd.openxmlformats-officedocument.presentationml.presentation")


if __name__ == "__main__":
    main()
