"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { api, apiPost, NetworkGraphData, ContagionSimResponse } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { EChart, useChartTheme } from "@/components/echart";
import { fmtSigned, toneColor } from "@/lib/format";
import {
  Share2,
  ArrowRight,
  Layers,
  Sliders,
  Zap,
  Flame,
  Radio,
  RotateCcw,
  CheckCircle2,
} from "lucide-react";
import type { EChartsCoreOption, ECharts } from "echarts";

export default function NetworkPage() {
  const theme = useChartTheme();
  const [minCorr, setMinCorr] = useState(0.25);
  const [data, setData] = useState<NetworkGraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<number | "all">("all");
  const chartInstance = useRef<ECharts | null>(null);

  // Contagion Simulation State
  const [shockMagnitude, setShockMagnitude] = useState<number>(-3.0);
  const [simLoading, setSimLoading] = useState(false);
  const [simResult, setSimResult] = useState<ContagionSimResponse | null>(null);
  const [activeSimStep, setActiveSimStep] = useState<number>(0);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api<NetworkGraphData>("/api/network/graph", { min_correlation: minCorr, max_nodes: 32 })
      .then((res) => {
        setData(res);
        if (res.nodes.length > 0 && !selectedNode) {
          setSelectedNode(res.nodes[0]);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [minCorr]);

  const handleRunContagionSim = async (nodeId?: string) => {
    const targetId = nodeId || selectedNode?.id || "inflation";
    setSimLoading(true);
    try {
      const res = await apiPost<ContagionSimResponse>("/api/network/simulate-contagion", {
        seed_topic: targetId,
        shock_magnitude: shockMagnitude,
        attenuation: 0.65,
        max_steps: 3,
      });
      setSimResult(res);
      setActiveSimStep(0);
    } catch (err: any) {
      console.error(err);
    } finally {
      setSimLoading(false);
    }
  };

  // Filter nodes/links if cluster filtered
  const filteredNodes = data
    ? data.nodes.filter((n) => selectedCluster === "all" || n.cluster_id === selectedCluster)
    : [];
  const nodeIds = new Set(filteredNodes.map((n) => n.id));
  const filteredLinks = data
    ? data.links.filter((l) => nodeIds.has(l.source) && nodeIds.has(l.target))
    : [];

  const graphOption: EChartsCoreOption = data ? {
    backgroundColor: "transparent",
    tooltip: {
      formatter: (params: any) => {
        if (params.dataType === "node") {
          return `
            <div style="font-size:12px; padding:2px;">
              <strong>${params.data.name}</strong><br/>
              Cluster: ${params.data.cluster_name}<br/>
              Latest Tone: <span style="font-weight:bold; color:${params.data.latest_tone >= 0 ? '#10b981' : '#f43f5e'}">${params.data.latest_tone > 0 ? '+' : ''}${params.data.latest_tone}</span><br/>
              Coverage Volume: ${params.data.volume.toLocaleString()} articles
            </div>
          `;
        } else if (params.dataType === "edge") {
          return `
            <div style="font-size:12px; padding:2px;">
              <strong>${params.data.source_label}</strong> ↔ <strong>${params.data.target_label}</strong><br/>
              Correlation: <strong>${params.data.value > 0 ? '+' : ''}${params.data.value}</strong> (${params.data.relationship.replace('_', ' ')})
            </div>
          `;
        }
      },
      backgroundColor: theme.card,
      borderColor: theme.border,
      textStyle: { color: theme.fg },
    },
    series: [
      {
        type: "graph",
        layout: "force",
        data: filteredNodes,
        links: filteredLinks,
        roam: true,
        label: {
          show: true,
          position: "right",
          color: theme.fg,
          fontSize: 11,
        },
        force: {
          repulsion: 220,
          edgeLength: [60, 160],
          gravity: 0.12,
        },
        emphasis: {
          focus: "adjacency",
          lineStyle: { width: 4 },
        },
      },
    ],
  } : {};

  const handleChartReady = (chart: ECharts) => {
    chartInstance.current = chart;
    chart.on("click", (params: any) => {
      if (params.dataType === "node") {
        setSelectedNode(params.data);
      }
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Share2 className="h-6 w-6 text-accent" />
            <h1 className="text-2xl font-bold tracking-tight">Ideological Network Graph &amp; Contagion Simulator</h1>
          </div>
          <p className="text-sm text-muted">
            Force-directed clustering and shock propagation simulating cross-narrative spillover across global political entities.
          </p>
        </div>
      </div>

      {/* Control Bar: Threshold Slider + Cluster Filter */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-card p-4">
        {/* Dynamic Correlation Threshold Slider */}
        <div className="flex items-center gap-3">
          <Sliders size={15} className="text-accent" />
          <div className="flex flex-col">
            <span className="text-xs font-semibold uppercase text-muted">
              Min Correlation Threshold: <strong className="text-accent font-mono">r &ge; {minCorr.toFixed(2)}</strong>
            </span>
            <input
              type="range"
              min={0.10}
              max={0.80}
              step={0.05}
              value={minCorr}
              onChange={(e) => setMinCorr(parseFloat(e.target.value))}
              className="w-48 h-1.5 bg-card2 rounded-lg appearance-none cursor-pointer accent-accent mt-1"
            />
          </div>
        </div>

        {/* Cluster Filter Buttons */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setSelectedCluster("all")}
            className={cx(
              "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
              selectedCluster === "all"
                ? "bg-accent text-white"
                : "bg-card2 text-muted hover:bg-card hover:text-foreground border border-border"
            )}
          >
            All Clusters
          </button>
          {data?.clusters.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCluster(c.id)}
              className={cx(
                "flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors border",
                selectedCluster === c.id
                  ? "bg-card text-foreground border-accent shadow-sm"
                  : "bg-card2 text-muted hover:bg-card hover:text-foreground border-border"
              )}
            >
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: c.color }} />
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex h-96 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Calculating pairwise correlation matrices and force vectors...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Network engine error: {error}
        </div>
      )}

      {data && !loading && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Main Network Graph */}
          <div className="lg:col-span-2 space-y-4">
            <Card className="p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <div className="flex items-center gap-2">
                  <Layers size={16} className="text-accent" />
                  <span className="font-bold text-sm">Force-Directed Topology</span>
                </div>
                <div className="flex items-center gap-3 text-xs text-muted font-mono">
                  <span>{filteredNodes.length} Nodes</span>
                  <span>{filteredLinks.length} Edges</span>
                </div>
              </div>

              <div className="h-[460px] w-full">
                <EChart option={graphOption} onReady={handleChartReady} className="h-[460px] w-full" />
              </div>
            </Card>

            {/* CONTAGION SIMULATION CASCADE DRAWER */}
            {simResult && (
              <Card className="p-5 space-y-4 border-amber-500/40 bg-card">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
                  <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
                    <Zap size={16} />
                    <span>Contagion Cascade: {simResult.seed_label} ({simResult.shock_magnitude > 0 ? "+" : ""}{simResult.shock_magnitude} Shock)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {simResult.steps.map((st) => (
                      <button
                        key={st.step}
                        onClick={() => setActiveSimStep(st.step)}
                        className={cx(
                          "px-2.5 py-1 rounded text-xs font-semibold transition-all",
                          activeSimStep === st.step
                            ? "bg-amber-500 text-white"
                            : "bg-card2 text-muted hover:text-foreground border border-border"
                        )}
                      >
                        Wave {st.step} ({st.affected_nodes.length})
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-xs text-muted font-medium">
                    {simResult.steps[activeSimStep]?.description}
                  </div>

                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3 pt-1">
                    {simResult.steps[activeSimStep]?.affected_nodes.map((node, nIdx) => (
                      <div key={nIdx} className="rounded-lg border border-border bg-card2 p-2.5 text-xs space-y-1">
                        <div className="flex items-center justify-between font-bold">
                          <span className="truncate">{node.label}</span>
                          <span className={node.delta >= 0 ? "text-emerald-400" : "text-rose-400"}>
                            {fmtSigned(node.delta)} pts
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-muted">
                          <span>{node.pre_shock_tone > 0 ? "+" : ""}{node.pre_shock_tone} &rarr; {node.post_shock_tone > 0 ? "+" : ""}{node.post_shock_tone}</span>
                          <span className="font-mono text-[10px]">r = {node.correlation_weight}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* Node Inspector & Shock Trigger Panel */}
          <div className="space-y-4">
            {selectedNode ? (
              <Card className="p-5 space-y-4 sticky top-6">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h2 className="text-base font-bold">{selectedNode.name}</h2>
                    <span className="text-xs text-muted">{selectedNode.category}</span>
                  </div>
                  <Badge tone={selectedNode.latest_tone >= 0 ? "positive" : "negative"}>
                    {fmtSigned(selectedNode.latest_tone)}
                  </Badge>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1 border-b border-border/50">
                    <span className="text-muted">Assigned Cluster:</span>
                    <span className="font-semibold">{selectedNode.cluster_name}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-border/50">
                    <span className="text-muted">Article Coverage Volume:</span>
                    <span className="font-mono font-semibold">{selectedNode.volume.toLocaleString()}</span>
                  </div>
                </div>

                {/* Contagion Simulation Launcher */}
                <div className="rounded-xl border border-accent/30 bg-accent/5 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-accent flex items-center gap-1">
                      <Zap size={14} /> Contagion Shock Engine
                    </span>
                    <Badge tone="accent">{shockMagnitude > 0 ? `+${shockMagnitude}` : shockMagnitude} Tone</Badge>
                  </div>

                  <div className="space-y-1">
                    <div className="flex justify-between text-[11px] text-muted">
                      <span>Hypothetical Sentiment Shock:</span>
                      <span className="font-mono font-bold">{shockMagnitude > 0 ? `+${shockMagnitude}` : shockMagnitude} pts</span>
                    </div>
                    <input
                      type="range"
                      min={-5.0}
                      max={5.0}
                      step={0.5}
                      value={shockMagnitude}
                      onChange={(e) => setShockMagnitude(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-card rounded-lg appearance-none cursor-pointer accent-accent"
                    />
                  </div>

                  <button
                    onClick={() => handleRunContagionSim(selectedNode.id)}
                    disabled={simLoading}
                    className="w-full flex items-center justify-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-xs font-semibold text-white shadow hover:bg-accent/90 disabled:opacity-50 transition-all"
                  >
                    {simLoading ? <Zap size={13} className="animate-spin" /> : <Zap size={13} />}
                    <span>Simulate Shock Transmission</span>
                  </button>
                </div>

                <Link
                  href={`/topic?q=${encodeURIComponent(selectedNode.id)}`}
                  className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-border bg-card2 px-3 py-2 text-xs font-semibold text-foreground shadow hover:border-accent hover:text-accent transition-all"
                >
                  <span>Open Topic Telemetry</span>
                  <ArrowRight size={13} />
                </Link>
              </Card>
            ) : (
              <div className="flex h-48 items-center justify-center rounded-xl border border-dashed border-border text-center p-6 text-sm text-muted">
                Click any node in the network to inspect its connections and trigger contagion simulation.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
