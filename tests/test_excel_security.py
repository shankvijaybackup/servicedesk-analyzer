"""Security-focused tests for Excel report cell serialization."""

from __future__ import annotations

import pytest

from sda.report.excel import _cell


@pytest.mark.parametrize("value", ["=1+1", "+SUM(A1:A2)", "-cmd|' /C calc'!A0", "@SUM(1,1)"])
def test_formula_like_strings_are_forced_to_literal_text(value):
    assert _cell(value) == "'" + value


def test_negative_numeric_values_remain_numeric():
    assert _cell(-42) == -42
    assert _cell(-3.5) == -3.5


def test_safe_strings_and_nulls_keep_existing_behavior():
    assert _cell("Service Desk") == "Service Desk"
    assert _cell(None) == ""
    assert _cell(["safe", "values"]) == "safe, values"


def test_formula_like_joined_list_is_forced_to_literal_text():
    assert _cell(["=malicious", "value"]) == "'=malicious, value"
