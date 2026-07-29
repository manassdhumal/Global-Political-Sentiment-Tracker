"use client";

import Link from "next/link";
import { useState } from "react";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { TopicCard, TopicStat } from "@/components/topic-card";
import { Card, PageHeader, StatTile, EmptyState, Banner, Badge, CardGridSkeleton, Skeleton, DISCLAIMER, cx } from "@/components/ui";
import { fmtSigned, fmtNum, toneColor } from "@/lib/format";

interface AlertsResp { threshold: number; count: number; alerts: TopicStat[]; }

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
  const { data, loading, error, reload } = useApi<TrendingResp>("/api/trending", { top_n: 12 });
  const [threshold, setThreshold] = useState(2);
  const { data: alerts } = useApi<AlertsResp>("/api/alerts", { threshold });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Trending political sentiment"
        subtitle="What the world's media and social platforms are talking about right now — ranked by attention and sentiment movement. Media & social sentiment, not public opinion."
      />
      {config?.synthetic && <Banner>⚠ Running on synthetic (fabricated) demo data — not real coverage.</Banner>}
      {loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20" />)}</div>
          <CardGridSkeleton n={6} />
        </div>
      )}
      {error && <EmptyState title="Couldn't load trends" hint={error + " — is the API running on :8000?"} onRetry={reload} />}

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

          <Card className="p-4">
            <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-medium text-warning">
                ⚠ Sentiment-shift alerts {alerts && <Badge tone="warning">{alerts.count}</Badge>}
              </div>
              <label className="flex items-center gap-2 text-xs text-muted">
                threshold ±{threshold.toFixed(1)}
                <input type="range" min={0.5} max={6} step={0.5} value={threshold}
                  onChange={(e) => setThreshold(Number(e.target.value))} className="accent-[var(--accent)]" />
              </label>
            </div>
            {!alerts ? (
              <div className="flex gap-2">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-7 w-28 rounded-full" />)}</div>
            ) : alerts.alerts.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {alerts.alerts.map((a) => (
                  <Link key={a.id} href={`/topic?q=${encodeURIComponent(a.id)}`}
                    className="flex items-center gap-2 rounded-full border border-border px-3 py-1 text-sm hover:border-accent/50">
                    <span>{a.label}</span>
                    <span className={cx("tnum text-xs", a.movement >= 0 ? "text-positive" : "text-negative")}>
                      {a.movement >= 0 ? "▲" : "▼"} {fmtSigned(a.movement)}
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted">No topics moved beyond ±{threshold.toFixed(1)} this week.</div>
            )}
          </Card>

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
