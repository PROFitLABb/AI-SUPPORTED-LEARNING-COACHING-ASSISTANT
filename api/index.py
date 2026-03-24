import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_SYSTEM = (
    "Sen yalnızca eğitim ve öğrenme konularında uzman bir AI öğrenme koçusun. "
    "Kullanıcının öğrenme hedeflerini ve kariyer gelişimini destekle. "
    "SADECE eğitim ve öğrenme konularında yardım et. Türkçe yanıt ver. "
    "JSON formatında yanıt ver: "
    "{\"content\": \"...\", \"suggested_resources\": [], \"next_step_hint\": \"\"}"
)


class ChatRequest(BaseModel):
    message: str
    history: list = []


class ChatResponse(BaseModel):
    content: str
    suggested_resources: list = []
    next_step_hint: str = ""


@app.get("/health")
async def health():
    return {"status": "ok", "groq_key_set": bool(os.environ.get("GROQ_API_KEY"))}


@app.post("/chat")
async def chat(payload: ChatRequest):
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=os.environ.get("GROQ_API_KEY", ""),
            base_url="https://api.groq.com/openai/v1",
        )
        messages = [{"role": "system", "content": _SYSTEM}]
        for msg in payload.history[-10:]:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": payload.message})

        resp = await client.chat.completions.create(
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
        return ChatResponse(content=f"Hata: {str(e)}")
