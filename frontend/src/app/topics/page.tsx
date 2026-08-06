"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { TopicCard, TopicStat } from "@/components/topic-card";
import { PageHeader, EmptyState, CardGridSkeleton, DISCLAIMER, cx } from "@/components/ui";
import { Globe, Search, Layers } from "lucide-react";

interface TopicsResp {
  categories: string[];
  count: number;
  topics: (TopicStat & { category: string })[];
}

const CATEGORY_LABELS: Record<string, string> = {
  all: "All Narratives",
  geopolitics: "Geopolitics & Conflicts",
  figure: "World Leaders & Figures",
  party: "Political Parties & Blocs",
  issue: "Socio-Economic Issues",
  macro_tech: "Macro & Tech Sovereignty",
  institution: "Multilateral Institutions",
};

export default function BrowsePage() {
  const { data, loading, error, reload } = useApi<TopicsResp>("/api/topics");
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("all");

  const categoryCounts = useMemo(() => {
    if (!data) return {};
    const counts: Record<string, number> = { all: data.topics.length };
    data.topics.forEach((t) => {
      counts[t.category] = (counts[t.category] || 0) + 1;
    });
    return counts;
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    const ql = q.trim().toLowerCase();
    return data.topics.filter((t) =>
      (cat === "all" || t.category === cat) &&
      (!ql || t.label.toLowerCase().includes(ql) || t.id.toLowerCase().includes(ql) || t.category.toLowerCase().includes(ql))
    );
  }, [data, q, cat]);

  const cats = ["all", ...(data?.categories ?? [])];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Global Political Narratives & Topics"
        subtitle={`Explore the comprehensive worldwide universe${data ? ` of ${data.count} tracked topics` : ""} across geopolitics, world leaders, parties, macroeconomic issues, and multilateral institutions.`}
      />

      <div className="flex flex-col gap-3.5">
        {/* Search Input */}
        <div className="relative">
          <Search size={16} className="absolute left-3.5 top-3.5 text-muted pointer-events-none" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search worldwide narratives by topic, leader, party, country, or keyword…"
            className="h-11 w-full rounded-xl border border-border bg-card pl-10 pr-4 text-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {cats.map((c) => {
            const count = categoryCounts[c] ?? 0;
            const label = CATEGORY_LABELS[c] || c;
            const active = cat === c;
            return (
              <button
                key={c}
                onClick={() => setCat(c)}
                className={cx(
                  "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                  active
                    ? "border-accent bg-accent/15 text-accent shadow-sm font-semibold"
                    : "border-border bg-card2 text-muted hover:border-border/80 hover:text-foreground"
                )}
              >
                <span>{label}</span>
                <span
                  className={cx(
                    "rounded-full px-1.5 py-0.2 text-[10px]",
                    active ? "bg-accent/25 text-accent" : "bg-card text-muted"
                  )}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {loading && <CardGridSkeleton n={12} />}
      {error && <EmptyState title="Couldn't load topic catalog" hint={error} onRetry={reload} />}

      {data && (
        <>
          <div className="flex items-center justify-between text-sm text-muted">
            <div className="flex items-center gap-2">
              <Layers size={15} className="text-accent" />
              <span>
                Showing <strong className="text-foreground">{filtered.length}</strong> of {data.count} topics
              </span>
            </div>
            <Link
              href={q ? `/topic?q=${encodeURIComponent(q)}` : "/topic"}
              className="text-accent hover:underline text-xs sm:text-sm font-medium"
            >
              Analyze &ldquo;{q || "any unlisted topic"}&rdquo; on demand →
            </Link>
          </div>

          {filtered.length === 0 ? (
            <EmptyState
              title={`No catalog topic matches “${q}”`}
              hint="You can still analyze any custom political topic or world event dynamically on the topic analyzer page."
            />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((t) => (
                <TopicCard key={t.id} t={t} />
              ))}
            </div>
          )}

          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
