"""Report assembly: runs the full pipeline and produces deliverables A-N
as a structured dict that renderers turn into Markdown / HTML / PPTX.

The pipeline is stateless: pass in CSV bytes or a path, get a report dict.
Nothing is written to disk by this module and the dataframe is discarded
when the function returns.
"""

from . import loader, quality, normalize, themes, analysis, opportunities


def _validation_challenges(qa: dict, view, theme_stats) -> list[dict]:
    """Step 11: self-challenge before finalizing."""
    out = []
    other = next((t for t in theme_stats if t["theme"] == "Other / Unclear"), None)
    low_conf_share = (view["theme_confidence"] == "low").mean() if len(view) else 0

    out.append({
        "question": "Could categories be misclassified?",
        "finding": (f"{round(low_conf_share * 100, 1)}% of tickets were classified with low "
                    "keyword confidence. These need SME review."),
        "severity": "high" if low_conf_share > 0.3 else "medium" if low_conf_share > 0.15 else "low",
    })
    if other:
        out.append({
            "question": "Are 'Other' tickets hiding important patterns?",
            "finding": (f"'Other / Unclear' holds {other['count']} tickets ({other['pct']}%). "
                        + ("This is a significant blind spot; sample and review manually."
                           if other["pct"] > 15 else "Within tolerable range but worth sampling.")),
            "severity": "high" if other["pct"] > 15 else "low",
        })
    if qa["short_summary_pct"] is not None:
        out.append({
            "question": "Are ticket descriptions too short?",
            "finding": (f"{qa['short_summary_pct']}% of summaries are under 15 characters."),
            "severity": "high" if qa["short_summary_pct"] > 25 else "low",
        })
    if qa["duplicate_ticket_ids"] or qa["duplicate_rows"]:
        out.append({
            "question": "Are there duplicate tickets?",
            "finding": (f"{qa['duplicate_rows']} duplicate rows and "
                        f"{qa['duplicate_ticket_ids']} duplicate ticket IDs found. "
                        "Duplicate rows were excluded from analysis."),
            "severity": "medium",
        })
    if qa["resolved_parse_rate"] is not None:
        out.append({
            "question": "Is MTTR calculated correctly / are resolved dates reliable?",
            "finding": (f"Resolved dates parse for {qa['resolved_parse_rate']}% of records. "
                        "MTTR figures cover only resolved tickets; business-hours vs "
                        "clock-hours distinction is unknown from CSV alone."),
            "severity": "medium" if qa["resolved_parse_rate"] < 80 else "low",
        })
    # Volume distortion check: single day spikes
    if len(view) and view["created_date"].notna().any():
        by_day = view.groupby(view["created_date"].dt.date).size()
        if len(by_day) > 5 and by_day.max() > 4 * by_day.median():
            out.append({
                "question": "Are volumes distorted by one-time events?",
                "finding": (f"Day {by_day.idxmax()} has {int(by_day.max())} tickets vs a median of "
                            f"{int(by_day.median())}/day. Possible incident spike or bulk import; "
                            "verify before treating volumes as steady-state."),
                "severity": "medium",
            })
    out.append({
        "question": "Does this require SME validation?",
        "finding": "Yes. All theme mappings, automation feasibility, and API availability "
                   "assumptions must be validated in a customer workshop before roadmap commitment.",
        "severity": "medium",
    })
    return out


def _workshop_questions(theme_stats, agentic) -> list[str]:
    qs = [
        "Which of the top ticket themes shown here match your team's intuition, and which look wrong?",
        "Are resolved dates in your export set automatically by the tool or manually by agents?",
        "Is MTTR measured in business hours or clock hours in your reporting today?",
        "Which of these systems have API or admin credentials your team can grant to an integration user?",
        "What percentage of tickets are raised via portal vs email vs chat today?",
        "Are there seasonal or event-driven spikes we should exclude from baseline volumes?",
    ]
    for ts in theme_stats[:3]:
        if ts["theme"] != "Other / Unclear":
            qs.append(f"For '{ts['theme']}' ({ts['count']} tickets): who resolves these today "
                      "and what tools do they touch to close one?")
    for a in agentic[:3]:
        qs.append(f"For the '{a['name']}' scenario: is {a['system_of_action']} API-accessible "
                  "in your tenant, and who owns approval?")
    qs.append("Which knowledge sources (Confluence, SharePoint, SOPs) exist and how current are they?")
    qs.append("What is the loaded hourly cost of L1/L2 agents for ROI modeling?")
    return qs


