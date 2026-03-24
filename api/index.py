"""Vercel serverless — veritabanısız, sadece Groq AI sohbet."""
import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI

app = FastAPI(title="AI Learning Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Groq client
_client = AsyncOpenAI(
    api_key=os.environ.get("GROQ_API_KEY", ""),
    base_url="https://api.groq.com/openai/v1",
)

_SYSTEM = (
    "Sen yalnızca eğitim ve öğrenme konularında uzman bir AI öğrenme koçusun. "
    "Kullanıcının öğrenme hedeflerini, zorlandığı konuları ve kariyer gelişimini destekle. "
    "SADECE eğitim, öğrenme, kariyer gelişimi ve beceri kazanımı konularında yardım et. "
    "Yanıtların kısa, net ve motive edici olsun. Türkçe yanıt ver. "
    "JSON formatında yanıt ver: "
    '{\"content\": \"...\", \"suggested_resources\": [], \"next_step_hint\": \"\"}'
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{"role": "user"|"assistant", "content": "..."}]


class ChatResponse(BaseModel):
    content: str
    suggested_resources: list[str] = []
    next_step_hint: str = ""


@app.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    messages = [{"role": "system", "content": _SYSTEM}]
    # Son 10 mesajı geçmişe ekle (hafıza)
    for msg in payload.history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": payload.message})

    try:
        resp = await _client.chat.completions.create(
            model=os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile"),
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1024,
        )
        raw = resp.choices[0].message.content
        data = json.loads(raw)
        return ChatResponse(
            content=data.get("content", raw),
            suggested_resources=data.get("suggested_resources", []),
            next_step_hint=data.get("next_step_hint", ""),
        )
    except Exception as e:
        return ChatResponse(content=f"Koç şu an yanıt veremiyor: {e}")


@app.get("/health")
async def health():
    return {"status": "ok"}
