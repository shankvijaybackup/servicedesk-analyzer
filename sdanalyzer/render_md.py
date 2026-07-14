"""Markdown renderer for the full deliverable set A-N."""


def _kv_table(d: dict, k_hdr: str, v_hdr: str) -> str:
    if not d:
        return "_Not available in this dataset._\n"
    lines = [f"| {k_hdr} | {v_hdr} |", "| --- | --- |"]
    lines += [f"| {k} | {v} |" for k, v in d.items()]
    return "\n".join(lines) + "\n"


def _rng(pair, unit=""):
    return f"{pair[0]}-{pair[1]}{unit}" if pair else "n/a"


def render(r: dict) -> str:
    q = r["quality"]
    m = r["mttr"]
    p = r["pareto"]
    out = []
    a = out.append

    a(f"# Service Desk Intelligence Assessment\n")
    a(f"**Source:** {r['meta']['source_name']}  ")
    a(f"**Period:** {r['meta']['date_range_str']}  ")
    a(f"**Records analyzed:** {r['n_analyzed']}  ")
    a("**Method:** Deterministic rule-based analysis. No AI training, no data retention. "
      "The dataset was processed in memory and discarded.\n")
    if r["meta"].get("short_period"):
        a(f"> **Short observation window: {r['meta']['period_days']} days.** Volumes and "
          "rankings in this report are a snapshot, not a baseline. Weekly cycles, "
          "month-end effects, and one-off events cannot be separated. Use this to shape "
          "questions, not to size ROI. Request 3-6 months of data for a committed roadmap.\n")

    # A. Executive Summary
    a("## A. Executive Summary\n")
    a(f"Data quality verdict: **{q['verdict']}**. "
      f"{q['total_records']} records covering {r['meta']['date_range_str']}.\n")
    a("### Top findings\n")
    for f in r["findings"]:
        a(f"- {f['text']} _[{f['confidence']}]_")
    a("\n### Top automation opportunities\n")
    for o in r["opportunities"][:5]:
        a(f"- **{o['theme']}**: {_rng(o['deflection_range_tickets'])} tickets deflectable "
          f"({_rng(o['deflection_range_pct'], '%')}) via {o['solution_type']} _[{o['confidence']}]_")
    a("\n### Top Agentic AI opportunities\n")
    if r["agentic"]:
        for ag in r["agentic"][:5]:
            a(f"- **{ag['name']}** on {ag['system_of_action']} "
              f"(evidence: {ag['evidence_tickets']} tickets, risk {ag['risk']}) _[{ag['confidence']}]_")
    else:
        a("- No agentic scenarios evidenced in this dataset.")
    a("")

    # B. Data Quality Assessment
    a("## B. Data Quality Assessment\n")
    a(f"- Total records: **{q['total_records']}**")
    a(f"- Columns in file: {len(q['available_columns'])} ({', '.join(q['available_columns'][:15])}"
      + (", ..." if len(q["available_columns"]) > 15 else "") + ")")
    a(f"- Duplicate rows: {q['duplicate_rows']} | Duplicate ticket IDs: {q['duplicate_ticket_ids']}")
    if q["date_range"]:
        a(f"- Date range: {q['date_range'][0]:%Y-%m-%d} to {q['date_range'][1]:%Y-%m-%d}")
    if q["created_parse_rate"] is not None:
        a(f"- Created-date parse rate: {q['created_parse_rate']}%")
    if q["resolved_parse_rate"] is not None:
        a(f"- Resolved-date parse rate: {q['resolved_parse_rate']}%")
    a("")
    a("### Field mapping\n")
    a(_kv_table({k: v for k, v in q["column_mapping"].items()}, "Canonical field", "Source column"))
    if q["missing_required_fields"]:
        a(f"\n**Missing required fields:** {', '.join(q['missing_required_fields'])}. "
          "These are absent from the file; related analyses are marked not available.\n")
    if q["missing_optional_fields"]:
        a(f"**Missing optional fields:** {', '.join(q['missing_optional_fields'])}\n")
    a("### Field completeness (% populated)\n")
    a(_kv_table({k: f"{v}%" for k, v in sorted(q['completeness'].items(), key=lambda x: -x[1])},
                "Field", "Populated"))
    if q["issues"]:
        a("\n### Quality issues\n")
        for i in q["issues"]:
            a(f"- {i}")
    a("")

    # C. Ticket Volume Analysis
    a("## C. Ticket Volume Analysis\n")
    a(_kv_table({d["theme"]: f"{d['count']} ({d['pct']}%)" for d in p["drivers"]},
                "Theme", "Tickets"))
    for label, key in [("Ticket types", "ticket_types"), ("Priorities", "priorities"),
                       ("Statuses", "statuses"), ("Departments", "departments")]:
        inv = q["inventories"].get(key)
        if inv:
            a(f"\n### {label}\n")
            a(_kv_table(inv, label[:-1], "Count"))
    a("")

    # D. MTTR Analysis
    a("## D. MTTR Analysis\n")
    if m["overall"]:
        o = m["overall"]
        a(f"- Overall median: **{o['median']} hrs** | mean: {o['mean']} hrs | P90: {o['p90']} hrs")
        a(f"- Based on {o['resolved_n']} resolved tickets ({o['coverage_pct']}% coverage), "
          f"MTTR source: {o['source']}")
        a("- Note: clock hours from timestamps; business-hours calendars are not in the CSV.\n")
        a("### By theme\n")
        a(_kv_table({x['key']: f"median {x['median']}h / P90 {x['p90']}h (n={x['resolved_n']})"
                     for x in m["by_theme"]}, "Theme", "MTTR"))
        if m["by_priority"]:
            a("\n### By priority\n")
            a(_kv_table({x['key']: f"median {x['median']}h (n={x['resolved_n']})"
                         for x in m["by_priority"]}, "Priority", "MTTR"))
        if m["by_application"]:
            a("\n### By application\n")
            a(_kv_table({x['key']: f"median {x['median']}h (n={x['resolved_n']})"
                         for x in m["by_application"]}, "Application", "MTTR"))
        if m["by_assignment_group"]:
            a("\n### By assignment group\n")
            a(_kv_table({x['key']: f"median {x['median']}h (n={x['resolved_n']})"
                         for x in m["by_assignment_group"]}, "Group", "MTTR"))
        a("\n**Slowest themes:** " + ", ".join(f"{s['key']} ({s['median']}h)" for s in m["slowest_themes"]))
        a("**Fastest themes:** " + ", ".join(f"{s['key']} ({s['median']}h)" for s in m["fastest_themes"]) + "\n")
    else:
        a("MTTR could not be computed: this export has no parseable resolution timestamps. "
          "Ask for an export that includes a resolved/closed date column.\n")

    # Workflow-state friction (always shown when available; primary signal when MTTR absent)
    w = r.get("workflow", {})
    if w.get("available"):
        a("### Workflow-state friction signals\n")
        a(f"- Open (not closed/resolved/cancelled): {w['open_n']} tickets ({w['open_pct']}%)")
        a(f"- Stuck in On Hold / Pending: **{w['stuck_n']} tickets ({w['stuck_pct']}%)**"
          + (" - a large share of work is waiting on something; find out what."
             if w["stuck_pct"] >= 15 else ""))
        if w["transfer_n"]:
            a(f"- Transferred between teams: {w['transfer_n']} tickets ({w['transfer_pct']}%) - "
              "each transfer is a routing miss at intake")
            if w["transfer_targets"]:
                a("  - Transfer destinations: " +
                  ", ".join(f"{k} ({v})" for k, v in w["transfer_targets"].items()))
        if w["stuck_by_theme"]:
            a("\n**Where tickets get stuck:**\n")
            for s in w["stuck_by_theme"]:
                a(f"- {s['theme']}: {s['stuck']} of {s['count']} on hold ({s['pct']}%)")
        a("")

    # E. Theme and Category Breakdown
    a("## E. Theme and Category Breakdown\n")
    for t in r["theme_stats"]:
        a(f"### {t['theme']} - {t['count']} tickets ({t['pct']}%)\n")
        a(f"- MTTR: " + (f"median {t['mttr_median']}h, mean {t['mttr_mean']}h "
                         f"({t['mttr_coverage_pct']}% coverage)" if t['mttr_median'] is not None
                         else "not computable"))
        if t["top_issue_phrases"]:
            a(f"- Example ticket phrases: " + "; ".join(f"\"{x}\"" for x in t["top_issue_phrases"][:3]))
        if t["top_applications"]:
            a(f"- Top applications: " + ", ".join(f"{k} ({v})" for k, v in t["top_applications"].items()))
        if t["top_raw_categories"]:
            a(f"- Original categories: " + ", ".join(f"{k} ({v})" for k, v in t["top_raw_categories"].items()))
        a(f"- Classification confidence: **{t['confidence']}**\n")
        if t["theme"] == "Other / Unclear" and r.get("other_terms"):
            a("**What the unclassified tickets actually mention** (term mining, for SME review):\n")
            a(_kv_table({term: n for term, n in r["other_terms"]}, "Term", "Tickets mentioning"))
            a("These terms are candidates for new themes or keyword rules. "
              "Review with the customer, then re-run the analysis.\n")

    # F. Application Landscape
    a("## F. Application Landscape\n")
    if p["top_applications"]:
        a(_kv_table(p["top_applications"], "Application", "Tickets"))
    else:
        a("_No application/CI field available in this dataset._\n")
    if p["top_assignment_groups"]:
        a("\n### Top assignment groups\n")
        a(_kv_table(p["top_assignment_groups"], "Group", "Tickets"))
    a("")

    # G. Top Operational Friction Points
    a("## G. Top Operational Friction Points\n")
    a("### Pareto: themes covering ~80% of volume\n")
    for d in p["drivers"]:
        marker = " <-- 80% line" if d["theme"] == p["cutoff_themes"][-1] else ""
        a(f"- {d['theme']}: {d['count']} ({d['pct']}%, cumulative {d['cumulative_pct']}%){marker}")
    a("\n### High-volume themes (>=10% of tickets)\n")
    for h in p["high_volume"]:
        a(f"- {h['theme']}: {h['count']} tickets ({h['pct']}%)")
    a("\n### High-pain themes (MTTR >= 1.5x overall median)\n")
    if p["high_pain"]:
        for h in p["high_pain"]:
            a(f"- {h['theme']}: median {h['mttr_median']}h ({h['vs_overall']}x overall)")
    else:
        a("- None identified (or MTTR unavailable).")
    a("")

    # H. AI Automation Opportunity Backlog
    a("## H. AI Automation Opportunity Backlog\n")
    for o in r["opportunities"]:
        a(f"### {o['theme']}\n")
        a(f"- Tickets addressable: **{o['tickets_addressable']}** ({o['pct_of_total']}%)")
        a(f"- Solution type: {o['solution_type']}")
        a(f"- Estimated deflection: {_rng(o['deflection_range_pct'], '%')} "
          f"= {_rng(o['deflection_range_tickets'])} tickets")
        a(f"- MTTR reduction potential: {_rng(o['mttr_reduction_range_pct'], '%')}")
        if o["est_hours_saved_range"]:
            a(f"- Estimated hours returned: {_rng(o['est_hours_saved_range'], ' hrs')} "
              "(deflected tickets x median MTTR)")
        a(f"- Complexity: {o['complexity']} | Risk: {o['risk']}")
        a(f"- Dependencies: {', '.join(o['dependencies'])}")
        a(f"- Rationale: {o['rationale']}")
        a(f"- **{o['confidence']}**\n")

    # I. Agentic AI Use Case Backlog
    a("## I. Agentic AI Use Case Backlog\n")
    if not r["agentic"]:
        a("_No agentic scenarios evidenced in this dataset._\n")
    for ag in r["agentic"]:
        a(f"### {ag['name']}\n")
        a(f"- Theme evidence: {ag['evidence_tickets']} tickets ({ag['evidence_pct']}%)")
        a(f"- Trigger: {ag['trigger']}")
        a(f"- System of action: {ag['system_of_action']}")
        a(f"- Required permissions: {ag['permissions']}")
        a(f"- Workflow: " + " -> ".join(ag["steps"]))
        a(f"- Feasibility: {ag['feasibility']}")
        a(f"- Risk: {ag['risk']} | Human approval: {ag['human_approval']}")
        a(f"- Fallback: {ag['fallback']}")
        a(f"- Expected impact: {ag['expected_impact']}")
        a(f"- **{ag['confidence']}**\n")

    # J. Atomicwork Solution Mapping
    a("## J. Atomicwork Solution Mapping\n")
    a("| Theme | Atomicwork capabilities | Solution type |")
    a("| --- | --- | --- |")
    for o in r["opportunities"]:
        a(f"| {o['theme']} | {', '.join(o['atomicwork_capabilities'])} | {o['solution_type']} |")
    a("")

    # K. Roadmap
    a("## K. 30-60-90 Day Roadmap\n")
    for phase, plan in r["roadmap"].items():
        a(f"### Day {phase}: {plan['focus']}\n")
        for item in plan["items"]:
            a(f"- {item}")
        a("")

    # L. Workshop Questions
    a("## L. Workshop Questions for Customer\n")
    for i, qn in enumerate(r["workshop_questions"], 1):
        a(f"{i}. {qn}")
    a("")

    # M. PowerPoint Slide Outline
    a("## M. PowerPoint Slide Outline\n")
    for i, s in enumerate(r["slides"], 1):
        a(f"**Slide {i}: {s['title']}**")
        for b in s["bullets"]:
            a(f"- {b}")
        a("")

    # N. Final Recommendations + validation
    a("## N. Final Recommendations\n")
    a("1. Validate theme classification with SMEs before committing the roadmap "
      "(see challenges below).")
    for i, w in enumerate(r["quick_wins"], 2):
        a(f"{i}. Start with {w['theme']}: {w['solution_type']} using "
          f"{', '.join(w['atomicwork_capabilities'][:2])}. Low complexity, low risk.")
    nn = len(r["quick_wins"]) + 2
    a(f"{nn}. Sequence integration automations after credentials/API inventory is confirmed.")
    a(f"{nn+1}. Run agentic pilots only with human approval loops and audit logging.")
    a(f"{nn+2}. Re-run this analysis after 60 days to measure deflection against baseline.\n")

    a("### Self-challenge and validation (facts vs assumptions)\n")
    for c in r["challenges"]:
        a(f"- **{c['question']}** {c['finding']} _[severity: {c['severity']}]_")
    a("")
    a("---")
    a("_Facts are drawn only from the uploaded CSV. Deflection and MTTR-reduction figures are "
      "assumption-based ranges, not measurements. All recommendations require customer validation. "
      "The uploaded data was not stored, not used for training, and was discarded after this "
      "report was generated._")
    return "\n".join(out)
