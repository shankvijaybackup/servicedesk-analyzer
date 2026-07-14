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
        analysis = analyze_file(str(in_path))
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
        print("Wrote:")
        for path in written:
            print(f"  {path}")
        print("No data was retained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
