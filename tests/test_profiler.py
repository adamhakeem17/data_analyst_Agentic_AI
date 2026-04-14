"""Tests for profiler.py — no LLM calls, no file I/O."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import pytest
from profiler import profile_dataset, _profile_column


@pytest.fixture
def clean_df():
    return pd.DataFrame({
        "product": ["A", "B", "C", "D"],
        "revenue": [100.0, 200.0, 150.0, 300.0],
        "quantity": [10, 20, 15, 30],
    })

@pytest.fixture
def dirty_df():
    return pd.DataFrame({
        "name": ["Alice", None, "Charlie", None, None],
        "score": [90.0, 85.0, None, None, None],
        "region": ["North", "North", "South", "South", "South"],
    })

@pytest.fixture
def dup_df():
    return pd.DataFrame({"id": [1, 2, 2, 3], "value": [10, 20, 20, 30]})


class TestProfileDataset:
    def test_shape(self, clean_df):
        dp = profile_dataset(clean_df)
        assert dp.rows == 4
        assert dp.cols == 3

    def test_no_missing_clean(self, clean_df):
        dp = profile_dataset(clean_df)
        assert dp.total_missing == 0
        assert dp.missing_pct == 0.0

    def test_missing_count_dirty(self, dirty_df):
        dp = profile_dataset(dirty_df)
        assert dp.total_missing == 6  # 3 in name + 3 in score

    def test_duplicates_detected(self, dup_df):
        dp = profile_dataset(dup_df)
        assert dp.duplicates == 1

    def test_no_duplicates_clean(self, clean_df):
        dp = profile_dataset(clean_df)
        assert dp.duplicates == 0

    def test_quality_score_range(self, clean_df):
        dp = profile_dataset(clean_df)
        assert 0.0 <= dp.quality_score <= 100.0

    def test_quality_score_high_for_clean(self, clean_df):
        dp = profile_dataset(clean_df)
        assert dp.quality_score > 90.0

    def test_quality_score_lower_for_dirty(self, dirty_df):
        clean_dp = profile_dataset(pd.DataFrame({"a": [1, 2, 3]}))
        dirty_dp = profile_dataset(dirty_df)
        assert dirty_dp.quality_score < clean_dp.quality_score

    def test_column_count_matches(self, clean_df):
        dp = profile_dataset(clean_df)
        assert len(dp.columns) == len(clean_df.columns)

    def test_to_display_df_shape(self, clean_df):
        dp = profile_dataset(clean_df)
        display = dp.to_display_df()
        assert len(display) == 3
        assert "Column" in display.columns
        assert "Quality" in display.columns


class TestProfileColumn:
    def test_numeric_column_sample_stat(self, clean_df):
        cp = _profile_column(clean_df, "revenue")
        assert "min=" in cp.sample_stat
        assert "max=" in cp.sample_stat
        assert "mean=" in cp.sample_stat

    def test_categorical_column_sample_stat(self, clean_df):
        cp = _profile_column(clean_df, "product")
        assert "top=" in cp.sample_stat

    def test_good_quality_no_missing(self, clean_df):
        cp = _profile_column(clean_df, "revenue")
        assert cp.quality == "✅ Good"
        assert cp.missing == 0
        assert cp.missing_pct == 0.0

    def test_high_quality_band_for_dirty_column(self, dirty_df):
        cp = _profile_column(dirty_df, "score")
        assert cp.quality == "❌ High"

    def test_warn_quality_band(self):
        df = pd.DataFrame({"x": [1, None, 3, 4, 5, 6, 7, 8, 9, 10]})
        cp = _profile_column(df, "x")
        assert cp.quality == "⚠️ Warn"

    def test_unique_count(self, clean_df):
        cp = _profile_column(clean_df, "product")
        assert cp.unique == 4
