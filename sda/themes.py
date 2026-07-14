"""Step 3: Enterprise theme categorization (deterministic, rule-based).

Each ticket's combined text is scored against keyword rules in rules/themes.yaml.
Highest-scoring theme wins; no match goes to "Other / Unclear". Matching uses
word boundaries so short tokens do not create false hits. This is a transparent
bag-of-keywords classifier, not a model: the same input always yields the same
theme, and every assignment can be traced to the keywords it matched.
"""

from __future__ import annotations

import functools
import re
from importlib import resources

import pandas as pd
import yaml

from . import util

OTHER = "Other / Unclear"


@functools.lru_cache(maxsize=1)
def load_rules() -> list[dict]:
    text = resources.files("sda.rules").joinpath("themes.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    rules = data["themes"]
    for r in rules:
        r["_pos"] = [_compile(k) for k in r.get("keywords", [])]
        r["_neg"] = [_compile(k) for k in r.get("negatives", [])]
    return rules


def _compile(phrase: str) -> re.Pattern:
    # Word-boundary match, phrase-aware (spaces become flexible whitespace).
    escaped = r"\s+".join(re.escape(tok) for tok in phrase.split())
    return re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)


def _score_text(text: str, rules: list[dict]) -> tuple[str, int, list[str]]:
    if not text:
        return OTHER, 0, []
    best_name, best_score, best_hits = OTHER, 0, []
    for r in rules:
        hits = [p.pattern for p in r["_pos"] if p.search(text)]
        score = len(hits)
        score -= sum(1 for p in r["_neg"] if p.search(text))
        if score > best_score:
            best_name, best_score, best_hits = r["name"], score, hits
    if best_score <= 0:
        return OTHER, 0, []
    return best_name, best_score, best_hits


def classify(norm: pd.DataFrame) -> pd.DataFrame:
    rules = load_rules()
    results = norm["_text"].fillna("").map(lambda t: _score_text(t, rules))
    out = norm.copy()
    out["_theme"] = results.map(lambda x: x[0])
    out["_theme_score"] = results.map(lambda x: x[1])
    return out


def theme_summary(classified: pd.DataFrame) -> list[dict]:
    total = len(classified)
    summaries = []
    for theme, grp in classified.groupby("_theme"):
        count = len(grp)
        mttr = grp["mttr_hours"].dropna()
        top_types = _top(grp["type"], 3)
        top_apps = _top(grp["application"], 3)
        examples = [str(x) for x in grp["short_description"].dropna().head(3).tolist()]
        avg_score = float(grp["_theme_score"].mean()) if count else 0.0
        desc_share = util.pct(grp["short_description"].notna().sum(), count)
        summaries.append({
            "theme": theme,
            "count": count,
            "pct": util.pct(count, total),
            "mttr_median_hours": util.safe_round(mttr.median()) if len(mttr) else None,
            "mttr_p90_hours": util.safe_round(mttr.quantile(0.9)) if len(mttr) else None,
            "top_types": top_types,
            "top_applications": top_apps,
            "examples": examples,
            "avg_match_score": util.safe_round(avg_score, 2),
            "description_coverage_pct": desc_share,
            "confidence": _theme_confidence(theme, count, avg_score, desc_share),
        })
    summaries.sort(key=lambda s: s["count"], reverse=True)
    return summaries


def _top(series: pd.Series, n: int) -> list[dict]:
    vc = series.dropna().value_counts().head(n)
    return [{"value": str(k), "count": int(v)} for k, v in vc.items()]


def _theme_confidence(theme: str, count: int, avg_score: float, desc_share: float) -> str:
    if theme == OTHER:
        return "Low"
    if count < 15:
        return "Low"
    if avg_score >= 2 and desc_share >= 70 and count >= 40:
        return "High"
    if avg_score >= 1 and desc_share >= 40:
        return "Medium"
    return "Low"
