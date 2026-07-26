"use client";

import { useMemo, useState } from "react";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { horizontalBar } from "@/components/charts";
import { Card, PageHeader, StatTile, Select, Field, Spinner, EmptyState, DISCLAIMER } from "@/components/ui";
import { useWindow, WindowControls } from "@/components/controls";
import { fmtNum } from "@/lib/format";

interface Row { country: string; country_name: string; avg_tone: number; article_volume: number; source_diversity: number; }
interface Drill { theme: string; total_articles: number; countries_covering: number; ranking: Row[]; }

export default function IssuesPage() {
  const { config, entityName } = useConfig();
  const { w0, w1, setW0, setW1 } = useWindow(config?.weeks);
  const themes = (config?.entities ?? []).filter((e) => e.type === "theme");
  const [theme, setTheme] = useState<string>("");
  const t = useChartTheme();
  const tid = theme || themes[0]?.id || "";

  const { data, loading, error } = useApi<Drill>(tid ? "/api/issue-drilldown" : null, { theme: tid, w0, w1, top_n: 15 });

  const option = useMemo(() => {
    if (!data) return {};
    return horizontalBar(t, data.ranking.map((r) => ({ label: r.country_name, value: r.article_volume, color: r.avg_tone >= 0 ? t.accent : t.negative })), { xName: "article volume (attention)" });
  }, [data, t]);

  return (
    <div className="space-y-6">
      <PageHeader title="Issue drill-down" subtitle="For an issue: which countries cover it most (bar length), and how they frame it (color = tone).">
        <Field label="Issue / theme"><Select value={tid} onChange={setTheme} options={themes.map((e) => ({ value: e.id, label: e.name }))} /></Field>
        <WindowControls weeks={config?.weeks} w0={w0} w1={w1} setW0={setW0} setW1={setW1} />
      </PageHeader>
      {loading && <Spinner />}
      {error && <EmptyState title="No data" hint={error} />}
      {data && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <StatTile label="Countries covering this issue" value={data.countries_covering} />
            <StatTile label="Total articles (window)" value={fmtNum(data.total_articles)} />
          </div>
          <Card className="p-4">
            <div className="mb-2 text-sm font-medium">{entityName(tid)} — coverage by country</div>
            <EChart height={Math.max(320, data.ranking.length * 26)} option={option} />
            <div className="mt-2 text-xs text-muted">Blue bars = net-positive coverage · red = net-negative.</div>
          </Card>
          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
