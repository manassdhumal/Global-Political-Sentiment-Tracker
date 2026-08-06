"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, WorldMapData, WorldCountrySentiment } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { EChart } from "@/components/echart";
import { toneColor, fmtSigned } from "@/lib/format";
import { Globe, Flame, TrendingUp, TrendingDown, ArrowRight, Filter } from "lucide-react";
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

export default function WorldMapPage() {
  const [region, setRegion] = useState("all");
  const [data, setData] = useState<WorldMapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<WorldCountrySentiment | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api<WorldMapData>("/api/geography/world-map", { region })
      .then((res) => {
        setData(res);
        if (res.countries.length > 0) {
          setSelectedCountry(res.countries[0]);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [region]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌍</span>
            <h1 className="text-2xl font-bold tracking-tight">World Sentiment Map &amp; Hotspots</h1>
          </div>
          <p className="text-sm text-muted">
            Real-time geopolitical tone, domestic public sentiment divergence, and statistical anomaly hotspots across world nations.
          </p>
        </div>
      </div>

      {/* Summary KPI Strip */}
      {data && (
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

      {loading && (
        <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Aggregating global geopolitical signals...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Failed to load geographical map data: {error}
        </div>
      )}

      {/* Main Grid: Country Cards & Selected Inspector Drawer */}
      {data && !loading && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Countries Grid (2 Cols on lg) */}
          <div className="lg:col-span-2 space-y-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {data.countries.map((c) => {
                const isSelected = selectedCountry?.iso3 === c.iso3;
                const color = toneColor(c.latest_tone);
                return (
                  <div
                    key={c.iso3}
                    onClick={() => setSelectedCountry(c)}
                    className={cx(
                      "cursor-pointer rounded-xl border p-4 transition-all duration-200 hover:border-accent/50",
                      isSelected
                        ? "border-accent bg-accent/5 shadow-md shadow-accent/5 ring-1 ring-accent/30"
                        : "border-border bg-card hover:bg-card2",
                      c.is_hotspot && !isSelected && "border-rose-500/40 bg-rose-500/[0.03]"
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
                          {fmtSigned(c.latest_tone)}
                        </div>
                        <div className={cx(
                          "text-[10px] tabular-nums font-medium flex items-center justify-end gap-0.5",
                          c.movement >= 0 ? "text-emerald-500" : "text-rose-400"
                        )}>
                          {c.movement >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                          {fmtSigned(c.movement)} WoW
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 flex items-center justify-between pt-2 border-t border-border/50">
                      <div className="text-[11px] text-muted">
                        Public Gap: <span className="font-mono text-foreground font-medium">{fmtSigned(c.gap)}</span>
                      </div>
                      <div className="w-24 h-8">
                        <EChart height={32} option={sparkOption(c.spark, color)} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Selected Country Detailed Inspector */}
          <div className="lg:col-span-1">
            {selectedCountry ? (
              <Card className="sticky top-6 p-5 space-y-4 border-border/80 bg-card">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="text-3xl">{selectedCountry.flag}</span>
                    <div>
                      <h3 className="font-bold text-lg leading-tight">{selectedCountry.name}</h3>
                      <span className="text-xs text-muted font-mono">{selectedCountry.iso3} · GDELT {selectedCountry.gdelt}</span>
                    </div>
                  </div>
                  {selectedCountry.is_hotspot && (
                    <Badge tone="negative">
                      <Flame size={12} className="mr-1 inline" /> HOTSPOT
                    </Badge>
                  )}
                </div>

                {/* Score Breakdown */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="rounded-lg bg-card2 p-3 border border-border/50">
                    <div className="text-[11px] text-muted">Press Tone</div>
                    <div className="text-xl font-bold tabular-nums" style={{ color: toneColor(selectedCountry.latest_tone) }}>
                      {fmtSigned(selectedCountry.latest_tone)}
                    </div>
                  </div>
                  <div className="rounded-lg bg-card2 p-3 border border-border/50">
                    <div className="text-[11px] text-muted">Public Sentiment</div>
                    <div className="text-xl font-bold tabular-nums" style={{ color: toneColor(selectedCountry.public_sentiment) }}>
                      {fmtSigned(selectedCountry.public_sentiment)}
                    </div>
                  </div>
                </div>

                {/* Historical 12-week Trend */}
                <div className="space-y-1.5">
                  <div className="text-xs font-medium text-muted">12-Week Tone Velocity</div>
                  <div className="h-14 w-full rounded-lg bg-card2/60 p-2 border border-border/40">
                    <EChart height={45} option={sparkOption(selectedCountry.spark, toneColor(selectedCountry.latest_tone))} />
                  </div>
                </div>

                {/* Key Political Figures & Tracked Topics */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted/80">Tracked Entities &amp; Figures</div>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedCountry.leaders.map((ldr) => (
                      <Link
                        key={ldr}
                        href={`/topic?q=${encodeURIComponent(ldr)}`}
                        className="flex items-center gap-1 rounded-md bg-card2 hover:bg-accent/15 hover:text-accent border border-border px-2.5 py-1 text-xs transition-colors"
                      >
                        {ldr} <ArrowRight size={11} />
                      </Link>
                    ))}
                  </div>
                </div>

                {/* Regional Group Memberships */}
                <div className="space-y-1.5 pt-2 border-t border-border text-xs text-muted">
                  <div>Regional Blocs: <span className="text-foreground uppercase">{selectedCountry.groups.join(", ")}</span></div>
                  <div>Coverage Volume: <span className="text-foreground font-mono">{selectedCountry.volume.toLocaleString()} articles</span></div>
                </div>
              </Card>
            ) : (
              <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-border p-4 text-center text-sm text-muted">
                Select a country to inspect intelligence breakdown.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
