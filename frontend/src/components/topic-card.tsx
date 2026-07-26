"use client";

import Link from "next/link";
import type { EChartsCoreOption } from "echarts";
import { EChart, useChartTheme } from "./echart";
import { Badge, cx } from "./ui";
import { fmtSigned, fmtNum, toneColor } from "@/lib/format";

export interface TopicStat {
  id: string; label: string; category: string;
  latest_tone: number; movement: number; recent_volume?: number;
  gap: number | null; spark: number[];
}

function sparkOption(spark: number[], color: string): EChartsCoreOption {
  return {
    grid: { left: 2, right: 2, top: 4, bottom: 2 },
    xAxis: { type: "category", show: false, data: spark.map((_, i) => i) },
    yAxis: { type: "value", show: false, scale: true },
    tooltip: { show: false },
    series: [{ type: "line", data: spark, showSymbol: false, smooth: 0.3,
      lineStyle: { width: 2, color }, areaStyle: { color, opacity: 0.12 } }],
  };
}

export function TopicCard({ t }: { t: TopicStat }) {
  const theme = useChartTheme();
  const up = t.movement >= 0;
  return (
    <Link href={`/topic?q=${encodeURIComponent(t.id)}`}>
      <div className="group h-full rounded-xl border border-border bg-card p-4 transition-colors hover:border-accent/50">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="truncate font-medium group-hover:text-accent">{t.label}</div>
            <Badge>{t.category}</Badge>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold tnum" style={{ color: toneColor(t.latest_tone) }}>{fmtSigned(t.latest_tone)}</div>
            <div className={cx("text-[11px] tnum", up ? "text-positive" : "text-negative")}>{up ? "▲" : "▼"} {fmtSigned(t.movement)}</div>
          </div>
        </div>
        {t.spark?.length > 0 && (
          <div className="mt-2 h-10"><EChart height={40} option={sparkOption(t.spark, toneColor(t.latest_tone))} /></div>
        )}
        <div className="mt-2 flex items-center justify-between text-[11px] text-muted">
          {t.recent_volume !== undefined && <span>{fmtNum(t.recent_volume)} recent articles</span>}
          {t.gap !== null && <span>gap {fmtSigned(t.gap)}</span>}
        </div>
      </div>
    </Link>
  );
}
