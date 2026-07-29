"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { TrendingUp, LayoutGrid, Search, GitCompareArrows, BookOpen, Menu, X } from "lucide-react";
import { ThemeToggle } from "./theme-toggle";
import { useConfig } from "./config-context";
import { cx, Badge } from "./ui";

type Item = { href: string; label: string; icon: React.ComponentType<{ size?: number }> };
const NAV: { section: string; items: Item[] }[] = [
  { section: "", items: [
    { href: "/", label: "Trending", icon: TrendingUp },
    { href: "/topics", label: "Browse topics", icon: LayoutGrid },
    { href: "/topic", label: "Analyze a topic", icon: Search },
    { href: "/compare", label: "Compare topics", icon: GitCompareArrows },
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
                    active ? "bg-accent/15 text-accent" : "text-muted hover:bg-card2 hover:text-foreground",
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
          <span>v2</span>
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
              <span>v2</span><ThemeToggle />
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
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  );
}
