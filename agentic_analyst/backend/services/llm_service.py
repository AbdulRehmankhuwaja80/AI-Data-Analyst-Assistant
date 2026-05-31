"""
LLM Service — Ollama / Llama 3 via LangChain ChatOllama
"""
import os
import logging
from functools import lru_cache
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL_NAME      = os.getenv("OLLAMA_MODEL", "llama3")


@lru_cache(maxsize=1)
def get_llm() -> Ollama:
    """Return a cached Ollama LLM instance for chain/tool use."""
    logger.info("Initialising Ollama LLM: model=%s base=%s", MODEL_NAME, OLLAMA_BASE_URL)
    return Ollama(
        base_url=OLLAMA_BASE_URL,
        model=MODEL_NAME,
        temperature=0.1,
    )


@lru_cache(maxsize=1)
def get_chat_llm() -> ChatOllama:
    """Return a cached ChatOllama instance for conversational chains."""
    return ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=MODEL_NAME,
        temperature=0.2,
    )
