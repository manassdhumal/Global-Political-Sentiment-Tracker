"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { api, WorldMapData, WorldCountrySentiment } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { EChart, useChartTheme } from "@/components/echart";
import { toneColor, fmtSigned } from "@/lib/format";
import {
  Globe,
  Flame,
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Filter,
  Anchor,
  ShieldAlert,
  Vote,
  Layers,
  Play,
  Pause,
  RotateCcw,
  GitCompare,
  X,
  History,
} from "lucide-react";
import type { EChartsCoreOption } from "echarts";

const REGIONS = [
  { id: "all", label: "🌍 Global (All)" },
  { id: "g7", label: "🏛️ G7 Nations" },
  { id: "nato", label: "🛡️ NATO Allies" },
  { id: "brics", label: "🌐 BRICS+" },
  { id: "eu", label: "🇪🇺 European Union" },
  { id: "americas", label: "🌎 Americas" },
  { id: "europe", label: "🏰 Europe" },
  { id: "apac", label: "🌏 Asia-Pacific" },
  { id: "middle_east", label: "🏜️ Middle East" },
];

interface ChokepointItem {
  id: string;
  name: string;
  lat: number;
  lng: number;
  type: string;
  oil_transit_mbpd: number;
  share_of_global_oil_pct: number;
  primary_actors: string[];
  security_status: string;
  risk_tier: string;
  summary: string;
}

interface FlashpointItem {
  id: string;
  title: string;
  lat: number;
  lng: number;
  category: string;
  intensity: string;
  summary: string;
}

interface ElectionItem {
  country: string;
  flag: string;
  lat: number;
  lng: number;
  date: string;
  event: string;
  stakes: string;
}

interface MapLayersData {
  chokepoints: ChokepointItem[];
  conflict_flashpoints: FlashpointItem[];
  elections: ElectionItem[];
}

function sparkOption(spark: number[], color: string): EChartsCoreOption {
  return {
    grid: { left: 2, right: 2, top: 4, bottom: 2 },
    xAxis: { type: "category", show: false, data: spark.map((_, i) => i) },
    yAxis: { type: "value", show: false, scale: true },
    tooltip: { show: false },
    series: [
      {
        type: "line",
        data: spark,
        showSymbol: false,
        smooth: 0.3,
        lineStyle: { width: 2, color },
        areaStyle: { color, opacity: 0.12 },
      },
    ],
  };
}

function bilateralComparisonOption(
  c1: WorldCountrySentiment,
  c2: WorldCountrySentiment,
  dates: string[]
): EChartsCoreOption {
  const d = dates && dates.length > 0 ? dates : c1.spark.map((_, i) => `W${i + 1}`);
  return {
    backgroundColor: "transparent",
    grid: { left: 35, right: 15, top: 30, bottom: 25 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "#1e293b",
      borderColor: "#334155",
      textStyle: { color: "#f8fafc" },
    },
    legend: {
      data: [`${c1.flag} ${c1.name}`, `${c2.flag} ${c2.name}`],
      textStyle: { color: "#94a3b8", fontSize: 11 },
      top: 2,
    },
    xAxis: {
      type: "category",
      data: d,
      axisLabel: { color: "#64748b", fontSize: 9 },
      axisLine: { lineStyle: { color: "#334155" } },
    },
    yAxis: {
      type: "value",
      axisLabel: { color: "#64748b", fontSize: 10 },
      splitLine: { lineStyle: { color: "#1e293b" } },
    },
    series: [
      {
        name: `${c1.flag} ${c1.name}`,
        type: "line",
        data: c1.spark,
        smooth: true,
        lineStyle: { width: 2.5, color: "#38bdf8" },
        itemStyle: { color: "#38bdf8" },
      },
      {
        name: `${c2.flag} ${c2.name}`,
        type: "line",
        data: c2.spark,
        smooth: true,
        lineStyle: { width: 2.5, color: "#f59e0b" },
        itemStyle: { color: "#f59e0b" },
      },
    ],
  };
}

