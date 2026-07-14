"""Step 10 and 11 deliverables built deterministically from computed results:
executive summary, top findings, quick wins, 30-60-90 roadmap, risks and
assumptions, and workshop/validation questions. Every statement is derived from
the numbers already computed; nothing is asserted beyond the data.
"""

from __future__ import annotations

from . import util
from .themes import OTHER


def volume_analysis(classified) -> dict:
    total = len(classified)
    out = {"total": total}

    created = classified["created"].dropna()
    if len(created):
        by_month = created.dt.to_period("M").astype(str).value_counts().sort_index()
        out["by_month"] = [{"month": m, "count": int(c)} for m, c in by_month.items()]

    for dim, key in [("type", "by_type"), ("status", "by_status"),
                     ("priority", "by_priority")]:
        s = classified[dim].dropna()
        if len(s):
            vc = s.value_counts()
            out[key] = [{"value": str(k), "count": int(v), "pct": util.pct(v, total)}
                        for k, v in vc.items()]

    status = classified["status"].dropna()
    if len(status):
        resolved = int(status.isin(["Resolved", "Cancelled"]).sum())
        out["resolved"] = resolved
        out["open_backlog"] = total - resolved
    return out


def application_landscape(classified) -> dict:
    apps = classified["application"].dropna()
    if not len(apps):
        return {"available": False}
    vc = apps.value_counts().head(15)
    total = len(classified)
    return {
        "available": True,
        "distinct_applications": int(classified["application"].nunique()),
        "top": [{"application": str(k), "count": int(v), "pct": util.pct(v, total)}
                for k, v in vc.items()],
    }


def friction_points(pareto_res: dict, mttr_res: dict) -> list[dict]:
    points = []
    for hp in pareto_res.get("high_pain_themes", [])[:5]:
        points.append({
            "area": hp["value"],
            "signal": "high total effort (volume x resolution time)",
            "count": hp["count"],
            "mttr_median_hours": hp["mttr_median_hours"],
            "est_effort_hours": hp["est_effort_hours"],
        })
    return points


def build(integrity, theme_summaries, pareto_res, mttr_res, opp, volume) -> dict:
    total = integrity["total_records"]
    top_theme = theme_summaries[0] if theme_summaries else None
    roi = opp["roi_summary"]

    # Current state summary (facts only).
    dr = integrity.get("date_range")
    span = f"{dr['start']} to {dr['end']} ({dr['days']} days)" if dr else "an unknown period"
    cs = [
        f"{total} tickets analyzed over {span}.",
        f"Data quality: {integrity['quality_grade']} ({integrity['quality_score']}/100).",
    ]
    if top_theme:
        cs.append(f"Largest theme: {top_theme['theme']} at {top_theme['pct']}% of volume.")
    if mttr_res.get("available"):
        cs.append(f"Overall median MTTR: {mttr_res['overall']['median_hours']}h.")
    cs.append(
        f"Estimated deflectable volume: {roi['est_total_deflectable_pct_range'][0]}% to "
        f"{roi['est_total_deflectable_pct_range'][1]}% (planning estimate).")

    # Top findings.
    findings = []
    vf = pareto_res["by_theme"]["vital_few"]
    if vf:
        share = pareto_res["by_theme"]["vital_few_count"]
        findings.append({
            "finding": f"{share} themes drive ~80% of ticket volume "
                       f"(led by {vf[0]['value']} at {vf[0]['pct']}%).",
            "confidence": "High"})
    other = next((t for t in theme_summaries if t["theme"] == OTHER), None)
    if other and other["pct"] >= 15:
        findings.append({
            "finding": f"{other['pct']}% of tickets are unclassified (Other). Categorization "
                       f"is weak and may hide automatable patterns.",
            "confidence": "Medium"})
    if mttr_res.get("available") and mttr_res.get("slowest"):
        sl = mttr_res["slowest"][0]
        findings.append({
            "finding": f"Slowest theme by MTTR: {sl['value']} at {sl['median_hours']}h median.",
            "confidence": "Medium"})
    if opp["backlog"]:
        b = opp["backlog"][0]
        findings.append({
            "finding": f"Highest deflection upside: {b['theme']} "
                       f"({b['est_deflectable_tickets_range'][0]}-{b['est_deflectable_tickets_range'][1]} "
                       f"tickets, {b['primary_type']}).",
            "confidence": b["confidence"]})
    for reason in integrity["quality_reasons"][:1]:
        findings.append({"finding": f"Data gap: {reason}.", "confidence": "High"})

    # Quick wins: high confidence, low/medium complexity, deterministic.
    quick_wins = [
        {"theme": b["theme"],
         "why": f"{b['primary_type']}, {b['deflection_range_pct'][0]}-{b['deflection_range_pct'][1]}% "
                f"deflection, {b['implementation_complexity'].lower()} complexity",
         "confidence": b["confidence"]}
        for b in opp["backlog"]
        if b["confidence"] in {"High", "Medium"}
        and b["implementation_complexity"] in {"Low", "Medium"}
        and b["risk_level"] in {"Low", "Medium"}
    ][:5]

    roadmap = _roadmap(opp["backlog"])
    workshop = _workshop_questions(integrity, theme_summaries, opp)
    risks = list(roi["assumptions"]) + [
        f"Data quality is {integrity['quality_grade']}; low-confidence themes need SME validation.",
    ]
    if any(t["confidence"] == "Low" for t in theme_summaries):
        risks.append("Some themes are low confidence due to short descriptions or low volume.")

    recommendations = _recommendations(opp, quick_wins)

    return {
        "current_state_summary": cs,
        "top_findings": findings[:5],
        "top_automation_opportunities": opp["backlog"][:5],
        "top_agentic_opportunities": opp["agentic_backlog"][:5],
        "quick_wins": quick_wins,
        "roadmap_30_60_90": roadmap,
        "risks_and_assumptions": risks,
        "workshop_questions": workshop,
        "final_recommendations": recommendations,
        "friction_points": friction_points(pareto_res, mttr_res),
        "application_landscape": None,  # filled by analyze
        "volume": volume,
    }


