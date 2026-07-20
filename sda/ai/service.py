"""Advisory AI features over safe aggregate evidence only."""

from __future__ import annotations

import json
from typing import Any

from .base import AIProvider, AIUnavailableError
from .evidence import build_evidence_packet, evidence_paths

_SYSTEM = (
    "You are a precise service-desk analyst. Use only the supplied aggregate evidence. "
    "Do not invent facts, causes, business impact, urgency, ROI, or outcomes. "
    "Do not call an issue critical, significant, or high ROI unless those exact conclusions "
    "exist in the evidence. Distinguish observed metrics from planning estimates. "
    "Write two concise paragraphs in plain language, each under 100 words and ending with "
    "complete punctuation. Avoid generic phrases about organizational productivity. "
    "Return JSON matching the schema. "
    "Every factual statement must cite supplied evidence. The citations array may contain "
    "only these exact values: data_quality, mttr, themes, opportunities."
)

_APPROVED_CITATION_ROOTS = {"data_quality", "mttr", "themes", "opportunities"}


def executive_narrative(provider: AIProvider, analysis: dict[str, Any]) -> dict[str, Any]:
    """Draft an executive narrative without changing the analysis."""
    return _generate(provider, analysis, "executive narrative", {
        "type": "object",
        "additionalProperties": False,
        "required": ["title", "paragraphs", "citations"],
        "properties": {
            "title": {"type": "string", "maxLength": 120},
            "paragraphs": {"type": "array", "minItems": 2, "maxItems": 2,
                           "items": {"type": "string", "maxLength": 650}},
            "citations": {"type": "array", "minItems": 1, "maxItems": 8,
                          "items": {"type": "string", "maxLength": 160}},
        },
    })


def draft_pilot(provider: AIProvider, analysis: dict[str, Any]) -> dict[str, Any]:
    """Draft pilot wording from existing evidence, never select or approve a pilot."""
    return _generate(provider, analysis, "pilot charter draft", {
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "problem", "scope", "intervention", "measurement_notes", "citations"],
        "properties": {
            "name": {"type": "string", "maxLength": 120},
            "problem": {"type": "string", "maxLength": 500},
            "scope": {"type": "string", "maxLength": 300},
            "intervention": {"type": "string", "maxLength": 500},
            "measurement_notes": {"type": "array", "maxItems": 5,
                                  "items": {"type": "string", "maxLength": 300}},
            "citations": {"type": "array", "minItems": 1, "maxItems": 8,
                          "items": {"type": "string", "maxLength": 160}},
        },
    })


def _generate(
    provider: AIProvider,
    analysis: dict[str, Any],
    task: str,
    schema: dict[str, Any],
) -> dict[str, Any]:
    packet = build_evidence_packet(analysis)
    if not provider.available():
        return _unavailable(provider.name, "Local AI is not running or configured")
    prompt = f"Task: {task}\nAggregate evidence:\n{json.dumps(packet, sort_keys=True)}"
    content = None
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            content = provider.generate_json(system=_SYSTEM, prompt=prompt, schema=schema)
            _validate(content, schema, evidence_paths(packet))
            last_error = None
            break
        except AIUnavailableError as error:
            return _unavailable(provider.name, str(error))
        except (ValueError, TypeError) as error:
            last_error = error
            prompt += ("\nYour previous response was rejected: " + str(error) +
                       ". Return a corrected response using only observed evidence and "
                       "clearly labeled planning estimates.")
    if last_error is not None or content is None:
        return _unavailable(provider.name, str(last_error))
    return {
        "status": "available",
        "label": "AI-generated advisory draft. Verify before use.",
        "provider": provider.name,
        "advisory_only": True,
        "content": content,
    }


def _validate(content: dict[str, Any], schema: dict[str, Any], allowed_paths: set[str]) -> None:
    if not isinstance(content, dict):
        raise TypeError("AI response must be a JSON object")
    missing = [key for key in schema.get("required", []) if key not in content]
    if missing:
        raise ValueError(f"AI response missing required fields: {', '.join(missing)}")
    citations = content.get("citations")
    if not isinstance(citations, list) or not citations:
        raise ValueError("AI response must include evidence citations")
    invalid = []
    for path in citations:
        if not isinstance(path, str):
            invalid.append(path)
            continue
        root = path.split(".", 1)[0].split("[", 1)[0]
        if root not in _APPROVED_CITATION_ROOTS or path not in allowed_paths:
            invalid.append(path)
    if invalid:
        raise ValueError("AI response cited evidence outside the safe packet")
    paragraphs = content.get("paragraphs")
    if paragraphs is not None:
        if not isinstance(paragraphs, list) or any(
                not isinstance(p, str) or not p.strip().endswith((".", "!", "?"))
                for p in paragraphs):
            raise ValueError("AI response contained incomplete narrative text")
        prose = " ".join(paragraphs).lower()
        unsupported = (
            "actively working", "indicating that", "this suggests", "high roi",
            "critical issue", "critical challenge", "significant challenge",
            "impacting productivity", "driving business growth",
        )
        if any(phrase in prose for phrase in unsupported):
            raise ValueError("AI response contained an unsupported inference")


def _unavailable(provider: str, reason: str) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "label": "AI assistance unavailable. Deterministic analysis is unaffected.",
        "provider": provider,
        "advisory_only": True,
        "reason": reason,
        "content": None,
    }
