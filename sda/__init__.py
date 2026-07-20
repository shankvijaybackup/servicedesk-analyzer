"""Service Desk Analyzer.

Deterministic, offline analysis of service desk exports (CSV/XLSX) from any
ITSM tool. No LLM, no model training, no data retention. Every number is
computed by explicit, inspectable Python rules and is traceable to the input.
"""

__version__ = "0.2.0"

from .analyze import analyze_dataframe, analyze_file  # noqa: E402,F401
from .iteration import compare_dataframes  # noqa: E402,F401
from .pilots import CohortSpec, Guardrail, PilotCharter, recommend_pilot  # noqa: E402,F401

__all__ = ["analyze_dataframe", "analyze_file", "compare_dataframes", "CohortSpec",
           "Guardrail", "PilotCharter", "recommend_pilot", "__version__"]
