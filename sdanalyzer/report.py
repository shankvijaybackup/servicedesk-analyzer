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
                   workflow=None) -> list[dict]:
    workflow = workflow or {}
    top_themes = ", ".join(t["theme"] for t in theme_stats[:3])
    period_note = (f"Period: {meta['date_range_str']}"
                   + (f" (ONLY {meta['period_days']} DAYS - snapshot, not baseline)"
                      if meta.get("short_period") else ""))
    slides = [
        {"title": "Service Desk Intelligence Assessment",
         "bullets": [f"Dataset: {meta['source_name']}", f"{qa['total_records']} records analyzed",
                     period_note, "Method: deterministic rule-based analysis, no data retained"]},
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

    return {
        "meta": meta,
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
                                 theme_stats, opps, agentic, wins, workflow),  # M
        "findings": findings,               # A
        "challenges": challenges,           # step 11
        "n_analyzed": n_records,
    }
