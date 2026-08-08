"use client";

import { useEffect, useState } from "react";
import { api, EconometricData, MultiTopicOverlayData } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { EChart, useChartTheme } from "@/components/echart";
import { fmtSigned } from "@/lib/format";
import {
  Activity,
  Sliders,
  AlertCircle,
  ShieldCheck,
  Zap,
  TrendingUp,
  Layers,
  CheckSquare,
  Square,
  Info,
} from "lucide-react";
import type { EChartsCoreOption } from "echarts";

const TOPIC_PRESETS = [
  { id: "inflation", label: "Inflation & Cost of Living" },
  { id: "donald_trump", label: "Donald Trump" },
  { id: "keir_starmer", label: "Keir Starmer" },
  { id: "olaf_scholz", label: "Olaf Scholz" },
  { id: "housing_crisis", label: "Housing & Rent Crisis" },
  { id: "defense_spending", label: "Defense & Military Spending" },
  { id: "ai_regulation", label: "AI & Tech Regulation" },
];

export default function TimeseriesPage() {
  const theme = useChartTheme();
  const [viewMode, setViewMode] = useState<"single" | "multi">("single");
  const [topic, setTopic] = useState("inflation");
  const [smoothness, setSmoothness] = useState(1600);
  const [showVolatilityBands, setShowVolatilityBands] = useState(true);
  const [selectedBreak, setSelectedBreak] = useState<any | null>(null);

  // Single Topic Data State
  const [data, setData] = useState<EconometricData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Multi-Topic Overlay State
  const [overlayTopics, setOverlayTopics] = useState<string[]>(["inflation", "defense_spending", "donald_trump"]);
  const [multiData, setMultiData] = useState<MultiTopicOverlayData | null>(null);
  const [multiLoading, setMultiLoading] = useState(false);

  // Fetch Single Topic Data
  useEffect(() => {
    if (viewMode === "single") {
      setLoading(true);
      setError(null);
      api<EconometricData>("/api/timeseries/analysis", { topic, smoothness })
        .then((res) => {
          setData(res);
          if (res.structural_breaks && res.structural_breaks.length > 0) {
            setSelectedBreak(res.structural_breaks[0]);
          } else {
            setSelectedBreak(null);
          }
        })
        .catch((err) => setError(err.message))
        .finally(() => setLoading(false));
    }
  }, [topic, smoothness, viewMode]);

  // Fetch Multi-Topic Data
  useEffect(() => {
    if (viewMode === "multi" && overlayTopics.length > 0) {
      setMultiLoading(true);
      api<MultiTopicOverlayData>("/api/timeseries/multi-overlay", {
        topics: overlayTopics.join(","),
        smoothness,
      })
        .then((res) => setMultiData(res))
        .catch((err) => setError(err.message))
        .finally(() => setMultiLoading(false));
    }
  }, [overlayTopics, smoothness, viewMode]);

  const toggleOverlayTopic = (tid: string) => {
    if (overlayTopics.includes(tid)) {
      if (overlayTopics.length > 1) {
        setOverlayTopics(overlayTopics.filter((t) => t !== tid));
      }
    } else {
      if (overlayTopics.length < 4) {
        setOverlayTopics([...overlayTopics, tid]);
      }
    }
  };

  // HP Filter Chart Option with Optional Volatility Confidence Bands
  const hpOption: EChartsCoreOption = data ? {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: theme.card,
      borderColor: theme.border,
      textStyle: { color: theme.fg, fontSize: 12 },
    },
    legend: {
      data: [
        "Raw Tone Series",
        "HP Secular Trend (g_t)",
        ...(showVolatilityBands ? ["Upper 95% Volatility Band", "Lower 95% Volatility Band"] : []),
        "Cyclical Component (c_t)",
      ],
      textStyle: { color: theme.muted },
      bottom: 0,
      icon: "roundRect",
    },
    grid: { left: 45, right: 45, top: 25, bottom: 40 },
    xAxis: {
      type: "category",
      data: data.dates,
      axisLine: { lineStyle: { color: theme.border } },
      axisLabel: { color: theme.muted, fontSize: 11 },
    },
    yAxis: [
      {
        type: "value",
        name: "Tone / Trend",
        nameTextStyle: { color: theme.accent, fontSize: 11 },
        splitLine: { lineStyle: { color: theme.grid, opacity: 0.35, type: "dashed" } },
        axisLabel: { color: theme.muted, fontSize: 11 },
      },
      {
        type: "value",
        name: "Cycle Deviation",
        nameTextStyle: { color: theme.accent2, fontSize: 11 },
        splitLine: { show: false },
        axisLabel: { color: theme.muted, fontSize: 11 },
      },
    ],
    series: [
      {
        name: "Raw Tone Series",
        type: "line",
        yAxisIndex: 0,
        data: data.raw_tone,
        lineStyle: { color: "rgba(148, 163, 184, 0.45)", width: 1.5 },
        symbol: "none",
      },
      {
        name: "HP Secular Trend (g_t)",
        type: "line",
        yAxisIndex: 0,
        data: data.hp_decomposition.trend,
        lineStyle: { color: theme.accent, width: 3 },
        itemStyle: { color: theme.accent },
        symbol: "none",
      },
      ...(showVolatilityBands && data.volatility_bands ? [
        {
          name: "Upper 95% Volatility Band",
          type: "line",
          yAxisIndex: 0,
          data: data.volatility_bands.upper,
          lineStyle: { color: "rgba(56, 189, 248, 0.25)", width: 1, type: "dashed" as const },
          symbol: "none",
        },
        {
          name: "Lower 95% Volatility Band",
          type: "line",
          yAxisIndex: 0,
          data: data.volatility_bands.lower,
          lineStyle: { color: "rgba(56, 189, 248, 0.25)", width: 1, type: "dashed" as const },
          symbol: "none",
        },
      ] : []),
      {
        name: "Cyclical Component (c_t)",
        type: "bar",
        yAxisIndex: 1,
        data: data.hp_decomposition.cycle,
        itemStyle: {
          color: (params: any) => (params.value >= 0 ? "rgba(52, 211, 153, 0.5)" : "rgba(248, 113, 113, 0.5)"),
        },
      },
    ],
  } : {};

  // Volatility Regime Chart
  const volOption: EChartsCoreOption = data ? {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: theme.card,
      borderColor: theme.border,
      textStyle: { color: theme.fg, fontSize: 12 },
    },
    grid: { left: 45, right: 25, top: 15, bottom: 25 },
    xAxis: {
      type: "category",
      data: data.dates,
      axisLine: { lineStyle: { color: theme.border } },
      axisLabel: { color: theme.muted, fontSize: 10 },
    },
    yAxis: {
      type: "value",
      name: "Std Dev (Tone)",
      splitLine: { lineStyle: { color: theme.grid, opacity: 0.35, type: "dashed" } },
      axisLabel: { color: theme.muted, fontSize: 10 },
    },
    series: [
      {
        type: "line",
        data: data.volatility.series,
        smooth: true,
        lineStyle: { color: "#f59e0b", width: 2.5 },
        areaStyle: {
          color: "#f59e0b",
          opacity: 0.12,
        },
        symbol: "none",
      },
    ],
  } : {};

  // Multi-Topic Trend Overlay Option
  const multiTrendOption: EChartsCoreOption = multiData ? {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: theme.card,
      borderColor: theme.border,
      textStyle: { color: theme.fg, fontSize: 12 },
    },
    legend: {
      data: multiData.series.map((s) => s.label),
      textStyle: { color: theme.muted },
      top: 0,
    },
    grid: { left: 45, right: 25, top: 35, bottom: 30 },
    xAxis: {
      type: "category",
      data: multiData.dates,
      axisLine: { lineStyle: { color: theme.border } },
      axisLabel: { color: theme.muted, fontSize: 10 },
    },
    yAxis: {
      type: "value",
      name: "Secular Trend",
      splitLine: { lineStyle: { color: theme.grid, opacity: 0.35, type: "dashed" } },
      axisLabel: { color: theme.muted, fontSize: 10 },
    },
    series: multiData.series.map((s) => ({
      name: s.label,
      type: "line",
      data: s.trend,
      smooth: true,
      lineStyle: { width: 3, color: s.color },
      itemStyle: { color: s.color },
      symbol: "none",
    })),
  } : {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-accent" />
            <h1 className="text-2xl font-bold tracking-tight">Applied Econometric Time-Series Studio</h1>
          </div>
          <p className="text-sm text-muted">
            Decompose media tone trajectories into secular trends, cyclical oscillations, structural regime breaks, and multi-topic overlays.
          </p>
        </div>

        {/* View Mode Switcher */}
        <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
          <button
            onClick={() => setViewMode("single")}
            className={cx(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all",
              viewMode === "single" ? "bg-accent text-white shadow-sm" : "text-muted hover:text-foreground"
            )}
          >
            <Activity size={13} /> Single Topic Suite
          </button>
          <button
            onClick={() => setViewMode("multi")}
            className={cx(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all",
              viewMode === "multi" ? "bg-accent text-white shadow-sm" : "text-muted hover:text-foreground"
            )}
          >
            <Layers size={13} /> Multi-Topic Overlay
          </button>
        </div>
      </div>

      {/* SINGLE TOPIC VIEW */}
      {viewMode === "single" && (
        <div className="space-y-6">
          {/* Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-card p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-semibold uppercase text-muted">Topic:</span>
              {TOPIC_PRESETS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setTopic(p.id)}
                  className={cx(
                    "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                    topic === p.id
                      ? "bg-accent text-white"
                      : "bg-card2 text-muted hover:bg-card hover:text-foreground border border-border"
                  )}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-xs text-muted cursor-pointer">
                <input
                  type="checkbox"
                  checked={showVolatilityBands}
                  onChange={(e) => setShowVolatilityBands(e.target.checked)}
                  className="rounded border-border text-accent focus:ring-accent"
                />
                <span>95% Volatility Bands</span>
              </label>

              <div className="flex items-center gap-2 border-l border-border pl-4">
                <Sliders size={14} className="text-muted" />
                <span className="text-xs text-muted font-medium">HP Lambda ($\lambda$):</span>
                <select
                  value={smoothness}
                  onChange={(e) => setSmoothness(Number(e.target.value))}
                  className="rounded-md border border-border bg-card2 px-2 py-1 text-xs font-mono text-foreground"
                >
                  <option value={100}>100 (High Frequency)</option>
                  <option value={1600}>1,600 (Quarterly Standard)</option>
                  <option value={14400}>14,400 (Low Frequency / Macro)</option>
                </select>
              </div>
            </div>
          </div>

          {loading && (
            <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card">
              <div className="text-sm text-muted animate-pulse">Running econometric filters and stationarity diagnostics...</div>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
              Econometric engine error: {error}
            </div>
          )}

          {data && !loading && (
            <>
              {/* Diagnostic Status Cards */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Card className="p-4 space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted">
                    <span>HP Cyclical Variance</span>
                    <Badge tone="accent">{data.hp_decomposition.smoothness_lambda} $\lambda$</Badge>
                  </div>
                  <div className="text-2xl font-bold font-mono">
                    {data.hp_decomposition.cyclical_variance_pct}%
                  </div>
                  <div className="text-[11px] text-muted">Share of variance driven by transient news cycles.</div>
                </Card>

                <Card className="p-4 space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted">
                    <span>ADF Stationarity</span>
                    <Badge tone={data.stationarity.is_stationary ? "positive" : "warning"}>
                      {data.stationarity.is_stationary ? "Stationary (I(0))" : "Unit Root (I(1))"}
                    </Badge>
                  </div>
                  <div className="text-2xl font-bold font-mono">
                    p = {data.stationarity.p_value}
                  </div>
                  <div className="text-[11px] text-muted truncate">{data.stationarity.interpretation}</div>
                </Card>

                <Card className="p-4 space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted">
                    <span>Volatility Regime</span>
                    <Badge tone="warning">4W Rolling</Badge>
                  </div>
                  <div className="text-2xl font-bold font-mono">
                    {data.volatility.current_volatility}
                  </div>
                  <div className="text-[11px] text-muted">{data.volatility.regime}</div>
                </Card>

                <Card className="p-4 space-y-1">
                  <div className="flex items-center justify-between text-xs text-muted">
                    <span>Detected Structural Breaks</span>
                    <Badge tone="accent">Chow / CUSUM</Badge>
                  </div>
                  <div className="text-2xl font-bold font-mono">
                    {data.structural_breaks.length} Regimes
                  </div>
                  <div className="text-[11px] text-muted">Statistically significant permanent trajectory ruptures.</div>
                </Card>
              </div>

              {/* Main HP Filter Decomposition Chart */}
              <Card className="p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h2 className="text-base font-bold">Hodrick-Prescott Trend vs. Cyclical Decomposition</h2>
                    <p className="text-xs text-muted">Separates the underlying secular trend line from weekly transient media noise.</p>
                  </div>
                  <Badge tone="accent" className="font-mono text-xs">
                    {data.topic.label}
                  </Badge>
                </div>
                <div className="h-80 w-full">
                  <EChart option={hpOption} className="h-80 w-full" />
                </div>
              </Card>

              {/* Volatility & Structural Breaks Grid */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                {/* Volatility Clustering */}
                <Card className="p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <div>
                      <h3 className="font-bold text-sm">Rolling Conditional Volatility</h3>
                      <p className="text-xs text-muted">Tracks clustering periods of intense narrative turbulence.</p>
                    </div>
                  </div>
                  <div className="h-56 w-full">
                    <EChart option={volOption} className="h-56 w-full" />
                  </div>
                </Card>

                {/* Structural Breaks Inspector */}
                <Card className="p-5 space-y-3">
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <div>
                      <h3 className="font-bold text-sm">Regime Shift &amp; Structural Break Inspector</h3>
                      <p className="text-xs text-muted">Permanent pivot dates identified by statistical change-point tests.</p>
                    </div>
                  </div>

                  {data.structural_breaks.length === 0 ? (
                    <div className="flex h-48 items-center justify-center text-xs text-muted">
                      No structural breaks detected. Narrative trend has remained stationary.
                    </div>
                  ) : (
                    <div className="space-y-2.5 max-h-56 overflow-y-auto pr-1">
                      {data.structural_breaks.map((b, idx) => {
                        const isSelected = selectedBreak?.date === b.date;
                        return (
                          <div
                            key={idx}
                            onClick={() => setSelectedBreak(b)}
                            className={cx(
                              "cursor-pointer rounded-lg border p-3 text-xs transition-all",
                              isSelected
                                ? "border-accent bg-accent/10 shadow-sm"
                                : "border-border bg-card2 hover:border-accent/40"
                            )}
                          >
                            <div className="flex items-center justify-between font-semibold">
                              <span className="text-foreground">{b.date}</span>
                              <span className={b.magnitude >= 0 ? "text-emerald-400" : "text-rose-400"}>
                                {b.type} ({fmtSigned(b.magnitude)} pts)
                              </span>
                            </div>
                            <div className="mt-1 text-muted text-[11px]">
                              Pre-break Mean: {b.pre_mean} → Post-break Mean: {b.post_mean} (t = {b.t_statistic})
                            </div>
                            {b.catalyst_note && (
                              <div className="mt-1.5 text-[11px] text-accent/90 italic">
                                💡 {b.catalyst_note}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </Card>
              </div>
            </>
          )}
        </div>
      )}

      {/* MULTI-TOPIC OVERLAY VIEW */}
      {viewMode === "multi" && (
        <div className="space-y-6">
          {/* Multi-Topic Selector Checklist */}
          <Card className="p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-muted">
                Select Topics to Overlay (Max 4):
              </span>
              <span className="text-xs text-accent font-mono">
                {overlayTopics.length}/4 Selected
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {TOPIC_PRESETS.map((p) => {
                const isSelected = overlayTopics.includes(p.id);
                return (
                  <button
                    key={p.id}
                    onClick={() => toggleOverlayTopic(p.id)}
                    className={cx(
                      "flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-all",
                      isSelected
                        ? "border-accent bg-accent text-white shadow-sm"
                        : "border-border bg-card2 text-muted hover:text-foreground"
                    )}
                  >
                    {isSelected ? <CheckSquare size={13} /> : <Square size={13} />}
                    {p.label}
                  </button>
                );
              })}
            </div>
          </Card>

          {multiLoading && (
            <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card">
              <div className="text-sm text-muted animate-pulse">Aligning econometric series and computing cross-correlations...</div>
            </div>
          )}

          {multiData && !multiLoading && (
            <>
              {/* Correlation Summary Cards */}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {multiData.series.map((s, idx) => (
                  <Card key={s.id} className="p-4 space-y-2 border-border">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="h-3 w-3 rounded-full" style={{ backgroundColor: s.color }} />
                        <span className="font-bold text-sm truncate">{s.label}</span>
                      </div>
                      <Badge tone="accent">{s.category}</Badge>
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1 border-t border-border/50">
                      <span className="text-muted">Corr. with {multiData.series[0].label}:</span>
                      <span className="font-bold font-mono">
                        {fmtSigned(s.correlation_with_primary)}
                      </span>
                    </div>
                  </Card>
                ))}
              </div>

              {/* Overlaid Secular Trends */}
              <Card className="p-5 space-y-3">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h2 className="text-base font-bold">Comparative Secular Trajectory Overlay</h2>
                    <p className="text-xs text-muted">Overlays long-term filtered trendlines across multiple macro narratives.</p>
                  </div>
                </div>
                <div className="h-80 w-full">
                  <EChart option={multiTrendOption} className="h-80 w-full" />
                </div>
              </Card>
            </>
          )}
        </div>
      )}
    </div>
  );
}