def _slide_outline(meta, qa, pareto_res, mttr_res, theme_stats, opps, agentic, wins,
                   workflow=None, outcomes=None, stakeholders=None) -> list[dict]:
    workflow = workflow or {}
    top_themes = ", ".join(t["theme"] for t in theme_stats[:3])
    period_note = (f"Period: {meta['date_range_str']}"
                   + (f" (ONLY {meta['period_days']} DAYS - snapshot, not baseline)"
                      if meta.get("short_period") else ""))
    outcome_slides = []
    if outcomes and outcomes["deflect_range"][1] > 0:
        oc = outcomes
        ob = [f"{oc['addressable']} of {oc['total_n']} tickets ({oc['addressable_pct']}%) "
              "have a viable automation path",
              f"{oc['deflect_range'][0]}-{oc['deflect_range'][1]} tickets need no human "
              f"agent ({oc['deflect_pct_range'][0]}-{oc['deflect_pct_range'][1]}%)"]
        if oc["wait_hours_range"]:
            ob.append(f"{oc['wait_hours_range'][0]:,}-{oc['wait_hours_range'][1]:,} employee "
                      "waiting hours eliminated (measured)")
        ob.append(f"{oc['effort_hours_range'][0]:,}-{oc['effort_hours_range'][1]:,} "
                  "agent-hours returned (assumption: 15-45 min/ticket)")
        if oc["fte_range"]:
            ob.append(f"~{oc['fte_range'][0]}-{oc['fte_range'][1]} FTE-equivalent per month "
                      "redirected to project work")
        ob.append("Cost = hours x your loaded rate (bring to workshop)")
        outcome_slides.append({"title": "Business Outcomes", "bullets": ob})
    if stakeholders:
        outcome_slides.append({"title": "Value by Stakeholder", "bullets": [
            f"{s['stakeholder']}: {s['outcome'][:110]}" for s in stakeholders[:6]]})

    slides = [
        {"title": "Service Desk Intelligence Assessment",
         "bullets": [f"Dataset: {meta['source_name']}", f"{qa['total_records']} records analyzed",
                     period_note, "Method: deterministic rule-based analysis, no data retained"]},
        *outcome_slides,
        {"title": "Data Quality", "bullets": [
            f"Verdict: {qa['verdict']}",
            *(qa["issues"][:4] or ["No blocking quality issues found"])]},
        {"title": "Where the Volume Is", "bullets": [
            f"Top themes: {top_themes}",
            *(f"{d['theme']}: {d['count']} tickets ({d['pct']}%)" for d in pareto_res["drivers"][:4])]},
        {"title": "Where the Pain Is", "bullets": (
            ([f"Overall median MTTR: {mttr_res['overall']['median']} hrs "
              f"(coverage {mttr_res['overall']['coverage_pct']}%)"]
             + [f"Slowest: {s['key']} at {s['median']} hrs median" for s in mttr_res["by_theme"][:3]])
            if mttr_res["overall"] else
            (["MTTR not computable (no resolution timestamps in export)"]
             + ([f"{workflow['stuck_n']} tickets ({workflow['stuck_pct']}%) stuck in On Hold/Pending",
                 f"{workflow['transfer_n']} tickets ({workflow['transfer_pct']}%) transferred between teams"]
                if workflow.get("available") else [])))},
        {"title": "Automation Opportunity Backlog", "bullets": [
            f"{o['theme']}: {o['deflection_range_tickets'][0]}-{o['deflection_range_tickets'][1]} "
            f"tickets deflectable ({o['solution_type'].split('+')[0].strip()})"
            for o in opps[:5]]},
        {"title": "Agentic AI Opportunities", "bullets": [
            f"{a['name']} ({a['system_of_action']}), risk {a['risk']}, approval: {a['human_approval']}"
            for a in agentic[:5]] or ["No agentic scenarios evidenced in this dataset"]},
        {"title": "Quick Wins (30 days)", "bullets": [
            f"{w['theme']}: {', '.join(w['atomicwork_capabilities'][:2])}" for w in wins] or
            ["Quick wins pending SME validation"]},
        {"title": "30-60-90 Roadmap", "bullets": [
            "30: knowledge AI + quick-win workflows, baseline metrics",
            "60: integration automations (identity, MDM, collaboration)",
            "90: agentic pilots with human approval, ROI review"]},
        {"title": "Risks and Assumptions", "bullets": [
            "Deflection ranges assume API access and knowledge quality",
            "MTTR from timestamps, business-hours unverified",
            "Theme classification is keyword-based, needs SME validation"]},
        {"title": "Asks", "bullets": [
            "SME workshop to validate top 3 themes",
            "API/credential inventory for target systems",
            "Agent hourly cost for ROI model"]},
    ]
    return slides


