"use client";

import { useApi } from "@/lib/useApi";
import { EChart, useChartTheme } from "@/components/echart";
import { horizontalBar } from "@/components/charts";
import { Card, PageHeader, StatTile, Spinner, EmptyState, Banner, Badge, DISCLAIMER, cx } from "@/components/ui";
import { useConfig } from "@/components/config-context";
import { fmtNum, fmtSigned, toneColor } from "@/lib/format";

interface Mover { entity_id: string; name: string; type: string; latest: number; delta: number; volume: number; anomaly: boolean; }
interface Mood {
  global_tone: number; total_articles: number; n_entities: number; n_countries: number;
  latest_week: string; improving: Mover[]; worsening: Mover[]; ranking: Mover[]; alerts: Mover[];
}

function MoverRow({ m }: { m: Mover }) {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="min-w-0">
        <div className="truncate text-sm">{m.name}</div>
        <div className="text-[11px] text-muted">{m.type}</div>
      </div>
      <div className="flex items-center gap-3 tnum">
        <span className="text-sm" style={{ color: toneColor(m.latest) }}>{fmtSigned(m.latest)}</span>
        <span className={cx("text-xs", m.delta >= 0 ? "text-positive" : "text-negative")}>{fmtSigned(m.delta)}</span>
      </div>
    </div>
  );
}

export default function HomePage() {
  const { config } = useConfig();
  const { data, loading, error } = useApi<Mood>("/api/mood");
  const t = useChartTheme();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Political mood"
        subtitle="A weekly read on the tone of world news coverage across all tracked entities and countries — media sentiment, not public opinion."
      />
      {config?.synthetic && <Banner>⚠ Running on synthetic (fabricated) demo data — not real coverage.</Banner>}
      {loading && <Spinner />}
      {error && <EmptyState title="Couldn't load data" hint={error + " — is the API running on :8000?"} />}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatTile label="Global coverage tone" value={fmtSigned(data.global_tone)} accent={toneColor(data.global_tone)} />
            <StatTile label="Articles tracked" value={fmtNum(data.total_articles)} />
            <StatTile label="Entities × countries" value={`${data.n_entities} × ${data.n_countries}`} />
            <StatTile label="Latest week" value={data.latest_week} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="p-4">
              <div className="mb-1 text-sm font-medium text-positive">▲ Improving coverage</div>
              <div className="divide-y divide-border">
                {data.improving.map((m) => <MoverRow key={m.entity_id} m={m} />)}
              </div>
            </Card>
            <Card className="p-4">
              <div className="mb-1 text-sm font-medium text-negative">▼ Worsening coverage</div>
              <div className="divide-y divide-border">
                {data.worsening.map((m) => <MoverRow key={m.entity_id} m={m} />)}
              </div>
            </Card>
          </div>

          <Card className="p-4">
            <div className="mb-3 text-sm font-medium">Where each entity stands (latest week)</div>
            <EChart
              height={Math.max(320, data.ranking.length * 22)}
              option={horizontalBar(t, data.ranking.map((m) => ({ label: m.name, value: m.latest })), { xName: "Latest weekly tone (−100 … +100)", colorByTone: true })}
            />
          </Card>

          {data.alerts.length > 0 && (
            <Card className="p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-medium text-warning">
                ⚠ Early-warning flags <Badge tone="warning">{data.alerts.length}</Badge>
              </div>
              <div className="space-y-1 text-sm">
                {data.alerts.map((m) => (
                  <div key={m.entity_id} className="flex items-center justify-between">
                    <span>{m.name}</span>
                    <span className="tnum text-muted">{fmtSigned(m.latest)} ({fmtSigned(m.delta)} vs prior)</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
