"use client";

import { useEffect, useMemo, useState } from "react";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { lineTimeSeries } from "@/components/charts";
import { Card, PageHeader, StatTile, Select, Field, Spinner, EmptyState, DISCLAIMER } from "@/components/ui";
import { fmtSigned, fmtNum } from "@/lib/format";

interface Ev { date: string; scope_type: string; scope_id: string; label: string; }
interface Impact {
  entity: string; country: string; event_date: string;
  before_tone: number | null; after_tone: number | null; delta: number | null;
  n_before: number; n_after: number; vol_before: number; vol_after: number;
  p_value: number | null; note: string;
}
interface Point { week_start: string; avg_tone: number; }
interface TS { aggregate: Point[]; }

export default function EventImpactPage() {
  const { config, entityName } = useConfig();
  const { data: events } = useApi<Ev[]>("/api/events");
  const [evIdx, setEvIdx] = useState(0);
  const [entity, setEntity] = useState<string>("");
  const [country, setCountry] = useState("__all__");
  const t = useChartTheme();

  const ev = events?.[evIdx];
  useEffect(() => {
    if (ev?.scope_type === "entity") setEntity(ev.scope_id);
    if (ev?.scope_type === "country") setCountry(ev.scope_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [evIdx, events]);

  const eid = entity || config?.entities[0]?.id || "";
  const c = country === "__all__" ? undefined : country;
  const eventDate = ev?.date;

  const { data, loading, error } = useApi<Impact>(eid && eventDate ? "/api/event-impact" : null, { entity: eid, event_date: eventDate, country: c, window_weeks: 3 });
  const { data: ts } = useApi<TS>(eid ? "/api/timeseries" : null, { entity: eid, countries: c });

  const option = useMemo(() => {
    if (!ts || !eventDate) return {};
    return lineTimeSeries(t, [{ name: entityName(eid), points: ts.aggregate.map((p) => ({ week_start: p.week_start, value: p.avg_tone })) }],
      { yName: "tone", showZero: true, legend: false, markLines: [{ x: eventDate, label: "event" }] });
  }, [ts, eventDate, t, eid, entityName]);

  return (
    <div className="space-y-6">
      <PageHeader title="Event impact scoring" subtitle="Coverage tone before vs after an event — an association around a date, not proof of causation.">
        <Field label="Event"><Select value={String(evIdx)} onChange={(v) => setEvIdx(Number(v))} options={(events ?? []).map((e, i) => ({ value: String(i), label: `${e.date} — ${e.label}` }))} /></Field>
        <Field label="Entity"><Select value={eid} onChange={setEntity} options={(config?.entities ?? []).map((e) => ({ value: e.id, label: e.name }))} /></Field>
        <Field label="Coverage origin"><Select value={country} onChange={setCountry} options={[{ value: "__all__", label: "All countries" }, ...(config?.countries ?? []).map((x) => ({ value: x.gdelt, label: x.name }))]} /></Field>
      </PageHeader>
      {loading && <Spinner />}
      {error && <EmptyState title="No data" hint={error} />}
      {data && (
        <>
          <div className="grid grid-cols-3 gap-3">
            <StatTile label={`Tone before (${data.n_before} wks)`} value={fmtSigned(data.before_tone)} sub={`${fmtNum(data.vol_before)} articles`} />
            <StatTile label={`Tone after (${data.n_after} wks)`} value={fmtSigned(data.after_tone)} sub={`${fmtNum(data.vol_after)} articles`} />
            <StatTile label="Δ tone (after − before)" value={fmtSigned(data.delta)} accent={data.delta != null && data.delta >= 0 ? t.positive : t.negative} />
          </div>
          {data.p_value != null && (
            <div className="text-xs text-muted">Welch t-test p = {data.p_value.toFixed(3)} — the shift is {data.p_value < 0.05 ? "likely meaningful" : "not statistically clear"} given weekly variability.</div>
          )}
          <Card className="p-4">
            <div className="mb-2 text-sm font-medium">{entityName(eid)} · event {eventDate}</div>
            <EChart height={400} option={option} />
          </Card>
          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
