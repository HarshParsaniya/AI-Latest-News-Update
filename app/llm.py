from __future__ import annotations

import logging

from langchain_core.language_models.chat_models import BaseChatModel

from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def get_chat_model(settings: Settings | None = None) -> BaseChatModel | None:
    settings = settings or get_settings()
    if settings.gemini_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.model_name or "gemini-2.0-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.2,
        )
    if settings.groq_api_key:
        from langchain_groq import ChatGroq

        model = settings.model_name
        if model.startswith("gemini"):
            model = "llama-3.3-70b-versatile"
        return ChatGroq(model=model, api_key=settings.groq_api_key, temperature=0.2)
    logger.warning("No LLM API key set; summaries will use RSS snippets.")
    return None


def get_langfuse_handler(settings: Settings | None = None):
    settings = settings or get_settings()
    if not settings.langfuse_ready:
        return None
    try:
        from langfuse.langchain import CallbackHandler

        return CallbackHandler()
    except ImportError:
        from langfuse.callback import CallbackHandler

        return CallbackHandler()
