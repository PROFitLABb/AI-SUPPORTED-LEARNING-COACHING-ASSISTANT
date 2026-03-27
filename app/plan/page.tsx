"use client";
import { useState } from "react";
import { useApp } from "@/components/AppContext";
import { CheckCircle, Circle, PlayCircle, ExternalLink, ChevronDown, ChevronUp, Sparkles, Plus } from "lucide-react";

interface Resource { title: string; url: string; type: string; provider: string; estimated_hours: number; }
interface Step { id: string; order: number; title: string; description: string; estimated_hours: number; status: string; deadline: string; resources: Resource[]; }
interface Plan { id: string; title: string; total_weeks: number; status: string; steps: Step[]; }

const DEMO_PLAN: Plan = {
  id: "demo-1", title: "Python ile Veri Bilimi", total_weeks: 12, status: "active",
  steps: [
    { id: "s1", order: 1, title: "Python Temelleri", description: "Değişkenler, döngüler, fonksiyonlar.", estimated_hours: 8, status: "completed", deadline: "2026-02-01", resources: [{ title: "Python.org Tutorial", url: "https://docs.python.org/3/tutorial/", type: "article", provider: "Python.org", estimated_hours: 3 }] },
    { id: "s2", order: 2, title: "NumPy & Pandas", description: "Veri manipülasyonu ve analizi.", estimated_hours: 10, status: "in_progress", deadline: "2026-03-01", resources: [{ title: "Pandas Docs", url: "https://pandas.pydata.org/docs/", type: "article", provider: "Pandas", estimated_hours: 5 }] },
    { id: "s3", order: 3, title: "Veri Görselleştirme", description: "Matplotlib ve Seaborn ile grafikler.", estimated_hours: 8, status: "pending", deadline: "2026-04-01", resources: [{ title: "Matplotlib Tutorial", url: "https://matplotlib.org/stable/tutorials/", type: "article", provider: "Matplotlib", estimated_hours: 4 }] },
    { id: "s4", order: 4, title: "Makine Öğrenmesi Giriş", description: "Scikit-learn ile temel modeller.", estimated_hours: 15, status: "pending", deadline: "2026-05-01", resources: [{ title: "Scikit-learn Guide", url: "https://scikit-learn.org/stable/user_guide.html", type: "article", provider: "Scikit-learn", estimated_hours: 8 }] },
  ],
};

const STATUS = {
  completed:   { icon: CheckCircle, color: "text-green-400",  bg: "bg-green-400/10 border-green-400/30",  label: "Tamamlandı"    },
  in_progress: { icon: PlayCircle,  color: "text-accent",     bg: "bg-accent/10 border-accent/30",        label: "Devam Ediyor"  },
  pending:     { icon: Circle,      color: "text-muted",      bg: "bg-card border-border",                label: "Bekliyor"      },
};

