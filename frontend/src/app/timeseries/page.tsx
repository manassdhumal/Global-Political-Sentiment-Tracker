"use client";

import { useEffect, useState } from "react";
import { api, EconometricData } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { EChart, useChartTheme } from "@/components/echart";
import { fmtSigned } from "@/lib/format";
import { Activity, Sliders, AlertCircle, ShieldCheck, Zap, TrendingUp } from "lucide-react";
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
  const [topic, setTopic] = useState("inflation");
  const [smoothness, setSmoothness] = useState(1600);
  const [data, setData] = useState<EconometricData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api<EconometricData>("/api/timeseries/analysis", { topic, smoothness })
      .then((res) => setData(res))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [topic, smoothness]);

  // HP Filter Chart: Raw vs Secular Trend vs Business Cycle
  const hpOption: EChartsCoreOption = data ? {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: theme.card,
      borderColor: theme.border,
      textStyle: { color: theme.fg, fontSize: 12 },
    },
    legend: {
      data: ["Raw Tone Series", "HP Secular Trend (g_t)", "Cyclical Component (c_t)"],
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
      name: "Rolling Std Dev",
      nameTextStyle: { color: theme.muted, fontSize: 10 },
      splitLine: { lineStyle: { color: theme.grid, opacity: 0.35, type: "dashed" } },
      axisLabel: { color: theme.muted, fontSize: 10 },
    },
    series: [
      {
        name: "Conditional Volatility",
        type: "line",
        data: data.volatility.series,
        lineStyle: { color: theme.negative, width: 2 },
        areaStyle: { color: theme.negative, opacity: 0.15 },
        symbol: "none",
      },
    ],
  } : {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">📉</span>
            <h1 className="text-2xl font-bold tracking-tight">Applied Econometric Time-Series Suite</h1>
          </div>
          <p className="text-sm text-muted">
            Hodrick-Prescott trend/cycle decomposition, Augmented Dickey-Fuller stationarity tests, CUSUM structural break detection, and volatility clustering.
          </p>
        </div>

        {data && (
          <a
            href={`/api/export/csv/timeseries?topic=${topic}`}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card2 px-3.5 py-1.5 text-xs font-semibold text-foreground shadow-sm hover:border-accent hover:text-accent transition-colors"
          >
            <Activity size={14} className="text-accent" /> Download Quant CSV
          </a>
        )}
      </div>

      {/* Control Bar */}
      <Card className="p-4 bg-card border-border/80 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-accent shrink-0" />
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

        <div className="flex items-center gap-3">
          <span className="text-xs text-muted font-medium">HP Smoothing (λ = {smoothness}):</span>
          <div className="flex items-center gap-1.5">
            {[
              { label: "Monthly (128)", val: 128 },
              { label: "Quarterly (1600)", val: 1600 },
              { label: "Weekly (270k)", val: 270400 },
            ].map((preset) => (
              <button
                key={preset.val}
                onClick={() => setSmoothness(preset.val)}
                className={cx(
                  "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                  smoothness === preset.val ? "bg-accent text-white" : "bg-card2 hover:bg-card border border-border text-muted"
                )}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {loading && (
        <div className="flex h-72 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Running econometric time-series decomposition...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Failed to load time-series analysis: {error}
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6">
          {/* Econometric Diagnostic KPI Tiles */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card className="p-4">
              <div className="text-xs text-muted">ADF Unit-Root Test</div>
              <div className="mt-1 text-lg font-bold font-mono text-accent">
                t = {data.stationarity.adf_statistic}
              </div>
              <div className="text-[11px] text-muted">p-value: {data.stationarity.p_value} ({data.stationarity.is_stationary ? "Stationary" : "Non-Stationary"})</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Cyclical Variance Ratio</div>
              <div className="mt-1 text-lg font-bold font-mono text-emerald-400">
                {data.hp_decomposition.cyclical_variance_pct}%
              </div>
              <div className="text-[11px] text-muted">Noise vs. Secular Trend</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Current Volatility (4W)</div>
              <div className="mt-1 text-lg font-bold font-mono text-foreground">
                σ = {data.volatility.current_volatility}
              </div>
              <div className="text-[11px] text-muted">{data.volatility.regime}</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Structural Breakpoints</div>
              <div className="mt-1 text-lg font-bold font-mono text-rose-400">
                {data.structural_breaks.length} Regimes
              </div>
              <div className="text-[11px] text-muted">CUSUM detected shifts</div>
            </Card>
          </div>

          {/* HP Filter Chart */}
          <Card className="p-5">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h3 className="font-semibold text-sm">Hodrick-Prescott Secular Trend &amp; Cyclical Deconstruction</h3>
                <div className="text-xs text-muted">Separates underlying structural direction from transient media hype cycles</div>
              </div>
              <Badge tone="accent">λ = {smoothness}</Badge>
            </div>
            <div className="h-80 w-full">
              <EChart height={300} option={hpOption} />
            </div>
          </Card>

          {/* Bottom Grid: Volatility Regime & Structural Breakpoint Log */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Conditional Volatility */}
            <Card className="p-5 space-y-3">
              <div>
                <h3 className="font-semibold text-sm">Rolling Conditional Volatility (ARCH Proxy)</h3>
                <div className="text-xs text-muted">Isolates high-variance crisis clusters vs. consensus periods</div>
              </div>
              <div className="h-56 w-full">
                <EChart height={210} option={volOption} />
              </div>
            </Card>

            {/* Structural Breakpoint Timeline */}
            <Card className="p-5 space-y-3">
              <div>
                <h3 className="font-semibold text-sm">Structural Breaks &amp; Regime Shifts</h3>
                <div className="text-xs text-muted">Statistically significant permanent shifts in narrative momentum (p &lt; 0.05)</div>
              </div>

              {data.structural_breaks.length > 0 ? (
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {data.structural_breaks.map((b, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg bg-card2 p-3 border border-border/50 text-xs">
                      <div>
                        <div className="font-semibold text-foreground flex items-center gap-1.5">
                          <span className={cx(
                            "w-2 h-2 rounded-full",
                            b.magnitude > 0 ? "bg-emerald-400" : "bg-rose-400"
                          )} />
                          {b.type} ({b.date})
                        </div>
                        <div className="text-[11px] text-muted mt-0.5">
                          Pre-mean: {b.pre_mean} → Post-mean: {b.post_mean}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={cx(
                          "font-mono font-bold",
                          b.magnitude > 0 ? "text-emerald-400" : "text-rose-400"
                        )}>
                          {fmtSigned(b.magnitude)} pts
                        </div>
                        <div className="text-[10px] text-muted font-mono">t = {b.t_statistic}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex h-40 items-center justify-center rounded-lg border border-dashed border-border p-4 text-center text-xs text-muted">
                  No structural regime breaks detected at the 95% confidence threshold.
                </div>
              )}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
