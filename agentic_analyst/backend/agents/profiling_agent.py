"""
Data Profiling Agent — full statistical profile of a DataFrame
"""
import logging
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logger = logging.getLogger(__name__)


class DataProfilingAgent:

    def run(self, df: pd.DataFrame) -> Dict[str, Any]:
        profile: Dict[str, Any] = {}

        profile["row_count"]    = len(df)
        profile["column_count"] = len(df.columns)

        # Per-column stats
        columns_info: List[Dict[str, Any]] = []
        for col in df.columns:
            info: Dict[str, Any] = {
                "name":      col,
                "dtype":     str(df[col].dtype),
                "null_count":  int(df[col].isna().sum()),
                "null_pct":    round(df[col].isna().mean() * 100, 2),
                "unique_count": int(df[col].nunique()),
            }
            if pd.api.types.is_numeric_dtype(df[col]):
                s = df[col].dropna()
                info.update({
                    "mean":   round(float(s.mean()), 4)   if len(s) else None,
                    "std":    round(float(s.std()), 4)    if len(s) else None,
                    "min":    round(float(s.min()), 4)    if len(s) else None,
                    "max":    round(float(s.max()), 4)    if len(s) else None,
                    "median": round(float(s.median()), 4) if len(s) else None,
                    "p25":    round(float(s.quantile(0.25)), 4) if len(s) else None,
                    "p75":    round(float(s.quantile(0.75)), 4) if len(s) else None,
                })
            else:
                top = df[col].value_counts().head(5).to_dict()
                info["top_values"] = {str(k): int(v) for k, v in top.items()}

            columns_info.append(info)
        profile["columns"] = columns_info

        # Correlation matrix for numeric columns
        num_cols = df.select_dtypes(include="number")
        if len(num_cols.columns) >= 2:
            corr = num_cols.corr().round(3)
            profile["correlations"] = corr.to_dict()
        else:
            profile["correlations"] = {}

        # Build distribution charts (one per numeric column, max 6)
        profile["distribution_charts"] = self._build_distributions(df)
        profile["correlation_chart"]   = self._build_corr_heatmap(df)

        return profile

    @staticmethod
    def _build_distributions(df: pd.DataFrame) -> List[str]:
        """Returns list of Plotly JSON strings for distribution histograms."""
        charts: List[str] = []
        num_cols = df.select_dtypes(include="number").columns[:6]
        for col in num_cols:
            fig = px.histogram(
                df, x=col, title=f"Distribution: {col}",
                nbins=30, template="plotly_white",
                color_discrete_sequence=["#5DCAA5"],
            )
            fig.update_layout(margin=dict(l=30, r=30, t=50, b=30))
            charts.append(fig.to_json())
        return charts

    @staticmethod
    def _build_corr_heatmap(df: pd.DataFrame) -> str:
        num_df = df.select_dtypes(include="number")
        if len(num_df.columns) < 2:
            return ""
        corr = num_df.corr()
        fig = px.imshow(
            corr,
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            title="Correlation Matrix",
            template="plotly_white",
        )
        fig.update_layout(margin=dict(l=30, r=30, t=60, b=30))
        return fig.to_json()


profiling_agent = DataProfilingAgent()
