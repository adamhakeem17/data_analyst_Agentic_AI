"""LangChain Pandas agent wrapper — handles LLM interaction and response parsing."""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from langchain_ollama import OllamaLLM
from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_experimental.agents.agent_toolkits.pandas.base import AgentType

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


@dataclass
class AnalysisResult:
    query: str
    answer: str
    chart_spec: Optional[dict] = None
    error: Optional[str] = None

    @property
    def has_chart_spec(self) -> bool:
        return self.chart_spec is not None

    @property
    def success(self) -> bool:
        return self.error is None


_CHART_INSTRUCTION = """

Additionally, if a chart would genuinely help illustrate the answer,
append a chart specification at the very end of your response in this
exact format (no other text after it):

```chart
{{"type": "bar|line|pie|scatter", "x": "column_name", "y": "column_name", "title": "Chart Title"}}
```

Only include the chart block if it adds real value. Omit it for
purely numerical or text answers."""


class DataAnalyst:
    """One instance per uploaded dataset. Wraps the LangChain Pandas agent
    with automatic chart-spec extraction from LLM responses."""

    def __init__(self, df: pd.DataFrame, model: str = "llama3", temperature: float = 0.0):
        self._df = df
        self._model = model
        log.info("Setting up %s (temperature=%.1f)", model, temperature)
        self._llm = OllamaLLM(model=model, temperature=temperature)
        self._agent = create_pandas_dataframe_agent(
            self._llm,
            self._df,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            allow_dangerous_code=True,
        )
        log.info("Agent ready")

    def query(self, user_query: str) -> AnalysisResult:
        enhanced = user_query + _CHART_INSTRUCTION
        try:
            log.info("Query: %s", user_query)
            t0 = time.time()
            result = self._agent.invoke({"input": enhanced})
            raw = result.get("output", str(result))
            log.info("Response in %.1fs (%d chars)", time.time() - t0, len(raw))
        except Exception as exc:
            log.error("Agent error: %s", exc, exc_info=True)
            return AnalysisResult(query=user_query, answer="", error=str(exc))

        answer, chart_spec = _parse_response(raw)
        return AnalysisResult(query=user_query, answer=answer, chart_spec=chart_spec)


def _parse_response(raw: str) -> tuple[str, Optional[dict]]:
    """Split the agent response into (answer_text, chart_spec_or_none)."""
    match = re.search(r"```chart\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if not match:
        return raw.strip(), None

    answer = raw[:match.start()].strip()
    try:
        spec = json.loads(match.group(1))
        if spec.get("type") in {"bar", "line", "pie", "scatter"} and spec.get("x") and spec.get("y"):
            return answer, spec
    except json.JSONDecodeError:
        pass

    return answer, None
