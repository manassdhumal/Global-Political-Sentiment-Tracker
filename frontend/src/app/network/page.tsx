"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { api, NetworkGraphData } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { EChart, useChartTheme } from "@/components/echart";
import { fmtSigned } from "@/lib/format";
import { Share2, ArrowRight, Layers } from "lucide-react";
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

  useEffect(() => {
    setLoading(true);
    setError(null);
    api<NetworkGraphData>("/api/network/graph", { min_correlation: minCorr, max_nodes: 32 })
      .then((res) => {
        setData(res);
        if (res.nodes.length > 0) {
          setSelectedNode(res.nodes[0]);
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [minCorr]);

  // Filter nodes/links if cluster filtered
  const filteredNodes = data ? data.nodes.filter((n) => selectedCluster === "all" || n.cluster_id === selectedCluster) : [];
  const nodeIds = new Set(filteredNodes.map((n) => n.id));
  const filteredLinks = data ? data.links.filter((l) => nodeIds.has(l.source) && nodeIds.has(l.target)) : [];

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
            <span className="text-2xl">🕸️</span>
            <h1 className="text-2xl font-bold tracking-tight">Ideological Network &amp; Entity Clusters</h1>
          </div>
          <p className="text-sm text-muted">
            Force-directed clustering revealing political alignment, shared narrative velocity, and ideological community groupings.
          </p>
        </div>
      </div>

      {/* Control Bar: Cluster Filter & Min Correlation Slider */}
      <Card className="p-4 bg-card border-border/80 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        {/* Cluster Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          <Layers size={15} className="text-muted shrink-0 ml-1" />
          <button
            onClick={() => setSelectedCluster("all")}
            className={cx(
              "rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap transition-all",
              selectedCluster === "all"
                ? "bg-accent text-white font-semibold"
                : "bg-card2 hover:bg-card border border-border text-muted"
            )}
          >
            All Clusters
          </button>
          {data?.clusters.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCluster(c.id)}
              className={cx(
                "rounded-full px-3 py-1 text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1.5",
                selectedCluster === c.id
                  ? "bg-accent text-white font-semibold"
                  : "bg-card2 hover:bg-card border border-border text-muted"
              )}
            >
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: c.color }} />
              {c.name}
            </button>
          ))}
        </div>

        {/* Min Correlation Slider */}
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-xs text-muted font-medium whitespace-nowrap">Link Threshold:</span>
          <input
            type="range"
            min="0.15"
            max="0.55"
            step="0.05"
            value={minCorr}
            onChange={(e) => setMinCorr(Number(e.target.value))}
            className="w-28 accent-accent"
          />
          <span className="text-xs font-mono font-bold text-accent">|r| ≥ {minCorr.toFixed(2)}</span>
        </div>
      </Card>

      {/* Graph Area & Inspector */}
      {loading && (
        <div className="flex h-96 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Building ideological force graph...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Failed to load network graph: {error}
        </div>
      )}

      {data && !loading && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Force-Directed Canvas */}
          <Card className="lg:col-span-2 p-3 bg-card border-border/80 relative">
            <div className="absolute top-4 left-4 z-10 text-[11px] text-muted flex items-center gap-2 bg-card2/80 px-2.5 py-1 rounded-md border border-border/50">
              <span>🔵 Blue = Positive Co-movement</span>
              <span>🔴 Red = Polarized Inverse</span>
            </div>
            <div className="h-[520px] w-full">
              <EChart height={520} option={graphOption} onReady={handleChartReady} />
            </div>
          </Card>

          {/* Node & Cluster Detail Drawer */}
          <div className="lg:col-span-1 space-y-4">
            {selectedNode ? (
              <Card className="p-5 space-y-4 bg-card border-border">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h3 className="font-bold text-base">{selectedNode.name}</h3>
                    <div className="text-xs text-muted capitalize">{selectedNode.category}</div>
                  </div>
                  <span
                    className="px-2.5 py-1 text-xs font-bold rounded-md"
                    style={{ backgroundColor: `${selectedNode.itemStyle?.color}20`, color: selectedNode.itemStyle?.color }}
                  >
                    {selectedNode.cluster_name}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg bg-card2 p-3 border border-border/50">
                    <div className="text-muted">Latest Tone</div>
                    <div className={cx(
                      "text-lg font-bold font-mono",
                      selectedNode.latest_tone >= 0 ? "text-emerald-500" : "text-rose-500"
                    )}>
                      {fmtSigned(selectedNode.latest_tone)}
                    </div>
                  </div>
                  <div className="rounded-lg bg-card2 p-3 border border-border/50">
                    <div className="text-muted">Media Volume</div>
                    <div className="text-lg font-bold font-mono text-foreground">
                      {selectedNode.volume.toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Connected Topic Associations */}
                <div className="space-y-2">
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted/80">Strongest Associations</div>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {data.links
                      .filter((l) => l.source === selectedNode.id || l.target === selectedNode.id)
                      .slice(0, 6)
                      .map((l, i) => {
                        const partner = l.source === selectedNode.id ? l.target_label : l.source_label;
                        return (
                          <div key={i} className="flex items-center justify-between rounded bg-card2 px-2.5 py-1.5 text-xs">
                            <span className="font-medium text-foreground">{partner}</span>
                            <span className={cx(
                              "font-mono font-bold",
                              l.value > 0 ? "text-emerald-400" : "text-rose-400"
                            )}>
                              {fmtSigned(l.value)}
                            </span>
                          </div>
                        );
                      })}
                  </div>
                </div>

                <Link
                  href={`/topic?q=${encodeURIComponent(selectedNode.id)}`}
                  className="flex items-center justify-center gap-2 rounded-lg bg-accent/15 hover:bg-accent/25 text-accent p-2.5 text-xs font-medium transition-colors w-full"
                >
                  Deep-Dive Topic Intelligence <ArrowRight size={13} />
                </Link>
              </Card>
            ) : (
              <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-border p-4 text-center text-sm text-muted">
                Click any node in the force graph to inspect associations.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
