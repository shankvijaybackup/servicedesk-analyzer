"""Command-line interface.

Usage:
    sda path/to/tickets.csv --out reports --formats html,pptx,md,json,xlsx
    python -m sda.cli tickets.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyze import analyze_file
from .ingest import read_table
from .iteration import compare_dataframes
from .pilots import CohortSpec, PilotCharter
from .report import FORMATS, write_all


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sda",
        description="Deterministic, offline service desk analyzer. "
                    "No LLM, no training, no data retained.",
    )
    p.add_argument("input", help="Path to a CSV, TSV, or XLSX export from any ITSM tool.")
    p.add_argument("-o", "--out", default="reports", help="Output directory (default: reports).")
    p.add_argument("-f", "--formats", default="html,md,json,xlsx,pptx",
                   help=f"Comma-separated subset of: {','.join(FORMATS)} (default: all).")
    p.add_argument("-n", "--name", default=None,
                   help="Base filename for outputs (default: derived from input).")
    p.add_argument("--quiet", action="store_true", help="Suppress the summary printout.")
    p.add_argument("--compare-with", default=None,
                   help="Follow-up CSV/XLSX for an iterative pilot comparison.")
    p.add_argument("--pilot-name", default="Service desk improvement pilot")
    p.add_argument("--theme", default=None, help="Limit comparison to one classified theme.")
    p.add_argument("--assignment-group", default=None, help="Limit comparison to one team/queue.")
    p.add_argument("--primary-metric", default="median_mttr_hours")
    p.add_argument("--minimum-improvement", type=float, default=10.0)
    p.add_argument("--minimum-cohort-size", type=int, default=20)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"error: file not found: {in_path}", file=sys.stderr)
        return 2

    formats = tuple(f.strip().lower() for f in args.formats.split(",") if f.strip())
    unknown = [f for f in formats if f not in FORMATS]
    if unknown:
        print(f"error: unknown formats {unknown}; choose from {list(FORMATS)}", file=sys.stderr)
        return 2

    basename = args.name or in_path.stem + "-analysis"

    try:
        analysis_source = args.compare_with or str(in_path)
        analysis = analyze_file(analysis_source)
        if args.compare_with:
            follow_path = Path(args.compare_with)
            if not follow_path.exists():
                print(f"error: follow-up file not found: {follow_path}", file=sys.stderr)
                return 2
            charter = PilotCharter(
                pilot_id="cli-pilot",
                name=args.pilot_name,
                intervention="User-defined pilot intervention",
                cohort=CohortSpec(
                    themes=(args.theme,) if args.theme else (),
                    assignment_groups=(args.assignment_group,) if args.assignment_group else (),
                ),
                primary_metric=args.primary_metric,
                minimum_improvement_pct=args.minimum_improvement,
                minimum_cohort_size=args.minimum_cohort_size,
            )
            analysis["iteration"] = compare_dataframes(
                read_table(str(in_path)), read_table(str(follow_path)), charter,
                baseline_name=in_path.name, follow_up_name=follow_path.name,
            )
        written = write_all(analysis, args.out, basename=basename, formats=formats)
    except Exception as err:  # surface a clean message, not a traceback, to end users
        print(f"error: {err}", file=sys.stderr)
        return 1

    if not args.quiet:
        dq = analysis["data_quality"]
        roi = analysis["opportunities"]["roi_summary"]
        print(f"Analyzed {dq['total_records']} records "
              f"(quality {dq['quality_grade']} {dq['quality_score']}/100).")
        print(f"Estimated deflectable: {roi['est_total_deflectable_pct_range'][0]}-"
              f"{roi['est_total_deflectable_pct_range'][1]}% of volume (planning range).")
        if analysis.get("iteration"):
            print(f"Pilot decision: {analysis['iteration']['decision']['code']} "
                  f"(comparability {analysis['iteration']['comparability']['status']}).")
        print("Wrote:")
        for path in written:
            print(f"  {path}")
        print("No data was retained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
