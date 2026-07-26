"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import type { EChartsCoreOption } from "echarts";
import * as echarts from "echarts";
import { useApi } from "@/lib/useApi";
import { EChart, useChartTheme } from "@/components/echart";
import { lineTimeSeries, horizontalBar } from "@/components/charts";
import { Card, PageHeader, StatTile, Spinner, EmptyState, Badge, DISCLAIMER } from "@/components/ui";
import { fmtSigned, fmtNum, toneColor } from "@/lib/format";

const NAME_FIX: Record<string, string> = { "South Korea": "Korea" };
const EXAMPLES = ["inflation", "Donald Trump", "AI regulation", "war in Ukraine", "housing crisis", "NATO"];

interface Topic { id: string; label: string; query: string; category: string; custom: boolean; }
interface MV { week_start: string; media_tone: number | null; public_sentiment: number | null; gap: number | null; }
interface FRow { week_start: string; forecast: number; lower: number; upper: number; }
interface CRow { country: string; country_name: string; iso3: string; avg_tone: number; article_volume: number; }
interface Analysis {
  topic: Topic; inception: string; age_weeks: number;
  media_series: { week_start: string; avg_tone: number }[];
  media_vs_public: MV[]; avg_media: number | null; avg_public: number | null; avg_gap: number | null;
  forecast: { method: string; note: string; points: FRow[] };
  anomalies: { week_start: string; avg_tone: number; kind: string; direction: string }[];
  drivers: { spike_week: string | null; topics: { words: string[]; weight: number }[] };
  by_country: CRow[];
  by_language: { language: string; avg_tone: number; volume: number }[];
  stats: { total_articles: number; total_posts: number; max_diversity: number; low_conf_weeks: number; n_weeks: number;
    source_media: string; source_opinion: string; geo_modelled: boolean };
}

function SearchBar({ initial }: { initial: string }) {
  const router = useRouter();
  const [q, setQ] = useState(initial);
  const go = () => { if (q.trim()) router.push(`/topic?q=${encodeURIComponent(q.trim())}`); };
  return (
    <div className="flex flex-col gap-2 sm:flex-row">
      <input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && go()}
        placeholder="Analyze any topic — a person, party, issue, or phrase…"
        className="h-11 flex-1 rounded-lg border border-border bg-card px-4 text-sm outline-none focus:border-accent/60" />
      <button onClick={go} className="h-11 rounded-lg bg-accent px-5 text-sm font-medium text-white">Analyze</button>
    </div>
  );
}

