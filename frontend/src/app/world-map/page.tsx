"use client";

import { useEffect, useMemo, useState } from "react";
import * as echarts from "echarts";
import { useApi } from "@/lib/useApi";
import { useConfig } from "@/components/config-context";
import { EChart, useChartTheme } from "@/components/echart";
import { Card, PageHeader, StatTile, Select, Field, Spinner, EmptyState, DISCLAIMER } from "@/components/ui";
import { useWindow, WindowControls } from "@/components/controls";
import { fmtSigned, fmtNum, toneColor } from "@/lib/format";

interface MapRow {
  country: string; country_name: string; iso3: string;
  avg_tone: number; article_volume: number; source_diversity: number;
  low_conf_weeks: number; n_weeks: number;
}
interface MapResp { entity: string; global_tone: number; countries: MapRow[]; }

// GeoJSON uses "Korea" for South Korea; everything else matches by name.
const NAME_FIX: Record<string, string> = { "South Korea": "Korea" };

export default function WorldMapPage() {
  const { config, entityOptions } = useConfig();
  const { w0, w1, setW0, setW1 } = useWindow(config?.weeks);
  const [entity, setEntity] = useState("__all__");
  const [mapReady, setMapReady] = useState(false);
  const t = useChartTheme();

  useEffect(() => {
    let alive = true;
    fetch("/world.json")
      .then((r) => r.json())
      .then((geo) => { if (alive) { echarts.registerMap("world", geo); setMapReady(true); } })
      .catch(() => setMapReady(false));
    return () => { alive = false; };
  }, []);

  const { data, loading, error } = useApi<MapResp>("/api/map", { entity, w0, w1 });

  const option = useMemo(() => {
    if (!data) return {};
    const rows = data.countries;
    const clip = Math.max(1, ...rows.map((r) => Math.abs(r.avg_tone)));
    const byName: Record<string, MapRow> = {};
    const seriesData = rows.map((r) => {
      const name = NAME_FIX[r.country_name] ?? r.country_name;
      byName[name] = r;
      return { name, value: r.avg_tone };
    });
    return {
      tooltip: {
        trigger: "item",
        backgroundColor: t.card, borderColor: t.border, textStyle: { color: t.fg, fontSize: 12 },
        formatter: (p: { name: string; value: number }) => {
          const r = byName[p.name];
          if (!r || p.value == null || Number.isNaN(p.value)) return `${p.name}<br/>no data`;
          return `<b>${r.country_name}</b><br/>Tone: ${fmtSigned(r.avg_tone)}<br/>` +
            `Articles: ${fmtNum(r.article_volume)}<br/>Outlets: ${r.source_diversity}<br/>` +
            `Low-conf weeks: ${r.low_conf_weeks}/${r.n_weeks}`;
        },
      },
      visualMap: {
        min: -clip, max: clip, calculable: true, orient: "horizontal", left: "center", bottom: 8,
        inRange: { color: [t.negative, "#7d8597", t.accent] },
        textStyle: { color: t.muted, fontSize: 11 }, text: ["positive", "negative"],
      },
      series: [{
        type: "map", map: "world", roam: false,
        data: seriesData,
        itemStyle: { areaColor: t.card2, borderColor: t.border, borderWidth: 0.4 },
        emphasis: { itemStyle: { areaColor: t.accent2 }, label: { show: false } },
        select: { itemStyle: { areaColor: t.accent2 }, label: { show: false } },
      }],
    } as echarts.EChartsCoreOption;
  }, [data, t]);

  const extremes = useMemo(() => {
    if (!data || !data.countries.length) return null;
    const s = [...data.countries].sort((a, b) => a.avg_tone - b.avg_tone);
    return { neg: s[0], pos: s[s.length - 1] };
  }, [data]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="World map"
        subtitle="Average media coverage tone per country — blue = more positive, red = more negative."
      >
        <Field label="Entity"><Select value={entity} onChange={setEntity} options={entityOptions({ includeAll: true })} /></Field>
        <WindowControls weeks={config?.weeks} w0={w0} w1={w1} setW0={setW0} setW1={setW1} />
      </PageHeader>

      {(loading || !mapReady) && <Spinner label={mapReady ? "Loading…" : "Loading map…"} />}
      {error && <EmptyState title="Couldn't load map" hint={error} />}

      {data && mapReady && (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <StatTile label="Global tone (selection)" value={fmtSigned(data.global_tone)} accent={toneColor(data.global_tone)} />
            {extremes && <StatTile label="Most negative" value={extremes.neg.country_name} sub={fmtSigned(extremes.neg.avg_tone)} />}
            {extremes && <StatTile label="Most positive" value={extremes.pos.country_name} sub={fmtSigned(extremes.pos.avg_tone)} />}
          </div>
          <Card className="p-2">
            <EChart height={520} option={option} />
          </Card>
          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
