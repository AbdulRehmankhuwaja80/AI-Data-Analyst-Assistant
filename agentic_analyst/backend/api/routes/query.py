"""
Query routes — /api/query
Routes natural language questions through the Router Agent.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.orm_models import ChatHistory
from backend.schemas.schemas import QueryRequest, QueryResponse
from backend.services.dataset_service import dataset_service
from backend.agents.router_agent import router_agent, AgentType
from backend.agents.sql_agent import sql_agent
from backend.agents.visualization_agent import visualization_agent
from backend.agents.insight_agent import insight_agent
from backend.agents.cleaning_agent import cleaning_agent
from backend.agents.profiling_agent import profiling_agent

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=QueryResponse)
def run_query(req: QueryRequest, db: Session = Depends(get_db)):
    try:
        df = dataset_service.load(req.dataset_id, db)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(404, str(exc))

    # Build handler map
    def handle_sql(q):
        return sql_agent.run(q, df)

    def handle_viz(q):
        return visualization_agent.run(q, df)

    def handle_insight(q):
        return insight_agent.run(q, df)

    def handle_cleaning(q):
        _, report = cleaning_agent.run(df)
        return {"insights": report["summary"], "answer": "; ".join(report["summary"])}

    def handle_profiling(q):
        profile = profiling_agent.run(df)
        summary = (
            f"Rows: {profile['row_count']}, Columns: {profile['column_count']}. "
            f"See profiling page for full report."
        )
        return {"answer": summary}

    def handle_general(q):
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain
        from backend.services.llm_service import get_llm
        prompt = PromptTemplate(
            input_variables=["question", "columns"],
            template="You are a data analyst assistant. The dataset has these columns: {columns}.\nAnswer: {question}",
        )
        chain = LLMChain(llm=get_llm(), prompt=prompt)
        cols  = ", ".join(df.columns.tolist())
        return {"answer": chain.run(question=q, columns=cols)}

    agents_map = {
        AgentType.SQL:           handle_sql,
        AgentType.VISUALIZATION: handle_viz,
        AgentType.INSIGHT:       handle_insight,
        AgentType.CLEANING:      handle_cleaning,
        AgentType.PROFILING:     handle_profiling,
        AgentType.GENERAL:       handle_general,
    }

    result = router_agent.route(req.question, agents_map)

    # Persist chat history
    db.add(ChatHistory(
        dataset_id=req.dataset_id,
        user_query=req.question,
        agent_used=result.get("agent_used", ""),
        response=result.get("answer", ""),
    ))
    db.commit()

    return QueryResponse(
        agent_used=str(result.get("agent_used", "general")),
        sql=result.get("sql"),
        result_data=result.get("result_data"),
        chart_json=result.get("chart_json"),
        insights=result.get("insights"),
        answer=result.get("answer", ""),
    )
