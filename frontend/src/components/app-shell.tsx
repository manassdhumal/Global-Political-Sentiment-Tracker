"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  TrendingUp,
  LayoutGrid,
  Search,
  GitCompareArrows,
  BookOpen,
  Globe,
  SlidersHorizontal,
  Share2,
  Vote,
  Activity,
  DollarSign,
  Newspaper,
  Bot,
  Radio,
  Menu,
  X,
} from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import { useConfig } from "./config-context";
import { cx, Badge } from "./ui";
import { api } from "@/lib/api";

type Item = { href: string; label: string; icon: React.ComponentType<{ size?: number }> };
const NAV: { section: string; items: Item[] }[] = [
  { section: "Core Intelligence", items: [
    { href: "/", label: "Trending", icon: TrendingUp },
    { href: "/map", label: "World Map & Hotspots", icon: Globe },
    { href: "/topics", label: "Browse topics", icon: LayoutGrid },
    { href: "/topic", label: "Analyze a topic", icon: Search },
    { href: "/compare", label: "Compare topics", icon: GitCompareArrows },
  ]},
  { section: "Applied Analytics & AI", items: [
    { href: "/analyst", label: "AI Geopolitical Analyst", icon: Bot },
    { href: "/timeseries", label: "Applied Econometrics", icon: Activity },
    { href: "/markets", label: "Financial Spillover", icon: DollarSign },
    { href: "/polarization", label: "Media Polarization", icon: Newspaper },
  ]},
  { section: "Simulations & Research", items: [
    { href: "/simulator", label: "Policy Simulator", icon: SlidersHorizontal },
    { href: "/network", label: "Ideological Graph", icon: Share2 },
    { href: "/polling", label: "Polling vs Media", icon: Vote },
    { href: "/methodology", label: "Methodology", icon: BookOpen },
  ]},
];

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
      {NAV.map((group) => (
        <div key={group.section}>
          {group.section && (
            <div className="px-2 pb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted/70">
              {group.section}
            </div>
          )}
          <div className="space-y-0.5">
            {group.items.map((it) => {
              const active = it.href === "/"
                ? pathname === "/"
                : pathname === it.href || pathname.startsWith(it.href + "/");
              const Icon = it.icon;
              return (
                <Link
                  key={it.href}
                  href={it.href}
                  onClick={onNavigate}
                  className={cx(
                    "flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition-colors",
                    active ? "bg-accent/15 text-accent font-semibold" : "text-muted hover:bg-card2 hover:text-foreground",
                  )}
                >
                  <Icon size={17} />
                  {it.label}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

function LiveTickerBar() {
  const [pulse, setPulse] = useState<any>({
    topic: "Global Macro",
    outlet: "Reuters",
    headline: "Monitoring real-time narrative velocity & market contagion.",
    tone: 0.0,
    velocity: "+15% vol",
  });

  useEffect(() => {
    // Initial fetch
    api<any>("/api/live/latest")
      .then((res) => setPulse(res))
      .catch(() => {});

    // Periodic live tick update
    const interval = setInterval(() => {
      api<any>("/api/live/latest")
        .then((res) => setPulse(res))
        .catch(() => {});
    }, 6000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex w-full items-center justify-between border-b border-border bg-card/70 px-4 py-2 text-xs backdrop-blur-sm">
      <div className="flex items-center gap-2 overflow-hidden">
        <span className="flex h-2 w-2 relative shrink-0">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
        </span>
        <span className="font-semibold text-[11px] uppercase tracking-wider text-rose-500 shrink-0 flex items-center gap-1">
          <Radio size={12} /> LIVE PULSE:
        </span>
        <span className="font-medium text-foreground truncate max-w-xl">
          <strong className="text-accent">{pulse.topic}</strong> ({pulse.outlet}): {pulse.headline}
        </span>
      </div>
      <div className="hidden sm:flex items-center gap-3 shrink-0 text-[11px] font-mono">
        <span className="text-muted">Net: <strong className={pulse.tone >= 0 ? "text-emerald-400" : "text-rose-400"}>{pulse.tone > 0 ? "+" : ""}{pulse.tone}</strong></span>
        <span className="text-muted">Velocity: <strong className="text-foreground">{pulse.velocity}</strong></span>
      </div>
    </div>
  );
}

function Brand() {
  const { config } = useConfig();
  return (
    <div className="flex items-center justify-between border-b border-border px-4 py-4">
      <Link href="/" className="flex items-center gap-2">
        <span className="text-lg">🌍</span>
        <div className="leading-tight">
          <div className="text-sm font-semibold">Sentiment Tracker</div>
          <div className="text-[10px] text-muted">media &amp; social · not opinion</div>
        </div>
      </Link>
      {config?.synthetic && <Badge tone="warning">synthetic</Badge>}
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex min-h-screen">
      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-border bg-card/40 md:flex">
        <Brand />
        <NavList />
        <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted">
          <span>v2.1 Enterprise</span>
          <ThemeToggle />
        </div>
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} />
          <aside className="absolute left-0 top-0 flex h-full w-72 flex-col border-r border-border bg-card">
            <Brand />
            <NavList onNavigate={() => setOpen(false)} />
            <div className="flex items-center justify-between border-t border-border px-4 py-3 text-xs text-muted">
              <span>v2.1 Enterprise</span><ThemeToggle />
            </div>
          </aside>
        </div>
      )}

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-border px-4 py-3 md:hidden">
          <button onClick={() => setOpen(true)} className="rounded-lg border border-border p-2" aria-label="Menu">
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
          <span className="text-sm font-semibold">🌍 Sentiment Tracker</span>
        </header>

        {/* Live Ticker Pulse Header */}
        <LiveTickerBar />

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}
