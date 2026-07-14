"""File ingestion for CSV and Excel. Stateless: nothing is written or cached."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def read_table(source, *, filename: str | None = None) -> pd.DataFrame:
    """Load a CSV/TSV/XLSX into a DataFrame from a path or bytes.

    Everything stays in memory. No file is created and no data is persisted.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        data = path.read_bytes()
        name = filename or path.name
    elif isinstance(source, (bytes, bytearray)):
        data = bytes(source)
        name = filename or ""
    elif hasattr(source, "read"):  # file-like (e.g. Streamlit UploadedFile)
        data = source.read()
        name = filename or getattr(source, "name", "")
    else:
        raise TypeError(f"Unsupported source type: {type(source)!r}")

    suffix = Path(name).suffix.lower()

    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return _clean(pd.read_excel(io.BytesIO(data), engine="openpyxl"))

    sep = "\t" if suffix in {".tsv", ".tab"} else None
    last_err: Exception | None = None
    for enc in _ENCODINGS:
        try:
            return _clean(
                pd.read_csv(
                    io.BytesIO(data),
                    encoding=enc,
                    sep=sep,
                    engine="python",
                    on_bad_lines="skip",
                )
            )
        except (UnicodeDecodeError, pd.errors.ParserError) as err:  # try next encoding
            last_err = err
            continue
    raise ValueError(f"Could not parse '{name}' as CSV/TSV: {last_err}")


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace from headers and drop fully empty rows/columns."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df = df.reset_index(drop=True)
    return df