export default function WorldMapPage() {
  const [activeLayer, setActiveLayer] = useState<"sentiment" | "chokepoints" | "conflicts" | "elections">("sentiment");
  const [region, setRegion] = useState("all");
  const [data, setData] = useState<WorldMapData | null>(null);
  const [layersData, setLayersData] = useState<MapLayersData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<WorldCountrySentiment | null>(null);
  const [comparisonCountry, setComparisonCountry] = useState<WorldCountrySentiment | null>(null);

  // Time-Machine Playback State
  const [playbackIndex, setPlaybackIndex] = useState<number>(11);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([
      api<WorldMapData>("/api/geography/world-map", { region }),
      api<MapLayersData>("/api/geography/layers"),
    ])
      .then(([mapRes, layersRes]) => {
        setData(mapRes);
        setLayersData(layersRes);
        if (mapRes.countries.length > 0 && !selectedCountry) {
          setSelectedCountry(mapRes.countries[0]);
        }
        if (mapRes.timeline_weeks && mapRes.timeline_weeks.length > 0) {
          setPlaybackIndex(mapRes.timeline_weeks.length - 1);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [region]);

  // Handle Playback Interval
  useEffect(() => {
    if (isPlaying) {
      timerRef.current = setInterval(() => {
        setPlaybackIndex((prev) => {
          const maxIdx = data?.timeline_weeks ? data.timeline_weeks.length - 1 : 11;
          return prev >= maxIdx ? 0 : prev + 1;
        });
      }, 1400);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, data]);

  const timelineWeeks = data?.timeline_weeks || [];
  const currentWeekDate = timelineWeeks[playbackIndex] || "Latest Week";
  const isLatestWeek = timelineWeeks.length === 0 || playbackIndex === timelineWeeks.length - 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌍</span>
            <h1 className="text-2xl font-bold tracking-tight">Geopolitical Map &amp; Strategic Layers</h1>
          </div>
          <p className="text-sm text-muted">
            Interactive multi-layer geospatial terminal tracking world sentiment, maritime chokepoint transit flows, combat flashpoints, and national election calendars.
          </p>
        </div>
      </div>

      {/* Layer Switcher Tabs */}
      <div className="flex items-center gap-2 border-b border-border pb-3 overflow-x-auto">
        <button
          onClick={() => setActiveLayer("sentiment")}
          className={cx(
            "flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0",
            activeLayer === "sentiment"
              ? "bg-accent text-white shadow-sm"
              : "bg-card text-muted hover:text-foreground hover:bg-card2"
          )}
        >
          <Globe size={14} /> World Sentiment &amp; Heatmap
          {data && <Badge tone="muted" className="ml-1">{data.countries.length}</Badge>}
        </button>

        <button
          onClick={() => setActiveLayer("chokepoints")}
          className={cx(
            "flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0",
            activeLayer === "chokepoints"
              ? "bg-accent text-white shadow-sm"
              : "bg-card text-muted hover:text-foreground hover:bg-card2"
          )}
        >
          <Anchor size={14} /> Strategic Maritime Chokepoints
          {layersData && <Badge tone="accent" className="ml-1">{layersData.chokepoints.length}</Badge>}
        </button>

        <button
          onClick={() => setActiveLayer("conflicts")}
          className={cx(
            "flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0",
            activeLayer === "conflicts"
              ? "bg-accent text-white shadow-sm"
              : "bg-card text-muted hover:text-foreground hover:bg-card2"
          )}
        >
          <ShieldAlert size={14} /> Conflict Flashpoints &amp; Combat
          {layersData && <Badge tone="negative" className="ml-1">{layersData.conflict_flashpoints.length}</Badge>}
        </button>

        <button
          onClick={() => setActiveLayer("elections")}
          className={cx(
            "flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all shrink-0",
            activeLayer === "elections"
              ? "bg-accent text-white shadow-sm"
              : "bg-card text-muted hover:text-foreground hover:bg-card2"
          )}
        >
          <Vote size={14} /> Global Elections Countdown
          {layersData && <Badge tone="muted" className="ml-1">{layersData.elections.length}</Badge>}
        </button>
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Aggregating global geopolitical and maritime signals...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Failed to load geographical map data: {error}
        </div>
      )}

      {/* VIEW 1: SENTIMENT HEATMAP */}
      {activeLayer === "sentiment" && data && !loading && (
        <div className="space-y-6">
          {/* Summary KPI Strip */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card className="p-4">
              <div className="text-xs text-muted">Monitored Countries</div>
              <div className="mt-1 text-2xl font-bold">{data.summary.country_count}</div>
            </Card>
            <Card className="p-4 border-rose-500/30 bg-rose-500/5">
              <div className="flex items-center gap-1.5 text-xs text-rose-400 font-medium">
                <Flame size={14} /> Active Hotspots
              </div>
              <div className="mt-1 text-2xl font-bold text-rose-500">{data.summary.hotspot_count}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Global Mean Media Tone</div>
              <div className={cx(
                "mt-1 text-2xl font-bold",
                data.summary.global_avg_tone > 0 ? "text-emerald-500" : "text-rose-500"
              )}>
                {data.summary.global_avg_tone > 0 ? `+${data.summary.global_avg_tone}` : data.summary.global_avg_tone}
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Aggregated Press Volume</div>
              <div className="mt-1 text-2xl font-bold">{data.summary.total_articles.toLocaleString()}</div>
            </Card>
          </div>

          {/* 12-WEEK TIME-MACHINE PLAYBACK BAR */}
          {timelineWeeks.length > 0 && (
            <Card className="p-4 bg-card/80 border-accent/30 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <History size={16} className="text-accent" />
                  <span className="text-xs font-bold uppercase tracking-wider text-accent">12-Week Time-Machine Playback</span>
                  <Badge tone={isLatestWeek ? "positive" : "warning"} className="font-mono text-[10px]">
                    {isLatestWeek ? "LIVE / LATEST" : `WEEK ${playbackIndex + 1}/12`}
                  </Badge>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted font-mono">{currentWeekDate}</span>
                  {!isLatestWeek && (
                    <button
                      onClick={() => {
                        setIsPlaying(false);
                        setPlaybackIndex(timelineWeeks.length - 1);
                      }}
                      className="rounded bg-accent/20 px-2 py-0.5 text-[11px] font-semibold text-accent hover:bg-accent/30 transition-colors"
                    >
                      Jump to Live
                    </button>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent text-white hover:bg-accent/90 transition-all shadow-sm"
                  title={isPlaying ? "Pause Timeline" : "Play Timeline"}
                >
                  {isPlaying ? <Pause size={14} /> : <Play size={14} className="ml-0.5" />}
                </button>

                <button
                  onClick={() => {
                    setIsPlaying(false);
                    setPlaybackIndex(0);
                  }}
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-border bg-card text-muted hover:text-foreground transition-all"
                  title="Reset to Week 1"
                >
                  <RotateCcw size={13} />
                </button>

                <div className="flex-1 flex flex-col gap-1">
                  <input
                    type="range"
                    min={0}
                    max={timelineWeeks.length - 1}
                    value={playbackIndex}
                    onChange={(e) => {
                      setIsPlaying(false);
                      setPlaybackIndex(parseInt(e.target.value, 10));
                    }}
                    className="w-full h-1.5 bg-card2 rounded-lg appearance-none cursor-pointer accent-accent"
                  />
                  <div className="flex justify-between text-[10px] text-muted font-mono">
                    <span>{timelineWeeks[0]}</span>
                    <span>{timelineWeeks[Math.floor(timelineWeeks.length / 2)]}</span>
                    <span>{timelineWeeks[timelineWeeks.length - 1]}</span>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Region Filter Bar */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
            <Filter size={15} className="text-muted shrink-0 ml-1" />
            {REGIONS.map((r) => (
              <button
                key={r.id}
                onClick={() => setRegion(r.id)}
                className={cx(
                  "rounded-full px-3.5 py-1.5 text-xs font-medium whitespace-nowrap transition-all",
                  region === r.id
                    ? "bg-accent text-white shadow-sm"
                    : "bg-card hover:bg-card2 border border-border text-muted hover:text-foreground"
                )}
              >
                {r.label}
              </button>
            ))}
          </div>

          {/* Countries Grid & Inspector */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {data.countries.map((c) => {
                  const isSelected = selectedCountry?.iso3 === c.iso3;
                  const isCompared = comparisonCountry?.iso3 === c.iso3;
                  // Dynamic playback tone if time machine active
                  const activeTone = (c.history && c.history[playbackIndex] !== undefined)
                    ? c.history[playbackIndex]
                    : c.latest_tone;
                  const color = toneColor(activeTone);

                  return (
                    <div
                      key={c.iso3}
                      onClick={() => setSelectedCountry(c)}
                      className={cx(
                        "cursor-pointer rounded-xl border p-4 transition-all duration-200 hover:border-accent/50",
                        isSelected
                          ? "border-accent bg-accent/5 shadow-md shadow-accent/5 ring-1 ring-accent/30"
                          : isCompared
                          ? "border-amber-500 bg-amber-500/5 shadow-md ring-1 ring-amber-500/30"
                          : "border-border bg-card hover:bg-card2",
                        c.is_hotspot && !isSelected && !isCompared && "border-rose-500/40 bg-rose-500/[0.03]"
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{c.flag}</span>
                          <div>
                            <div className="font-semibold text-sm leading-tight flex items-center gap-1.5">
                              {c.name}
                              {c.is_hotspot && (
                                <span className="flex items-center gap-0.5 text-[10px] font-bold text-rose-500 uppercase tracking-wider bg-rose-500/10 px-1.5 py-0.5 rounded">
                                  <Flame size={11} /> Hotspot
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-muted">{c.status_label}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-base font-bold tabular-nums" style={{ color }}>
                            {fmtSigned(activeTone)}
                          </div>
                          <div className={cx(
                            "text-[10px] tabular-nums font-medium flex items-center justify-end gap-0.5",
                            c.movement >= 0 ? "text-emerald-500" : "text-rose-500"
                          )}>
                            {c.movement >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                            {fmtSigned(c.movement)}
                          </div>
                        </div>
                      </div>

                      <div className="mt-3 flex items-center justify-between text-[11px] text-muted border-t border-border/50 pt-2">
                        <span>Articles: <strong>{c.volume.toLocaleString()}</strong></span>
                        <div className="flex items-center gap-2">
                          <span>Divergence: <strong>{c.gap > 0 ? `+${c.gap}` : c.gap}</strong></span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              if (comparisonCountry?.iso3 === c.iso3) {
                                setComparisonCountry(null);
                              } else {
                                setComparisonCountry(c);
                              }
                            }}
                            className={cx(
                              "flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium transition-colors",
                              isCompared ? "bg-amber-500 text-white" : "bg-card2 hover:bg-card hover:text-foreground"
                            )}
                            title="Compare with selected country"
                          >
                            <GitCompare size={10} /> {isCompared ? "Comparing" : "Compare"}
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Country Detail Inspector & Bilateral Comparison Drawer */}
            <div className="space-y-4">
              {/* BILATERAL HEAD-TO-HEAD COMPARISON DRAWER */}
              {selectedCountry && comparisonCountry && selectedCountry.iso3 !== comparisonCountry.iso3 ? (
                <Card className="sticky top-6 p-5 space-y-4 border-amber-500/40 bg-card">
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
                      <GitCompare size={15} /> Bilateral Country Comparison
                    </div>
                    <button
                      onClick={() => setComparisonCountry(null)}
                      className="text-muted hover:text-foreground p-1"
                      title="Close Comparison"
                    >
                      <X size={14} />
                    </button>
                  </div>

                  {/* Head-to-Head Cards */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-card2 p-3 text-center space-y-1">
                      <span className="text-3xl">{selectedCountry.flag}</span>
                      <div className="text-sm font-bold truncate">{selectedCountry.name}</div>
                      <div className="text-base font-bold tabular-nums" style={{ color: toneColor(selectedCountry.latest_tone) }}>
                        {fmtSigned(selectedCountry.latest_tone)}
                      </div>
                      <div className="text-[10px] text-muted">Public Tone: {fmtSigned(selectedCountry.public_sentiment)}</div>
                    </div>

                    <div className="rounded-lg bg-card2 p-3 text-center space-y-1">
                      <span className="text-3xl">{comparisonCountry.flag}</span>
                      <div className="text-sm font-bold truncate">{comparisonCountry.name}</div>
                      <div className="text-base font-bold tabular-nums" style={{ color: toneColor(comparisonCountry.latest_tone) }}>
                        {fmtSigned(comparisonCountry.latest_tone)}
                      </div>
                      <div className="text-[10px] text-muted">Public Tone: {fmtSigned(comparisonCountry.public_sentiment)}</div>
                    </div>
                  </div>

                  {/* Dual 12-Week Trend Line Chart */}
                  <div className="space-y-1 rounded-lg bg-card2 p-3">
                    <div className="text-[10px] uppercase font-bold text-muted">12-Week Comparative Sentiment Trajectory</div>
                    <div className="h-44 w-full">
                      <EChart
                        option={bilateralComparisonOption(selectedCountry, comparisonCountry, timelineWeeks)}
                        className="h-44 w-full"
                      />
                    </div>
                  </div>

                  {/* Divergence Metric Strip */}
                  <div className="rounded-lg bg-card2 p-2.5 flex items-center justify-between text-xs">
                    <span className="text-muted font-medium">Bilateral Sentiment Delta</span>
                    <span className="font-bold font-mono">
                      {fmtSigned(round(selectedCountry.latest_tone - comparisonCountry.latest_tone, 2))} pts
                    </span>
                  </div>
                </Card>
              ) : selectedCountry ? (
                /* SINGLE COUNTRY INSPECTOR DRAWER */
                <Card className="sticky top-6 p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="text-3xl">{selectedCountry.flag}</span>
                      <div>
                        <h2 className="text-base font-bold leading-tight">{selectedCountry.name}</h2>
                        <span className="text-xs text-muted font-mono">{selectedCountry.iso3} · {selectedCountry.groups.join(", ").toUpperCase()}</span>
                      </div>
                    </div>
                    <Badge tone={selectedCountry.is_hotspot ? "negative" : "accent"}>
                      {selectedCountry.is_hotspot ? "ANOMALY ALERT" : "STABLE"}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-lg bg-card2 p-2.5">
                      <div className="text-[10px] uppercase font-bold text-muted">Media Coverage Tone</div>
                      <div className="text-lg font-bold tabular-nums" style={{ color: toneColor(selectedCountry.latest_tone) }}>
                        {fmtSigned(selectedCountry.latest_tone)}
                      </div>
                    </div>
                    <div className="rounded-lg bg-card2 p-2.5">
                      <div className="text-[10px] uppercase font-bold text-muted">Public Social Tone</div>
                      <div className="text-lg font-bold tabular-nums" style={{ color: toneColor(selectedCountry.public_sentiment) }}>
                        {fmtSigned(selectedCountry.public_sentiment)}
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg bg-card2 p-3 text-xs space-y-1">
                    <div className="text-[10px] uppercase font-bold text-muted">12-Week Sentiment Trend</div>
                    <div className="h-16 w-full">
                      <EChart option={sparkOption(selectedCountry.spark, toneColor(selectedCountry.latest_tone))} className="h-16 w-full" />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="text-xs font-bold text-muted uppercase tracking-wider">Key Monitored Leaders</div>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedCountry.leaders.map((leader, idx) => (
                        <span key={idx} className="rounded-md border border-border bg-card2 px-2 py-1 text-xs font-medium text-foreground">
                          {leader}
                        </span>
                      ))}
                    </div>
                  </div>

                  <Link
                    href={`/topic?q=${encodeURIComponent(selectedCountry.name)}`}
                    className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-xs font-semibold text-white shadow hover:bg-accent/90"
                  >
                    <span>Full Deep Dive Telemetry</span>
                    <ArrowRight size={13} />
                  </Link>
                </Card>
              ) : (
                <div className="flex h-48 items-center justify-center rounded-xl border border-dashed border-border text-center p-6 text-sm text-muted">
                  Select any country card on the left to inspect detailed geopolitical vectors.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: MARITIME CHOKEPOINTS */}
      {activeLayer === "chokepoints" && layersData && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {layersData.chokepoints.map((cp) => (
              <Card key={cp.id} className="p-5 space-y-3 border-border hover:border-accent/50 transition-all">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-base flex items-center gap-1.5">
                      <Anchor size={16} className="text-accent" /> {cp.name}
                    </h3>
                    <div className="text-xs text-muted mt-0.5">{cp.type.toUpperCase()} · Lat {cp.lat}, Lng {cp.lng}</div>
                  </div>
                  <Badge tone={cp.risk_tier === "Critical" ? "negative" : cp.risk_tier === "Elevated" ? "warning" : "positive"}>
                    {cp.risk_tier} Risk
                  </Badge>
                </div>

                <p className="text-xs text-muted leading-relaxed">{cp.summary}</p>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-border/50 text-xs">
                  <div>
                    <span className="text-[10px] text-muted uppercase">Daily Oil Flow</span>
                    <div className="font-bold font-mono">{cp.oil_transit_mbpd}M bpd</div>
                  </div>
                  <div>
                    <span className="text-[10px] text-muted uppercase">Global Share</span>
                    <div className="font-bold font-mono text-accent">{cp.share_of_global_oil_pct}% of world</div>
                  </div>
                </div>

                <div className="pt-2">
                  <span className="text-[10px] text-muted uppercase font-bold">Key Actors &amp; Littoral States:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {cp.primary_actors.map((actor, i) => (
                      <span key={i} className="rounded bg-card2 px-2 py-0.5 text-[11px] font-medium border border-border">
                        {actor}
                      </span>
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* VIEW 3: CONFLICT FLASHPOINTS */}
      {activeLayer === "conflicts" && layersData && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {layersData.conflict_flashpoints.map((fp) => (
              <Card key={fp.id} className="p-5 space-y-3 border-rose-500/20 bg-rose-500/[0.02]">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-bold text-base flex items-center gap-1.5 text-rose-400">
                      <ShieldAlert size={16} /> {fp.title}
                    </h3>
                    <div className="text-xs text-muted mt-0.5">{fp.category.toUpperCase()} · Intensity: {fp.intensity}</div>
                  </div>
                  <span className="animate-pulse rounded-full bg-rose-500/20 px-2 py-0.5 text-[10px] font-bold text-rose-500 border border-rose-500/30">
                    LIVE THEATER
                  </span>
                </div>
                <p className="text-xs text-muted leading-relaxed">{fp.summary}</p>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* VIEW 4: ELECTIONS COUNTDOWN */}
      {activeLayer === "elections" && layersData && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {layersData.elections.map((el, i) => (
              <Card key={i} className="p-5 space-y-3 border-border hover:border-accent/40 transition-all">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{el.flag}</span>
                    <div>
                      <h3 className="font-bold text-sm leading-tight">{el.country}</h3>
                      <div className="text-xs text-accent font-semibold">{el.event}</div>
                    </div>
                  </div>
                  <Badge tone="accent" className="font-mono text-[11px]">{el.date}</Badge>
                </div>
                <div className="text-xs text-muted bg-card2 p-2.5 rounded-lg border border-border/50">
                  <strong className="text-foreground">Strategic Stakes:</strong> {el.stakes}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function round(val: number, decimals: number = 2): number {
  return Number(Math.round(Number(val + "e" + decimals)) + "e-" + decimals);
}
