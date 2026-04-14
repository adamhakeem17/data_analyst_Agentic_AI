"""Tests for suggester.py and analyst.py response parsing."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest
from loader import DatasetInfo
from suggester import suggest_questions
from analyst import _parse_response


def _make_dataset(numeric=(), date=(), cat=()):
    df = pd.DataFrame({c: [1] for c in numeric} |
                      {c: ["2024-01-01"] for c in date} |
                      {c: ["A"] for c in cat})
    return DatasetInfo(
        df=df, filename="test.csv",
        numeric_cols=list(numeric),
        date_cols=list(date),
        cat_cols=list(cat),
    )


class TestSuggestQuestions:
    def test_returns_list(self):
        ds = _make_dataset(numeric=("revenue",), cat=("region",))
        assert isinstance(suggest_questions(ds), list)

    def test_max_six_suggestions(self):
        ds = _make_dataset(
            numeric=("revenue", "quantity", "cost"),
            date=("date",),
            cat=("region", "product"),
        )
        assert len(suggest_questions(ds)) <= 6

    def test_contains_numeric_question(self):
        ds = _make_dataset(numeric=("revenue",))
        assert any("revenue" in q for q in suggest_questions(ds))

    def test_contains_trend_question_when_date_and_numeric(self):
        ds = _make_dataset(numeric=("revenue",), date=("date",))
        assert any("trend" in q.lower() or "over" in q.lower() for q in suggest_questions(ds))

    def test_no_trend_without_date(self):
        ds = _make_dataset(numeric=("revenue",))
        assert not any("over" in q.lower() for q in suggest_questions(ds))

    def test_always_includes_summary(self):
        ds = _make_dataset()
        assert any("summary" in q.lower() for q in suggest_questions(ds))

    def test_empty_dataset_still_returns_list(self):
        ds = _make_dataset()
        assert isinstance(suggest_questions(ds), list)


class TestParseResponse:
    def test_no_chart_block_returns_full_text(self):
        raw = "The average revenue is $1,234."
        answer, spec = _parse_response(raw)
        assert answer == raw
        assert spec is None

    def test_valid_chart_block_extracted(self):
        raw = (
            'The top regions are North and South.\n\n'
            '```chart\n'
            '{"type": "bar", "x": "region", "y": "revenue", "title": "Revenue by Region"}\n'
            '```'
        )
        answer, spec = _parse_response(raw)
        assert "top regions" in answer
        assert "```chart" not in answer
        assert spec is not None
        assert spec["type"] == "bar"
        assert spec["x"] == "region"
        assert spec["y"] == "revenue"

    def test_invalid_json_in_chart_block_returns_none(self):
        _, spec = _parse_response("Some answer.\n```chart\n{not valid json}\n```")
        assert spec is None

    def test_invalid_chart_type_returns_none(self):
        _, spec = _parse_response('```chart\n{"type": "heatmap", "x": "a", "y": "b", "title": "T"}\n```')
        assert spec is None

    def test_missing_x_returns_none(self):
        _, spec = _parse_response('```chart\n{"type": "bar", "y": "revenue", "title": "T"}\n```')
        assert spec is None

    def test_answer_stripped(self):
        answer, _ = _parse_response("  Some answer.  ")
        assert answer == "Some answer."
