"""Steps 6-9 and 11: opportunity mapping, Atomicwork mapping, agentic backlog,
ROI ranges, and confidence. All rule-based and traceable to the theme data.

Nothing here fabricates value. ROI is expressed as ranges derived from the
actual ticket counts and the conservative deflection bands in the rules file,
always gated on the stated assumptions.
"""

from __future__ import annotations

import functools
from importlib import resources

import yaml

from . import util

_TYPE_LABELS = {
    "A": "Knowledge AI",
    "B": "Workflow Automation",
    "C": "Integration Automation",
    "D": "Agentic AI",
    "E": "Human-in-the-loop AI",
    "F": "No Automation Recommended",
}


@functools.lru_cache(maxsize=1)
def load_map() -> dict:
    text = resources.files("sda.rules").joinpath("atomicwork.yaml").read_text(encoding="utf-8")
    return yaml.safe_load(text)


def build(theme_summaries: list[dict], total_tickets: int) -> dict:
    rules = load_map()
    defaults = rules.get("defaults", {})
    theme_rules = rules["themes"]

    backlog, agentic, solution_map = [], [], []

    for ts in theme_summaries:
        theme = ts["theme"]
        r = theme_rules.get(theme, {})
        types = r.get("automation_types", ["F"])
        drange = r.get("deflection_range", defaults.get("deflection_range", [10, 30]))
        count = ts["count"]

        low = int(round(count * drange[0] / 100.0))
        high = int(round(count * drange[1] / 100.0))
        conf = _opportunity_confidence(ts, types)

        item = {
            "theme": theme,
            "tickets_addressable": count,
            "pct_of_total": ts["pct"],
            "automation_types": [{"code": t, "label": _TYPE_LABELS.get(t, t)} for t in types],
            "primary_type": _TYPE_LABELS.get(types[0], types[0]),
            "atomicwork_capabilities": r.get("capabilities", []),
            "deflection_range_pct": drange,
            "est_deflectable_tickets_range": [low, high],
            "mttr_reduction_potential": r.get("mttr_reduction", defaults.get("mttr_reduction", "Low")),
            "implementation_complexity": r.get("complexity", defaults.get("complexity", "Medium")),
            "risk_level": r.get("risk", defaults.get("risk", "Medium")),
            "integration_dependency": r.get("integration", []),
            "confidence": conf,
            "note": r.get("note"),
        }
        if types != ["F"]:
            backlog.append(item)

        solution_map.append({
            "theme": theme,
            "tickets": count,
            "capabilities": r.get("capabilities", []),
            "primary_type": item["primary_type"],
        })

        ag = r.get("agentic")
        if ag and count >= 10:
            agentic.append({
                "theme": theme,
                "tickets_addressable": count,
                "trigger": ag.get("trigger"),
                "system_of_action": ag.get("system_of_action"),
                "required_permissions": ag.get("permissions"),
                "workflow_steps": ag.get("steps", []),
                "automation_feasibility": ag.get("feasibility"),
                "risk_level": ag.get("risk"),
                "fallback_path": ag.get("fallback"),
                "human_approval_required": ag.get("human_approval"),
                "expected_impact": ag.get("expected_impact"),
                "confidence": conf,
            })

    backlog.sort(key=lambda x: x["est_deflectable_tickets_range"][1], reverse=True)
    agentic.sort(key=lambda x: x["tickets_addressable"], reverse=True)

    total_low = sum(b["est_deflectable_tickets_range"][0] for b in backlog)
    total_high = sum(b["est_deflectable_tickets_range"][1] for b in backlog)

    return {
        "backlog": backlog,
        "agentic_backlog": agentic,
        "solution_map": solution_map,
        "roi_summary": {
            "total_tickets": total_tickets,
            "addressable_tickets": sum(b["tickets_addressable"] for b in backlog),
            "est_total_deflectable_range": [total_low, total_high],
            "est_total_deflectable_pct_range": [
                util.pct(total_low, total_tickets), util.pct(total_high, total_tickets)],
            "assumptions": [
                "Deflection ranges assume the resolution path is API-accessible and knowledge quality is good.",
                "Ranges are planning estimates, not commitments; validate with SMEs before quoting.",
                "Physical fulfilment (hardware) and ambiguous 'Other' tickets are excluded from deflection upside.",
            ],
        },
    }


def _opportunity_confidence(ts: dict, types: list[str]) -> str:
    """High only when the theme is well-evidenced and the pattern is deterministic."""
    base = ts.get("confidence", "Low")
    deterministic = any(t in {"A", "B"} for t in types)
    if base == "High" and deterministic:
        return "High"
    if base == "Low":
        return "Low"
    return "Medium"
