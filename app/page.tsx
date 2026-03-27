"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Trash2, Zap, BookOpen, ChevronDown } from "lucide-react";
import { useApp } from "@/components/AppContext";

interface Msg {
  role: "user" | "assistant";
  content: string;
  resources?: string[];
  hint?: string;
  time: string;
}

const QUICK = [
  "Python öğrenmek istiyorum, nereden başlamalıyım?",
  "Makine öğrenmesi için kaynak önerir misin?",
  "Haftalık çalışma programı nasıl yapmalıyım?",
  "Motivasyonum düşük, ne yapmalıyım?",
  "Veri bilimi yol haritası nedir?",
  "JavaScript mi Python mi öğrenmeliyim?",
];

function now() { return new Date().toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" }); }

export default function ChatPage() {
  const { apiUrl } = useApp();
  const [messages, setMessages] = useState<Msg[]>([{
    role: "assistant",
    content: "Merhaba! Ben AI öğrenme koçunuzum. Öğrenme hedefleriniz, zorlandığınız konular veya kariyer gelişiminiz hakkında benimle konuşabilirsiniz. Size nasıl yardımcı olabilirim?",
    time: now(),
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showQuick, setShowQuick] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    const userMsg: Msg = { role: "user", content: text, time: now() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    let aiMsg: Msg;
    {
      try {
        const history = messages.map(m => ({ role: m.role, content: m.content }));
        const r = await fetch(apiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, history }),
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail);
        aiMsg = { role: "assistant", content: data.content, resources: data.suggested_resources, hint: data.next_step_hint, time: now() };
      } catch (e: any) {
        aiMsg = { role: "assistant", content: `Bağlantı hatası: ${e.message}`, time: now() };
      }
    }
    setMessages(prev => [...prev, aiMsg]);
    setLoading(false);
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-text">AI Koç ile Sohbet</h1>
          <p className="text-sm text-muted">Groq LLM destekli kişisel öğrenme koçunuz</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted bg-card border border-border px-3 py-1 rounded-full">
            {messages.filter(m => m.role === "user").length} mesaj
          </span>
          <button onClick={() => { setMessages([{ role: "assistant", content: "Sohbet temizlendi. Yeni bir konuyla başlayabilirsiniz!", time: now() }]); }}
            className="p-2 text-muted hover:text-red-400 transition-colors rounded-lg hover:bg-card">
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Hızlı sorular */}
      <div className="mb-3">
        <button onClick={() => setShowQuick(!showQuick)}
          className="flex items-center gap-2 text-sm text-muted hover:text-accent transition-colors bg-card border border-border px-3 py-2 rounded-xl">
          <Zap size={14} /> Hızlı Sorular <ChevronDown size={14} className={`transition-transform ${showQuick ? "rotate-180" : ""}`} />
        </button>
        {showQuick && (
          <div className="mt-2 grid grid-cols-2 gap-2">
            {QUICK.map((q, i) => (
              <button key={i} onClick={() => { send(q); setShowQuick(false); }}
                className="text-left text-xs text-muted hover:text-text bg-card border border-border hover:border-primary/50 px-3 py-2 rounded-xl transition-all">
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Mesajlar */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-3 pr-1">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm flex-shrink-0 ${msg.role === "user" ? "bg-primary/20 border border-primary/40" : "bg-accent/20 border border-accent/40"}`}>
              {msg.role === "user" ? "👤" : "🎓"}
            </div>
            <div className={`max-w-[75%] ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col gap-1`}>
              <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.role === "user" ? "bg-primary/20 border border-primary/30 text-text rounded-tr-sm" : "bg-card border border-border text-text rounded-tl-sm"}`}>
                {msg.content}
              </div>
              {msg.resources && msg.resources.length > 0 && (
                <div className="bg-card border border-border rounded-xl px-3 py-2 text-xs text-muted">
                  <div className="flex items-center gap-1 mb-1 text-accent"><BookOpen size={12} /> Kaynaklar</div>
                  {msg.resources.map((r, j) => <div key={j}>• {r}</div>)}
                </div>
              )}
              {msg.hint && (
                <div className="bg-accent/10 border border-accent/30 rounded-xl px-3 py-2 text-xs text-accent">
                  💡 {msg.hint}
                </div>
              )}
              <span className="text-xs text-muted px-1">{msg.time}</span>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-accent/20 border border-accent/40 flex items-center justify-center text-sm">🎓</div>
            <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0,1,2].map(i => <div key={i} className="w-2 h-2 bg-muted rounded-full animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />)}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 bg-card border border-border rounded-2xl px-4 py-3 text-sm text-text placeholder-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/30"
          placeholder="Koçunuza bir şey sorun..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && send(input)}
        />
        <button onClick={() => send(input)} disabled={loading || !input.trim()}
          className="gradient-btn text-white px-4 py-3 rounded-2xl disabled:opacity-40 disabled:cursor-not-allowed">
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
