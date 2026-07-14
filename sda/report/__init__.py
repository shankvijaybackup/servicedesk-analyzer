"""Report writers. Each turns the analysis dict into a deliverable file.

Reports contain aggregated analysis only (themes, metrics, opportunities), never
raw ticket rows, so no customer PII is written to disk.
"""

from __future__ import annotations

from pathlib import Path

FORMATS = ("html", "md", "json", "xlsx", "pptx")


def write_all(analysis: dict, outdir, *, basename: str = "servicedesk-analysis",
              formats=FORMATS) -> list[str]:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    if "json" in formats:
        from .json_out import write as wj
        written.append(wj(analysis, outdir / f"{basename}.json"))
    if "md" in formats:
        from .markdown import write as wm
        written.append(wm(analysis, outdir / f"{basename}.md"))
    if "html" in formats:
        from .html import write as wh
        written.append(wh(analysis, outdir / f"{basename}.html"))
    if "xlsx" in formats:
        from .excel import write as we
        written.append(we(analysis, outdir / f"{basename}.xlsx"))
    if "pptx" in formats:
        from .pptx import write as wp
        written.append(wp(analysis, outdir / f"{basename}.pptx"))

    return written
