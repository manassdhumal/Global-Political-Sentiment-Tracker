"use client";

import { useEffect, useMemo, useState } from "react";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { lineTimeSeries } from "@/components/charts";
import { Card, PageHeader, Select, MultiSelect, Field, Spinner, EmptyState, DISCLAIMER } from "@/components/ui";
import { useWindow, WindowControls } from "@/components/controls";

interface Point { week_start: string; avg_tone: number; }
interface TS { entity: string; by_country: Record<string, Point[]>; }

export default function CrossCountryPage() {
  const { config, entityName, countryName } = useConfig();
  const { w0, w1, setW0, setW1 } = useWindow(config?.weeks);
  const [entity, setEntity] = useState<string>("");
  const [countries, setCountries] = useState<string[]>([]);
  const t = useChartTheme();

  useEffect(() => {
    if (config && countries.length === 0) {
      setCountries(config.countries.slice(0, 5).map((c) => c.gdelt));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [config]);

  const eid = entity || config?.entities[0]?.id || "";
  const { data, loading, error } = useApi<TS>(eid && countries.length ? "/api/timeseries" : null, { entity: eid, countries: countries.join(",") || undefined, w0, w1 });

  const option = useMemo(() => {
    if (!data) return {};
    const series = Object.entries(data.by_country).map(([c, pts]) => ({
      name: countryName(c), points: pts.map((p) => ({ week_start: p.week_start, value: p.avg_tone })),
    }));
    return lineTimeSeries(t, series, { yName: "tone", showZero: true });
  }, [data, t, countryName]);

  return (
    <div className="space-y-6">
      <PageHeader title="Cross-country comparison" subtitle="One entity's coverage tone across countries — domestic vs foreign framing often diverges.">
        <Field label="Entity / issue"><Select value={eid} onChange={setEntity} options={(config?.entities ?? []).map((e) => ({ value: e.id, label: e.name }))} /></Field>
        <Field label="Countries"><MultiSelect options={(config?.countries ?? []).map((c) => ({ value: c.gdelt, label: c.name }))} value={countries} onChange={setCountries} /></Field>
        <WindowControls weeks={config?.weeks} w0={w0} w1={w1} setW0={setW0} setW1={setW1} />
      </PageHeader>
      {loading && <Spinner />}
      {error && <EmptyState title="No data" hint={error} />}
      {!countries.length && <EmptyState title="Pick at least one country" />}
      {data && (
        <Card className="p-4">
          <div className="mb-2 text-sm font-medium">{entityName(eid)} — coverage tone by country</div>
          <EChart height={460} option={option} />
        </Card>
      )}
      <p className="text-xs text-muted">{DISCLAIMER}</p>
    </div>
  );
}
