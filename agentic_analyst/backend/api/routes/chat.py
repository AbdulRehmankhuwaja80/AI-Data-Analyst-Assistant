"""Chat route — /api/chat — multi-turn conversation with dataset context"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.orm_models import ChatHistory
from backend.schemas.schemas import ChatRequest, ChatResponse
from backend.services.dataset_service import dataset_service
from backend.services.llm_service import get_chat_llm
from langchain.schema import HumanMessage, AIMessage, SystemMessage

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        df = dataset_service.load(req.dataset_id, db)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(404, str(exc))

    llm = get_chat_llm()

    cols_info = ", ".join(f"{c} ({t})" for c, t in df.dtypes.items())
    system_msg = SystemMessage(content=(
        f"You are an expert data analyst assistant. "
        f"The user has uploaded a dataset with {len(df)} rows and {len(df.columns)} columns.\n"
        f"Columns: {cols_info}\n"
        f"Statistical summary:\n{df.describe(include='all').to_string()}\n\n"
        f"Answer questions about this dataset concisely and accurately. "
        f"If you generate SQL, wrap it in ```sql``` fences."
    ))

    lc_messages = [system_msg]
    for msg in req.messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        else:
            lc_messages.append(AIMessage(content=msg.content))

    response = llm(lc_messages)
    reply    = response.content

    # Save to chat_history
    last_user = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
    db.add(ChatHistory(
        dataset_id=req.dataset_id,
        user_query=last_user,
        agent_used="chat_llm",
        response=reply,
    ))
    db.commit()

    return ChatResponse(reply=reply, agent_used="chat_llm")


@router.get("/history/{dataset_id}")
def get_history(dataset_id: int, limit: int = 50, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.dataset_id == dataset_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {"id": r.id, "query": r.user_query, "agent": r.agent_used,
         "response": r.response, "ts": r.created_at}
        for r in rows
    ]
