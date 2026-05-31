"""
Router Agent — classifies user intent and delegates to specialist agents.
"""
import logging
import re
from enum import Enum
from typing import Any, Dict

from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from backend.services.llm_service import get_llm

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    SQL           = "sql"
    VISUALIZATION = "visualization"
    INSIGHT       = "insight"
    CLEANING      = "cleaning"
    PROFILING     = "profiling"
    REPORT        = "report"
    GENERAL       = "general"


ROUTER_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are a query router for a data analyst system.
Classify the following user question into exactly one category:

Categories:
- sql: the user wants raw data, table results, aggregations, or asks "show me data", "list", "top N", "how many"
- visualization: the user wants a chart, graph, plot, trend line, comparison visual
- insight: the user wants analysis, recommendations, anomalies, patterns, business insights
- cleaning: the user wants to fix data quality, handle missing values, remove duplicates
- profiling: the user wants a summary, statistics, data overview, column types, null counts
- report: the user wants to generate or download a PDF report
- general: anything else or unclear

User question: {question}

Respond with ONLY the category name (one word, lowercase). Do not explain.""",
)


class RouterAgent:
    """Determines which specialist agent should handle the user query."""

    def __init__(self) -> None:
        self._chain = LLMChain(llm=get_llm(), prompt=ROUTER_PROMPT)

    def classify(self, question: str) -> AgentType:
        """Returns the most appropriate AgentType for the given question."""
        try:
            raw = self._chain.run(question=question).strip().lower()
            # Extract first word to be safe
            word = re.sub(r"[^a-z]", "", raw.split()[0]) if raw else "general"
            return AgentType(word)
        except (ValueError, IndexError):
            logger.warning("Router could not classify '%s', defaulting to general", question)
            return AgentType.GENERAL

    def route(
        self,
        question: str,
        agents: Dict[AgentType, Any],
    ) -> Dict[str, Any]:
        """
        Classify question and invoke the matching agent.

        agents: mapping of AgentType → callable(question, **kwargs)
        """
        agent_type = self.classify(question)
        logger.info("Router → %s for: %s", agent_type, question[:80])

        handler = agents.get(agent_type) or agents.get(AgentType.GENERAL)
        if handler is None:
            return {"agent_used": agent_type, "answer": "No handler registered for this query type."}

        result = handler(question)
        result["agent_used"] = agent_type
        return result


router_agent = RouterAgent()
