"""Optional, local-only AI assistance.

AI output is advisory prose. It is deliberately separate from the deterministic
analysis pipeline and cannot change metrics, recommendations, or decisions.
"""

from .base import AIProvider, AIUnavailableError
from .evidence import build_evidence_packet
from .service import draft_pilot, executive_narrative

__all__ = [
    "AIProvider",
    "AIUnavailableError",
    "build_evidence_packet",
    "draft_pilot",
    "executive_narrative",
]
