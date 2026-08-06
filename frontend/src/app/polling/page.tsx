"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { api, PollingComparisonData } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { Vote, Scale, TrendingUp, TrendingDown, Info, ShieldCheck, Newspaper } from "lucide-react";

export default function PollingPage() {
  const [entities, setEntities] = useState<any[]>([]);
  const [selectedEntity, setSelectedEntity] = useState("donald_trump");
  const [weeks, setWeeks] = useState(26);
  const [data, setData] = useState<PollingComparisonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch supported political figures
  useEffect(() => {
    api<any[]>("/api/polling/entities")
      .then((res) => setEntities(res))
      .catch((err) => console.error(err));
  }, []);

  // Fetch polling vs sentiment comparison
  useEffect(() => {
    setLoading(true);
    setError(null);
    api<PollingComparisonData>("/api/polling/comparison", { entity: selectedEntity, weeks })
      .then((res) => setData(res))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [selectedEntity, weeks]);

  // ECharts Multi-Axis Synchronized Chart
  const chartOption = data ? {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(20, 24, 33, 0.95)",
      borderColor: "#334155",
      textStyle: { color: "#f1f5f9", fontSize: 12 },
    },
    legend: {
      data: ["Voter Approval (%)", "Press Media Tone", "Media Framing Gap"],
      textStyle: { color: "#94a3b8" },
      bottom: 0,
    },
    grid: { left: 45, right: 45, top: 25, bottom: 40 },
    xAxis: {
      type: "category",
      data: data.series.map((s) => s.date),
      axisLine: { lineStyle: { color: "#334155" } },
      axisLabel: { color: "#94a3b8", fontSize: 11 },
    },
    yAxis: [
      {
        type: "value",
        name: "Approval %",
        min: 0,
        max: 100,
        nameTextStyle: { color: "#38bdf8", fontSize: 11 },
        splitLine: { lineStyle: { color: "#1e293b", type: "dashed" } },
        axisLabel: { color: "#38bdf8", fontSize: 11 },
      },
      {
        type: "value",
        name: "Tone Score",
        min: -10,
        max: 10,
        nameTextStyle: { color: "#a855f7", fontSize: 11 },
        splitLine: { show: false },
        axisLabel: { color: "#a855f7", fontSize: 11 },
      },
    ],
    series: [
      {
        name: "Voter Approval (%)",
        type: "line",
        yAxisIndex: 0,
        data: data.series.map((s) => s.approval_pct),
        lineStyle: { color: "#38bdf8", width: 3 },
        itemStyle: { color: "#38bdf8" },
        symbol: "circle",
        symbolSize: 6,
      },
      {
        name: "Press Media Tone",
        type: "line",
        yAxisIndex: 1,
        data: data.series.map((s) => s.media_tone),
        lineStyle: { color: "#a855f7", width: 2.5 },
        itemStyle: { color: "#a855f7" },
        symbol: "diamond",
        symbolSize: 6,
      },
      {
        name: "Media Framing Gap",
        type: "bar",
        yAxisIndex: 1,
        data: data.series.map((s) => s.bias_gap),
        itemStyle: {
          color: (params: any) => (params.value >= 0 ? "rgba(16, 185, 129, 0.45)" : "rgba(239, 68, 68, 0.45)"),
        },
      },
    ],
  } : {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">📊</span>
            <h1 className="text-2xl font-bold tracking-tight">Real-Life Polling vs. Media Tone</h1>
          </div>
          <p className="text-sm text-muted">
            Benchmark actual voter approval polling percentages against journalistic press coverage tone to uncover Media Framing Bias.
          </p>
        </div>
      </div>

      {/* Control Selector Bar */}
      <Card className="p-4 bg-card border-border/80 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        {/* Figure Selector */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          <Vote size={16} className="text-accent shrink-0 ml-1" />
          {entities.map((e) => (
            <button
              key={e.id}
              onClick={() => setSelectedEntity(e.id)}
              className={cx(
                "rounded-full px-3.5 py-1.5 text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1.5",
                selectedEntity === e.id
                  ? "bg-accent text-accent-foreground shadow-sm shadow-accent/20"
                  : "bg-card2 hover:bg-card border border-border text-muted hover:text-foreground"
              )}
            >
              <span>{e.flag}</span>
              <span>{e.label}</span>
            </button>
          ))}
        </div>

        {/* Horizon Tabs */}
        <div className="flex items-center gap-1.5 shrink-0">
          {[
            { w: 12, label: "3M" },
            { w: 26, label: "6M" },
            { w: 52, label: "1Y" },
          ].map((h) => (
            <button
              key={h.w}
              onClick={() => setWeeks(h.w)}
              className={cx(
                "rounded-lg px-2.5 py-1 text-xs font-medium transition-colors",
                weeks === h.w ? "bg-accent/20 text-accent font-bold" : "text-muted hover:text-foreground"
              )}
            >
              {h.label}
            </button>
          ))}
        </div>
      </Card>

      {loading && (
        <div className="flex h-72 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Synchronizing voter polling feeds with media tone...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Failed to load polling comparison: {error}
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6">
          {/* Key Metric Tiles */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card className="p-4">
              <div className="text-xs text-muted">Latest Voter Approval</div>
              <div className="mt-1 text-2xl font-bold font-mono text-sky-400">
                {data.latest.approval_pct}%
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Press Coverage Tone</div>
              <div className={cx(
                "mt-1 text-2xl font-bold font-mono",
                data.latest.media_tone >= 0 ? "text-emerald-400" : "text-rose-400"
              )}>
                {data.latest.media_tone > 0 ? `+${data.latest.media_tone}` : data.latest.media_tone}
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Media Bias Index</div>
              <div className={cx(
                "mt-1 text-2xl font-bold font-mono",
                data.latest.media_bias_index >= 0 ? "text-emerald-400" : "text-rose-400"
              )}>
                {data.latest.media_bias_index > 0 ? `+${data.latest.media_bias_index}` : data.latest.media_bias_index} pts
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Polling-Tone Correlation</div>
              <div className="mt-1 text-2xl font-bold font-mono text-purple-400">
                r = {data.latest.correlation_r > 0 ? `+${data.latest.correlation_r}` : data.latest.correlation_r}
              </div>
            </Card>
          </div>

          {/* Dual Axis Chart & Bias Analysis */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2 p-5">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-sm">Voter Approval Rating vs. Press Tone Trajectory</h3>
                  <div className="text-xs text-muted">{data.entity.title} ({data.entity.country})</div>
                </div>
                <Badge tone={data.latest.verdict_code === "balanced_framing" ? "success" : "warning"}>
                  {data.latest.verdict_code === "balanced_framing" ? "Balanced Tracking" : "Framing Divergence"}
                </Badge>
              </div>
              <div className="h-80 w-full">
                <ReactECharts option={chartOption} style={{ height: "100%", width: "100%" }} />
              </div>
            </Card>

            {/* Framing Verdict & Methodology Breakdown */}
            <Card className="p-5 space-y-4 bg-card flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted/80">
                  <Scale size={14} className="text-accent" /> Framing Bias Assessment
                </div>
                <div className="rounded-lg bg-card2 p-3.5 border border-border/60">
                  <div className="text-xs font-bold text-foreground leading-snug">
                    {data.latest.verdict}
                  </div>
                  <p className="text-[11px] text-muted mt-2 leading-relaxed">
                    A Media Bias Gap of <span className="font-mono font-semibold text-foreground">{data.latest.media_bias_index > 0 ? `+${data.latest.media_bias_index}` : data.latest.media_bias_index}</span> indicates the degree to which mainstream media framing diverges from ballot-box voter sentiment.
                  </p>
                </div>

                {/* Pollster Transparency */}
                <div className="space-y-1.5">
                  <div className="text-xs font-medium text-muted">Aggregated Pollsters:</div>
                  <div className="flex flex-wrap gap-1">
                    {data.entity.pollsters.map((p, i) => (
                      <span key={i} className="rounded bg-card2 px-2 py-0.5 text-[10px] font-mono text-muted border border-border/50">
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-accent/20 bg-accent/5 p-3 text-[11px] text-muted">
                🛡️ <strong>Methodology Note:</strong> Polling data tracks representative voter sample surveys normalized on a -10 to +10 net score and cross-correlated against GDELT tone timelines.
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
