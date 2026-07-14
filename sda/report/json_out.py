"""Machine-readable JSON of the full analysis."""

from __future__ import annotations

import json
from pathlib import Path


def write(analysis: dict, path) -> str:
    path = Path(path)
    path.write_text(json.dumps(analysis, indent=2, default=str), encoding="utf-8")
    return str(path)
