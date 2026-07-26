"use client";

import { useMemo, useState } from "react";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { horizontalBar } from "@/components/charts";
import { Card, PageHeader, Segmented, Field, Spinner, EmptyState, DISCLAIMER } from "@/components/ui";
import { useWindow, WindowControls } from "@/components/controls";

interface Row {
  entity_id?: string; entity_name?: string; country?: string; country_name?: string;
  volatility: number; mean_tone: number; tone_range: number; n_weeks: number; article_volume: number;
}
interface Vol { group: string; ranking: Row[]; }

export default function VolatilityPage() {
  const { config } = useConfig();
  const { w0, w1, setW0, setW1 } = useWindow(config?.weeks);
  const [group, setGroup] = useState("entity");
  const t = useChartTheme();

  const { data, loading, error } = useApi<Vol>("/api/volatility", { group, w0, w1, min_weeks: 4, top_n: 18 });

  const label = (r: Row) =>
    group === "entity" ? r.entity_name ?? r.entity_id ?? ""
    : group === "country" ? r.country_name ?? r.country ?? ""
    : `${r.entity_name ?? r.entity_id} · ${r.country_name ?? r.country}`;

  const option = useMemo(() => {
    if (!data) return {};
    return horizontalBar(t, data.ranking.map((r) => ({ label: label(r), value: r.volatility })), { xName: "volatility — σ of weekly tone", barColor: t.accent2 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, t, group]);

  return (
    <div className="space-y-6">
      <PageHeader title="Sentiment volatility index" subtitle="Most volatile coverage — the largest week-to-week swings (standard deviation of weekly tone).">
        <Field label="Group by"><Segmented value={group} onChange={setGroup} options={[{ value: "entity", label: "Entity" }, { value: "country", label: "Country" }, { value: "entity_country", label: "Entity × country" }]} /></Field>
        <WindowControls weeks={config?.weeks} w0={w0} w1={w1} setW0={setW0} setW1={setW1} />
      </PageHeader>
      {loading && <Spinner />}
      {error && <EmptyState title="No data" hint={error} />}
      {data && (
        <Card className="p-4">
          <EChart height={Math.max(320, data.ranking.length * 26)} option={option} />
        </Card>
      )}
      <p className="text-xs text-muted">{DISCLAIMER}</p>
    </div>
  );
}