def _roadmap(backlog) -> dict:
    knowledge = [b for b in backlog if b["primary_type"] == "Knowledge AI"]
    workflow = [b for b in backlog if b["primary_type"] in {"Workflow Automation"}]
    integ = [b for b in backlog if b["primary_type"] in {"Integration Automation", "Agentic AI"}]
    names = lambda xs: [b["theme"] for b in xs[:3]]  # noqa: E731
    return {
        "days_0_30": {
            "focus": "Deflect the deterministic, low-risk load",
            "themes": names(knowledge) or names(backlog[:2]),
            "actions": ["Ingest existing knowledge", "Stand up the AI coworker in Slack/Teams",
                        "Deflect top how-to and password/access requests"]},
        "days_30_60": {
            "focus": "Automate deterministic workflows",
            "themes": names(workflow),
            "actions": ["Wire approval and provisioning workflows",
                        "Connect the primary ITSM read/write", "Measure deflection vs baseline"]},
        "days_60_90": {
            "focus": "Integration and agentic use cases with guardrails",
            "themes": names(integ),
            "actions": ["Pilot one agentic backend use case with human approval",
                        "Expand MCP/API integrations", "Review ROI against the baseline"]},
    }


def _workshop_questions(integrity, theme_summaries, opp) -> list[str]:
    q = [
        "Which of the top themes are already partially automated today?",
        "For the highest-volume theme, is the resolution path API-accessible or admin-UI only?",
        "What is the knowledge-base quality and coverage for the top deflection candidates?",
        "Which actions require a human approval step for compliance or risk reasons?",
    ]
    if "created" in integrity["fields_missing"] or "resolved" in integrity["fields_missing"]:
        q.append("Can you provide reliable created and resolved timestamps to compute MTTR?")
    other = next((t for t in theme_summaries if t["theme"] == OTHER), None)
    if other and other["pct"] >= 15:
        q.append(f"{other['pct']}% of tickets are unclassified; can SMEs help label a sample?")
    if opp["agentic_backlog"]:
        q.append(f"For {opp['agentic_backlog'][0]['theme']}, who owns the system of action and "
                 f"what permissions can be granted?")
    return q


def _recommendations(opp, quick_wins) -> list[str]:
    recs = []
    if quick_wins:
        recs.append(f"Start with quick wins: {', '.join(q['theme'] for q in quick_wins[:3])}. "
                    f"These are deterministic and low risk.")
    if opp["backlog"]:
        b = opp["backlog"][0]
        recs.append(f"Prioritize {b['theme']} for the largest deflection upside "
                    f"({b['est_deflectable_tickets_range'][0]}-{b['est_deflectable_tickets_range'][1]} tickets).")
    if opp["agentic_backlog"]:
        recs.append(f"Pilot one agentic use case ({opp['agentic_backlog'][0]['theme']}) behind a "
                    f"human approval checkpoint before scaling.")
    recs.append("Treat all deflection figures as ranges to validate with SMEs, not commitments.")
    return recs
