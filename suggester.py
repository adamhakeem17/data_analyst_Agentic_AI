"""Generates suggested questions from column names and types."""

from __future__ import annotations

from typing import List

from loader import DatasetInfo


def suggest_questions(dataset: DatasetInfo) -> List[str]:
    """Return up to 6 relevant questions based on detected column types."""
    suggestions: List[str] = []
    nc, dc, cc = dataset.numeric_cols, dataset.date_cols, dataset.cat_cols

    if nc:
        suggestions.append(f"What is the total and average of {nc[0]}?")
        if len(nc) >= 2:
            suggestions.append(f"Is there a correlation between {nc[0]} and {nc[1]}?")
        suggestions.append(f"Are there any outliers or anomalies in {nc[0]}?")

    if cc:
        suggestions.append(f"What are the top 5 values in {cc[0]} by count?")
        if nc:
            suggestions.append(f"Which {cc[0]} has the highest total {nc[0]}?")

    if dc and nc:
        suggestions.append(f"Show me the trend of {nc[0]} over {dc[0]} as a line chart.")

    suggestions.append("Give me a one-paragraph executive summary of this dataset.")
    return suggestions[:6]
