import { NextRequest, NextResponse } from "next/server";

const GROQ_API = "https://api.groq.com/openai/v1/chat/completions";
const MODEL = process.env.LLM_MODEL ?? "llama-3.3-70b-versatile";
const SYSTEM = `Sen yalnızca eğitim ve öğrenme konularında uzman bir AI öğrenme koçusun. Kullanıcının öğrenme hedeflerini ve kariyer gelişimini destekle. SADECE eğitim ve öğrenme konularında yardım et. Türkçe yanıt ver. JSON formatında yanıt ver: {"content": "...", "suggested_resources": [], "next_step_hint": ""}`;

export async function POST(req: NextRequest) {
  try {
    const { message, history = [] } = await req.json();

    const messages = [{ role: "system", content: SYSTEM }];
    for (const msg of (history as any[]).slice(-10)) {
      if (msg?.role === "user" || msg?.role === "assistant") {
        messages.push({ role: msg.role, content: msg.content });
      }
    }
    messages.push({ role: "user", content: message });

    const res = await fetch(GROQ_API, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.GROQ_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: MODEL,
        messages,
        response_format: { type: "json_object" },
        temperature: 0.7,
        max_tokens: 1024,
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Groq API hatası: ${err}`);
    }

    const groqData = await res.json();
    const raw = groqData.choices[0].message.content;
    const data = JSON.parse(raw);

    return NextResponse.json({
      content: data.content ?? raw,
      suggested_resources: data.suggested_resources ?? [],
      next_step_hint: data.next_step_hint ?? "",
    });
  } catch (e: any) {
    return NextResponse.json(
      { content: `Hata: ${e.message}`, suggested_resources: [], next_step_hint: "" },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({ status: "ok" });
}
