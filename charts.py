"""Plotly chart builders — spec-driven, keyword auto-detect, and histogram."""

from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from loader import DatasetInfo

TEMPLATE = "plotly_dark"


def chart_from_spec(df: pd.DataFrame, spec: dict) -> Optional[go.Figure]:
    """Build a Plotly figure from an LLM-generated chart spec.
    Returns None if the columns don't exist in df."""
    chart_type = spec.get("type", "bar")
    x, y, title = spec.get("x", ""), spec.get("y", ""), spec.get("title", "")

    if x not in df.columns or y not in df.columns:
        return None

    builders = {
        "bar":     lambda: px.bar(df, x=x, y=y, title=title, template=TEMPLATE),
        "line":    lambda: px.line(df, x=x, y=y, title=title, template=TEMPLATE),
        "scatter": lambda: px.scatter(df, x=x, y=y, title=title, template=TEMPLATE),
        "pie":     lambda: px.pie(df, names=x, values=y, title=title, template=TEMPLATE),
    }
    builder = builders.get(chart_type)
    return builder() if builder else None


def auto_chart_from_query(query: str, dataset: DatasetInfo) -> Optional[go.Figure]:
    """Try to pick a sensible chart based on keywords in the user's question."""
    q = query.lower()
    df = dataset.df

    # Trend / time-series → line
    if any(w in q for w in ("trend", "over time", "by month", "by year", "over year")):
        if dataset.date_cols and dataset.numeric_cols:
            x, y = dataset.date_cols[0], dataset.numeric_cols[0]
            return px.line(df, x=x, y=y, title=f"{y} over {x}", template=TEMPLATE)

    # Rankings → bar
    if any(w in q for w in ("top", "highest", "most", "ranking", "best", "largest")):
        if dataset.cat_cols and dataset.numeric_cols:
            grp, val = dataset.cat_cols[0], dataset.numeric_cols[0]
            top10 = df.groupby(grp)[val].sum().nlargest(10).reset_index()
            return px.bar(top10, x=grp, y=val, title=f"Top {grp} by {val}", template=TEMPLATE)

    # Distribution → pie
    if any(w in q for w in ("distribution", "breakdown", "split", "proportion", "share")):
        if dataset.cat_cols:
            col = dataset.cat_cols[0]
            vc = df[col].value_counts().reset_index()
            vc.columns = [col, "count"]
            return px.pie(vc, names=col, values="count", title=f"Distribution of {col}", template=TEMPLATE)

    return None


def distribution_histogram(df: pd.DataFrame, column: str, nbins: int = 40) -> go.Figure:
    """Simple histogram for the data profile tab."""
    fig = px.histogram(df, x=column, nbins=nbins, title=f"Distribution of {column}", template=TEMPLATE)
    fig.update_layout(bargap=0.05)
    return fig
