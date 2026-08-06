"use client";

import { useEffect, useMemo, useState } from "react";
import { useApi } from "@/lib/useApi";
import { EChart, useChartTheme } from "@/components/echart";
import { lineTimeSeries } from "@/components/charts";
import { Card, PageHeader, MultiSelect, Field, Segmented, Spinner, EmptyState, StatTile, DISCLAIMER } from "@/components/ui";
import { fmtSigned } from "@/lib/format";

interface CatalogTopic { id: string; label: string; category: string; }
interface TopicsResp { topics: CatalogTopic[]; }
interface Series { week_start: string; avg_tone?: number; avg_sentiment?: number }
interface CmpTopic { id: string; label: string; media_series: Series[]; opinion_series: Series[]; avg_media: number | null; avg_public: number | null; avg_gap: number | null; }
interface CompareResp { topics: CmpTopic[]; }

interface CorrPair {
  topic_a: string;
  topic_b: string;
  correlation: number;
  relationship: string;
}
interface LeadLagItem {
  label_a: string;
  label_b: string;
  optimal_lag: number;
  max_correlation: number;
  zero_lag_correlation: number;
  summary: string;
}
interface CorrelationResp {
  metric: string;
  columns: string[];
  matrix: [number, number, number][];
  pairs: CorrPair[];
  lead_lag: LeadLagItem[];
}

