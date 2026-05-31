"""
SQL Agent — natural language → SQL → execution → DataFrame
"""
import logging
import re
from typing import Any, Dict, Optional

import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.services.llm_service import get_llm

logger = logging.getLogger(__name__)

SQL_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template="""You are an expert SQL analyst. Given the database schema below and the user's question,
generate a single valid MySQL SELECT query.

Schema:
{schema}

Rules:
- Write only a SELECT statement, no INSERT/UPDATE/DELETE/DROP
- Always use LIMIT 1000 unless the question asks for a specific count
- Use column aliases for readability
- Return ONLY the SQL query, nothing else

Question: {question}

SQL:""",
)

EXPLAIN_PROMPT = PromptTemplate(
    input_variables=["sql", "question"],
    template="""Explain in plain English what the following SQL query does in relation to the question asked.
Be concise — 1-2 sentences.

Question: {question}
SQL: {sql}

Explanation:""",
)


class SQLAgent:
    def __init__(self) -> None:
        self._sql_chain     = LLMChain(llm=get_llm(), prompt=SQL_PROMPT)
        self._explain_chain = LLMChain(llm=get_llm(), prompt=EXPLAIN_PROMPT)

    def _build_schema(self, df: pd.DataFrame, table_name: str = "data") -> str:
        lines = [f"Table: {table_name}"]
        for col, dtype in df.dtypes.items():
            sample = df[col].dropna().head(3).tolist()
            lines.append(f"  {col} ({dtype}) — sample: {sample}")
        return "\n".join(lines)

    def _extract_sql(self, raw: str) -> str:
        """Strip markdown fences and extract the first SELECT statement."""
        raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE).strip()
        match = re.search(r"(SELECT\b.+)", raw, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else raw

    def _sanitise(self, sql: str) -> str:
        """Block write operations."""
        forbidden = re.compile(
            r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE)\b",
            re.IGNORECASE,
        )
        if forbidden.search(sql):
            raise ValueError("Generated SQL contains forbidden write operations.")
        return sql

    def run(
        self,
        question: str,
        df: pd.DataFrame,
        db: Optional[Session] = None,
        table_name: str = "data",
    ) -> Dict[str, Any]:
        """
        Generate + execute SQL against the in-memory DataFrame using pandasql.
        Falls back to error message on failure.
        """
        schema = self._build_schema(df, table_name)

        try:
            raw_sql = self._sql_chain.run(schema=schema, question=question)
            sql     = self._sanitise(self._extract_sql(raw_sql))
        except Exception as exc:
            logger.error("SQL generation failed: %s", exc)
            return {"sql": None, "result_data": [], "answer": f"Could not generate SQL: {exc}"}

        try:
            import pandasql as ps
            env = {table_name: df}
            result_df = ps.sqldf(sql, env)
            records = result_df.to_dict(orient="records")
        except Exception as exc:
            logger.warning("SQL execution failed (%s), returning raw LLM answer", exc)
            records = []

        explanation = self._explain_chain.run(sql=sql, question=question)

        return {
            "sql":         sql,
            "result_data": records,
            "answer":      explanation.strip(),
        }


sql_agent = SQLAgent()
