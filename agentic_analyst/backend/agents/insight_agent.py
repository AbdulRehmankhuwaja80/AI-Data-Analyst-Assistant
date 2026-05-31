"""
Insight Agent — statistical analysis + LLM-generated business insights
"""
import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from backend.services.llm_service import get_llm

logger = logging.getLogger(__name__)

INSIGHT_PROMPT = PromptTemplate(
    input_variables=["stats_summary", "question"],
    template="""You are a senior business analyst. Based on the statistical summary below,
generate 4-6 concise, actionable business insights in bullet form.
Focus on: trends, outliers, top performers, risks, and recommendations.

Statistical summary:
{stats_summary}

User question: {question}

Output exactly one insight per line, starting with a dash (-). No preamble.""",
)


class InsightAgent:

    def __init__(self) -> None:
        self._chain = LLMChain(llm=get_llm(), prompt=INSIGHT_PROMPT)

    # ── Statistical helpers ──────────────────────────────────────────────────

    def _compute_stats(self, df: pd.DataFrame) -> str:
        lines: List[str] = []
        lines.append(f"Rows: {len(df)}, Columns: {len(df.columns)}")

        num_cols = df.select_dtypes(include="number").columns.tolist()
        for col in num_cols[:10]:   # cap for prompt length
            s = df[col].dropna()
            if len(s) == 0:
                continue
            lines.append(
                f"{col}: mean={s.mean():.2f}, std={s.std():.2f}, "
                f"min={s.min():.2f}, max={s.max():.2f}, "
                f"nulls={df[col].isna().sum()}"
            )

        # Top categorical values
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        for col in cat_cols[:5]:
            top = df[col].value_counts().head(3)
            lines.append(f"{col} top values: {top.to_dict()}")

        return "\n".join(lines)

    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, List]:
        anomalies: Dict[str, List] = {}
        for col in df.select_dtypes(include="number").columns:
            s = df[col].dropna()
            if len(s) < 10:
                continue
            q1, q3 = s.quantile(0.25), s.quantile(0.75)
            iqr = q3 - q1
            outlier_mask = (s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)
            if outlier_mask.sum() > 0:
                anomalies[col] = s[outlier_mask].tolist()
        return anomalies

    def run(self, question: str, df: pd.DataFrame) -> Dict[str, Any]:
        stats_summary = self._compute_stats(df)
        anomalies     = self._detect_anomalies(df)

        if anomalies:
            anom_text = "; ".join(
                f"{col}: {len(vals)} outliers" for col, vals in list(anomalies.items())[:5]
            )
            stats_summary += f"\nAnomalies detected: {anom_text}"

        raw = self._chain.run(stats_summary=stats_summary, question=question)

        insights = [
            line.lstrip("- ").strip()
            for line in raw.splitlines()
            if line.strip().startswith("-")
        ]

        return {
            "insights": insights,
            "answer":   "\n".join(f"• {i}" for i in insights),
        }


insight_agent = InsightAgent()
