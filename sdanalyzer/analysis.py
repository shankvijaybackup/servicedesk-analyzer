"""Pareto, MTTR, and workflow-state analysis (methodology steps 4-5).

When resolution timestamps are missing, status distribution becomes the
primary friction signal (stuck/on-hold/transferred work), so the report
still says something useful instead of "MTTR not computable" and silence.
"""

import pandas as pd

STUCK_STATUSES = {"Pending", "On Hold", "Awaiting", "Waiting"}


def pareto(view: pd.DataFrame) -> dict:
    total = len(view)
    if not total:
        return {"drivers": [], "cutoff_themes": [], "high_volume": [], "high_pain": []}

    counts = view["theme"].value_counts()
    cum = counts.cumsum() / total * 100
    drivers = [
        {"theme": t, "count": int(c), "pct": round(c / total * 100, 1),
         "cumulative_pct": round(cum[t], 1)}
        for t, c in counts.items()
    ]
    cutoff = [d["theme"] for d in drivers if d["cumulative_pct"] <= 82 or d == drivers[0]]

    # High volume vs high pain (MTTR-weighted)
    med_all = view["mttr_hours"].dropna().median()
    high_volume, high_pain = [], []
    for t, grp in view.groupby("theme"):
        share = len(grp) / total
        med = grp["mttr_hours"].dropna().median()
        if share >= 0.10:
            high_volume.append({"theme": t, "count": len(grp), "pct": round(share * 100, 1)})
        if med is not None and not pd.isna(med) and med_all and med >= 1.5 * med_all and len(grp) >= max(3, total * 0.02):
            high_pain.append({"theme": t, "count": len(grp),
                              "mttr_median": round(float(med), 1),
                              "vs_overall": round(float(med / med_all), 1)})
    high_volume.sort(key=lambda d: d["count"], reverse=True)
    high_pain.sort(key=lambda d: d["mttr_median"], reverse=True)

    top_apps = view.loc[view["application"] != "", "application"].value_counts().head(10)
    top_groups = view.loc[view["assignment_group"] != "", "assignment_group"].value_counts().head(10)
    top_depts = view.loc[view["department"] != "", "department"].value_counts().head(10)

    return {
        "drivers": drivers,
        "cutoff_themes": cutoff,
        "high_volume": high_volume,
        "high_pain": high_pain,
        "top_applications": top_apps.to_dict(),
        "top_assignment_groups": top_groups.to_dict(),
        "top_departments": top_depts.to_dict(),
    }


def _mttr_by(view: pd.DataFrame, col: str, min_n: int = 3, top: int = 12) -> list[dict]:
    rows = []
    grp_src = view[view[col] != ""] if view[col].dtype == object else view
    for key, grp in grp_src.groupby(col):
        vals = grp["mttr_hours"].dropna()
        if len(vals) < min_n:
            continue
        rows.append({
            "key": str(key), "count": len(grp), "resolved_n": len(vals),
            "median": round(float(vals.median()), 1),
            "mean": round(float(vals.mean()), 1),
            "p90": round(float(vals.quantile(0.9)), 1),
        })
    rows.sort(key=lambda d: d["median"], reverse=True)
    return rows[:top]


def workflow_state_analysis(view: pd.DataFrame) -> dict:
    """Friction signals from ticket status: stuck share, transfer/bounce
    share, per-theme stuck rates. Works even when MTTR cannot be computed."""
    total = len(view)
    if not total:
        return {"available": False}
    status = view["status"].fillna("Unspecified")
    counts = status.value_counts()

    stuck_mask = status.isin(STUCK_STATUSES) | status.str.contains(
        r"hold|pending|await|waiting", case=False, na=False)
    transfer_mask = status.str.contains(r"transfer|escalat|reassign", case=False, na=False)
    open_mask = ~status.str.contains(r"closed|resolved|cancel", case=False, na=False)

    stuck_by_theme = []
    for theme, grp in view.groupby("theme"):
        s = grp["status"].str.contains(r"hold|pending|await|waiting", case=False, na=False).sum()
        if s >= 2:
            stuck_by_theme.append({"theme": theme, "stuck": int(s), "count": len(grp),
                                   "pct": round(s / len(grp) * 100, 1)})
    stuck_by_theme.sort(key=lambda d: d["stuck"], reverse=True)

    transfer_targets = None
    if transfer_mask.any():
        transfer_targets = status[transfer_mask].value_counts().head(8).to_dict()

    return {
        "available": True,
        "status_counts": counts.head(12).to_dict(),
        "stuck_n": int(stuck_mask.sum()),
        "stuck_pct": round(stuck_mask.mean() * 100, 1),
        "transfer_n": int(transfer_mask.sum()),
        "transfer_pct": round(transfer_mask.mean() * 100, 1),
        "transfer_targets": transfer_targets,
        "open_n": int(open_mask.sum()),
        "open_pct": round(open_mask.mean() * 100, 1),
        "stuck_by_theme": stuck_by_theme[:8],
    }


def mttr_analysis(view: pd.DataFrame) -> dict:
    vals = view["mttr_hours"].dropna()
    overall = None
    if len(vals):
        overall = {
            "resolved_n": len(vals),
            "coverage_pct": round(len(vals) / len(view) * 100, 1),
            "median": round(float(vals.median()), 1),
            "mean": round(float(vals.mean()), 1),
            "p90": round(float(vals.quantile(0.9)), 1),
            "source": view["mttr_source"].iloc[0] if len(view) else "computed",
        }
    by_theme = _mttr_by(view, "theme")
    by_priority = _mttr_by(view, "priority")
    by_app = _mttr_by(view, "application")
    by_group = _mttr_by(view, "assignment_group")
    by_subcat = _mttr_by(view, "subcategory_raw")

    slowest = by_theme[:3]
    fastest = sorted(by_theme, key=lambda d: d["median"])[:3]

    return {
        "overall": overall,
        "by_theme": by_theme,
        "by_priority": by_priority,
        "by_application": by_app,
        "by_assignment_group": by_group,
        "by_subcategory": by_subcat,
        "slowest_themes": slowest,
        "fastest_themes": fastest,
    }
