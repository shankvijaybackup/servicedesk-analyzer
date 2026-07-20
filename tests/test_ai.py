"""Tests for the optional local AI boundary. No network is used."""

from __future__ import annotations

from sda import analyze_dataframe
from sda.ai import build_evidence_packet, draft_pilot, executive_narrative
from sda.ai.llamacpp import LlamaCppHTTPProvider

from test_pipeline import _df


class FakeProvider:
    name = "fake-local"

    def __init__(self, *, ready=True, content=None):
        self.ready = ready
        self.content = content
        self.last_prompt = ""

    def available(self):
        return self.ready

    def generate_json(self, *, system, prompt, schema):
        self.last_prompt = prompt
        return self.content


def test_evidence_packet_is_allowlisted_and_excludes_raw_ticket_text():
    analysis = analyze_dataframe(_df(), source_name="private-file.csv")
    packet = build_evidence_packet(analysis)
    serialized = str(packet)
    assert "Password reset for the portal" not in serialized
    assert "private-file.csv" not in serialized
    assert "examples" not in serialized
    assert "user213" not in serialized
    assert packet["data_quality"]["total_records"] == 10


def test_executive_narrative_is_labeled_advisory_and_does_not_mutate_analysis():
    analysis = analyze_dataframe(_df())
    before = repr(analysis)
    provider = FakeProvider(content={
        "title": "Observed service desk patterns",
        "paragraphs": ["The dataset contains ten records."],
        "citations": ["data_quality.total_records"],
    })
    result = executive_narrative(provider, analysis)
    assert result["status"] == "available"
    assert result["advisory_only"] is True
    assert "AI-generated" in result["label"]
    assert repr(analysis) == before
    assert "Password reset for the portal" not in provider.last_prompt


def test_unavailable_provider_fails_closed_without_generation():
    analysis = analyze_dataframe(_df())
    provider = FakeProvider(ready=False)
    result = draft_pilot(provider, analysis)
    assert result["status"] == "unavailable"
    assert result["content"] is None
    assert "unaffected" in result["label"]


def test_invalid_or_unsupported_citation_is_rejected():
    analysis = analyze_dataframe(_df())
    provider = FakeProvider(content={
        "title": "Unsafe",
        "paragraphs": ["Invented claim"],
        "citations": ["raw_tickets[0].description"],
    })
    result = executive_narrative(provider, analysis)
    assert result["status"] == "unavailable"
    assert result["content"] is None


def test_llamacpp_provider_rejects_non_loopback_endpoints():
    try:
        LlamaCppHTTPProvider("https://example.com")
    except ValueError as error:
        assert "loopback" in str(error)
    else:
        raise AssertionError("non-local endpoint should be rejected")