function StepCard({ step, planId, apiUrl, onUpdate }: { step: Step; planId: string; apiUrl: string; onUpdate: () => void }) {
  const [open, setOpen] = useState(step.status === "in_progress");
  const [loading, setLoading] = useState(false);
  const s = STATUS[step.status as keyof typeof STATUS] || STATUS.pending;
  const Icon = s.icon;

  async function updateStatus(status: string) {
    setLoading(true);
    try {
      await fetch(`${apiUrl}/plans/${planId}/steps/${step.id}?status=${status}`, { method: "PUT" });
      onUpdate();
    } catch {}
    setLoading(false);
  }

  return (
    <div className={`border rounded-2xl overflow-hidden transition-all ${s.bg}`}>
      <button className="w-full flex items-center gap-3 p-4 text-left" onClick={() => setOpen(!open)}>
        <Icon size={20} className={s.color} />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">Adım {step.order}</span>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${s.bg} ${s.color}`}>{s.label}</span>
          </div>
          <p className="font-medium text-sm mt-0.5">{step.title}</p>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted">
          <span>{step.estimated_hours}h</span>
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 flex flex-col gap-3 border-t border-border/50 pt-3">
          <p className="text-sm text-muted">{step.description}</p>
          <div className="flex gap-4 text-xs text-muted">
            <span>⏱ {step.estimated_hours}h</span>
            <span>📅 {step.deadline}</span>
          </div>

          {step.resources.length > 0 && (
            <div>
              <p className="text-xs text-muted mb-2">📚 Kaynaklar</p>
              <div className="flex flex-col gap-1">
                {step.resources.map((r, i) => (
                  <a key={i} href={r.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-2 text-xs text-accent hover:text-primary transition-colors">
                    <ExternalLink size={12} /> {r.title} — {r.provider} ({r.estimated_hours}h)
                  </a>
                ))}
              </div>
            </div>
          )}

          {step.status !== "completed" && planId !== "demo-1" && (
            <div className="flex gap-2 mt-1">
              {step.status === "pending" && (
                <button onClick={() => updateStatus("in_progress")} disabled={loading}
                  className="text-xs bg-accent/10 border border-accent/30 text-accent px-3 py-1.5 rounded-xl hover:bg-accent/20 transition-colors disabled:opacity-50">
                  ▶ Başla
                </button>
              )}
              <button onClick={() => updateStatus("completed")} disabled={loading}
                className="text-xs bg-green-500/10 border border-green-500/30 text-green-400 px-3 py-1.5 rounded-xl hover:bg-green-500/20 transition-colors disabled:opacity-50">
                ✔ Tamamlandı
              </button>
            </div>
          )}
          {step.status === "completed" && <p className="text-xs text-green-400">🎉 Bu adım tamamlandı!</p>}
        </div>
      )}
    </div>
  );
}

