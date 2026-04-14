"""Dataset loading and column type detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pandas as pd


@dataclass
class DatasetInfo:
    """Holds the DataFrame plus inferred column groups."""
    df: pd.DataFrame
    filename: str
    numeric_cols: List[str] = field(default_factory=list)
    date_cols: List[str] = field(default_factory=list)
    cat_cols: List[str] = field(default_factory=list)

    @property
    def shape(self) -> tuple[int, int]:
        return self.df.shape

    @property
    def row_count(self) -> int:
        return len(self.df)

    @property
    def col_count(self) -> int:
        return len(self.df.columns)


def load_dataset(file_obj, filename: str) -> DatasetInfo:
    """Load a CSV/Excel/JSON file and return a DatasetInfo with column groups."""
    name = filename.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(file_obj)
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_obj)
    elif name.endswith(".json"):
        df = pd.read_json(file_obj)
    else:
        raise ValueError(f"Unsupported format: {filename}")

    return DatasetInfo(
        df=df,
        filename=filename,
        numeric_cols=df.select_dtypes(include="number").columns.tolist(),
        date_cols=[c for c in df.columns if any(kw in c.lower() for kw in ("date", "time", "month", "year", "day"))],
        cat_cols=df.select_dtypes(include="object").columns.tolist(),
    )
