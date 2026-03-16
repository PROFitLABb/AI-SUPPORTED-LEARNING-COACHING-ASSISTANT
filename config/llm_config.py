from dataclasses import dataclass
from typing import Optional
from openai import AsyncOpenAI
from config.settings import settings


@dataclass
class LLMParams:
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout: int = 30
    fallback_model: Optional[str] = None


GROQ_CONFIG = LLMParams(
    model=settings.LLM_MODEL if settings.LLM_PROVIDER == "groq" else "llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=2048,
    timeout=30,
    fallback_model="llama-3.1-8b-instant",
)

OPENAI_CONFIG = LLMParams(
    model=settings.LLM_MODEL if settings.LLM_PROVIDER == "openai" else "gpt-4o-mini",
    temperature=0.7,
    max_tokens=2048,
    timeout=30,
    fallback_model="gpt-3.5-turbo",
)

OLLAMA_CONFIG = LLMParams(
    model=settings.LLM_MODEL if settings.LLM_PROVIDER == "ollama" else "llama3",
    temperature=0.7,
    max_tokens=2048,
    timeout=60,
    fallback_model="mistral",
)


def get_llm_config() -> LLMParams:
    """Aktif LLM sağlayıcısına göre konfigürasyonu döndür."""
    if settings.LLM_PROVIDER == "groq":
        return GROQ_CONFIG
    if settings.LLM_PROVIDER == "ollama":
        return OLLAMA_CONFIG
    return OPENAI_CONFIG


def get_openai_client() -> AsyncOpenAI:
    """
    Groq, OpenAI-uyumlu API sunduğu için AsyncOpenAI client'ı
    base_url değiştirilerek Groq ile de kullanılabilir.
    """
    if settings.LLM_PROVIDER == "groq":
        return AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
    # OpenAI
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
