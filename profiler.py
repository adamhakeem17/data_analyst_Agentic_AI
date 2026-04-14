"""Data quality profiling — per-column stats and a dataset-level summary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pandas as pd


@dataclass
class ColumnProfile:
    name: str
    dtype: str
    missing: int
    missing_pct: float
    unique: int
    sample_stat: str     # e.g. "min=1  max=99  mean=50" or "top='Laptop'"
    quality: str         # "✅ Good" / "⚠️ Warn" / "❌ High"

    def to_dict(self) -> dict:
        return {
            "Column": self.name,
            "Type": self.dtype,
            "Missing": f"{self.missing} ({self.missing_pct:.1f}%)",
            "Unique": self.unique,
            "Sample Stats": self.sample_stat,
            "Quality": self.quality,
        }


@dataclass
class DatasetProfile:
    rows: int
    cols: int
    total_missing: int
    missing_pct: float
    duplicates: int
    quality_score: float
    columns: List[ColumnProfile] = field(default_factory=list)

    def to_display_df(self) -> pd.DataFrame:
        return pd.DataFrame([c.to_dict() for c in self.columns])


def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    """Build a full quality profile for a DataFrame."""
    total_missing = int(df.isnull().sum().sum())
    total_cells = df.shape[0] * df.shape[1]
    missing_pct = total_missing / total_cells * 100 if total_cells else 0.0
    duplicates = int(df.duplicated().sum())

    columns = [_profile_column(df, col) for col in df.columns]

    dup_pct = duplicates / len(df) * 100 if len(df) else 0.0
    quality_score = max(0.0, 100.0 - missing_pct - dup_pct * 0.5)

    return DatasetProfile(
        rows=len(df),
        cols=len(df.columns),
        total_missing=total_missing,
        missing_pct=round(missing_pct, 1),
        duplicates=duplicates,
        quality_score=round(quality_score, 1),
        columns=columns,
    )


def _profile_column(df: pd.DataFrame, col: str) -> ColumnProfile:
    series = df[col]
    missing = int(series.isnull().sum())
    missing_pct = missing / len(df) * 100 if len(df) else 0.0
    unique = int(series.nunique())

    if pd.api.types.is_numeric_dtype(series):
        mn, mx, mu = series.min(), series.max(), series.mean()
        sample_stat = f"min={mn:.3g}  max={mx:.3g}  mean={mu:.3g}"
    else:
        top = series.value_counts().index[0] if unique > 0 else "—"
        sample_stat = f"top='{top}'"

    if missing_pct < 5:
        quality = "✅ Good"
    elif missing_pct < 20:
        quality = "⚠️ Warn"
    else:
        quality = "❌ High"

    return ColumnProfile(
        name=col,
        dtype=str(series.dtype),
        missing=missing,
        missing_pct=round(missing_pct, 1),
        unique=unique,
        sample_stat=sample_stat,
        quality=quality,
    )
