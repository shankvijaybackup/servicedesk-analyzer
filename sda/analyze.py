"""Orchestrator: run the full deterministic pipeline and return one analysis dict.

Pipeline: ingest -> detect schema -> integrity -> normalize -> classify ->
theme summary -> pareto -> MTTR -> opportunities -> executive layer.

Stateless: the input DataFrame lives only for the duration of the call. Nothing
is written to disk here and nothing is retained after the function returns.
"""

from __future__ import annotations

import datetime as _dt

import pandas as pd

from . import executive, integrity, mttr, opportunities, pareto, themes, uat
from .ingest import read_table
from .normalize import normalize
from .schema import detect_schema
from . import __version__


def analyze_dataframe(df: pd.DataFrame, *, source_name: str = "uploaded data") -> dict:
    schema = detect_schema(df)
    integ = integrity.assess(df, schema)

    norm = normalize(df, schema)
    classified = themes.classify(norm)

    theme_summaries = themes.theme_summary(classified)
    pareto_res = pareto.build(classified)
    mttr_res = mttr.build(classified)
    opp = opportunities.build(theme_summaries, integ["total_records"])
    volume = executive.volume_analysis(classified)

    exec_layer = executive.build(integ, theme_summaries, pareto_res, mttr_res, opp, volume)
    exec_layer["application_landscape"] = executive.application_landscape(classified)
    implementation = uat.build(classified, integ, theme_summaries, mttr_res)

    return {
        "meta": {
            "tool": "servicedesk-analyzer",
            "version": __version__,
            "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
            "source_name": source_name,
            "stateless_note": ("Analysis is deterministic and in-memory. No model was used, "
                               "no data was retained, and no data left this machine."),
        },
        "data_quality": integ,
        "volume": volume,
        "mttr": mttr_res,
        "themes": theme_summaries,
        "pareto": pareto_res,
        "application_landscape": exec_layer["application_landscape"],
        "opportunities": opp,
        "executive": exec_layer,
        "implementation": implementation,
    }


def analyze_file(source, *, filename: str | None = None) -> dict:
    """Load a CSV/XLSX (path, bytes, or file-like) and analyze it."""
    df = read_table(source, filename=filename)
    name = filename
    if name is None and isinstance(source, str):
        name = source
    return analyze_dataframe(df, source_name=name or "uploaded data")
