"use client";

import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { api, apiPost, SimulationResult } from "@/lib/api";
import { Card, Badge, Button, Input, Metric, cx } from "@/components/ui";
import { SlidersHorizontal, Play, Sparkles, AlertTriangle, ShieldCheck, RefreshCw, Zap } from "lucide-react";

const TOPIC_PRESETS = [
  { id: "inflation", label: "Inflation & Cost of Living" },
  { id: "donald_trump", label: "Donald Trump" },
  { id: "keir_starmer", label: "Keir Starmer" },
  { id: "olaf_scholz", label: "Olaf Scholz" },
  { id: "housing_crisis", label: "Housing & Rent Crisis" },
  { id: "defense_spending", label: "Defense & Military Spending" },
  { id: "ai_regulation", label: "AI & Tech Regulation" },
];

export default function SimulatorPage() {
  const [topic, setTopic] = useState("inflation");
  const [eventType, setEventType] = useState("rate_hike");
  const [magnitude, setMagnitude] = useState(1.0);
  const [weeksAhead, setWeeksAhead] = useState(6);
  const [customDescription, setCustomDescription] = useState("");
  const [presets, setPresets] = useState<any[]>([]);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch simulation event models
  useEffect(() => {
    api<{ presets: any[] }>("/api/simulator/presets")
      .then((res) => setPresets(res.presets))
      .catch((err) => console.error(err));
  }, []);

  const runSimulation = () => {
    setLoading(true);
    setError(null);
    apiPost<SimulationResult>("/api/simulator/run", {
      topic,
      event_type: eventType,
      magnitude,
      weeks_ahead: weeksAhead,
      custom_description: customDescription || undefined,
    })
      .then((res) => setResult(res))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  // Run initial simulation on load
  useEffect(() => {
    runSimulation();
  }, []);

  // ECharts Option for Baseline vs Counterfactual Scenario
  const chartOption = result ? {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(20, 24, 33, 0.95)",
      borderColor: "#334155",
      textStyle: { color: "#f1f5f9", fontSize: 12 },
    },
    legend: {
      data: ["Baseline Forecast", "Simulated Shock (Media)", "Simulated Shock (Public)", "Confidence Envelope"],
      textStyle: { color: "#94a3b8" },
      bottom: 0,
    },
    grid: { left: 45, right: 25, top: 25, bottom: 40 },
    xAxis: {
      type: "category",
      data: result.simulation.dates,
      axisLine: { lineStyle: { color: "#334155" } },
      axisLabel: { color: "#94a3b8", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      name: "Tone Score",
      nameTextStyle: { color: "#64748b", fontSize: 11 },
      splitLine: { lineStyle: { color: "#1e293b", type: "dashed" } },
      axisLabel: { color: "#94a3b8", fontSize: 11 },
    },
    series: [
      {
        name: "Baseline Forecast",
        type: "line",
        data: result.simulation.baseline_media,
        lineStyle: { color: "#64748b", width: 2, type: "dashed" },
        itemStyle: { color: "#64748b" },
        symbol: "none",
      },
      {
        name: "Simulated Shock (Media)",
        type: "line",
        data: result.simulation.shocked_media,
        lineStyle: { color: "#ef4444", width: 3 },
        itemStyle: { color: "#ef4444" },
        symbol: "circle",
        symbolSize: 6,
      },
      {
        name: "Simulated Shock (Public)",
        type: "line",
        data: result.simulation.shocked_public,
        lineStyle: { color: "#38bdf8", width: 2.5 },
        itemStyle: { color: "#38bdf8" },
        symbol: "circle",
        symbolSize: 5,
      },
      {
        name: "Confidence Envelope",
        type: "line",
        data: result.simulation.shocked_upper,
        lineStyle: { opacity: 0 },
        stack: "confidence",
        symbol: "none",
      },
      {
        name: "Confidence Envelope",
        type: "line",
        data: result.simulation.shocked_lower.map((low, i) => result.simulation.shocked_upper[i] - low),
        lineStyle: { opacity: 0 },
        areaStyle: { color: "rgba(239, 68, 68, 0.12)" },
        stack: "confidence",
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
            <span className="text-2xl">🔮</span>
            <h1 className="text-2xl font-bold tracking-tight">AI Policy Impact &amp; Scenario Simulator</h1>
          </div>
          <p className="text-sm text-muted">
            Model counterfactual geopolitical shocks and forecast 30-day sentiment trajectories, media divergence, and volatility shifts.
          </p>
        </div>
      </div>

      {/* Control Sandbox Form */}
      <Card className="p-5 border-border/80 bg-card space-y-4">
        <div className="flex items-center gap-2 text-sm font-semibold border-b border-border pb-3">
          <SlidersHorizontal size={16} className="text-accent" /> Scenario Parameters
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {/* Target Topic */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted">Target Topic / Figure</label>
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full rounded-lg border border-border bg-card2 px-3 py-2 text-sm focus:border-accent focus:outline-none"
            >
              {TOPIC_PRESETS.map((t) => (
                <option key={t.id} value={t.id}>{t.label}</option>
              ))}
            </select>
          </div>

          {/* Shock Event Type */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted">Simulated Shock Event</label>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="w-full rounded-lg border border-border bg-card2 px-3 py-2 text-sm focus:border-accent focus:outline-none"
            >
              {presets.map((p) => (
                <option key={p.key} value={p.key}>{p.label}</option>
              ))}
            </select>
          </div>

          {/* Horizon */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted">Forecast Horizon ({weeksAhead} Weeks)</label>
            <input
              type="range"
              min="2"
              max="12"
              value={weeksAhead}
              onChange={(e) => setWeeksAhead(Number(e.target.value))}
              className="w-full accent-accent"
            />
          </div>
        </div>

        {/* Intensity Slider & Run Action */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-2 border-t border-border">
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted font-medium whitespace-nowrap">Shock Intensity:</span>
            <input
              type="range"
              min="0.5"
              max="2.5"
              step="0.1"
              value={magnitude}
              onChange={(e) => setMagnitude(Number(e.target.value))}
              className="w-36 accent-accent"
            />
            <span className="text-xs font-mono font-bold text-accent">{magnitude.toFixed(1)}x</span>
          </div>

          <Button onClick={runSimulation} disabled={loading} className="gap-2">
            {loading ? <RefreshCw size={15} className="animate-spin" /> : <Play size={15} />}
            Run Simulation
          </Button>
        </div>
      </Card>

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Simulation Failed: {error}
        </div>
      )}

      {/* Simulation Results Section */}
      {result && (
        <div className="space-y-6">
          {/* Key Strategic KPI Cards */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Card className="p-4">
              <div className="text-xs text-muted">Pre-Shock Baseline Tone</div>
              <div className="mt-1 text-2xl font-bold font-mono">
                {result.metrics.initial_tone > 0 ? `+${result.metrics.initial_tone}` : result.metrics.initial_tone}
              </div>
            </Card>
            <Card className="p-4 border-rose-500/30 bg-rose-500/5">
              <div className="text-xs text-rose-400 font-medium">Peak Sentiment Drawdown</div>
              <div className="mt-1 text-2xl font-bold font-mono text-rose-500">
                {result.metrics.peak_delta > 0 ? `+${result.metrics.peak_delta}` : result.metrics.peak_delta} pts
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Public-Media Divergence Gap</div>
              <div className="mt-1 text-2xl font-bold font-mono text-amber-400">
                ±{result.metrics.max_divergence_gap} pts
              </div>
            </Card>
            <Card className="p-4">
              <div className="text-xs text-muted">Projected Recovery Half-Life</div>
              <div className="mt-1 text-2xl font-bold font-mono text-foreground">
                ~{result.metrics.recovery_weeks} Weeks
              </div>
            </Card>
          </div>

          {/* Chart & Narrative Interpretation */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2 p-5">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-sm">Counterfactual Trajectory vs Baseline</h3>
                  <div className="text-xs text-muted">{result.event.label} ({result.event.magnitude}x) on {result.topic.label}</div>
                </div>
                <Badge tone={result.metrics.peak_delta < -3 ? "danger" : "warning"}>
                  {result.metrics.severity_assessment}
                </Badge>
              </div>
              <div className="h-80 w-full">
                <ReactECharts option={chartOption} style={{ height: "100%", width: "100%" }} />
              </div>
            </Card>

            {/* Strategic Scenario Breakdown Card */}
            <Card className="p-5 space-y-4 bg-card flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted/80">
                  <Zap size={14} className="text-accent" /> Scenario Assessment
                </div>
                <p className="text-xs text-muted leading-relaxed">
                  {result.event.description}
                </p>
                <div className="rounded-lg bg-card2 p-3 space-y-2 text-xs border border-border/50">
                  <div className="flex justify-between">
                    <span className="text-muted">Expected Volume Spike:</span>
                    <span className="font-semibold text-foreground">+{result.metrics.volume_surge_pct}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Systemic Risk Tier:</span>
                    <span className="font-semibold text-rose-400">{result.metrics.severity_assessment}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Reversion Probability:</span>
                    <span className="font-semibold text-emerald-400">High (&gt;85%)</span>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-accent/20 bg-accent/5 p-3 text-[11px] text-muted">
                💡 <strong>Analyst Insight:</strong> Sentiment shocks in category <span className="text-foreground capitalize font-medium">{result.event.category}</span> exhibit initial emotional overshoots in social commentary, followed by stabilized journalistic framing by week 3.
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
