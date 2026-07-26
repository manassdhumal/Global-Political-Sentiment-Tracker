"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { TopicCard, TopicStat } from "@/components/topic-card";
import { PageHeader, Spinner, EmptyState, Segmented, Badge, DISCLAIMER, cx } from "@/components/ui";

interface TopicsResp { categories: string[]; count: number; topics: (TopicStat & { category: string })[]; }

export default function BrowsePage() {
  const { data, loading, error } = useApi<TopicsResp>("/api/topics");
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("all");

  const filtered = useMemo(() => {
    if (!data) return [];
    const ql = q.trim().toLowerCase();
    return data.topics.filter((t) =>
      (cat === "all" || t.category === cat) &&
      (!ql || t.label.toLowerCase().includes(ql)));
  }, [data, q, cat]);

  const cats = ["all", ...(data?.categories ?? [])];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Browse topics"
        subtitle={`Explore the full catalog${data ? ` of ${data.count} tracked topics` : ""} — or analyze any topic that isn't listed.`}
      />

      <div className="flex flex-col gap-3">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter topics by name…"
          className="h-11 w-full rounded-lg border border-border bg-card px-4 text-sm outline-none focus:border-accent/60" />
        <div className="flex flex-wrap items-center gap-2">
          {cats.map((c) => (
            <button key={c} onClick={() => setCat(c)}
              className={cx("rounded-full border px-3 py-1 text-xs capitalize transition-colors",
                cat === c ? "border-accent bg-accent/15 text-accent" : "border-border text-muted hover:text-foreground")}>
              {c}
            </button>
          ))}
        </div>
      </div>

      {loading && <Spinner />}
      {error && <EmptyState title="Couldn't load catalog" hint={error} />}

      {data && (
        <>
          <div className="flex items-center justify-between text-sm text-muted">
            <span>{filtered.length} topic{filtered.length !== 1 ? "s" : ""}</span>
            <Link href={q ? `/topic?q=${encodeURIComponent(q)}` : "/topic"} className="text-accent hover:underline">
              Can&apos;t find it? Analyze &ldquo;{q || "any topic"}&rdquo; →
            </Link>
          </div>
          {filtered.length === 0
            ? <EmptyState title={`No catalog topic matches “${q}”`} hint="Use ‘Analyze a topic’ to run it on demand anyway." />
            : <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {filtered.map((t) => <TopicCard key={t.id} t={t} />)}
              </div>}
          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
