"use client";

import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { TopicCard, TopicStat } from "@/components/topic-card";
import { Card, PageHeader, StatTile, Spinner, EmptyState, Banner, DISCLAIMER, cx } from "@/components/ui";
import { fmtSigned, fmtNum, toneColor } from "@/lib/format";

interface Snapshot {
  global_tone: number | null; total_volume: number; n_topics: number; avg_gap: number | null;
  top_rising: TopicStat[]; top_falling: TopicStat[];
}
interface TrendingResp { snapshot: Snapshot; trending: TopicStat[]; cached?: boolean; computed_at?: string; source?: string; }

function MoverRow({ t }: { t: TopicStat }) {
  const up = t.movement >= 0;
  return (
    <Link href={`/topic?q=${encodeURIComponent(t.id)}`} className="flex items-center justify-between py-2 hover:text-accent">
      <span className="truncate text-sm">{t.label}</span>
      <span className="flex items-center gap-3 tnum">
        <span className="text-sm" style={{ color: toneColor(t.latest_tone) }}>{fmtSigned(t.latest_tone)}</span>
        <span className={cx("text-xs", up ? "text-positive" : "text-negative")}>{up ? "▲" : "▼"} {fmtSigned(t.movement)}</span>
      </span>
    </Link>
  );
}

export default function TrendingPage() {
  const { config } = useConfig();
  const { data, loading, error } = useApi<TrendingResp>("/api/trending", { top_n: 12 });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Trending political sentiment"
        subtitle="What the world's media and social platforms are talking about right now — ranked by attention and sentiment movement. Media & social sentiment, not public opinion."
      />
      {config?.synthetic && <Banner>⚠ Running on synthetic (fabricated) demo data — not real coverage.</Banner>}
      {loading && <Spinner label="Computing trends…" />}
      {error && <EmptyState title="Couldn't load trends" hint={error + " — is the API running on :8000?"} />}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile label="Global tone" value={fmtSigned(data.snapshot.global_tone)} accent={toneColor(data.snapshot.global_tone)} />
            <StatTile label="Recent article volume" value={fmtNum(data.snapshot.total_volume)} />
            <StatTile label="Topics tracked" value={data.snapshot.n_topics} sub="+ any custom topic" />
            <StatTile label="Avg media↔public gap" value={fmtSigned(data.snapshot.avg_gap)} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="p-4">
              <div className="mb-1 text-sm font-medium text-positive">▲ Rising this week</div>
              <div className="divide-y divide-border">{data.snapshot.top_rising.map((t) => <MoverRow key={t.id} t={t} />)}</div>
            </Card>
            <Card className="p-4">
              <div className="mb-1 text-sm font-medium text-negative">▼ Falling this week</div>
              <div className="divide-y divide-border">{data.snapshot.top_falling.map((t) => <MoverRow key={t.id} t={t} />)}</div>
            </Card>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-baseline gap-2">
              <h2 className="text-sm font-semibold">Trending topics</h2>
              {data.computed_at && (
                <span className="text-[11px] text-muted">
                  · {data.source} · updated {new Date(data.computed_at).toLocaleString()}
                </span>
              )}
            </div>
            <Link href="/topics" className="text-sm text-accent hover:underline">Browse all topics →</Link>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.trending.map((t) => <TopicCard key={t.id} t={t} />)}
          </div>

          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
