"use client";
import { useEffect, useState } from "react";
import { useApp } from "@/components/AppContext";

interface Analytics {
  progress_percentage: number;
  completed_topics: string[];
  streak_days: number;
  total_messages: number;
  active_plans: number;
  time_distribution: { plan_id: string; title: string; estimated_hours: number; completed_hours: number }[];
}

const DEMO: Analytics = {
  progress_percentage: 42.5,
  completed_topics: ["Python Temelleri", "Değişkenler & Tipler", "Döngüler", "Fonksiyonlar"],
  streak_days: 7, total_messages: 24, active_plans: 2,
  time_distribution: [
    { plan_id: "1", title: "Python Programlama", estimated_hours: 40, completed_hours: 17 },
    { plan_id: "2", title: "Veri Analizi", estimated_hours: 30, completed_hours: 8 },
    { plan_id: "3", title: "Makine Öğrenmesi", estimated_hours: 50, completed_hours: 5 },
  ],
};

const BADGES = [
  { emoji: "🥇", name: "İlk Adım",     desc: "İlk konuyu tamamladın!",  kind: "topics",   threshold: 1  },
  { emoji: "🔥", name: "Haftalık Seri", desc: "7 gün üst üste!",         kind: "streak",   threshold: 7  },
  { emoji: "📚", name: "Kitap Kurdu",   desc: "5 konu tamamladın!",      kind: "topics",   threshold: 5  },
  { emoji: "⚡", name: "Hız Treni",     desc: "10 saat öğrendin!",       kind: "hours",    threshold: 10 },
  { emoji: "🏆", name: "Şampiyon",      desc: "20 konu tamamladın!",     kind: "topics",   threshold: 20 },
  { emoji: "💬", name: "Konuşkan",      desc: "10 AI mesajı!",           kind: "messages", threshold: 10 },
  { emoji: "🌟", name: "Yıldız",        desc: "30 günlük seri!",         kind: "streak",   threshold: 30 },
  { emoji: "🎯", name: "Odaklı",        desc: "50 saat öğrendin!",       kind: "hours",    threshold: 50 },
  { emoji: "🚀", name: "Roket",         desc: "10 konu tamamladın!",     kind: "topics",   threshold: 10 },
];

const TABS = ["📊 Grafikler", "✅ Konular", "🏆 Rozetler", "📅 Aktivite"] as const;

