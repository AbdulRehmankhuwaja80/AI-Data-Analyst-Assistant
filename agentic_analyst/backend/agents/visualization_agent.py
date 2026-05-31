"""
Visualization Agent — determines best chart type and produces Plotly figure JSON.
"""
import logging
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from backend.services.llm_service import get_llm

logger = logging.getLogger(__name__)

CHART_SELECT_PROMPT = PromptTemplate(
    input_variables=["columns", "dtypes", "question"],
    template="""You are a data visualization expert.
Given the columns, their data types, and the user's question, choose the best chart type.

Columns and types:
{columns}

Question: {question}

Available chart types: line, bar, pie, scatter, histogram, heatmap, box

Respond with a JSON object ONLY (no markdown, no extra text):
{{
  "chart_type": "<chosen type>",
  "x_column": "<column name or null>",
  "y_column": "<column name or null>",
  "color_column": "<column name or null>",
  "title": "<short chart title>"
}}""",
)


class VisualizationAgent:

    COLOUR_PALETTE = px.colors.qualitative.Pastel

    def __init__(self) -> None:
        self._chain = LLMChain(llm=get_llm(), prompt=CHART_SELECT_PROMPT)

    def _parse_chart_config(self, raw: str) -> Dict[str, Any]:
        import json, re
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Could not parse chart config JSON: %s", raw[:200])
            return {}

    def _build_figure(
        self,
        df: pd.DataFrame,
        cfg: Dict[str, Any],
    ) -> Optional[go.Figure]:
        ct     = cfg.get("chart_type", "bar")
        x_col  = cfg.get("x_column")
        y_col  = cfg.get("y_column")
        color  = cfg.get("color_column")
        title  = cfg.get("title", "Chart")

        # Validate columns exist
        valid_x     = x_col if x_col and x_col in df.columns else None
        valid_y     = y_col if y_col and y_col in df.columns else None
        valid_color = color if color and color in df.columns else None

        try:
            fig: go.Figure
            if ct == "line":
                fig = px.line(df, x=valid_x, y=valid_y, color=valid_color, title=title,
                              color_discrete_sequence=self.COLOUR_PALETTE)
            elif ct == "bar":
                fig = px.bar(df, x=valid_x, y=valid_y, color=valid_color, title=title,
                             color_discrete_sequence=self.COLOUR_PALETTE)
            elif ct == "pie":
                names_col  = valid_x or df.columns[0]
                values_col = valid_y or df.select_dtypes("number").columns[0]
                fig = px.pie(df, names=names_col, values=values_col, title=title,
                             color_discrete_sequence=self.COLOUR_PALETTE)
            elif ct == "scatter":
                fig = px.scatter(df, x=valid_x, y=valid_y, color=valid_color, title=title,
                                 color_discrete_sequence=self.COLOUR_PALETTE)
            elif ct == "histogram":
                col = valid_x or df.select_dtypes("number").columns[0]
                fig = px.histogram(df, x=col, color=valid_color, title=title,
                                   color_discrete_sequence=self.COLOUR_PALETTE)
            elif ct == "heatmap":
                num_df = df.select_dtypes("number")
                fig = px.imshow(num_df.corr(), title=title, color_continuous_scale="RdBu_r")
            elif ct == "box":
                fig = px.box(df, x=valid_x, y=valid_y, color=valid_color, title=title,
                             color_discrete_sequence=self.COLOUR_PALETTE)
            else:
                fig = px.bar(df, x=valid_x, y=valid_y, title=title,
                             color_discrete_sequence=self.COLOUR_PALETTE)

            fig.update_layout(
                template="plotly_white",
                font_family="sans-serif",
                margin=dict(l=40, r=40, t=60, b=40),
            )
            return fig
        except Exception as exc:
            logger.error("Figure build failed: %s", exc)
            return None

    def run(self, question: str, df: pd.DataFrame) -> Dict[str, Any]:
        cols_info = "\n".join(f"  {c}: {dt}" for c, dt in df.dtypes.items())

        raw_cfg = self._chain.run(columns=cols_info, question=question)
        cfg     = self._parse_chart_config(raw_cfg)

        fig = self._build_figure(df, cfg)
        if fig is None:
            return {"chart_json": None, "answer": "Could not build a visualization for this query."}

        return {
            "chart_json": fig.to_json(),
            "answer":     f"Generated a {cfg.get('chart_type', 'chart')}: {cfg.get('title', '')}",
        }


visualization_agent = VisualizationAgent()
