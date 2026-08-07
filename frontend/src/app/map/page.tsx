"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, WorldMapData, WorldCountrySentiment } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { EChart } from "@/components/echart";
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

export default function WorldMapPage() {
  const [activeLayer, setActiveLayer] = useState<"sentiment" | "chokepoints" | "conflicts" | "elections">("sentiment");
  const [region, setRegion] = useState("all");
  const [data, setData] = useState<WorldMapData | null>(null);
  const [layersData, setLayersData] = useState<MapLayersData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<WorldCountrySentiment | null>(null);

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
          <Globe size={14} /> World Sentiment Heatmap
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
          <ShieldAlert size={14} /> Active Conflict Theaters
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
          {layersData && <Badge tone="neutral" className="ml-1">{layersData.elections.length}</Badge>}
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
                            c.weekly_delta >= 0 ? "text-emerald-500" : "text-rose-500"
                          )}>
                            {c.weekly_delta >= 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                            {fmtSigned(c.weekly_delta)}
                          </div>
                        </div>
                      </div>

                      <div className="mt-3 flex items-center justify-between text-[11px] text-muted border-t border-border/50 pt-2">
                        <span>Articles: <strong>{c.article_volume.toLocaleString()}</strong></span>
                        <span>Divergence: <strong>{c.divergence > 0 ? `+${c.divergence}` : c.divergence}</strong></span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Country Detail Inspector Drawer */}
            <div className="space-y-4">
              {selectedCountry ? (
                <Card className="sticky top-6 p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <div className="flex items-center gap-2.5">
                      <span className="text-3xl">{selectedCountry.flag}</span>
                      <div>
                        <h2 className="text-base font-bold leading-tight">{selectedCountry.name}</h2>
                        <span className="text-xs text-muted font-mono">{selectedCountry.iso3} · {selectedCountry.region.toUpperCase()}</span>
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
                    <div className="text-xs font-bold text-muted uppercase tracking-wider">Top National Narratives</div>
                    <div className="space-y-1.5">
                      {selectedCountry.top_topics.map((t, idx) => (
                        <div key={idx} className="flex items-center justify-between rounded-lg border border-border/50 bg-card2/50 px-2.5 py-1.5 text-xs">
                          <span className="font-medium text-foreground truncate max-w-[150px]">{t.topic}</span>
                          <span className="font-mono font-bold" style={{ color: toneColor(t.tone) }}>
                            {fmtSigned(t.tone)}
                          </span>
                        </div>
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
                <div className="rounded-xl border border-dashed border-border p-8 text-center text-xs text-muted">
                  Select a country on the map to inspect telemetry
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* VIEW 2: STRATEGIC MARITIME CHOKEPOINTS */}
      {activeLayer === "chokepoints" && layersData && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {layersData.chokepoints.map((cp) => (
            <Card key={cp.id} className="p-5 space-y-3 border-l-4 border-l-amber-500">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <Anchor size={16} className="text-amber-400" />
                    <h3 className="text-base font-bold text-foreground">{cp.name}</h3>
                  </div>
                  <div className="text-[11px] text-muted font-mono mt-0.5">
                    Coords: {cp.lat}° N, {cp.lng}° E
                  </div>
                </div>
                <Badge tone={cp.risk_tier === "Critical" || cp.risk_tier === "Severe" ? "negative" : "warning"}>
                  {cp.risk_tier} Risk
                </Badge>
              </div>

              <p className="text-xs text-muted leading-relaxed">{cp.summary}</p>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-lg bg-card2 p-2">
                  <span className="text-[10px] text-muted uppercase font-bold block">Oil Transit</span>
                  <span className="font-mono font-bold text-foreground">{cp.oil_transit_mbpd}M bpd ({cp.share_of_global_oil_pct}% global)</span>
                </div>
                <div className="rounded-lg bg-card2 p-2">
                  <span className="text-[10px] text-muted uppercase font-bold block">Security Posture</span>
                  <span className="font-mono font-bold text-amber-400 truncate block">{cp.security_status}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-border/50 text-[11px] text-muted truncate">
                <strong>Littoral Actors:</strong> {cp.primary_actors.join(", ")}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* VIEW 3: ACTIVE CONFLICT FLASHPOINTS */}
      {activeLayer === "conflicts" && layersData && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {layersData.conflict_flashpoints.map((fp) => (
            <Card key={fp.id} className="p-5 space-y-3 border-l-4 border-l-rose-500">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <ShieldAlert size={16} className="text-rose-500" />
                    <h3 className="text-base font-bold text-foreground">{fp.title}</h3>
                  </div>
                  <div className="text-[11px] text-rose-400 font-medium mt-0.5">{fp.category}</div>
                </div>
                <Badge tone="negative">{fp.intensity}</Badge>
              </div>

              <p className="text-xs text-muted leading-relaxed">{fp.summary}</p>

              <div className="text-[11px] font-mono text-muted pt-2 border-t border-border/50">
                Theater Coords: {fp.lat}° N, {fp.lng}° E
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* VIEW 4: GLOBAL ELECTIONS COUNTDOWN */}
      {activeLayer === "elections" && layersData && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {layersData.elections.map((el, i) => (
            <Card key={i} className="p-5 space-y-3 border-l-4 border-l-indigo-500">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{el.flag}</span>
                  <div>
                    <h3 className="text-sm font-bold text-foreground">{el.country}</h3>
                    <span className="text-xs text-accent font-medium">{el.event}</span>
                  </div>
                </div>
                <Badge tone="accent">
                  <Vote size={11} className="mr-1" /> {el.date}
                </Badge>
              </div>

              <div className="rounded-lg bg-card2 p-3 text-xs space-y-1">
                <div className="text-[10px] uppercase font-bold text-muted tracking-wider">Strategic Stakes</div>
                <p className="text-muted leading-relaxed">{el.stakes}</p>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
