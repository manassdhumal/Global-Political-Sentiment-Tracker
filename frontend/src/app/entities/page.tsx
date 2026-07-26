"use client";

import { useEffect, useMemo, useState } from "react";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { lineTimeSeries } from "@/components/charts";
import { Card, PageHeader, Select, MultiSelect, Field, Spinner, EmptyState, DISCLAIMER } from "@/components/ui";
import { useWindow, WindowControls } from "@/components/controls";

interface Point { week_start: string; avg_tone: number; }
interface Cmp { entities: string[]; country: string; series: Record<string, Point[]>; }

export default function EntitiesPage() {
  const { config, entityName } = useConfig();
  const { w0, w1, setW0, setW1 } = useWindow(config?.weeks);
  const [entities, setEntities] = useState<string[]>([]);
  const [country, setCountry] = useState("__all__");
  const t = useChartTheme();

  useEffect(() => {
    if (config && entities.length === 0) setEntities(config.entities.slice(0, 3).map((e) => e.id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config]);

  const { data, loading, error } = useApi<Cmp>(entities.length ? "/api/entity-compare" : null, {
    entities: entities.join(","), country: country === "__all__" ? undefined : country, w0, w1,
  });

  const option = useMemo(() => {
    if (!data) return {};
    const series = Object.entries(data.series).map(([id, pts]) => ({
      name: entityName(id), points: pts.map((p) => ({ week_start: p.week_start, value: p.avg_tone })),
    }));
    return lineTimeSeries(t, series, { yName: "tone", showZero: true });
  }, [data, t, entityName]);

  return (
    <div className="space-y-6">
      <PageHeader title="Entity vs entity" subtitle="Compare several figures / parties / issues side by side — globally or within one country.">
        <Field label="Entities"><MultiSelect options={(config?.entities ?? []).map((e) => ({ value: e.id, label: e.name }))} value={entities} onChange={setEntities} /></Field>
        <Field label="Coverage origin"><Select value={country} onChange={setCountry} options={[{ value: "__all__", label: "All countries" }, ...(config?.countries ?? []).map((c) => ({ value: c.gdelt, label: c.name }))]} /></Field>
        <WindowControls weeks={config?.weeks} w0={w0} w1={w1} setW0={setW0} setW1={setW1} />
      </PageHeader>
      {loading && <Spinner />}
      {error && <EmptyState title="No data" hint={error} />}
      {!entities.length && <EmptyState title="Pick at least one entity" />}
      {data && (
        <Card className="p-4">
          <div className="mb-2 text-sm font-medium">Coverage tone · {country === "__all__" ? "all countries" : config?.countries.find((c) => c.gdelt === country)?.name}</div>
          <EChart height={460} option={option} />
        </Card>
      )}
      <p className="text-xs text-muted">{DISCLAIMER}</p>
    </div>
  );
}
