import os
import json
import httpx
from http.server import BaseHTTPRequestHandler

_SYSTEM = (
    "Sen yalnızca eğitim ve öğrenme konularında uzman bir AI öğrenme koçusun. "
    "Kullanıcının öğrenme hedeflerini ve kariyer gelişimini destekle. "
    "SADECE eğitim ve öğrenme konularında yardım et. Türkçe yanıt ver. "
    'JSON formatında yanıt ver: {"content": "...", "suggested_resources": [], "next_step_hint": ""}'
)


def _call_groq(message: str, history: list) -> dict:
    messages = [{"role": "system", "content": _SYSTEM}]
    for msg in history[-10:]:
        if isinstance(msg, dict) and msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    with httpx.Client(timeout=30) as client:
        resp = client.post(
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
        return json.loads(raw)


class handler(BaseHTTPRequestHandler):

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {})

    def do_GET(self):
        self._send_json(200, {"status": "ok"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            message = body.get("message", "")
            history = body.get("history", [])
            data = _call_groq(message, history)
            self._send_json(200, {
                "content": data.get("content", ""),
                "suggested_resources": data.get("suggested_resources", []),
                "next_step_hint": data.get("next_step_hint", ""),
            })
        except Exception as e:
            self._send_json(500, {
                "content": f"Hata: {str(e)}",
                "suggested_resources": [],
                "next_step_hint": "",
            })
