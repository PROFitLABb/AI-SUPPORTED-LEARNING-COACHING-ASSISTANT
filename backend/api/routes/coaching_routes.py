"""Coaching API routes — Groq destekli gerçek LLM entegrasyonu."""
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.coaching_agent import CoachResponse, CoachingAgent
from backend.database.db import get_db
from backend.models.progress_model import Message, MessageDB, UserContext
from config.llm_config import get_openai_client, get_llm_config
from config.settings import settings

router = APIRouter(prefix="/coaching", tags=["coaching"])

# Prompt şablonları
_PROMPTS = {
    "coaching_feedback": {
        "system": (
            "Sen yalnızca eğitim ve öğrenme konularında uzman bir AI öğrenme koçusun. "
            "Kullanıcının öğrenme geçmişini, stilini ve hedeflerini dikkate alarak kişiselleştirilmiş yanıtlar ver. "
            "Önceki konuşmaları hatırla ve bağlam kur. "
            "SADECE eğitim, öğrenme, kariyer gelişimi ve beceri kazanımı konularında yardım et. "
            "Eğitimle ilgisi olmayan konularda kibarca konuyu öğrenmeye yönlendir. "
            "Kullanıcı 'teşekkürler', 'tamam', 'anladım', 'gerek yok' gibi kısa kapanış mesajları gönderirse "
            "kısa ve samimi bir şekilde karşılık ver, yeni konu açma. "
            "Yanıtların kısa ve net olsun. Türkçe yanıt ver. "
            "JSON formatında yanıt ver: "
            '{\"content\": \"...\", \"suggested_resources\": [], \"next_step_hint\": \"\", \"detected_topics\": []}'
        ),
        "user": (
            "Kullanıcı mesajı: {message}\n\n"
            "Mevcut öğrenme hedefleri: {current_goals}\n"
            "Tamamlanan konular: {completed_topics}\n"
            "Öğrenme stili: {learning_style}\n"
            "Son konuşmalar (hafıza):\n{recent_interactions}"
        ),
    }
}


class ChatRequest(BaseModel):
    user_id: str
    message: str
    context: UserContext | None = None


class ChatResponse(BaseModel):
    content: str
    suggested_resources: list[str] = []
    next_step_hint: str = ""
    message_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    context = payload.context or UserContext(user_id=payload.user_id)

    # Kullanıcının geçmiş mesajlarını bağlama ekle (hafıza sistemi)
    history_result = await db.execute(
        select(MessageDB)
        .where(MessageDB.user_id == payload.user_id)
        .order_by(MessageDB.timestamp.desc())
        .limit(15)
    )
    history_rows = history_result.scalars().all()
    context.recent_interactions = [
        f"[{r.role}] {r.content[:200]}" for r in reversed(history_rows)
    ]

    # Öğrenme stilini bağlama ekle
    learning_style = context.learning_preferences.get("style", "mixed")

    try:
        llm_client = get_openai_client()
        cfg = get_llm_config()
        llm_client._model = cfg.model  # type: ignore[attr-defined]
        agent = CoachingAgent(llm_client=llm_client, prompts=_PROMPTS)
        # learning_style'ı user template'e geç
        original_template = _PROMPTS["coaching_feedback"]["user"]
        _PROMPTS["coaching_feedback"]["user"] = original_template.replace(
            "{learning_style}", learning_style
        )
        coach_response = await agent.respond(payload.message, context)
        _PROMPTS["coaching_feedback"]["user"] = original_template
    except Exception as exc:
        # LLM hatası — kullanıcıya anlamlı mesaj dön
        coach_response = CoachResponse(
            content=f"Koç şu an yanıt veremiyor: {exc}",
            suggested_resources=[],
            next_step_hint="",
        )

    # Mesajları kaydet
    db.add(MessageDB(
        id=str(uuid.uuid4()),
        user_id=payload.user_id,
        role="user",
        content=payload.message,
        timestamp=datetime.utcnow(),
        context_snapshot={},
    ))
    assistant_id = str(uuid.uuid4())
    db.add(MessageDB(
        id=assistant_id,
        user_id=payload.user_id,
        role="assistant",
        content=coach_response.content,
        timestamp=datetime.utcnow(),
        context_snapshot={},
    ))
    await db.commit()

    return ChatResponse(
        content=coach_response.content,
        suggested_resources=coach_response.suggested_resources,
        next_step_hint=coach_response.next_step_hint,
        message_id=assistant_id,
    )


@router.get("/history/{user_id}", response_model=list[Message])
async def get_history(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[Message]:
    result = await db.execute(
        select(MessageDB)
        .where(MessageDB.user_id == user_id)
        .order_by(MessageDB.timestamp)
    )
    return [Message.model_validate(row) for row in result.scalars().all()]
