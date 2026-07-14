#!/usr/bin/env python3
"""CLI: analyze a service desk CSV or XLSX export and write reports.

Usage:
    python cli.py tickets.csv                       # writes report.html
    python cli.py tickets.xlsx -f md html pptx ppt-outline -o out_dir
"""

import argparse
import os
import sys

from sdanalyzer import report as report_mod
from sdanalyzer import render_md, render_html, render_pptx


def main():
    ap = argparse.ArgumentParser(description="Service Desk Intelligence Analyzer (no LLM, no data retention)")
    ap.add_argument("csv", help="Path to the service desk CSV or XLSX export")
    ap.add_argument("-f", "--formats", nargs="+", default=["html"],
                    choices=["html", "md", "pptx", "ppt-outline"],
                    help="Output formats (default: html)")
    ap.add_argument("-o", "--outdir", default=".", help="Output directory (default: current)")
    args = ap.parse_args()

    if not os.path.isfile(args.csv):
        sys.exit(f"File not found: {args.csv}")

    name = os.path.basename(args.csv)
    base = os.path.splitext(name)[0] + "_report"
    os.makedirs(args.outdir, exist_ok=True)

    rep = report_mod.analyze(args.csv, source_name=name)

    written = []
    if "md" in args.formats:
        path = os.path.join(args.outdir, base + ".md")
        with open(path, "w") as f:
            f.write(render_md.render(rep))
        written.append(path)
    if "html" in args.formats:
        path = os.path.join(args.outdir, base + ".html")
        with open(path, "w") as f:
            f.write(render_html.render(rep))
        written.append(path)
    if "pptx" in args.formats:
        path = os.path.join(args.outdir, base + ".pptx")
        with open(path, "wb") as f:
            f.write(render_pptx.render(rep))
        written.append(path)
    if "ppt-outline" in args.formats:
        path = os.path.join(args.outdir, base + "_slides.txt")
        lines = []
        for i, s in enumerate(rep["slides"], 1):
            lines.append(f"Slide {i}: {s['title']}")
            lines += [f"  - {b}" for b in s["bullets"]]
            lines.append("")
        with open(path, "w") as f:
            f.write("\n".join(lines))
        written.append(path)

    print(f"Analyzed {rep['n_analyzed']} records "
          f"(quality: {rep['quality']['verdict']}, period: {rep['meta']['date_range_str']})")
    for w in written:
        print(f"  -> {w}")
    print("Source data was processed in memory only and has been discarded.")


if __name__ == "__main__":
    main()
