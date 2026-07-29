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

  const opts = (catalog?.topics ?? []).map((x) => ({ value: x.id, label: x.label }));

  return (
    <div className="space-y-6">
      <PageHeader title="Compare topics" subtitle="Overlay the sentiment history of several topics — media coverage tone or public/social sentiment.">
        <Field label="Topics (up to 5)"><MultiSelect options={opts} value={selected} onChange={(v) => setSelected(v.slice(0, 5))} placeholder="Pick topics" /></Field>
        <Field label="Metric"><Segmented value={metric} onChange={setMetric} options={[{ value: "media", label: "Media" }, { value: "public", label: "Public" }]} /></Field>
      </PageHeader>

      {selected.length === 0 && <EmptyState title="Pick at least one topic to compare" />}
      {loading && <Spinner label="Analyzing topics…" />}
      {error && <EmptyState title="Couldn't load comparison" hint={error} onRetry={reload} />}

      {data && (
        <>
          <Card className="p-4"><EChart height={440} option={option} /></Card>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.topics.map((tp) => (
              <StatTile key={tp.id} label={tp.label}
                value={fmtSigned(metric === "media" ? tp.avg_media : tp.avg_public)}
                sub={`media↔public gap ${fmtSigned(tp.avg_gap)}`} />
            ))}
          </div>
          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