# Industry band for L1/L2 agent handle time per ticket, used ONLY when the
# export has no effort data (it never does). Always labeled as an assumption.
HANDLE_TIME_HOURS = (0.25, 0.75)  # 15-45 minutes


def _business_outcomes(opps, mttr_res, workflow, meta, total_n) -> dict:
    """Translate analysis into outcome ranges. Every figure is either
    measured (from the export) or assumption-based (explicitly labeled)."""
    automatable = [o for o in opps if not o["solution_type"].startswith("F.")]
    deflect_lo = sum(o["deflection_range_tickets"][0] for o in automatable)
    deflect_hi = sum(o["deflection_range_tickets"][1] for o in automatable)
    addressable = sum(o["tickets_addressable"] for o in automatable)

    # Employee wait time eliminated: measured (deflected x median MTTR elapsed)
    wait_lo = wait_hi = None
    if mttr_res.get("overall"):
        med = mttr_res["overall"]["median"]
        wait_lo, wait_hi = round(deflect_lo * med), round(deflect_hi * med)

    # Agent effort returned: assumption-based (no effort data in exports)
    effort_lo = round(deflect_lo * HANDLE_TIME_HOURS[0])
    effort_hi = round(deflect_hi * HANDLE_TIME_HOURS[1])

    # FTE-equivalent capacity per month: assumption-based. Suppressed when it
    # rounds to nothing (sub-0.1 FTE is noise, not an executive message).
    fte_lo = fte_hi = None
    period_days = meta.get("period_days")
    if period_days and period_days >= 7 and deflect_hi > 0:
        months = max(period_days / 30.4, 0.25)
        lo = round(effort_lo / months / 160, 1)
        hi = round(effort_hi / months / 160, 1)
        if hi >= 0.3:
            fte_lo, fte_hi = lo, hi

    stuck_n = workflow.get("stuck_n", 0) if workflow.get("available") else 0
    transfer_n = workflow.get("transfer_n", 0) if workflow.get("available") else 0

    return {
        "total_n": total_n,
        "addressable": addressable,
        "addressable_pct": round(addressable / total_n * 100, 1) if total_n else 0,
        "deflect_range": (deflect_lo, deflect_hi),
        "deflect_pct_range": (round(deflect_lo / total_n * 100, 1),
                              round(deflect_hi / total_n * 100, 1)) if total_n else (0, 0),
        "wait_hours_range": (wait_lo, wait_hi) if wait_lo is not None else None,
        "effort_hours_range": (effort_lo, effort_hi),
        "fte_range": (fte_lo, fte_hi) if fte_lo is not None else None,
        "stuck_n": stuck_n,
        "transfer_n": transfer_n,
        "period_days": period_days,
        "assumptions": [
            "Deflection ranges are conservative industry bands applied to your observed "
            "volumes; they assume API access and good knowledge quality per theme.",
            f"Agent effort uses an industry handle-time band of "
            f"{int(HANDLE_TIME_HOURS[0]*60)}-{int(HANDLE_TIME_HOURS[1]*60)} minutes per "
            "ticket because exports do not contain effort data. Replace with your own "
            "handle times for a committed business case.",
            "Employee wait-time figures use median MTTR from your export (elapsed clock "
            "time)." if wait_lo is not None else
            "Employee wait-time savings cannot be computed: this export has no "
            "resolution timestamps.",
            "Cost: multiply agent-hours returned by your loaded hourly cost for L1/L2. "
            "This report does not invent currency figures.",
        ],
    }


