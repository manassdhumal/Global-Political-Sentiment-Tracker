"use client";

import { useEffect, useState } from "react";
import { api, MarketSpilloverData } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { EChart, useChartTheme } from "@/components/echart";
import { fmtSigned } from "@/lib/format";
import { DollarSign, TrendingUp, TrendingDown, ArrowUpRight, Zap, ShieldAlert, BarChart3 } from "lucide-react";
import type { EChartsCoreOption } from "echarts";

const TOPIC_PRESETS = [
  { id: "inflation", label: "Inflation & Cost of Living" },
  { id: "defense_spending", label: "Defense & Military Spending" },
  { id: "donald_trump", label: "Donald Trump" },
  { id: "china_trade", label: "US-China Trade Relations" },
  { id: "housing_crisis", label: "Housing & Real Estate" },
];

export default function MarketsPage() {
  const theme = useChartTheme();
  const [topic, setTopic] = useState("inflation");
  const [asset, setAsset] = useState("brent_oil");
  const [weeks, setWeeks] = useState(52);
  const [assets, setAssets] = useState<any[]>([]);
  const [data, setData] = useState<MarketSpilloverData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch asset registry overview
  useEffect(() => {
    api<any[]>("/api/markets/assets")
      .then((res) => setAssets(res))
      .catch((err) => console.error(err));
  }, []);

  // Fetch market spillover analytics
  useEffect(() => {
    setLoading(true);
    setError(null);
    api<MarketSpilloverData>("/api/markets/spillover", { topic, asset, weeks })
      .then((res) => setData(res))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [topic, asset, weeks]);

  // Dual-Axis Synchronized Chart: Asset Price vs. Political Sentiment
  const chartOption: EChartsCoreOption = data ? {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: theme.card,
      borderColor: theme.border,
      textStyle: { color: theme.fg, fontSize: 12 },
    },
    legend: {
      data: [`${data.asset.name} Price (${data.asset.unit})`, "Political Sentiment Tone"],
      textStyle: { color: theme.muted },
      bottom: 0,
      icon: "roundRect",
    },
    grid: { left: 55, right: 55, top: 25, bottom: 40 },
    xAxis: {
      type: "category",
      data: data.series.map((s) => s.date),
      axisLine: { lineStyle: { color: theme.border } },
      axisLabel: { color: theme.muted, fontSize: 11 },
    },
    yAxis: [
      {
        type: "value",
        name: `Price (${data.asset.unit})`,
        nameTextStyle: { color: theme.accent, fontSize: 11 },
        splitLine: { lineStyle: { color: theme.grid, opacity: 0.35, type: "dashed" } },
        axisLabel: { color: theme.accent, fontSize: 11 },
      },
      {
        type: "value",
        name: "Political Tone Score",
        nameTextStyle: { color: theme.accent2, fontSize: 11 },
        splitLine: { show: false },
        axisLabel: { color: theme.accent2, fontSize: 11 },
      },
    ],
    series: [
      {
        name: `${data.asset.name} Price (${data.asset.unit})`,
        type: "line",
        yAxisIndex: 0,
        data: data.series.map((s) => s.price),
        lineStyle: { color: theme.accent, width: 3 },
        itemStyle: { color: theme.accent },
        symbol: "none",
      },
      {
        name: "Political Sentiment Tone",
        type: "line",
        yAxisIndex: 1,
        data: data.series.map((s) => s.sentiment_tone),
        lineStyle: { color: theme.accent2, width: 2, type: "dashed" },
        itemStyle: { color: theme.accent2 },
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
            <span className="text-2xl">📈</span>
            <h1 className="text-2xl font-bold tracking-tight">Cross-Asset Financial Spillover &amp; Market Contagion</h1>
          </div>
          <p className="text-sm text-muted">
            Quantify how political sentiment velocity transmits to currency volatility, sovereign bond yields, defense contractors, and energy benchmarks.
          </p>
        </div>

        {data && (
          <a
            href={`/api/export/csv/market-spillover?topic=${topic}&asset=${asset}`}
            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card2 px-3.5 py-1.5 text-xs font-semibold text-foreground shadow-sm hover:border-accent hover:text-accent transition-colors"
          >
            <BarChart3 size={14} className="text-accent" /> Download Spillover CSV
          </a>
        )}
      </div>

      {/* Asset Quick Selector Strip */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {assets.map((a) => {
          const isSelected = a.id === asset;
          const up = a.perf_12w_pct >= 0;
          return (
            <div
              key={a.id}
              onClick={() => setAsset(a.id)}
              className={cx(
                "cursor-pointer rounded-xl border p-3 transition-all duration-200 hover:border-accent/50",
                isSelected
                  ? "border-accent bg-accent/10 shadow-sm ring-1 ring-accent/30"
                  : "border-border bg-card hover:bg-card2"
              )}
            >
              <div className="text-xs font-semibold truncate text-foreground">{a.name}</div>
              <div className="mt-1 text-sm font-bold font-mono">
                {a.latest_price.toLocaleString()} <span className="text-[10px] font-normal text-muted">{a.unit}</span>
              </div>
              <div className={cx(
                "mt-1 text-[11px] font-semibold flex items-center gap-0.5",
                up ? "text-emerald-500" : "text-rose-500"
              )}>
                {up ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
                {fmtSigned(a.perf_12w_pct)}% (12W)
              </div>
            </div>
          );
        })}
      </div>

      {/* Topic & Horizon Filter Bar */}
      <Card className="p-4 bg-card border-border/80 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <DollarSign size={16} className="text-accent shrink-0" />
          <span className="text-xs text-muted font-medium">Political Catalyst:</span>
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

        <div className="flex items-center gap-1.5">
          {[
            { w: 26, label: "6M Horizon" },
            { w: 52, label: "1Y Horizon" },
            { w: 104, label: "2Y Full Cycle" },
          ].map((h) => (
            <button
              key={h.w}
              onClick={() => setWeeks(h.w)}
              className={cx(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                weeks === h.w ? "bg-accent text-white" : "bg-card2 hover:bg-card border border-border text-muted"
              )}
            >
              {h.label}
            </button>
          ))}
        </div>
      </Card>

      {loading && (
        <div className="flex h-72 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Running Granger causality regressions &amp; market beta...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Failed to load market spillover: {error}
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6">
          {/* Quantitative Risk Tiles */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card className="p-4">
              <div className="text-xs text-muted">Cross-Correlation</div>
              <div className={cx(
                "mt-1 text-xl font-bold font-mono",
                data.metrics.correlation_r >= 0 ? "text-emerald-400" : "text-rose-400"
              )}>
                r = {fmtSigned(data.metrics.correlation_r)}
              </div>
              <div className="text-[11px] text-muted">Directional co-movement</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Spillover Elasticity Beta</div>
              <div className="mt-1 text-xl font-bold font-mono text-accent">
                β = {data.metrics.spillover_beta}
              </div>
              <div className="text-[11px] text-muted">% return per +1.0 tone change</div>
            </Card>
            <Card className="p-4 border-amber-500/30 bg-amber-500/5">
              <div className="text-xs text-amber-400 font-medium">Contagion Score</div>
              <div className="mt-1 text-xl font-bold font-mono text-amber-400">
                {data.metrics.contagion_score} / 100
              </div>
              <div className="text-[11px] text-muted">Transmission vulnerability</div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Granger Lead Time</div>
              <div className="mt-1 text-xl font-bold font-mono text-foreground">
                {data.metrics.granger_causality.optimal_lag_weeks} Wk Lag
              </div>
              <div className="text-[11px] text-muted">
                {data.metrics.granger_causality.causality_detected ? "Statistically Significant" : "Independent"}
              </div>
            </Card>
          </div>

          {/* Chart & Econometric Interpretation */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2 p-5">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-sm">{data.asset.name} vs. {data.topic.label}</h3>
                  <div className="text-xs text-muted">Synchronized dual-axis historical timeline</div>
                </div>
                <Badge tone={data.metrics.granger_causality.causality_detected ? "positive" : "muted"}>
                  {data.metrics.granger_causality.causality_detected ? "Predictive Lead Detected" : "Synchronous"}
                </Badge>
              </div>
              <div className="h-80 w-full">
                <EChart height={300} option={chartOption} />
              </div>
            </Card>

            {/* Spillover Econometric Verdict */}
            <Card className="p-5 space-y-4 bg-card flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted/80">
                  <Zap size={14} className="text-accent" /> Macro Causality Diagnosis
                </div>
                <div className="rounded-lg bg-card2 p-3.5 border border-border/60">
                  <div className="text-xs font-bold text-foreground leading-snug">
                    {data.metrics.granger_causality.verdict}
                  </div>
                  <div className="mt-2 text-[11px] text-muted">
                    F-statistic: <span className="font-mono font-semibold text-foreground">{data.metrics.granger_causality.f_statistic}</span> (p = {data.metrics.granger_causality.p_value})
                  </div>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="text-muted">Asset Profile:</div>
                  <div className="text-xs text-foreground">{data.asset.description}</div>
                  <div className="text-[11px] text-muted">Sensitivity: <span className="text-foreground uppercase font-medium">{data.asset.geopolitical_sensitivity}</span></div>
                </div>
              </div>

              <div className="rounded-lg border border-accent/20 bg-accent/5 p-3 text-[11px] text-muted">
                💼 <strong>Trading Floor Note:</strong> Cross-asset Granger regressions identify whether narrative inflection points provide statistical leading indicators for macro portfolio rebalancing.
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
