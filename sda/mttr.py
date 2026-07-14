"""Step 5: MTTR analysis. Where resolution is slow, and where it is fast.

MTTR is reported only when it can be computed. Slow/fast areas are flagged, but
the module never claims a reduction is achievable; that judgement is made in the
opportunity engine only where a clear automation path exists.
"""

from __future__ import annotations

import pandas as pd

from . import util

_MIN_GROUP = 5  # do not rank a group's MTTR on fewer than this many resolved tickets


def _stats(mttr: pd.Series) -> dict | None:
    m = mttr.dropna()
    if len(m) == 0:
        return None
    return {
        "n": int(len(m)),
        "median_hours": util.safe_round(m.median()),
        "mean_hours": util.safe_round(m.mean()),
        "p90_hours": util.safe_round(m.quantile(0.9)),
    }


def _by(classified: pd.DataFrame, dim: str) -> list[dict]:
    rows = []
    for value, grp in classified.groupby(dim):
        s = _stats(grp["mttr_hours"])
        if s and s["n"] >= _MIN_GROUP:
            rows.append({"value": str(value), **s})
    rows.sort(key=lambda r: r["median_hours"] if r["median_hours"] is not None else -1,
              reverse=True)
    return rows


def build(classified: pd.DataFrame) -> dict:
    overall = _stats(classified["mttr_hours"])
    if overall is None:
        return {"available": False,
                "note": "MTTR could not be computed (no resolution time or timestamps)."}

    result = {"available": True, "overall": overall}
    for dim, key in [("_theme", "by_theme"), ("category", "by_category"),
                     ("subcategory", "by_subcategory"), ("application", "by_application"),
                     ("priority", "by_priority"), ("assignment_group", "by_assignment_group")]:
        if dim in classified and classified[dim].notna().sum() > 0:
            rows = _by(classified, dim)
            if rows:
                result[key] = rows

    themes = result.get("by_theme", [])
    result["slowest"] = themes[:5]
    result["fastest"] = sorted(
        themes, key=lambda r: r["median_hours"] if r["median_hours"] is not None else 1e9
    )[:5]
    return result
