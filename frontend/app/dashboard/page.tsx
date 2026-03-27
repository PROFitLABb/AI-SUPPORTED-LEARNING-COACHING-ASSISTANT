"use client";
import { useEffect, useState } from "react";
import { useApp } from "@/components/AppContext";
import { TrendingUp, CheckCircle, Flame, Clock, BarChart2, BookOpen } from "lucide-react";
import Link from "next/link";

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
  streak_days: 7,
  total_messages: 24,
  active_plans: 2,
  time_distribution: [
    { plan_id: "1", title: "Python Programlama", estimated_hours: 40, completed_hours: 17 },
    { plan_id: "2", title: "Veri Analizi", estimated_hours: 30, completed_hours: 8 },
    { plan_id: "3", title: "Makine Öğrenmesi", estimated_hours: 50, completed_hours: 5 },
  ],
};

const QUOTES = [
  "Öğrenmek bir hazinedir, sahibini her yerde takip eder.",
  "Başarı, her gün tekrarlanan küçük çabaların toplamıdır.",
  "Bugün zor olan, yarın alışkanlık olur.",
  "Her uzman, bir zamanlar acemiydi.",
];

function MetricCard({ icon: Icon, label, value, color = "text-accent" }: { icon: any; label: string; value: string; color?: string }) {
  return (
    <div className="bg-card border border-border rounded-2xl p-4 flex items-center gap-3">
      <div className={`p-2 rounded-xl bg-primary/10 ${color}`}><Icon size={20} /></div>
      <div>
        <p className="text-xs text-muted">{label}</p>
        <p className={`text-xl font-bold ${color}`}>{value}</p>
      </div>
    </div>
  );
}

function ProgressBar({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="w-full bg-border rounded-full h-2">
      <div className="progress-bar h-2 rounded-full" style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function DashboardPage() {
  const { userId, apiUrl } = useApp();
  const [data, setData] = useState<Analytics>(DEMO);
  const [loading, setLoading] = useState(false);
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Günaydın" : hour < 17 ? "İyi öğlenler" : "İyi akşamlar";
  const quote = QUOTES[Math.floor(Math.random() * QUOTES.length)];

  useEffect(() => {
    if (!userId) { setData(DEMO); return; }
    setLoading(true);
    fetch(`${apiUrl}/analytics/${userId}`)
      .then(r => r.json())
      .then(d => setData(d))
      .catch(() => setData(DEMO))
      .finally(() => setLoading(false));
  }, [userId, apiUrl]);

  const totalComp = data.time_distribution.reduce((s, i) => s + i.completed_hours, 0);

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{greeting}! 👋</h1>
          <p className="text-muted text-sm">{new Date().toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" })}</p>
        </div>
        {!userId && <span className="text-xs text-accent bg-accent/10 border border-accent/30 px-3 py-1 rounded-full">Demo mod</span>}
      </div>

      {/* Metrikler */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <MetricCard icon={TrendingUp}  label="Genel İlerleme"   value={`${data.progress_percentage.toFixed(1)}%`} />
        <MetricCard icon={CheckCircle} label="Tamamlanan Konu"  value={`${data.completed_topics.length}`} />
        <MetricCard icon={Flame}       label="Günlük Seri"      value={`${data.streak_days} gün`} color="text-orange-400" />
        <MetricCard icon={Clock}       label="Toplam Süre"      value={`${totalComp.toFixed(0)}h`} />
        <MetricCard icon={BookOpen}    label="Aktif Plan"       value={`${data.active_plans}`} />
      </div>

      {/* İlerleme + Grafik */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-card border border-border rounded-2xl p-5 flex flex-col gap-4">
          <h2 className="font-semibold flex items-center gap-2"><TrendingUp size={16} className="text-accent" /> Genel İlerleme</h2>
          <ProgressBar value={data.progress_percentage} />
          <p className="text-sm text-muted">{data.progress_percentage.toFixed(1)}% tamamlandı</p>

          <h3 className="font-medium text-sm mt-2">Plan Bazlı İlerleme</h3>
          {data.time_distribution.map(item => {
            const pct = item.estimated_hours > 0 ? Math.min((item.completed_hours / item.estimated_hours) * 100, 100) : 0;
            return (
              <div key={item.plan_id} className="flex flex-col gap-1">
                <div className="flex justify-between text-xs">
                  <span className="text-text">{item.title}</span>
                  <span className="text-muted">{item.completed_hours.toFixed(0)}h / {item.estimated_hours.toFixed(0)}h</span>
                </div>
                <ProgressBar value={pct} />
              </div>
            );
          })}
        </div>

        <div className="bg-card border border-border rounded-2xl p-5 flex flex-col gap-4">
          <h2 className="font-semibold flex items-center gap-2"><BarChart2 size={16} className="text-accent" /> Zaman Dağılımı</h2>
          {data.time_distribution.map(item => (
            <div key={item.plan_id} className="flex items-center gap-3">
              <span className="text-xs text-muted w-28 truncate">{item.title}</span>
              <div className="flex-1 flex gap-1 h-6 items-center">
                <div className="h-4 rounded bg-primary/70 transition-all" style={{ width: `${(item.completed_hours / Math.max(...data.time_distribution.map(i => i.estimated_hours))) * 100}%`, minWidth: item.completed_hours > 0 ? "4px" : "0" }} />
                <div className="h-4 rounded bg-border" style={{ width: `${(Math.max(item.estimated_hours - item.completed_hours, 0) / Math.max(...data.time_distribution.map(i => i.estimated_hours))) * 100}%` }} />
              </div>
              <span className="text-xs text-accent w-10 text-right">{item.completed_hours.toFixed(0)}h</span>
            </div>
          ))}

          <div className="mt-2">
            <h3 className="font-medium text-sm mb-2">🔥 Günlük Seri</h3>
            <ProgressBar value={data.streak_days} max={30} />
            <p className="text-xs text-muted mt-1">{data.streak_days} / 30 gün</p>
          </div>

          <p className="text-xs text-muted italic mt-auto border-t border-border pt-3">"{quote}"</p>
        </div>
      </div>

      {/* Tamamlanan konular */}
      <div className="bg-card border border-border rounded-2xl p-5">
        <h2 className="font-semibold mb-3 flex items-center gap-2"><CheckCircle size={16} className="text-green-400" /> Tamamlanan Konular</h2>
        {data.completed_topics.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {data.completed_topics.map((t, i) => (
              <span key={i} className="text-xs bg-green-500/10 border border-green-500/30 text-green-400 px-3 py-1 rounded-full">✅ {t}</span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted">Henüz tamamlanan konu yok. Öğrenmeye başla!</p>
        )}
      </div>

      {/* Hızlı erişim */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { href: "/",        label: "💬 Koça Sor",       desc: "AI ile sohbet et" },
          { href: "/plan",    label: "📚 Plan Görüntüle", desc: "Öğrenme planın" },
          { href: "/progress",label: "📈 İlerleme",       desc: "Detaylı analitik" },
        ].map(({ href, label, desc }) => (
          <Link key={href} href={href} className="bg-card border border-border hover:border-primary/50 rounded-2xl p-4 text-center transition-all hover:bg-primary/5 group">
            <p className="font-medium text-sm group-hover:text-accent transition-colors">{label}</p>
            <p className="text-xs text-muted mt-1">{desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
