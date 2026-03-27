"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageCircle, LayoutDashboard, BookOpen, TrendingUp, X, Menu } from "lucide-react";

const NAV = [
  { href: "/",          icon: MessageCircle,   label: "AI Koç ile Sohbet" },
  { href: "/dashboard", icon: LayoutDashboard, label: "Gösterge Paneli"   },
  { href: "/plan",      icon: BookOpen,        label: "Öğrenme Planı"     },
  { href: "/progress",  icon: TrendingUp,      label: "İlerleme"          },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const sidebar = (
    <div className="flex flex-col h-full p-4 gap-4">
      <div className="flex items-center gap-2 py-2">
        <span className="text-2xl">🎓</span>
        <div>
          <div className="font-bold text-text">AI Learning Coach</div>
          <div className="text-xs text-muted">Groq LLM destekli</div>
        </div>
      </div>

      <div className="h-px bg-border" />

      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, icon: Icon, label }) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href} onClick={() => setOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                active
                  ? "bg-primary/20 text-accent border border-primary/30"
                  : "text-muted hover:bg-card hover:text-text"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto">
        <div className="h-px bg-border mb-3" />
        <p className="text-xs text-muted text-center">v2.1.0 · Groq LLaMA 3.3 70B</p>
      </div>
    </div>
  );

  return (
    <>
      <button
        className="fixed top-4 left-4 z-50 md:hidden bg-card border border-border p-2 rounded-lg"
        onClick={() => setOpen(!open)}
      >
        {open ? <X size={18} /> : <Menu size={18} />}
      </button>

      {open && (
        <div className="fixed inset-0 z-40 md:hidden" onClick={() => setOpen(false)}>
          <div className="absolute inset-0 bg-black/60" />
          <div className="absolute left-0 top-0 h-full w-72 bg-card border-r border-border z-50" onClick={e => e.stopPropagation()}>
            {sidebar}
          </div>
        </div>
      )}

      <aside className="hidden md:flex flex-col w-72 min-h-screen bg-card border-r border-border fixed left-0 top-0">
        {sidebar}
      </aside>
    </>
  );
}
