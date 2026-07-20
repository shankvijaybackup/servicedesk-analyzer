"""Streamlit UI: drag-drop a CSV/XLSX, view the analysis, download reports.

Run with:  streamlit run sda/app.py
Stateless by default. Report generation uses a short-lived temporary directory
that is deleted immediately. Aggregate history is written only when opted in.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Streamlit executes this file as a standalone script and may add only the
# ``sda`` directory, not its parent, to sys.path. Add the repository root so
# package-qualified imports work both from a source checkout and an installed
# package. This must run before importing any ``sda`` modules.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from sda.analyze import analyze_file
from sda.ingest import read_table
from sda.iteration import compare_dataframes
from sda.pilots import CohortSpec, Guardrail, PilotCharter
from sda.report.excel import write as _  # noqa: F401  (ensure optional dep present early)


def _to_bytes(analysis, kind: str) -> bytes:
    import tempfile
    from pathlib import Path
    from sda.report import write_all
    with tempfile.TemporaryDirectory() as tmp:
        paths = write_all(analysis, tmp, basename="analysis", formats=(kind,))
        return Path(paths[0]).read_bytes()


def _render_analysis(analysis: dict) -> None:
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

    rec = analysis.get("recommended_pilot")
    if rec:
        st.subheader("Recommended first pilot")
        st.write(f"**{rec['theme']}** using {rec['intervention_type']}.")
        st.caption(f"Transparent score {rec['score']}/100. {rec['reason']}")
        st.json(rec["score_components"], expanded=False)

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

def _downloads(analysis: dict, filename: str) -> None:
    st.subheader("Download reports")
    d1, d2, d3, d4, d5 = st.columns(5)
    base = filename.rsplit(".", 1)[0] + "-analysis"
    d1.download_button("HTML", _to_bytes(analysis, "html"), f"{base}.html", "text/html")
    d2.download_button("Markdown", _to_bytes(analysis, "md"), f"{base}.md", "text/markdown")
    d3.download_button("JSON", _to_bytes(analysis, "json"), f"{base}.json", "application/json")
    d4.download_button("Excel", _to_bytes(analysis, "xlsx"), f"{base}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    d5.download_button("PowerPoint", _to_bytes(analysis, "pptx"), f"{base}.pptx",
                       "application/vnd.openxmlformats-officedocument.presentationml.presentation")


def _render_iteration(result: dict) -> None:
    code = result["decision"]["code"].replace("_", " ").title()
    st.subheader(f"Decision: {code}")
    st.caption(result["causality_note"])
    for reason in result["decision"]["reasons"]:
        st.write(f"- {reason}")
    rows = []
    for metric, change in result["changes"].items():
        rows.append({
            "metric": metric,
            "baseline": result["baseline"]["metrics"][metric]["value"],
            "follow_up": result["follow_up"]["metrics"][metric]["value"],
            "improvement_pct": change.get("improvement_pct"),
            "status": change["status"],
        })
    st.dataframe(rows, use_container_width=True)
    if result["comparability"]["blockers"]:
        st.error(" ".join(result["comparability"]["blockers"]))
    if result["comparability"]["warnings"]:
        st.warning(" ".join(result["comparability"]["warnings"]))


def main() -> None:
    st.set_page_config(page_title="Service Desk Analyzer", layout="wide")
    st.title("Service Desk Analyzer")
    st.caption("Deterministic core, local processing, and no data retention. Optional AI is "
               "advisory only and receives aggregate evidence.")

    analyze_tab, measure_tab, ai_tab = st.tabs(["Analyze", "Measure progress", "Local AI"])

    with analyze_tab:
        up = st.file_uploader("Drop a service desk export (CSV, TSV, or XLSX)",
                              type=["csv", "tsv", "xlsx", "xls"], key="analyze")
        if up is None:
            st.info("Upload one export to understand the current state and select a pilot.")
        else:
            with st.spinner("Analyzing locally..."):
                analysis = analyze_file(io.BytesIO(up.getvalue()), filename=up.name)
            _render_analysis(analysis)
            _downloads(analysis, up.name)

    with measure_tab:
        st.write("Compare one tightly scoped pilot against its baseline.")
        baseline_up = st.file_uploader("Baseline export", type=["csv", "tsv", "xlsx", "xls"],
                                       key="baseline")
        follow_up = st.file_uploader("Follow-up export", type=["csv", "tsv", "xlsx", "xls"],
                                     key="followup")
        if baseline_up and follow_up:
            baseline_df = read_table(io.BytesIO(baseline_up.getvalue()), filename=baseline_up.name)
            follow_df = read_table(io.BytesIO(follow_up.getvalue()), filename=follow_up.name)
            baseline_analysis = analyze_file(io.BytesIO(baseline_up.getvalue()), filename=baseline_up.name)
            themes = [t["theme"] for t in baseline_analysis["themes"]]
            default_theme = (baseline_analysis.get("recommended_pilot") or {}).get("theme")
            selected_theme = st.selectbox("Pilot theme", ["All themes"] + themes,
                                          index=(themes.index(default_theme) + 1
                                                 if default_theme in themes else 0))
            group = st.text_input("Assignment group or queue (optional)")
            pilot_name = st.text_input("Pilot name", "Service desk improvement pilot")
            intervention = st.text_input("Intervention", "Human-approved AI resolution draft")
            metric = st.selectbox("Primary success metric", [
                "median_mttr_hours", "p90_mttr_hours", "reopen_rate",
                "first_contact_resolution_rate", "sla_breach_rate", "escalation_rate",
                "human_override_rate", "confirmed_resolution_rate",
            ])
            threshold = st.number_input("Minimum improvement percent", 0.0, 100.0, 10.0)
            minimum_n = st.number_input("Minimum tickets per cohort", 1, 100000, 20)
            require_reopen = st.checkbox("Require reopen rate as a guardrail")
            save_history = st.checkbox("Save aggregate scorecard history locally")
            history_path = st.text_input("History database path", "~/.sda/history.db",
                                         disabled=not save_history)
            if st.button("Measure and decide", type="primary"):
                guardrails = (Guardrail("reopen_rate", 0.0, True),) if require_reopen else ()
                charter = PilotCharter(
                    pilot_id="ui-pilot", name=pilot_name, intervention=intervention,
                    cohort=CohortSpec(
                        themes=(selected_theme,) if selected_theme != "All themes" else (),
                        assignment_groups=(group.strip(),) if group.strip() else (),
                    ),
                    primary_metric=metric, minimum_improvement_pct=float(threshold),
                    guardrails=guardrails, minimum_cohort_size=int(minimum_n),
                )
                result = compare_dataframes(
                    baseline_df, follow_df, charter,
                    baseline_name=baseline_up.name, follow_up_name=follow_up.name,
                )
                follow_analysis = analyze_file(io.BytesIO(follow_up.getvalue()), filename=follow_up.name)
                follow_analysis["iteration"] = result
                if save_history:
                    from sda.history import SQLiteHistoryStore
                    SQLiteHistoryStore(history_path).save(result)
                    st.success("Aggregate scorecard saved. No source ticket rows were stored.")
                _render_iteration(result)
                _downloads(follow_analysis, follow_up.name.rsplit(".", 1)[0] + "-comparison.csv")
        else:
            st.info("Upload both exports. No comparison is made until both are present.")

    with ai_tab:
        st.write("Grounded executive summary plus optional local-AI pilot drafting.")
        ai_up = st.file_uploader("Export for advisory narrative", type=["csv", "tsv", "xlsx", "xls"],
                                 key="ai")
        endpoint = st.text_input("Local llama.cpp endpoint", "http://127.0.0.1:8080")
        model = st.text_input(
            "Server model identifier",
            "Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M",
            help="This identifies the model already loaded by the local llama.cpp server.",
        )
        if ai_up and st.button("Generate grounded executive summary"):
            from sda.narrative import build_executive_narrative
            analysis = analyze_file(io.BytesIO(ai_up.getvalue()), filename=ai_up.name)
            draft = build_executive_narrative(analysis)
            st.info(draft["label"])
            content = draft["content"]
            st.subheader(content["title"])
            for paragraph in content["paragraphs"]:
                st.write(paragraph)
            st.caption("Evidence: " + ", ".join(content["citations"]))

        if ai_up and st.button("Draft pilot wording with local AI"):
            from sda.ai import draft_pilot
            from sda.ai.llamacpp import LlamaCppHTTPProvider
            analysis = analyze_file(io.BytesIO(ai_up.getvalue()), filename=ai_up.name)
            try:
                provider = LlamaCppHTTPProvider(endpoint, model=model)
                draft = draft_pilot(provider, analysis)
            except ValueError as error:
                draft = {"status": "unavailable", "reason": str(error)}
            if draft["status"] == "available":
                st.warning(draft["label"])
                st.json(draft["content"])
            else:
                st.info(draft.get("reason", "Local AI is unavailable."))


if __name__ == "__main__":
    main()
