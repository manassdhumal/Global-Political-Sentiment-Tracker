"use client";

import { useEffect, useState } from "react";
import { api, PolarizationData } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { EChart, useChartTheme } from "@/components/echart";
import { fmtSigned, toneColor } from "@/lib/format";
import { Newspaper, Scale, Flame, ArrowRight, ShieldCheck, Layers } from "lucide-react";
import type { EChartsCoreOption } from "echarts";

const TOPIC_PRESETS = [
  { id: "inflation", label: "Inflation & Cost of Living" },
  { id: "donald_trump", label: "Donald Trump" },
  { id: "immigration", label: "Immigration & Border Security" },
  { id: "ukraine_war", label: "War in Ukraine & NATO" },
  { id: "climate_policy", label: "Climate & Energy Transition" },
  { id: "ai_regulation", label: "AI Regulation & Safety" },
];

export default function PolarizationPage() {
  const theme = useChartTheme();
  const [topic, setTopic] = useState("inflation");
  const [data, setData] = useState<PolarizationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api<PolarizationData>("/api/polarization/analysis", { topic })
      .then((res) => setData(res))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [topic]);

  // Polarization Spread Timeline Chart (Left vs. Right divergence)
  const spreadOption: EChartsCoreOption = data ? {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: theme.card,
      borderColor: theme.border,
      textStyle: { color: theme.fg, fontSize: 12 },
    },
    legend: {
      data: ["Center-Left Tone", "Center-Right Tone", "Polarization Spread Gap (Δ)"],
      textStyle: { color: theme.muted },
      bottom: 0,
      icon: "roundRect",
    },
    grid: { left: 45, right: 45, top: 25, bottom: 40 },
    xAxis: {
      type: "category",
      data: data.timeline.map((t) => t.date),
      axisLine: { lineStyle: { color: theme.border } },
      axisLabel: { color: theme.muted, fontSize: 11 },
    },
    yAxis: [
      {
        type: "value",
        name: "Tone Score",
        nameTextStyle: { color: theme.accent, fontSize: 11 },
        splitLine: { lineStyle: { color: theme.grid, opacity: 0.35, type: "dashed" } },
        axisLabel: { color: theme.muted, fontSize: 11 },
      },
      {
        type: "value",
        name: "Spread Gap",
        nameTextStyle: { color: theme.negative, fontSize: 11 },
        splitLine: { show: false },
        axisLabel: { color: theme.negative, fontSize: 11 },
      },
    ],
    series: [
      {
        name: "Center-Left Tone",
        type: "line",
        yAxisIndex: 0,
        data: data.timeline.map((t) => t.left_tone),
        lineStyle: { color: "#3b82f6", width: 2.5 },
        itemStyle: { color: "#3b82f6" },
        symbol: "none",
      },
      {
        name: "Center-Right Tone",
        type: "line",
        yAxisIndex: 0,
        data: data.timeline.map((t) => t.right_tone),
        lineStyle: { color: "#ef4444", width: 2.5 },
        itemStyle: { color: "#ef4444" },
        symbol: "none",
      },
      {
        name: "Polarization Spread Gap (Δ)",
        type: "bar",
        yAxisIndex: 1,
        data: data.timeline.map((t) => t.spread),
        itemStyle: { color: "rgba(239, 68, 68, 0.35)" },
      },
    ],
  } : {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">📰</span>
            <h1 className="text-2xl font-bold tracking-tight">Media Polarization &amp; Framing Spectrum Matrix</h1>
          </div>
          <p className="text-sm text-muted">
            Dissect editorial slant, partisan echo chambers, and framing divergence between Center-Left, Center-Right, Wire Services, and State-Affiliated outlets.
          </p>
        </div>
      </div>

      {/* Topic Filter Bar */}
      <Card className="p-4 bg-card border-border/80 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Newspaper size={16} className="text-accent shrink-0" />
          <span className="text-xs text-muted font-medium">Topic:</span>
          <select
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="rounded-lg border border-border bg-card2 px-3 py-1.5 text-xs font-medium focus:border-accent focus:outline-none"
          >
            {TOPIC_PRESETS.map((t) => (
              <option key={t.id} value={t.id}>{t.label}</option>
            ))}
          </select>
        </div>

        {data && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">Polarization Level:</span>
            <Badge tone={data.summary.tier_code === "consensus" ? "positive" : data.summary.tier_code === "severe" ? "negative" : "warning"}>
              {data.summary.polarization_tier}
            </Badge>
          </div>
        )}
      </Card>

      {loading && (
        <div className="flex h-72 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Deconstructing editorial spectra &amp; keyword divergence...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Failed to load media polarization: {error}
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6">
          {/* 4 Ideological Spectrum Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {data.spectra.map((s) => (
              <Card key={s.id} className="p-4 space-y-3 bg-card border-border hover:border-accent/40 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: s.color }} />
                    <span className="font-semibold text-xs text-foreground">{s.name}</span>
                  </div>
                  <span className="font-mono font-bold text-sm" style={{ color: toneColor(s.latest_tone) }}>
                    {fmtSigned(s.latest_tone)}
                  </span>
                </div>

                <div className="space-y-1">
                  <div className="text-[11px] text-muted font-medium">Monitored Outlets:</div>
                  <div className="text-[11px] text-foreground truncate">{s.outlets.slice(0, 3).join(", ")}...</div>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-border/50">
                  <div className="text-[10px] uppercase font-semibold text-muted tracking-wider">Distinctive Framing Keywords:</div>
                  <div className="flex flex-wrap gap-1">
                    {s.keywords.slice(0, 4).map((kw, i) => (
                      <span key={i} className="rounded bg-card2 px-1.5 py-0.5 text-[10px] text-muted border border-border/40">
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {/* Polarization Spread Timeline Chart */}
          <Card className="p-5">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h3 className="font-semibold text-sm">Partisan Framing Divergence Timeline (Left vs. Right)</h3>
                <div className="text-xs text-muted">Tracking ideological distance (Δ) and narrative divergence over time</div>
              </div>
              <div className="text-xs font-mono font-bold text-rose-400">
                Current Gap: {data.summary.latest_polarization_spread} pts
              </div>
            </div>
            <div className="h-80 w-full">
              <EChart height={300} option={spreadOption} />
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
