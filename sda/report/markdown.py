"""Markdown report covering deliverables A-N."""

from __future__ import annotations

from pathlib import Path


def write(a: dict, path) -> str:
    L: list[str] = []
    w = L.append
    meta, dq, ex = a["meta"], a["data_quality"], a["executive"]
    opp = a["opportunities"]

    w(f"# Service Desk Analysis: {meta['source_name']}")
    w("")
    w(f"_Generated {meta['generated_at']} by {meta['tool']} v{meta['version']}. "
      f"Deterministic, offline, no model used._")
    w("")

    # A. Executive Summary
    w("## A. Executive Summary")
    w("")
    for line in ex["current_state_summary"]:
        w(f"- {line}")
    w("")
    w("**Top findings**")
    w("")
    for f in ex["top_findings"]:
        w(f"- ({f['confidence']}) {f['finding']}")
    w("")

    # B. Data Quality
    w("## B. Data Quality Assessment")
    w("")
    w(f"- Records: {dq['total_records']}")
    w(f"- Quality: {dq['quality_grade']} ({dq['quality_score']}/100)")
    w(f"- Fields detected: {', '.join(dq['fields_detected']) or 'none'}")
    w(f"- Fields missing: {', '.join(dq['fields_missing']) or 'none'}")
    w(f"- Duplicates: {dq['duplicate_records']} (by {dq['duplicate_basis']})")
    if dq.get("date_range"):
        d = dq["date_range"]
        w(f"- Date range: {d['start']} to {d['end']} ({d['days']} days)")
    w(f"- MTTR: {'available (' + str(dq['mttr_source']) + ')' if dq['mttr_available'] else 'not available'}")
    if dq["quality_reasons"]:
        w("- Score deductions: " + "; ".join(dq["quality_reasons"]))
    w("")

    # C. Volume
    w("## C. Ticket Volume Analysis")
    w("")
    vol = a["volume"]
    w(f"- Total: {vol['total']}")
    if "resolved" in vol:
        w(f"- Resolved/closed: {vol['resolved']}; open backlog: {vol['open_backlog']}")
    for key, title in [("by_type", "By type"), ("by_priority", "By priority"),
                       ("by_status", "By status")]:
        if key in vol:
            w(f"- {title}: " + ", ".join(f"{r['value']} {r['count']} ({r['pct']}%)"
                                         for r in vol[key][:8]))
    w("")

    # D. MTTR
    w("## D. MTTR Analysis")
    w("")
    m = a["mttr"]
    if m.get("available"):
        o = m["overall"]
        w(f"- Overall: median {o['median_hours']}h, mean {o['mean_hours']}h, p90 {o['p90_hours']}h (n={o['n']})")
        if m.get("slowest"):
            w("- Slowest themes: " + ", ".join(f"{r['value']} {r['median_hours']}h"
                                                for r in m["slowest"]))
        if m.get("fastest"):
            w("- Fastest themes: " + ", ".join(f"{r['value']} {r['median_hours']}h"
                                                for r in m["fastest"]))
    else:
        w(f"- {m.get('note', 'MTTR not available.')}")
    w("")

    # E. Themes
    w("## E. Theme and Category Breakdown")
    w("")
    w("| Theme | Count | % | MTTR med (h) | Confidence |")
    w("| --- | ---: | ---: | ---: | --- |")
    for t in a["themes"]:
        w(f"| {t['theme']} | {t['count']} | {t['pct']} | "
          f"{t['mttr_median_hours'] if t['mttr_median_hours'] is not None else '-'} | {t['confidence']} |")
    w("")

    # F. Applications
    w("## F. Application Landscape")
    w("")
    al = a["application_landscape"]
    if al and al.get("available"):
        w(f"- Distinct applications: {al['distinct_applications']}")
        for r in al["top"][:10]:
            w(f"  - {r['application']}: {r['count']} ({r['pct']}%)")
    else:
        w("- No application/CI field detected in the data.")
    w("")

    # G. Friction
    w("## G. Top Operational Friction Points")
    w("")
    for fp in ex["friction_points"]:
        w(f"- {fp['area']}: {fp['count']} tickets, median {fp['mttr_median_hours']}h, "
          f"est effort {fp['est_effort_hours']}h ({fp['signal']})")
    w("")

    # H. Automation backlog
    w("## H. AI Automation Opportunity Backlog")
    w("")
    w("| Theme | Type | Addressable | Est. deflectable | MTTR impact | Complexity | Risk | Confidence |")
    w("| --- | --- | ---: | --- | --- | --- | --- | --- |")
    for b in opp["backlog"]:
        rng = b["est_deflectable_tickets_range"]
        w(f"| {b['theme']} | {b['primary_type']} | {b['tickets_addressable']} | "
          f"{rng[0]}-{rng[1]} ({b['deflection_range_pct'][0]}-{b['deflection_range_pct'][1]}%) | "
          f"{b['mttr_reduction_potential']} | {b['implementation_complexity']} | "
          f"{b['risk_level']} | {b['confidence']} |")
    w("")
    r = opp["roi_summary"]
    w(f"**ROI (planning estimate):** {r['est_total_deflectable_range'][0]}-"
      f"{r['est_total_deflectable_range'][1]} tickets "
      f"({r['est_total_deflectable_pct_range'][0]}-{r['est_total_deflectable_pct_range'][1]}% of total).")
    w("")
    for asm in r["assumptions"]:
        w(f"- Assumption: {asm}")
    w("")

    # I. Agentic
    w("## I. Agentic AI Use Case Backlog")
    w("")
    if opp["agentic_backlog"]:
        for g in opp["agentic_backlog"]:
            w(f"### {g['theme']} ({g['tickets_addressable']} tickets, confidence {g['confidence']})")
            w(f"- Trigger: {g['trigger']}")
            w(f"- System of action: {g['system_of_action']}")
            w(f"- Permissions: {g['required_permissions']}")
            w(f"- Steps: {', '.join(g['workflow_steps'])}")
            w(f"- Feasibility: {g['automation_feasibility']}")
            w(f"- Risk: {g['risk_level']}")
            w(f"- Fallback: {g['fallback_path']}")
            w(f"- Human approval: {g['human_approval_required']}")
            w(f"- Expected impact: {g['expected_impact']}")
            w("")
    else:
        w("- No agentic use cases met the volume threshold in this dataset.")
        w("")

    # J. Solution mapping
    w("## J. Atomicwork Solution Mapping")
    w("")
    for s in opp["solution_map"]:
        if s["capabilities"]:
            w(f"- {s['theme']} ({s['tickets']}): {', '.join(s['capabilities'])}")
    w("")

    # K. Roadmap
    w("## K. 30-60-90 Day Roadmap")
    w("")
    for key, title in [("days_0_30", "Days 0-30"), ("days_30_60", "Days 30-60"),
                       ("days_60_90", "Days 60-90")]:
        r = ex["roadmap_30_60_90"][key]
        w(f"**{title}: {r['focus']}**")
        if r["themes"]:
            w(f"- Themes: {', '.join(r['themes'])}")
        for act in r["actions"]:
            w(f"- {act}")
        w("")

    # L. Workshop questions
    w("## L. Workshop Questions for Customer")
    w("")
    for q in ex["workshop_questions"]:
        w(f"- {q}")
    w("")

    # M. Slide outline
    w("## M. PowerPoint Slide Outline")
    w("")
    for i, s in enumerate(_slide_outline(a), start=1):
        w(f"{i}. {s}")
    w("")

    # N. Final recommendations
    w("## N. Final Recommendations")
    w("")
    for rec in ex["final_recommendations"]:
        w(f"- {rec}")
    w("")

    iteration = a.get("iteration")
    if iteration:
        w("## Iterative Improvement Scorecard")
        w("")
        w(f"- Pilot: {iteration['pilot']['name']}")
        w(f"- Cohort sizes: baseline {iteration['baseline']['cohort_size']}; "
          f"follow-up {iteration['follow_up']['cohort_size']}")
        w(f"- Comparability: {iteration['comparability']['status']}")
        w(f"- Decision: **{iteration['decision']['code'].replace('_', ' ').title()}**")
        for reason in iteration["decision"]["reasons"]:
            w(f"- Evidence: {reason}")
        w(f"- Method note: {iteration['causality_note']}")
        w("")
        w("| Metric | Baseline | Follow-up | Improvement % |")
        w("| --- | ---: | ---: | ---: |")
        for metric, change in iteration["changes"].items():
            before = iteration["baseline"]["metrics"][metric]["value"]
            after = iteration["follow_up"]["metrics"][metric]["value"]
            improvement = change.get("improvement_pct")
            w(f"| {metric} | {before if before is not None else '-'} | "
              f"{after if after is not None else '-'} | "
              f"{improvement if improvement is not None else '-'} |")
        w("")

    # O-S. Implementation and UAT package
    impl = a.get("implementation")
    if impl:
        tp = impl["test_plan"]
        w("## O. UAT Test Plan")
        w("")
        w(f"_{tp['coverage_note']}_")
        w("")
        w(f"- Total cases: {tp['total_cases']} "
          f"(Must {tp['must_count']}, Should {tp['should_count']}, Could {tp['could_count']})")
        w("")
        w("| ID | Area | Test case | Role | Priority | Derived from |")
        w("| --- | --- | --- | --- | --- | --- |")
        for c in tp["cases"]:
            w(f"| {c['id']} | {c['area']} | {c['title']} | {c['role']} | "
              f"{c['priority']} | {c['source']} |")
        w("")
        for c in tp["cases"]:
            w(f"### {c['id']}: {c['title']} ({c['priority']})")
            w(f"- Role: {c['role']}")
            for i, s in enumerate(c["steps"], start=1):
                w(f"- Step {i}: {s}")
            w(f"- Expected: {c['expected']}")
            w("")

        w("## P. Role and Permission Test Matrix")
        w("")
        w("| Role | Can | Cannot | Derived from |")
        w("| --- | --- | --- | --- |")
        for r in impl["role_matrix"]:
            w(f"| {r['role']} | {'; '.join(r['can'])} | {'; '.join(r['cannot'])} | "
              f"{r['derived_from']} |")
        w("")

        w("## Q. Implementation RACI")
        w("")
        w("| Activity | Responsible | Accountable | Consulted | Informed |")
        w("| --- | --- | --- | --- | --- |")
        for r in impl["raci"]:
            w(f"| {r['activity']} | {r['responsible']} | {r['accountable']} | "
              f"{r['consulted']} | {r['informed']} |")
        w("")

        w("## R. Go-Live Readiness Checklist")
        w("")
        w("| Gate | Category | Item | Derived from |")
        w("| --- | --- | --- | --- |")
        for r in impl["readiness_checklist"]:
            w(f"| {r['gate']} | {r['category']} | {r['item']} | {r['source']} |")
        w("")

        w("## S. 15-Day Testing Phase Plan")
        w("")
        for ph in impl["phase_plan_15_day"]:
            w(f"**Days {ph['days']}: {ph['phase']}**")
            for act in ph["activities"]:
                w(f"- {act}")
            w(f"- Exit criteria: {ph['exit_criteria']}")
            w("")
        w("**Testing assumptions**")
        w("")
        for asm in impl["assumptions"]:
            w(f"- {asm}")
        w("")

    w("---")
    w(f"_{meta['stateless_note']}_")

    Path(path).write_text("\n".join(L), encoding="utf-8")
    return str(path)


def _slide_outline(a: dict) -> list[str]:
    return [
        f"Title: Service Desk Analysis, {a['meta']['source_name']}",
        "Executive summary and headline numbers",
        "Data quality and confidence",
        "Ticket volume and mix",
        "MTTR: slowest and fastest areas",
        "Theme breakdown (Pareto: the vital few)",
        "Application landscape",
        "Top operational friction points",
        "AI automation opportunity backlog",
        "Agentic AI use cases (with guardrails)",
        "Atomicwork solution mapping",
        "30-60-90 day roadmap",
        "ROI ranges and assumptions",
        "Risks, assumptions, and workshop questions",
    ]
