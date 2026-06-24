"""M4 — ExplainService 单测。"""
import pytest
from pydantic import ValidationError
from grammar_engine.ai.explain.explain_service import (
    ExplainResponseModel,
    parse_response,
    ParseFail,
)


def test_parse_valid_json():
    raw = '{"title":"t","summary":"s","why":"w","example":"e","common_mistakes":["m"],"tips":["t"]}'
    r = parse_response(raw)
    assert r.title == "t"
    assert r.common_mistakes == ["m"]


def test_parse_missing_fields_uses_defaults():
    raw = '{"title":"only title"}'
    r = parse_response(raw)
    assert r.title == "only title"
    assert r.summary == ""
    assert r.common_mistakes == []


def test_parse_invalid_json_raises_parse_fail():
    with pytest.raises(ParseFail):
        parse_response("not json at all")


def test_parse_non_object_raises_parse_fail():
    with pytest.raises(ParseFail):
        parse_response("[]")