def _stakeholder_value(outcomes, opps, agentic, workflow) -> list[dict]:
    """What each executive gets. Only claims backed by the computed outcomes."""
    d_lo, d_hi = outcomes["deflect_range"]
    e_lo, e_hi = outcomes["effort_hours_range"]
    period = (f"over this {outcomes['period_days']}-day window"
              if outcomes.get("period_days") else "over the export period")
    rows = []
    rows.append({
        "stakeholder": "CIO / Head of IT",
        "outcome": (f"{d_lo}-{d_hi} tickets ({outcomes['deflect_pct_range'][0]}-"
                    f"{outcomes['deflect_pct_range'][1]}% of volume) resolved without an "
                    f"agent {period}; L1 refocused on complex work"),
        "metric": "Deflection rate, MTTR trend, automation coverage by theme",
    })
    rows.append({
        "stakeholder": "CFO",
        "outcome": (f"{e_lo}-{e_hi} agent-hours returned {period} (assumption-based); "
                    "cost impact = hours x your loaded hourly rate. Capacity absorbed "
                    "without headcount growth"
                    + (f"; roughly {outcomes['fte_range'][0]}-{outcomes['fte_range'][1]} "
                       "FTE-equivalent per month" if outcomes.get("fte_range") else "")),
        "metric": "Agent-hours returned, cost per ticket, FTE-equivalent capacity",
    })
    if outcomes["wait_hours_range"]:
        w_lo, w_hi = outcomes["wait_hours_range"]
        emp_outcome = (f"{w_lo}-{w_hi} employee waiting hours eliminated {period}: "
                       "instant answers instead of waiting on a queue")
    else:
        emp_outcome = ("Instant 24/7 answers in Slack/Teams for deflected requests "
                       "instead of waiting on a queue (wait-hours not computable from "
                       "this export)")
    rows.append({
        "stakeholder": "CHRO / Head of HR",
        "outcome": emp_outcome + "; HR queries answered without HR team touch",
        "metric": "Employee wait time, HR ticket deflection, onboarding turnaround",
    })
    top_theme = next((o for o in opps if not o["solution_type"].startswith("F.")), None)
    rows.append({
        "stakeholder": "Service Desk Lead",
        "outcome": ((f"{outcomes['stuck_n']} stuck tickets and {outcomes['transfer_n']} "
                     "misrouted transfers become automation targets; " if outcomes["stuck_n"]
                     else "") +
                    (f"biggest relief: {top_theme['theme']} "
                     f"({top_theme['tickets_addressable']} tickets)" if top_theme else
                     "queue relief pending SME validation")),
        "metric": "Queue depth, stuck/on-hold share, transfer rate, first-contact resolution",
    })
    rows.append({
        "stakeholder": "Platform Owner (ITSM)",
        "outcome": ("Cleaner intake via AI categorization (reduces the misrouting and "
                    "'Other' bucket found in this export); integrations built once, "
                    "reused across workflows"),
        "metric": "Categorization accuracy, intake quality, integration reuse",
    })
    rows.append({
        "stakeholder": "Employees",
        "outcome": ("Self-service in Slack/Teams with instant answers for the most "
                    "common requests; no ticket status-chasing"),
        "metric": "CSAT, self-service adoption, repeat-contact rate",
    })
    return rows


def _roadmap(wins, opps, agentic) -> dict:
    integration = [o for o in opps if "C. Integration" in o["solution_type"]
                   and not o["solution_type"].startswith("F.")][:4]
    return {
        "30": {
            "focus": "Foundations and quick wins",
            "items": [
                "Baseline metrics agreed (volume, MTTR, deflection definitions)",
                "Knowledge ingestion for top how-to themes",
                *(f"Deploy: {w['theme']} ({w['solution_type'].split('+')[0].strip()})" for w in wins[:3]),
                "SME validation workshop on theme mapping",
            ],
        },
        "60": {
            "focus": "Integration automation",
            "items": [
                *(f"Integrate: {o['theme']} - {', '.join(o['dependencies'][:1])}" for o in integration),
                "AI coworker rollout in Slack/Teams to pilot departments",
                "Deflection and MTTR tracking dashboard",
            ],
        },
        "90": {
            "focus": "Agentic pilots and scale",
            "items": [
                *(f"Agentic pilot: {a['name']} (approval: {a['human_approval']})" for a in agentic[:3]),
                "Expand AI coworker to all departments",
                "ROI review against 30-day baseline; go/no-go on phase 2",
            ],
        },
    }