export default function PlanPage() {
  const { userId, apiUrl } = useApp();
  const [tab, setTab] = useState<"current" | "ai" | "manual">("current");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [aiForm, setAiForm] = useState({ name: "", goal: "", skill_level: "beginner", weekly_hours: 5, interests: "", learning_style: "reading" });
  const [manualForm, setManualForm] = useState({ title: "", total_weeks: 8, steps: [{ title: "", description: "", estimated_hours: 5 }] });
  const [msg, setMsg] = useState("");
  const demo = !userId;

  const currentPlan = plan || (demo ? DEMO_PLAN : null);

  async function loadPlan(id: string) {
    setLoadingPlan(true);
    try {
      const r = await fetch(`${apiUrl}/plans/${id}`);
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail);
      setPlan(d);
    } catch (e: any) { setMsg(`❌ ${e.message}`); }
    setLoadingPlan(false);
  }

  async function generateAI() {
    setLoadingPlan(true); setMsg("");
    try {
      const r = await fetch(`${apiUrl}/plans/ai-generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, ...aiForm, interests: aiForm.interests.split(",").map(s => s.trim()).filter(Boolean), weekly_hours: Number(aiForm.weekly_hours) }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail);
      setPlan(d); setTab("current");
      setMsg(`✅ Plan oluşturuldu: ${d.title}`);
    } catch (e: any) { setMsg(`❌ ${e.message}`); }
    setLoadingPlan(false);
  }

  async function createManual() {
    setLoadingPlan(true); setMsg("");
    try {
      const r = await fetch(`${apiUrl}/plans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, title: manualForm.title, total_weeks: manualForm.total_weeks, steps: manualForm.steps.map((s, i) => ({ ...s, order: i + 1 })) }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail);
      setPlan(d); setTab("current");
      setMsg(`✅ Plan oluşturuldu!`);
    } catch (e: any) { setMsg(`❌ ${e.message}`); }
    setLoadingPlan(false);
  }

  const TABS = [
    { key: "current", label: "📋 Mevcut Plan" },
    { key: "ai",      label: "🤖 AI ile Oluştur" },
    { key: "manual",  label: "✏️ Manuel" },
  ] as const;

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold">Öğrenme Planı</h1>
        <p className="text-sm text-muted">AI destekli kişiselleştirilmiş öğrenme yolu</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-card border border-border rounded-2xl p-1">
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`flex-1 text-sm py-2 rounded-xl transition-all font-medium ${tab === t.key ? "bg-primary/20 text-accent border border-primary/30" : "text-muted hover:text-text"}`}>
            {t.label}
          </button>
        ))}
      </div>

      {msg && <p className={`text-sm px-4 py-2 rounded-xl border ${msg.startsWith("✅") ? "bg-green-500/10 border-green-500/30 text-green-400" : "bg-red-500/10 border-red-500/30 text-red-400"}`}>{msg}</p>}

      {/* Mevcut Plan */}
      {tab === "current" && (
        <div className="flex flex-col gap-4">
          {!demo && !plan && (
            <div className="flex gap-2">
              <input id="pid" className="flex-1 bg-card border border-border rounded-xl px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" placeholder="Plan ID girin" />
              <button onClick={() => loadPlan((document.getElementById("pid") as HTMLInputElement).value)}
                className="gradient-btn text-white text-sm px-4 py-2 rounded-xl">Yükle</button>
            </div>
          )}
          {currentPlan && (
            <>
              {/* Plan özeti */}
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: "Plan", value: currentPlan.title.slice(0, 16) + "..." },
                  { label: "Hafta", value: `${currentPlan.total_weeks}` },
                  { label: "Tamamlanan", value: `${currentPlan.steps.filter(s => s.status === "completed").length}/${currentPlan.steps.length}` },
                  { label: "İlerleme", value: `${Math.round(currentPlan.steps.filter(s => s.status === "completed").length / currentPlan.steps.length * 100)}%` },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-card border border-border rounded-xl p-3 text-center">
                    <p className="text-xs text-muted">{label}</p>
                    <p className="font-bold text-accent text-sm mt-1">{value}</p>
                  </div>
                ))}
              </div>
              <div className="w-full bg-border rounded-full h-2">
                <div className="progress-bar h-2 rounded-full" style={{ width: `${currentPlan.steps.filter(s => s.status === "completed").length / currentPlan.steps.length * 100}%` }} />
              </div>
              <div className="flex flex-col gap-2">
                {currentPlan.steps.sort((a, b) => a.order - b.order).map(step => (
                  <StepCard key={step.id} step={step} planId={currentPlan.id} apiUrl={apiUrl} onUpdate={() => loadPlan(currentPlan.id)} />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* AI ile Oluştur */}
      {tab === "ai" && (
        <div className="bg-card border border-border rounded-2xl p-5 flex flex-col gap-4">
          <div className="flex items-center gap-2 text-accent"><Sparkles size={18} /><h2 className="font-semibold">AI ile Kişiselleştirilmiş Plan</h2></div>
          {demo && <p className="text-sm text-amber-400 bg-amber-400/10 border border-amber-400/30 px-3 py-2 rounded-xl">AI plan oluşturmak için Kullanıcı ID girin.</p>}
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-muted mb-1 block">Adınız</label><input className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" placeholder="örn: Ahmet" value={aiForm.name} onChange={e => setAiForm({ ...aiForm, name: e.target.value })} /></div>
            <div><label className="text-xs text-muted mb-1 block">Öğrenme Hedefiniz</label><input className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" placeholder="örn: Python ile web geliştirme" value={aiForm.goal} onChange={e => setAiForm({ ...aiForm, goal: e.target.value })} /></div>
            <div><label className="text-xs text-muted mb-1 block">Seviye</label>
              <select className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" value={aiForm.skill_level} onChange={e => setAiForm({ ...aiForm, skill_level: e.target.value })}>
                <option value="beginner">Başlangıç</option><option value="intermediate">Orta</option><option value="advanced">İleri</option>
              </select>
            </div>
            <div><label className="text-xs text-muted mb-1 block">Haftalık Saat</label><input type="number" min={1} max={40} className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" value={aiForm.weekly_hours} onChange={e => setAiForm({ ...aiForm, weekly_hours: Number(e.target.value) })} /></div>
            <div className="col-span-2"><label className="text-xs text-muted mb-1 block">İlgi Alanları (virgülle)</label><input className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" placeholder="örn: web, veri, oyun" value={aiForm.interests} onChange={e => setAiForm({ ...aiForm, interests: e.target.value })} /></div>
          </div>
          <button onClick={generateAI} disabled={loadingPlan || demo || !aiForm.name || !aiForm.goal}
            className="gradient-btn text-white py-3 rounded-xl font-medium disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2">
            {loadingPlan ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Oluşturuluyor...</> : <><Sparkles size={16} /> AI ile Plan Oluştur</>}
          </button>
        </div>
      )}

      {/* Manuel */}
      {tab === "manual" && (
        <div className="bg-card border border-border rounded-2xl p-5 flex flex-col gap-4">
          <h2 className="font-semibold">Manuel Plan Oluştur</h2>
          {demo && <p className="text-sm text-amber-400 bg-amber-400/10 border border-amber-400/30 px-3 py-2 rounded-xl">Plan oluşturmak için Kullanıcı ID girin.</p>}
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2"><label className="text-xs text-muted mb-1 block">Plan Başlığı</label><input className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" placeholder="örn: Python ile Veri Bilimi" value={manualForm.title} onChange={e => setManualForm({ ...manualForm, title: e.target.value })} /></div>
            <div><label className="text-xs text-muted mb-1 block">Toplam Hafta</label><input type="number" min={1} max={52} className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" value={manualForm.total_weeks} onChange={e => setManualForm({ ...manualForm, total_weeks: Number(e.target.value) })} /></div>
          </div>
          <div className="flex flex-col gap-3">
            {manualForm.steps.map((step, i) => (
              <div key={i} className="bg-bg border border-border rounded-xl p-3 flex flex-col gap-2">
                <p className="text-xs text-muted font-medium">Adım {i + 1}</p>
                <div className="grid grid-cols-2 gap-2">
                  <input className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" placeholder="Başlık" value={step.title} onChange={e => { const s = [...manualForm.steps]; s[i].title = e.target.value; setManualForm({ ...manualForm, steps: s }); }} />
                  <input type="number" className="bg-card border border-border rounded-lg px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" placeholder="Saat" value={step.estimated_hours} onChange={e => { const s = [...manualForm.steps]; s[i].estimated_hours = Number(e.target.value); setManualForm({ ...manualForm, steps: s }); }} />
                  <textarea className="col-span-2 bg-card border border-border rounded-lg px-3 py-2 text-sm text-text focus:border-primary focus:outline-none resize-none" rows={2} placeholder="Açıklama" value={step.description} onChange={e => { const s = [...manualForm.steps]; s[i].description = e.target.value; setManualForm({ ...manualForm, steps: s }); }} />
                </div>
              </div>
            ))}
            <button onClick={() => setManualForm({ ...manualForm, steps: [...manualForm.steps, { title: "", description: "", estimated_hours: 5 }] })}
              className="flex items-center gap-2 text-sm text-muted hover:text-accent transition-colors border border-dashed border-border rounded-xl py-2 justify-center">
              <Plus size={14} /> Adım Ekle
            </button>
          </div>
          <button onClick={createManual} disabled={loadingPlan || demo || !manualForm.title}
            className="gradient-btn text-white py-3 rounded-xl font-medium disabled:opacity-40 disabled:cursor-not-allowed">
            {loadingPlan ? "Oluşturuluyor..." : "Plan Oluştur"}
          </button>
        </div>
      )}
    </div>
  );
}
