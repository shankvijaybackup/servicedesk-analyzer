"""Step 4: Pareto analysis. Find the vital few driving most of the load.

Separates high-volume (many tickets) from high-pain (many hours of effort,
proxied by count x median MTTR) so the report does not conflate the two.
"""

from __future__ import annotations

import pandas as pd

from . import util


def pareto(series: pd.Series, *, top_share: float = 0.8) -> dict:
    """Rank the values of a dimension by volume and mark the 80% cut."""
    vc = series.dropna().value_counts()
    total = int(vc.sum())
    rows, cumulative = [], 0
    cut_index = None
    for rank, (value, count) in enumerate(vc.items(), start=1):
        cumulative += count
        cum_pct = util.pct(cumulative, total)
        rows.append({
            "rank": rank,
            "value": str(value),
            "count": int(count),
            "pct": util.pct(count, total),
            "cumulative_pct": cum_pct,
        })
        if cut_index is None and cum_pct >= top_share * 100:
            cut_index = rank
    vital_few = rows[:cut_index] if cut_index else rows
    return {
        "total": total,
        "distinct": len(rows),
        "vital_few_count": len(vital_few),
        "vital_few_share_of_categories": util.pct(len(vital_few), len(rows)) if rows else 0.0,
        "rows": rows,
        "vital_few": vital_few,
    }


def pain_ranking(classified: pd.DataFrame, dimension: str, n: int = 10) -> list[dict]:
    """Rank by estimated effort = count x median MTTR (hours). High-pain view."""
    rows = []
    for value, grp in classified.groupby(dimension):
        mttr = grp["mttr_hours"].dropna()
        med = float(mttr.median()) if len(mttr) else None
        effort = (len(grp) * med) if med is not None else None
        rows.append({
            "value": str(value),
            "count": len(grp),
            "mttr_median_hours": util.safe_round(med),
            "est_effort_hours": util.safe_round(effort),
        })
    ranked = [r for r in rows if r["est_effort_hours"] is not None]
    ranked.sort(key=lambda r: r["est_effort_hours"], reverse=True)
    return ranked[:n]


def build(classified: pd.DataFrame) -> dict:
    out = {"by_theme": pareto(classified["_theme"])}
    for dim, key in [("category", "by_category"), ("application", "by_application"),
                     ("assignment_group", "by_assignment_group")]:
        if classified[dim].notna().sum() > 0:
            out[key] = pareto(classified[dim])
    out["high_pain_themes"] = pain_ranking(classified, "_theme")
    if classified["application"].notna().sum() > 0:
        out["high_pain_applications"] = pain_ranking(classified, "application")
    return out