function TopicInner() {
  const params = useSearchParams();
  const router = useRouter();
  const q = params.get("q") ?? "";
  const t = useChartTheme();
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    let alive = true;
    fetch("/world.json").then((r) => r.json())
      .then((geo) => { if (alive) { echarts.registerMap("world", geo); setMapReady(true); } })
      .catch(() => setMapReady(false));
    return () => { alive = false; };
  }, []);

  const { data, loading, error } = useApi<Analysis>(q ? "/api/topic" : null, { q });

  const mvOption = useMemo(() => {
    if (!data) return {};
    return lineTimeSeries(t, [
      { name: "Media (coverage tone)", points: data.media_vs_public.map((r) => ({ week_start: r.week_start, value: r.media_tone })), color: t.accent },
      { name: "Public (social sentiment)", points: data.media_vs_public.map((r) => ({ week_start: r.week_start, value: r.public_sentiment })), color: t.accent2 },
    ], { yName: "sentiment", showZero: true });
  }, [data, t]);

  const fcOption = useMemo<EChartsCoreOption>(() => {
    if (!data) return {};
    const hist = data.media_series; const last = hist.at(-1); const fc = data.forecast.points;
    return {
      color: [t.accent, t.accent2, t.negative],
      grid: { left: 8, right: 16, top: 30, bottom: 8, containLabel: true },
      legend: { top: 0, data: ["Observed", "Forecast", "95% interval", "Anomaly"], textStyle: { color: t.muted, fontSize: 11 }, icon: "roundRect" },
      tooltip: { trigger: "axis", backgroundColor: t.card, borderColor: t.border, textStyle: { color: t.fg, fontSize: 12 }, valueFormatter: (v: unknown) => (typeof v === "number" ? v.toFixed(2) : "—") },
      xAxis: { type: "time", axisLine: { lineStyle: { color: t.border } }, axisLabel: { color: t.muted, fontSize: 11 }, splitLine: { show: false } },
      yAxis: { type: "value", axisLabel: { color: t.muted, fontSize: 11 }, splitLine: { lineStyle: { color: t.grid, opacity: 0.35 } } },
      series: [
        { name: "Observed", type: "line", showSymbol: false, smooth: 0.25, lineStyle: { width: 2, color: t.accent }, data: hist.map((h) => [h.week_start, h.avg_tone]) },
        { name: "_l", type: "line", stack: "b", symbol: "none", lineStyle: { opacity: 0 }, areaStyle: { opacity: 0 }, silent: true, data: fc.map((f) => [f.week_start, f.lower]) },
        { name: "95% interval", type: "line", stack: "b", symbol: "none", lineStyle: { opacity: 0 }, areaStyle: { color: t.muted, opacity: 0.18 }, silent: true, data: fc.map((f) => [f.week_start, f.upper - f.lower]) },
        { name: "Forecast", type: "line", showSymbol: false, lineStyle: { width: 2, type: "dashed", color: t.accent2 }, data: [...(last ? [[last.week_start, last.avg_tone]] : []), ...fc.map((f) => [f.week_start, f.forecast])] },
        { name: "Anomaly", type: "scatter", symbolSize: 11, itemStyle: { color: t.negative }, data: data.anomalies.map((a) => [a.week_start, a.avg_tone]) },
      ],
    };
  }, [data, t]);

  const mapOption = useMemo<EChartsCoreOption>(() => {
    if (!data) return {};
    const clip = Math.max(1, ...data.by_country.map((r) => Math.abs(r.avg_tone)));
    return {
      tooltip: { trigger: "item", backgroundColor: t.card, borderColor: t.border, textStyle: { color: t.fg, fontSize: 12 },
        formatter: (p: { name: string; value: number }) => `${p.name}<br/>Tone: ${p.value != null && !Number.isNaN(p.value) ? fmtSigned(p.value) : "no data"}` },
      visualMap: { min: -clip, max: clip, calculable: true, orient: "horizontal", left: "center", bottom: 4,
        inRange: { color: [t.negative, "#7d8597", t.accent] }, textStyle: { color: t.muted, fontSize: 11 }, text: ["+", "−"] },
      series: [{ type: "map", map: "world", roam: false,
        data: data.by_country.map((r) => ({ name: NAME_FIX[r.country_name] ?? r.country_name, value: r.avg_tone })),
        itemStyle: { areaColor: t.card2, borderColor: t.border, borderWidth: 0.4 },
        emphasis: { itemStyle: { areaColor: t.accent2 }, label: { show: false } } }],
    };
  }, [data, t]);

  const langOption = useMemo(() => {
    if (!data) return {};
    return horizontalBar(t, data.by_language.slice(0, 12).map((l) => ({ label: `${l.language} (${fmtNum(l.volume)})`, value: l.avg_tone })), { xName: "tone", colorByTone: true });
  }, [data, t]);

  return (
    <div className="space-y-6">
      <PageHeader title="Analyze a topic" subtitle="Enter any political topic — a person, party, issue, institution, or phrase — for its full sentiment history (media + public), forecast, drivers, and geography." />
      <SearchBar initial={q} />

      {!q && (
        <Card className="p-6">
          <div className="mb-2 text-sm text-muted">Try one of these:</div>
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((e) => (
              <button key={e} onClick={() => router.push(`/topic?q=${encodeURIComponent(e)}`)}
                className="rounded-full border border-border px-3 py-1.5 text-sm text-muted hover:border-accent/50 hover:text-foreground">{e}</button>
            ))}
          </div>
        </Card>
      )}

      {q && loading && <Spinner label={`Analyzing “${q}”…`} />}
      {q && error && <EmptyState title="Couldn't analyze that topic" hint={error} />}

      {data && (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold">{data.topic.label}</h2>
            <Badge tone="accent">{data.topic.category}</Badge>
            {data.topic.custom && <Badge tone="warning">custom</Badge>}
            <span className="text-xs text-muted">· tracked since {data.inception} ({data.age_weeks} weeks of history)</span>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted">
            <Badge>media: {data.stats.source_media}</Badge>
            <Badge>social: {data.stats.source_opinion}</Badge>
            {data.stats.source_media === "synthetic" && <span>· synthetic fallback (live needs GDELT/keys)</span>}
          </div>

          <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
            <StatTile label="Avg media tone" value={fmtSigned(data.avg_media)} accent={t.accent} />
            <StatTile label="Avg public sentiment" value={fmtSigned(data.avg_public)} accent={t.accent2} />
            <StatTile label="Media↔public gap" value={fmtSigned(data.avg_gap)} accent={data.avg_gap != null && data.avg_gap >= 0 ? t.positive : t.negative} />
            <StatTile label="Articles" value={fmtNum(data.stats.total_articles)} />
            <StatTile label="Social posts" value={fmtNum(data.stats.total_posts)} />
          </div>

          <Card className="p-4">
            <div className="mb-2 text-sm font-medium">Media vs public sentiment — full history</div>
            <EChart height={380} option={mvOption} />
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium">Forecast &amp; anomalies <Badge tone="accent">{data.forecast.method}</Badge></div>
              <EChart height={320} option={fcOption} />
              <div className="mt-1 text-xs text-muted">{data.forecast.note} Read the band, not just the line.</div>
            </Card>
            <Card className="p-4">
              <div className="mb-1 text-sm font-medium">🧩 What&apos;s driving it</div>
              {data.drivers.spike_week
                ? <>
                    <div className="mb-2 text-xs text-muted">Biggest swing around {data.drivers.spike_week}:</div>
                    <div className="space-y-1.5">
                      {data.drivers.topics.map((tp, i) => (
                        <div key={i} className="text-sm"><span className="text-muted">Topic {i + 1}: </span>
                          {tp.words.map((w) => <code key={w} className="mr-1 rounded bg-card2 px-1.5 py-0.5 text-xs">{w}</code>)}</div>
                      ))}
                    </div>
                  </>
                : <div className="text-sm text-muted">Not enough data to identify drivers.</div>}
            </Card>
          </div>

          <Card className="p-2">
            <div className="px-2 pt-2 text-sm font-medium">
              Coverage tone by country{data.stats.geo_modelled && <span className="ml-1 text-xs font-normal text-muted">(modelled distribution)</span>}
            </div>
            {mapReady ? <EChart height={420} option={mapOption} /> : <Spinner label="Loading map…" />}
          </Card>

          <Card className="p-4">
            <div className="mb-2 text-sm font-medium">Coverage tone by source language</div>
            <EChart height={Math.max(260, data.by_language.length * 24)} option={langOption} />
          </Card>

          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}

export default function TopicPage() {
  return <Suspense fallback={<Spinner />}><TopicInner /></Suspense>;
}
