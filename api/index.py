import os
import json
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

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
    'JSON formatında yanıt ver: {"content": "...", "suggested_resources": [], "next_step_hint": ""}'
)


@app.get("/api/health")
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/chat")
@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "")
        history = body.get("history", [])

        messages = [{"role": "system", "content": _SYSTEM}]
        for msg in history[-10:]:
            if isinstance(msg, dict) and msg.get("role") in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY', '')}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile"),
                    "messages": messages,
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
            data = json.loads(raw)

        return JSONResponse({
            "content": data.get("content", raw),
            "suggested_resources": data.get("suggested_resources", []),
            "next_step_hint": data.get("next_step_hint", ""),
        })
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "content": f"Hata: {str(e)}",
                "suggested_resources": [],
                "next_step_hint": "",
            },
        )


# Vercel serverless handler
handler = Mangum(app, lifespan="off")
