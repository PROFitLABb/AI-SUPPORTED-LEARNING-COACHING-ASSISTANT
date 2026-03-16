from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./ai_learning_coach.db",
        description="Async veritabanı bağlantı URL'si",
    )
    # Groq API key (.env'de GROQ_API_KEY olarak tanımlanır)
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    # Geriye dönük uyumluluk için OpenAI key de tutuldu
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key (opsiyonel)")
    VECTOR_DB_URL: str = Field(
        default="http://localhost:8000", description="ChromaDB server URL"
    )
    SECRET_KEY: str = Field(
        default="change-me-in-production", description="JWT secret key"
    )
    LLM_PROVIDER: Literal["openai", "ollama", "groq"] = Field(
        default="groq", description="LLM provider: groq, openai veya ollama"
    )
    LLM_MODEL: str = Field(default="llama-3.3-70b-versatile", description="LLM model adı")
    DEBUG: bool = Field(default=False, description="Debug modu")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
