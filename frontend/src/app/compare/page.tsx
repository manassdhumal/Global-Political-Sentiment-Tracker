"use client";

import { useMemo, useState } from "react";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { lineTimeSeries, horizontalBar } from "@/components/charts";
import { Card, PageHeader, StatTile, Select, Field, Spinner, EmptyState, Banner, DISCLAIMER } from "@/components/ui";
import { fmtSigned } from "@/lib/format";

interface Row { week_start: string; media_tone: number | null; public_sentiment: number | null; gap: number | null; }
interface Compare { entity: string; series: Row[]; avg_media: number | null; avg_public: number | null; avg_gap: number | null; }
interface DivRow { entity_id: string; name: string; media_tone: number; public_sentiment: number; gap: number; weeks: number; }
interface Div { available: boolean; ranking: DivRow[]; }
interface Status { available: boolean; sources: string[]; }

export default function ComparePage() {
  const { config, entityName } = useConfig();
  const [entity, setEntity] = useState<string>("");
  const t = useChartTheme();
  const eid = entity || config?.entities[0]?.id || "";

  const { data: status } = useApi<Status>("/api/opinion/status");
  const { data, loading, error } = useApi<Compare>(eid ? "/api/compare/media-vs-public" : null, { entity: eid });
  const { data: div } = useApi<Div>("/api/compare/divergence");

  const lineOption = useMemo(() => {
    if (!data) return {};
    return lineTimeSeries(t, [
      { name: "Media (coverage tone)", points: data.series.map((r) => ({ week_start: r.week_start, value: r.media_tone })), color: t.accent },
      { name: "Public (social sentiment)", points: data.series.map((r) => ({ week_start: r.week_start, value: r.public_sentiment })), color: t.accent2 },
    ], { yName: "sentiment", showZero: true });
  }, [data, t]);

  const divOption = useMemo(() => {
    if (!div?.ranking?.length) return {};
    const items = div.ranking.slice(0, 12).map((r) => ({ label: r.name, value: r.gap }));
    return horizontalBar(t, items, { xName: "gap  (public − media)", colorByTone: true });
  }, [div, t]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Media vs Public"
        subtitle="Where press coverage tone and public/social sentiment diverge. The gap (public − media) is the signal — neither is representative public opinion."
      >
        <Field label="Entity"><Select value={eid} onChange={setEntity} options={(config?.entities ?? []).map((e) => ({ value: e.id, label: e.name }))} /></Field>
      </PageHeader>

      {status && !status.available && (
        <Banner tone="accent">No public-opinion data yet. Run <code>python scripts/run_opinion_pipeline.py</code> to populate it.</Banner>
      )}
      {loading && <Spinner />}
      {error && <EmptyState title="No comparison data" hint={error} />}

      {data && (
        <>
          <div className="grid grid-cols-3 gap-3">
            <StatTile label="Avg media tone" value={fmtSigned(data.avg_media)} accent={t.accent} />
            <StatTile label="Avg public sentiment" value={fmtSigned(data.avg_public)} accent={t.accent2} />
            <StatTile label="Avg gap (public − media)" value={fmtSigned(data.avg_gap)} accent={data.avg_gap != null && data.avg_gap >= 0 ? t.positive : t.negative} />
          </div>
          <Card className="p-4">
            <div className="mb-2 text-sm font-medium">{entityName(eid)} — media vs public over time</div>
            <EChart height={420} option={lineOption} />
          </Card>
        </>
      )}

      {div?.available && div.ranking.length > 0 && (
        <Card className="p-4">
          <div className="mb-1 text-sm font-medium">Biggest divergences (all entities)</div>
          <div className="mb-3 text-xs text-muted">Positive = public warmer than the press; negative = public harsher.</div>
          <EChart height={Math.max(300, Math.min(div.ranking.length, 12) * 26)} option={divOption} />
        </Card>
      )}

      <p className="text-xs text-muted">{DISCLAIMER}</p>
    </div>
  );
}