def analyze(source, source_name: str = "uploaded.csv") -> dict:
    """Full pipeline. Returns the report dict; retains no data afterward."""
    df, mapping, mapping_notes = loader.load_csv(source, filename=source_name)
    qa = quality.assess(df, mapping)
    qa["mapping_notes"] = mapping_notes
    qa["issues"] = mapping_notes + qa["issues"]
    view = normalize.normalize(df, mapping)
    del df  # forget raw data immediately
    view = themes.classify(view)
    theme_stats = themes.theme_summary(view)
    other_terms = themes.mine_other_terms(view)
    pareto_res = analysis.pareto(view)
    mttr_res = analysis.mttr_analysis(view)
    workflow = analysis.workflow_state_analysis(view)
    opps = opportunities.build_opportunities(view, theme_stats)
    agentic = opportunities.build_agentic_backlog(view)
    wins = opportunities.quick_wins(opps)

    dr = qa["date_range"]
    period_days = (dr[1] - dr[0]).days + 1 if dr else None
    short_period = period_days is not None and period_days < 30
    meta = {
        "source_name": source_name,
        "date_range_str": (f"{dr[0]:%Y-%m-%d} to {dr[1]:%Y-%m-%d}" if dr else "unknown"),
        "period_days": period_days,
        "short_period": short_period,
    }

    # Executive summary content (deliverable A)
    top3 = [t for t in theme_stats if t["theme"] != "Other / Unclear"][:3]
    findings = []
    if short_period:
        findings.append({
            "text": (f"This export covers only {period_days} days. Volumes below are a "
                     "snapshot, not a baseline; do not size automation ROI from this "
                     "sample alone. Request 3-6 months of data."),
            "confidence": "High confidence",
        })
    for t in top3:
        findings.append({
            "text": (f"'{t['theme']}' is a top driver with {t['count']} tickets ({t['pct']}%)"
                     + (f", median MTTR {t['mttr_median']} hrs" if t["mttr_median"] is not None else "")),
            "confidence": {"high": "High confidence", "medium": "Medium confidence",
                           "low": "Low confidence"}[t["confidence"]],
        })
    for hp in pareto_res["high_pain"][:2]:
        findings.append({
            "text": (f"'{hp['theme']}' is a high-pain area: median MTTR {hp['mttr_median']} hrs, "
                     f"{hp['vs_overall']}x the overall median"),
            "confidence": "Medium confidence",
        })
    if workflow.get("available") and workflow["stuck_pct"] >= 10:
        findings.append({
            "text": (f"{workflow['stuck_n']} tickets ({workflow['stuck_pct']}%) are sitting in "
                     "On Hold/Pending states - a workflow friction signal independent of MTTR. "
                     "Investigate what these are waiting on (approvals, parts, third parties)."),
            "confidence": "High confidence",
        })
    if workflow.get("available") and workflow["transfer_n"] >= 3:
        findings.append({
            "text": (f"{workflow['transfer_n']} tickets ({workflow['transfer_pct']}%) were "
                     "transferred between teams - routing/triage friction that intelligent "
                     "categorization at intake can reduce."),
            "confidence": "Medium confidence",
        })
    if qa["verdict"] != "GOOD":
        findings.append({
            "text": f"Data quality is {qa['verdict']}: " + "; ".join(qa["issues"][:2]),
            "confidence": "High confidence",
        })
    findings = findings[:6]

    challenges = _validation_challenges(qa, view, theme_stats)
    n_records = len(view)
    del view  # forget normalized data

    outcomes = _business_outcomes(opps, mttr_res, workflow, meta, n_records)
    stakeholders = _stakeholder_value(outcomes, opps, agentic, workflow)

    return {
        "meta": meta,
        "outcomes": outcomes,               # business outcomes
        "stakeholders": stakeholders,       # per-stakeholder value
        "quality": qa,                      # B
        "theme_stats": theme_stats,         # C, E
        "other_terms": other_terms,         # blind-spot mining
        "pareto": pareto_res,               # C, F, G
        "mttr": mttr_res,                   # D
        "workflow": workflow,               # D fallback / friction
        "opportunities": opps,              # H, J
        "agentic": agentic,                 # I
        "quick_wins": wins,
        "roadmap": _roadmap(wins, opps, agentic),          # K
        "workshop_questions": _workshop_questions(theme_stats, agentic),  # L
        "slides": _slide_outline(meta, qa, pareto_res, mttr_res,
                                 theme_stats, opps, agentic, wins, workflow,
                                 outcomes, stakeholders),  # M
        "findings": findings,               # A
        "challenges": challenges,           # step 11
        "n_analyzed": n_records,
    }
