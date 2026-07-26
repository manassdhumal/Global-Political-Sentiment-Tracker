"use client";

import { useMemo, useState } from "react";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { lineTimeSeries } from "@/components/charts";
import { Card, PageHeader, StatTile, Select, MultiSelect, Field, Segmented, Spinner, EmptyState, DISCLAIMER } from "@/components/ui";
import { useWindow, WindowControls } from "@/components/controls";
import { fmtSigned, fmtNum, toneColor } from "@/lib/format";

interface Point { week_start: string; avg_tone: number; article_volume: number; source_diversity: number; low_confidence: number; }
interface TS {
  entity: string; countries: string[]; aggregate: Point[];
  by_country: Record<string, Point[]>;
  total_articles: number; max_source_diversity: number; low_confidence_weeks: number;
}
interface Ev { date: string; scope_type: string; scope_id: string; label: string; }

export default function TonePage() {
  const { config, entityName, countryName } = useConfig();
  const { w0, w1, setW0, setW1 } = useWindow(config?.weeks);
  const [entity, setEntity] = useState<string>("");
  const [countries, setCountries] = useState<string[]>([]);
  const [mode, setMode] = useState("aggregate");
  const t = useChartTheme();

  const eid = entity || config?.entities[0]?.id || "";
  const countryParam = countries.length ? countries.join(",") : undefined;
  const { data, loading, error } = useApi<TS>(eid ? "/api/timeseries" : null, { entity: eid, countries: countryParam, w0, w1 });
  const { data: events } = useApi<Ev[]>("/api/events");

  const countryOpts = useMemo(
    () => (config?.countries ?? []).map((c) => ({ value: c.gdelt, label: c.name })),
    [config],
  );

  const option = useMemo(() => {
    if (!data) return {};
    const marks = (events ?? [])
      .filter((e) => e.scope_type === "global" || (e.scope_type === "entity" && e.scope_id === eid))
      .map((e) => ({ x: e.date, label: e.label }));
    if (mode === "split") {
      const series = Object.entries(data.by_country).map(([c, pts]) => ({
        name: countryName(c),
        points: pts.map((p) => ({ week_start: p.week_start, value: p.avg_tone })),
      }));
      return lineTimeSeries(t, series, { yName: "tone", showZero: true, markLines: marks });
    }
    return lineTimeSeries(
      t,
      [{ name: "All selected (weighted)", points: data.aggregate.map((p) => ({ week_start: p.week_start, value: p.avg_tone })) }],
      { yName: "tone", showZero: true, markLines: marks, legend: false },
    );
  }, [data, events, mode, t, eid, countryName]);

  const last = data?.aggregate.at(-1)?.avg_tone ?? null;
  const first = data?.aggregate[0]?.avg_tone ?? null;

  return (
    <div className="space-y-6">
      <PageHeader title="Tone over time" subtitle="Weekly media coverage tone for one entity, with known events marked.">
        <Field label="Entity"><Select value={eid} onChange={setEntity} options={(config?.entities ?? []).map((e) => ({ value: e.id, label: e.name }))} /></Field>
        <Field label="Countries"><MultiSelect options={countryOpts} value={countries} onChange={setCountries} placeholder="All countries" /></Field>
        <Field label="View"><Segmented value={mode} onChange={setMode} options={[{ value: "aggregate", label: "Combined" }, { value: "split", label: "By country" }]} /></Field>
        <WindowControls weeks={config?.weeks} w0={w0} w1={w1} setW0={setW0} setW1={setW1} />
      </PageHeader>

      {loading && <Spinner />}
      {error && <EmptyState title="No data" hint={error} />}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile label="Latest weekly tone" value={fmtSigned(last)} accent={toneColor(last)} sub={first != null && last != null ? `${fmtSigned(last - first)} vs start` : undefined} />
            <StatTile label="Articles in window" value={fmtNum(data.total_articles)} />
            <StatTile label="Max source diversity" value={`${data.max_source_diversity} outlets`} />
            <StatTile label="Low-confidence weeks" value={data.low_confidence_weeks} />
          </div>
          <Card className="p-4">
            <div className="mb-2 text-sm font-medium">{entityName(eid)} — media coverage tone</div>
            <EChart height={420} option={option} />
          </Card>
          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
