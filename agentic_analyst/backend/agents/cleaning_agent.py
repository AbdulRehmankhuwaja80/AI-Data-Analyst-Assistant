"""
Data Cleaning Agent — validates and fixes data quality issues
"""
import logging
import re
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataCleaningAgent:

    def run(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Clean the DataFrame and return (cleaned_df, report).
        """
        original_shape = df.shape
        report: Dict[str, Any] = {
            "original_rows":    original_shape[0],
            "original_columns": original_shape[1],
            "missing_fixed":    0,
            "duplicates_removed": 0,
            "columns_converted": 0,
            "outliers_flagged": 0,
            "summary": [],
        }

        df = df.copy()

        # 1. Standardise column names
        df.columns = [self._standardise_col(c) for c in df.columns]

        # 2. Remove duplicates
        before = len(df)
        df = df.drop_duplicates()
        removed_dupes = before - len(df)
        report["duplicates_removed"] = removed_dupes
        if removed_dupes:
            report["summary"].append(f"{removed_dupes} duplicate rows removed")

        # 3. Handle missing values
        missing_before = df.isna().sum().sum()
        for col in df.columns:
            if df[col].isna().sum() == 0:
                continue
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "UNKNOWN")
        missing_fixed = missing_before - df.isna().sum().sum()
        report["missing_fixed"] = int(missing_fixed)
        if missing_fixed:
            report["summary"].append(f"{missing_fixed} missing values imputed")

        # 4. Convert numeric-looking string columns
        converted = 0
        for col in df.select_dtypes(include="object").columns:
            try:
                df[col] = pd.to_numeric(df[col])
                converted += 1
            except (ValueError, TypeError):
                pass
        report["columns_converted"] = converted
        if converted:
            report["summary"].append(f"{converted} columns converted to numeric")

        # 5. Detect and cap outliers (IQR method)
        outlier_count = 0
        for col in df.select_dtypes(include="number").columns:
            q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            mask = (df[col] < lower) | (df[col] > upper)
            outlier_count += int(mask.sum())
            df[col] = df[col].clip(lower, upper)
        report["outliers_flagged"] = outlier_count
        if outlier_count:
            report["summary"].append(f"{outlier_count} outliers detected and capped")

        if not report["summary"]:
            report["summary"].append("Data looks clean — no significant issues found")

        report["final_rows"]    = len(df)
        report["final_columns"] = len(df.columns)
        return df, report

    @staticmethod
    def _standardise_col(name: str) -> str:
        name = str(name).strip().lower()
        name = re.sub(r"[\s\-]+", "_", name)
        name = re.sub(r"[^\w]", "", name)
        return name


cleaning_agent = DataCleaningAgent()
