from sda import analyze_dataframe
from sda.narrative import build_executive_narrative

from test_pipeline import _df


def test_grounded_narrative_uses_verified_aggregates_and_labels_estimates():
    result = build_executive_narrative(analyze_dataframe(_df()))
    text = " ".join(result["content"]["paragraphs"])
    assert result["generation_method"] == "deterministic"
    assert "10 tickets" in text
    assert "planning estimates" in text
    assert "not measured savings" in text
    assert "actively working" not in text