export default function ComparePage() {
  const { data: catalog } = useApi<TopicsResp>("/api/topics");
  const [selected, setSelected] = useState<string[]>([]);
  const [metric, setMetric] = useState("media");
  const t = useChartTheme();

  useEffect(() => {
    if (catalog && selected.length === 0) {
      const ids = catalog.topics.map((x) => x.id);
      setSelected([ids.find((i) => i === "inflation") ?? ids[0], ids.find((i) => i === "donald_trump") ?? ids[1]].filter(Boolean) as string[]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalog]);

  const { data, loading, error, reload } = useApi<CompareResp>(
    selected.length ? "/api/compare-topics" : null, { topics: selected.join(",") });

  const { data: corrData } = useApi<CorrelationResp>(
    selected.length >= 2 ? "/api/topics/correlation" : null, { topics: selected.join(","), metric });

  const option = useMemo(() => {
    if (!data) return {};
    const series = data.topics.map((tp) => ({
      name: tp.label,
      points: (metric === "media" ? tp.media_series : tp.opinion_series).map((p) => ({
        week_start: p.week_start, value: metric === "media" ? p.avg_tone ?? null : p.avg_sentiment ?? null,
      })),
    }));
    return lineTimeSeries(t, series, { yName: metric === "media" ? "media tone" : "public sentiment", showZero: true });
  }, [data, metric, t]);

  const heatmapOption = useMemo(() => {
    if (!corrData || !corrData.columns || corrData.columns.length < 2) return {};
    const cols = corrData.columns;
    return {
      tooltip: {
        position: "top",
        backgroundColor: t.card,
        borderColor: t.border,
        textStyle: { color: t.fg, fontSize: 12 },
        formatter: (params: { data: [number, number, number] }) => {
          const [i, j, val] = params.data;
          return `<b>${cols[i]}</b> ↔ <b>${cols[j]}</b><br/>Correlation: <b>${val >= 0 ? "+" : ""}${val.toFixed(3)}</b>`;
        },
      },
      grid: { height: "70%", top: "10%", left: "15%", right: "8%" },
      xAxis: { type: "category", data: cols, splitArea: { show: true }, axisLabel: { interval: 0, rotate: 20, color: t.muted, fontSize: 11 } },
      yAxis: { type: "category", data: cols, splitArea: { show: true }, axisLabel: { color: t.muted, fontSize: 11 } },
      visualMap: {
        min: -1,
        max: 1,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: "0%",
        inRange: {
          color: ["#3b82f6", "#1e293b", "#ef4444"], // Blue (negative) -> Dark/Neutral -> Red (positive)
        },
        textStyle: { color: t.muted, fontSize: 11 },
      },
      series: [
        {
          name: "Correlation",
          type: "heatmap",
          data: corrData.matrix,
          label: {
            show: true,
            formatter: (p: { data: [number, number, number] }) => p.data[2].toFixed(2),
            color: "#ffffff",
            fontSize: 11,
          },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowColor: "rgba(0, 0, 0, 0.5)" },
          },
        },
      ],
    };
  }, [corrData, t]);

  const opts = (catalog?.topics ?? []).map((x) => ({ value: x.id, label: x.label }));

  return (
    <div className="space-y-6">
      <PageHeader title="Compare topics" subtitle="Overlay the sentiment history of several topics, measure cross-topic statistical correlation, and evaluate lead-lag dynamics.">
        <Field label="Topics (up to 5)"><MultiSelect options={opts} value={selected} onChange={(v) => setSelected(v.slice(0, 5))} placeholder="Pick topics" /></Field>
        <Field label="Metric"><Segmented value={metric} onChange={setMetric} options={[{ value: "media", label: "Media" }, { value: "public", label: "Public" }]} /></Field>
      </PageHeader>

      {selected.length === 0 && <EmptyState title="Pick at least one topic to compare" />}
      {loading && <Spinner label="Analyzing topics…" />}
      {error && <EmptyState title="Couldn't load comparison" hint={error} onRetry={reload} />}

      {data && (
        <>
          <Card className="p-4">
            <div className="mb-2 text-sm font-medium">Time-Series Sentiment Overlay ({metric.toUpperCase()})</div>
            <EChart height={420} option={option} />
          </Card>
          
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.topics.map((tp) => (
              <StatTile key={tp.id} label={tp.label}
                value={fmtSigned(metric === "media" ? tp.avg_media : tp.avg_public)}
                sub={`media↔public gap ${fmtSigned(tp.avg_gap)}`} />
            ))}
          </div>

          {corrData && corrData.columns.length >= 2 && (
            <div className="grid gap-6 lg:grid-cols-2">
              <Card className="p-4">
                <div className="mb-1 flex items-center justify-between">
                  <div className="text-sm font-medium">Pairwise Correlation Matrix</div>
                  <span className="rounded bg-accent/10 px-2 py-0.5 text-xs text-accent">Pearson r</span>
                </div>
                <p className="mb-2 text-xs text-muted">Values range from -1.0 (inverse) to +1.0 (synchronized movement).</p>
                <EChart height={340} option={heatmapOption} />
              </Card>

              <div className="space-y-4">
                <Card className="p-4">
                  <div className="mb-2 text-sm font-medium">⏱️ Temporal Lead-Lag Analysis</div>
                  <p className="mb-3 text-xs text-muted">Determines whether one topic shifts earlier and acts as a leading indicator for another.</p>
                  <div className="space-y-2.5">
                    {corrData.lead_lag.map((item, idx) => (
                      <div key={idx} className="rounded-lg border border-border/80 bg-card2/40 p-3 text-xs">
                        <div className="font-semibold text-foreground">{item.label_a} ↔ {item.label_b}</div>
                        <div className="mt-1 text-muted">{item.summary}</div>
                        <div className="mt-2 flex gap-4 text-[11px] text-muted">
                          <span>Sync r: <code>{item.zero_lag_correlation >= 0 ? "+" : ""}{item.zero_lag_correlation}</code></span>
                          <span>Max r: <code>{item.max_correlation >= 0 ? "+" : ""}{item.max_correlation}</code> (lag: {item.optimal_lag}w)</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>

                <Card className="p-4">
                  <div className="mb-2 text-sm font-medium">Ranked Topic Associations</div>
                  <div className="space-y-1.5">
                    {corrData.pairs.map((p, idx) => (
                      <div key={idx} className="flex items-center justify-between border-b border-border/40 py-1.5 text-xs last:border-0">
                        <span className="font-medium text-foreground">{p.topic_a} ↔ {p.topic_b}</span>
                        <div className="flex items-center gap-2">
                          <span className={`font-mono font-semibold ${p.correlation >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                            {p.correlation >= 0 ? "+" : ""}{p.correlation.toFixed(2)}
                          </span>
                          <span className="rounded bg-card px-1.5 py-0.5 text-[10px] uppercase text-muted">
                            {p.relationship.replace("_", " ")}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          )}

          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
