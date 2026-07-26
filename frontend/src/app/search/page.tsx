"use client";

import { useState } from "react";
import type { EChartsCoreOption } from "echarts";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { Card, PageHeader, Spinner, EmptyState, Badge, DISCLAIMER } from "@/components/ui";
import { fmtSigned, toneColor } from "@/lib/format";

interface Result {
  id: string; name: string; type: string; home_country: string | null; aliases: string[];
  latest: number | null; delta: number | null; spark: { week_start: string; avg_tone: number }[];
}
interface SearchResp { query: string; count: number; results: Result[]; }

function spark(points: { week_start: string; avg_tone: number }[], color: string): EChartsCoreOption {
  return {
    grid: { left: 2, right: 2, top: 4, bottom: 2 },
    xAxis: { type: "time", show: false }, yAxis: { type: "value", show: false, scale: true },
    tooltip: { show: false },
    series: [{ type: "line", showSymbol: false, smooth: 0.3, lineStyle: { width: 2, color }, areaStyle: { color, opacity: 0.12 }, data: points.map((p) => [p.week_start, p.avg_tone]) }],
  };
}

export default function SearchPage() {
  const { countryName } = useConfig();
  const [q, setQ] = useState("");
  const t = useChartTheme();
  const { data, loading } = useApi<SearchResp>("/api/search", { q });

  return (
    <div className="space-y-6">
      <PageHeader title="Search" subtitle="Find any tracked figure, party or issue by name or alias — with its current coverage tone." />
      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="e.g. Modi, climate, inflation, party…"
        className="h-11 w-full rounded-lg border border-border bg-card px-4 text-sm outline-none focus:border-accent/60" />
      {loading && <Spinner />}
      {data && data.results.length === 0 && <EmptyState title={`No matches for “${q}”`} hint="Add it to config/watchlist.yaml and re-run the pipeline." />}
      <div className="grid gap-3 md:grid-cols-2">
        {data?.results.map((r) => (
          <Card key={r.id} className="flex items-center gap-4 p-4">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate font-medium">{r.name}</span>
                <Badge>{r.type}</Badge>
              </div>
              <div className="mt-0.5 text-xs text-muted">
                {r.home_country ? `home ${countryName(r.home_country)}` : "cross-cutting"}
                {r.aliases.length > 0 && ` · aka ${r.aliases.join(", ")}`}
              </div>
            </div>
            <div className="w-28 shrink-0">
              {r.spark.length > 0 && <EChart height={44} option={spark(r.spark, toneColor(r.latest))} />}
            </div>
            <div className="w-16 shrink-0 text-right tnum">
              <div className="text-sm" style={{ color: toneColor(r.latest) }}>{fmtSigned(r.latest)}</div>
              {r.delta != null && <div className="text-[11px] text-muted">{fmtSigned(r.delta)}</div>}
            </div>
          </Card>
        ))}
      </div>
      <p className="text-xs text-muted">{DISCLAIMER}</p>
    </div>
  );
}