function ProgressBar({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full bg-border rounded-full h-2">
      <div className="progress-bar h-2 rounded-full" style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function ProgressPage() {
  const { userId, apiUrl } = useApp();
  const [data, setData] = useState<Analytics>(DEMO);
  const [tab, setTab] = useState(0);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!userId) { setData(DEMO); return; }
    fetch(`${apiUrl}/analytics/${userId}`)
      .then(r => r.json()).then(setData).catch(() => setData(DEMO));
  }, [userId, apiUrl]);

  const totalComp = data.time_distribution.reduce((s, i) => s + i.completed_hours, 0);
  const totalEst  = data.time_distribution.reduce((s, i) => s + i.estimated_hours, 0);
  const efficiency = totalEst > 0 ? Math.round((totalComp / totalEst) * 100) : 0;

  const metrics = [
    { label: "İlerleme",      value: `${data.progress_percentage.toFixed(1)}%`, color: "text-accent"      },
    { label: "Tamamlanan",    value: `${data.completed_topics.length}`,          color: "text-green-400"   },
    { label: "Toplam Süre",   value: `${totalComp.toFixed(0)}h`,                 color: "text-purple-400"  },
    { label: "Seri",          value: `${data.streak_days} gün`,                  color: "text-orange-400"  },
    { label: "Mesaj",         value: `${data.total_messages}`,                   color: "text-blue-400"    },
    { label: "Verimlilik",    value: `${efficiency}%`,                           color: "text-cyan-400"    },
  ];

  const earnedCount = BADGES.filter(b => {
    if (b.kind === "topics")   return data.completed_topics.length >= b.threshold;
    if (b.kind === "streak")   return data.streak_days >= b.threshold;
    if (b.kind === "messages") return data.total_messages >= b.threshold;
    return totalComp >= b.threshold;
  }).length;

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">İlerleme Görünümü</h1>
          <p className="text-sm text-muted">Detaylı öğrenme analitikleri ve başarı rozetleri</p>
        </div>
        {!userId && <span className="text-xs text-accent bg-accent/10 border border-accent/30 px-3 py-1 rounded-full">Demo mod</span>}
      </div>

      {/* Metrikler */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {metrics.map(({ label, value, color }) => (
          <div key={label} className="bg-card border border-border rounded-2xl p-3 text-center">
            <p className="text-xs text-muted">{label}</p>
            <p className={`text-lg font-bold mt-1 ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-card border border-border rounded-2xl p-1">
        {TABS.map((t, i) => (
          <button key={i} onClick={() => setTab(i)}
            className={`flex-1 text-xs md:text-sm py-2 rounded-xl transition-all font-medium ${tab === i ? "bg-primary/20 text-accent border border-primary/30" : "text-muted hover:text-text"}`}>
            {t}
          </button>
        ))}
      </div>

      {/* Grafikler */}
      {tab === 0 && (
        <div className="flex flex-col gap-4">
          <div className="bg-card border border-border rounded-2xl p-5">
            <h2 className="font-semibold mb-4">Tamamlanan vs Tahmini Süre</h2>
            {data.time_distribution.map(item => {
              const maxH = Math.max(...data.time_distribution.map(i => i.estimated_hours));
              const compW = (item.completed_hours / maxH) * 100;
              const remW  = (Math.max(item.estimated_hours - item.completed_hours, 0) / maxH) * 100;
              return (
                <div key={item.plan_id} className="flex items-center gap-3 mb-3">
                  <span className="text-xs text-muted w-32 truncate">{item.title}</span>
                  <div className="flex-1 flex gap-1 h-5 rounded overflow-hidden">
                    <div className="bg-primary rounded-l transition-all" style={{ width: `${compW}%` }} />
                    <div className="bg-border rounded-r" style={{ width: `${remW}%` }} />
                  </div>
                  <span className="text-xs text-accent w-16 text-right">{item.completed_hours.toFixed(0)}h / {item.estimated_hours.toFixed(0)}h</span>
                </div>
              );
            })}
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-card border border-border rounded-2xl p-5">
              <h2 className="font-semibold mb-3">Plan Bazlı İlerleme</h2>
              {data.time_distribution.map(item => {
                const pct = item.estimated_hours > 0 ? Math.min((item.completed_hours / item.estimated_hours) * 100, 100) : 0;
                return (
                  <div key={item.plan_id} className="mb-3">
                    <div className="flex justify-between text-xs mb-1">
                      <span>{item.title}</span>
                      <span className="text-muted">{pct.toFixed(0)}%</span>
                    </div>
                    <ProgressBar value={pct} />
                  </div>
                );
              })}
            </div>
            <div className="bg-card border border-border rounded-2xl p-5 flex flex-col gap-4">
              <div>
                <h2 className="font-semibold mb-2">🔥 Günlük Seri</h2>
                <ProgressBar value={data.streak_days} max={30} />
                <p className="text-xs text-muted mt-1">{data.streak_days} / 30 gün</p>
              </div>
              <div>
                <h2 className="font-semibold mb-2">Genel İlerleme</h2>
                <ProgressBar value={data.progress_percentage} />
                <p className="text-xs text-muted mt-1">{data.progress_percentage.toFixed(1)}% tamamlandı</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Konular */}
      {tab === 1 && (
        <div className="bg-card border border-border rounded-2xl p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Tamamlanan Konular</h2>
            <span className="text-xs text-muted">{data.completed_topics.length} konu</span>
          </div>
          <input className="bg-bg border border-border rounded-xl px-3 py-2 text-sm text-text focus:border-primary focus:outline-none" placeholder="Konu ara..." value={search} onChange={e => setSearch(e.target.value)} />
          {data.completed_topics.length > 0 ? (
            <div className="grid grid-cols-2 gap-2">
              {data.completed_topics.filter(t => t.toLowerCase().includes(search.toLowerCase())).map((t, i) => (
                <div key={i} className="flex items-center gap-2 bg-green-500/10 border border-green-500/30 rounded-xl px-3 py-2">
                  <span className="text-green-400">✅</span>
                  <span className="text-sm">{t}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">Henüz tamamlanan konu yok.</p>
          )}
        </div>
      )}

      {/* Rozetler */}
      {tab === 2 && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Başarı Rozetleri</h2>
            <span className="text-xs text-accent bg-accent/10 border border-accent/30 px-3 py-1 rounded-full">{earnedCount} / {BADGES.length} kazanıldı</span>
          </div>
          <ProgressBar value={earnedCount} max={BADGES.length} />
          <div className="grid grid-cols-3 gap-3">
            {BADGES.map((b, i) => {
              const earned = b.kind === "topics" ? data.completed_topics.length >= b.threshold
                : b.kind === "streak" ? data.streak_days >= b.threshold
                : b.kind === "messages" ? data.total_messages >= b.threshold
                : totalComp >= b.threshold;
              return (
                <div key={i} className={`rounded-2xl p-4 text-center border transition-all ${earned ? "bg-primary/10 border-primary/30" : "bg-card border-border opacity-50"}`}>
                  <div className="text-3xl mb-2">{earned ? b.emoji : "🔒"}</div>
                  <p className={`text-sm font-semibold ${earned ? "text-text" : "text-muted line-through"}`}>{b.name}</p>
                  <p className="text-xs text-muted mt-1">{b.desc}</p>
                  {!earned && (
                    <p className="text-xs text-accent mt-2">
                      {b.kind === "topics" ? `${Math.max(0, b.threshold - data.completed_topics.length)} konu kaldı`
                        : b.kind === "streak" ? `${Math.max(0, b.threshold - data.streak_days)} gün kaldı`
                        : b.kind === "messages" ? `${Math.max(0, b.threshold - data.total_messages)} mesaj kaldı`
                        : `${Math.max(0, b.threshold - totalComp).toFixed(0)}h kaldı`}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Aktivite */}
      {tab === 3 && (
        <div className="grid md:grid-cols-2 gap-4">
          {[
            { label: "AI ile Konuşma", value: data.total_messages, color: "text-blue-400" },
            { label: "Aktif Plan",     value: data.active_plans,   color: "text-accent"   },
            { label: "Öğrenme Serisi", value: `${data.streak_days} gün`, color: "text-orange-400" },
            { label: "Toplam Öğrenme", value: `${totalComp.toFixed(0)} saat`, color: "text-purple-400" },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-card border border-border rounded-2xl p-5 flex items-center gap-4">
              <p className={`text-3xl font-bold ${color}`}>{value}</p>
              <p className="text-sm text-muted">{label}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
