"use client";

import { useMemo, useState } from "react";
import type { EChartsCoreOption } from "echarts";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { Card, PageHeader, Select, Field, Spinner, EmptyState, Badge, DISCLAIMER } from "@/components/ui";

interface FRow { week_start: string; forecast: number; lower: number; upper: number; }
interface Forecast { entity: string; method: string; note: string; history: { week_start: string; avg_tone: number }[]; forecast: FRow[]; }
interface ARow { week_start: string; avg_tone: number; direction: string; kind: string; shift: number; }
interface Anom { series: ARow[]; flagged: ARow[]; }
interface Topic { words: string[]; weight: number; }
interface Topics { spike_week: string | null; n_titles: number; topics: Topic[]; }

export default function ForecastPage() {
  const { config, entityName } = useConfig();
  const [entity, setEntity] = useState<string>("");
  const [country, setCountry] = useState("__all__");
  const t = useChartTheme();
  const eid = entity || config?.entities[0]?.id || "";
  const c = country === "__all__" ? undefined : country;

  const { data: fc, loading, error } = useApi<Forecast>(eid ? "/api/forecast" : null, { entity: eid, country: c, periods: 4 });
  const { data: an } = useApi<Anom>(eid ? "/api/anomalies" : null, { entity: eid, country: c, z_thresh: 2.5 });
  const { data: topics } = useApi<Topics>(eid ? "/api/topics" : null, { entity: eid, country: c });

  const option = useMemo<EChartsCoreOption>(() => {
    if (!fc) return {};
    const hist = fc.history;
    const last = hist.at(-1);
    const flagged = an?.flagged ?? [];
    return {
      color: [t.accent, t.accent2, t.negative],
      grid: { left: 8, right: 16, top: 34, bottom: 8, containLabel: true },
      legend: { top: 0, data: ["Observed", "Forecast", "95% interval", "Anomaly"], textStyle: { color: t.muted, fontSize: 11 }, icon: "roundRect" },
      tooltip: { trigger: "axis", backgroundColor: t.card, borderColor: t.border, textStyle: { color: t.fg, fontSize: 12 }, valueFormatter: (v: unknown) => (typeof v === "number" ? v.toFixed(2) : "—") },
      xAxis: { type: "time", axisLine: { lineStyle: { color: t.border } }, axisLabel: { color: t.muted, fontSize: 11 }, splitLine: { show: false } },
      yAxis: { type: "value", axisLabel: { color: t.muted, fontSize: 11 }, splitLine: { lineStyle: { color: t.grid, opacity: 0.35 } } },
      series: [
        { name: "Observed", type: "line", showSymbol: false, smooth: 0.25, lineStyle: { width: 2.2, color: t.accent }, itemStyle: { color: t.accent }, data: hist.map((h) => [h.week_start, h.avg_tone]) },
        { name: "_lower", type: "line", stack: "band", symbol: "none", lineStyle: { opacity: 0 }, areaStyle: { opacity: 0 }, silent: true, data: fc.forecast.map((f) => [f.week_start, f.lower]) },
        { name: "95% interval", type: "line", stack: "band", symbol: "none", lineStyle: { opacity: 0 }, areaStyle: { color: t.muted, opacity: 0.18 }, silent: true, data: fc.forecast.map((f) => [f.week_start, f.upper - f.lower]) },
        { name: "Forecast", type: "line", showSymbol: false, lineStyle: { width: 2, type: "dashed", color: t.accent2 }, itemStyle: { color: t.accent2 }, data: [...(last ? [[last.week_start, last.avg_tone]] : []), ...fc.forecast.map((f) => [f.week_start, f.forecast])] },
        { name: "Anomaly", type: "scatter", symbolSize: 12, itemStyle: { color: t.negative }, data: flagged.map((a) => [a.week_start, a.avg_tone]) },
        { type: "line", markLine: { silent: true, symbol: "none", lineStyle: { color: t.muted, opacity: 0.5, type: "dashed" }, data: [{ yAxis: 0 }], label: { show: false } }, data: [] },
      ],
    };
  }, [fc, an, t]);

  return (
    <div className="space-y-6">
      <PageHeader title="Forecast & early-warning alerts" subtitle="Short-term projection of coverage tone (indicative — read the interval), flagged anomalies, and what the biggest swing is about.">
        <Field label="Entity"><Select value={eid} onChange={setEntity} options={(config?.entities ?? []).map((e) => ({ value: e.id, label: e.name }))} /></Field>
        <Field label="Coverage origin"><Select value={country} onChange={setCountry} options={[{ value: "__all__", label: "All countries" }, ...(config?.countries ?? []).map((x) => ({ value: x.gdelt, label: x.name }))]} /></Field>
      </PageHeader>
      {loading && <Spinner />}
      {error && <EmptyState title="No data" hint={error} />}
      {fc && (
        <>
          <Card className="p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-medium">{entityName(eid)} <Badge tone="accent">{fc.method}</Badge></div>
            <EChart height={420} option={option} />
            <div className="mt-2 text-xs text-muted">{fc.note} Short news series are noisy — read the band, not just the line.</div>
          </Card>

          {an && (
            <Card className="p-4">
              <div className="mb-2 text-sm font-medium text-warning">⚠ Early-warning flags {an.flagged.length > 0 && <Badge tone="warning">{an.flagged.length}</Badge>}</div>
              {an.flagged.length === 0 ? <div className="text-sm text-muted">No statistically unusual weeks at this sensitivity.</div>
                : <div className="space-y-1 text-sm">
                    {an.flagged.map((a) => (
                      <div key={a.week_start} className="flex items-center justify-between">
                        <span>{a.week_start} · <span className="text-muted">{a.kind} {a.direction}</span></span>
                        <span className="tnum text-muted">Δ {a.shift >= 0 ? "+" : ""}{a.shift}</span>
                      </div>
                    ))}
                  </div>}
            </Card>
          )}

          <Card className="p-4">
            <div className="mb-1 text-sm font-medium">🧩 What&apos;s driving the biggest swing?</div>
            {topics?.spike_week
              ? <>
                  <div className="mb-2 text-xs text-muted">Around <b>{topics.spike_week}</b> · {topics.n_titles.toLocaleString()} headlines · topics (LDA):</div>
                  <div className="space-y-1.5">
                    {topics.topics.map((tp, i) => (
                      <div key={i} className="text-sm">
                        <span className="text-muted">Topic {i + 1} ({Math.round(tp.weight * 100)}%): </span>
                        {tp.words.map((w) => <code key={w} className="mr-1 rounded bg-card2 px-1.5 py-0.5 text-xs">{w}</code>)}
                      </div>
                    ))}
                  </div>
                </>
              : <div className="text-sm text-muted">Not enough data to locate a spike.</div>}
          </Card>
          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
