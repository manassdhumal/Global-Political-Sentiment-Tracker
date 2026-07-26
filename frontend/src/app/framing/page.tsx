"use client";

import { useMemo, useState } from "react";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { horizontalBar } from "@/components/charts";
import { Card, PageHeader, StatTile, Select, Field, Spinner, EmptyState, DISCLAIMER } from "@/components/ui";
import { useWindow, WindowControls } from "@/components/controls";
import { fmtSigned, fmtNum } from "@/lib/format";

interface Lang { language: string; n: number; avg_tone: number; outlets: number; low_confidence: boolean; }
interface DVF { domestic_tone: number | null; domestic_vol: number; foreign_tone: number | null; foreign_vol: number; gap: number | null; }
interface Framing { entity: string; home_country: string | null; domestic_vs_foreign: DVF; by_language: Lang[]; }

export default function FramingPage() {
  const { config, entityName, countryName } = useConfig();
  const { w0, w1, setW0, setW1 } = useWindow(config?.weeks);
  const [entity, setEntity] = useState<string>("");
  const t = useChartTheme();
  const eid = entity || config?.entities[0]?.id || "";

  const { data, loading, error } = useApi<Framing>(eid ? "/api/framing" : null, { entity: eid, w0, w1 });

  const option = useMemo(() => {
    if (!data) return {};
    return horizontalBar(t, data.by_language.map((l) => ({ label: `${l.language} (n=${fmtNum(l.n)})`, value: l.avg_tone })), { xName: "coverage tone", colorByTone: true });
  }, [data, t]);

  return (
    <div className="space-y-6">
      <PageHeader title="Cross-language framing" subtitle="Same entity, different presses. Domestic vs foreign coverage and tone by language — differences in media framing, not public belief.">
        <Field label="Entity"><Select value={eid} onChange={setEntity} options={(config?.entities ?? []).map((e) => ({ value: e.id, label: e.name }))} /></Field>
        <WindowControls weeks={config?.weeks} w0={w0} w1={w1} setW0={setW0} setW1={setW1} />
      </PageHeader>
      {loading && <Spinner />}
      {error && <EmptyState title="No data" hint={error} />}
      {data && (
        <>
          <div className="text-sm text-muted">{entityName(eid)} · home country: {data.home_country ? countryName(data.home_country) : "none (theme)"}</div>
          <div className="grid grid-cols-3 gap-3">
            <StatTile label="Domestic press tone" value={fmtSigned(data.domestic_vs_foreign.domestic_tone)} sub={`${fmtNum(data.domestic_vs_foreign.domestic_vol)} articles`} />
            <StatTile label="Foreign press tone" value={fmtSigned(data.domestic_vs_foreign.foreign_tone)} sub={`${fmtNum(data.domestic_vs_foreign.foreign_vol)} articles`} />
            <StatTile label="Framing gap (dom − for)" value={fmtSigned(data.domestic_vs_foreign.gap)} accent={data.domestic_vs_foreign.gap != null && data.domestic_vs_foreign.gap >= 0 ? t.positive : t.negative} />
          </div>
          <Card className="p-4">
            <div className="mb-2 text-sm font-medium">Coverage tone by source language</div>
            <EChart height={Math.max(300, data.by_language.length * 26)} option={option} />
          </Card>
          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
