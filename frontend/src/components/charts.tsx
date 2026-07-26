import type { EChartsCoreOption } from "echarts";
import { ChartTheme } from "./echart";

export type Pt = { week_start: string; value: number | null };
export type Series = { name: string; points: Pt[]; color?: string; dashed?: boolean; area?: boolean };

function baseAxisText(t: ChartTheme) {
  return { color: t.muted, fontSize: 11 };
}

export function lineTimeSeries(
  t: ChartTheme,
  series: Series[],
  opts?: { yName?: string; markLines?: { x: string; label: string }[]; showZero?: boolean; legend?: boolean },
): EChartsCoreOption {
  const palette = [t.accent, t.accent2, t.positive, t.negative, "#22d3ee", "#f472b6", "#facc15"];
  const s = series.map((ser, i) => {
    const color = ser.color ?? palette[i % palette.length];
    return {
      name: ser.name,
      type: "line",
      showSymbol: false,
      smooth: 0.25,
      lineStyle: { width: 2.2, type: ser.dashed ? "dashed" : "solid", color },
      itemStyle: { color },
      areaStyle: ser.area ? { color, opacity: 0.12 } : undefined,
      data: ser.points.map((p) => [p.week_start, p.value]),
      z: 3,
    };
  });

  const markLine =
    (opts?.showZero || opts?.markLines?.length)
      ? {
          silent: true,
          symbol: "none",
          label: { show: false },
          lineStyle: { color: t.muted, opacity: 0.5, type: "dashed" as const },
          data: [
            ...(opts?.showZero ? [{ yAxis: 0 }] : []),
            ...((opts?.markLines ?? []).map((m) => ({
              xAxis: m.x,
              label: { show: true, formatter: m.label, color: t.muted, fontSize: 9, rotate: 90, position: "insideEndTop" },
            }))),
          ],
        }
      : undefined;

  if (markLine && s[0]) (s[0] as Record<string, unknown>).markLine = markLine;

  return {
    color: palette,
    grid: { left: 8, right: 16, top: opts?.legend === false ? 16 : 34, bottom: 8, containLabel: true },
    tooltip: {
      trigger: "axis",
      backgroundColor: t.card,
      borderColor: t.border,
      textStyle: { color: t.fg, fontSize: 12 },
      valueFormatter: (v: unknown) => (typeof v === "number" ? v.toFixed(2) : "—"),
    },
    legend: opts?.legend === false ? undefined : { top: 0, textStyle: { color: t.muted, fontSize: 11 }, icon: "roundRect" },
    xAxis: {
      type: "time",
      axisLine: { lineStyle: { color: t.border } },
      axisLabel: baseAxisText(t),
      splitLine: { show: false },
    },
    yAxis: {
      type: "value",
      name: opts?.yName,
      nameTextStyle: { color: t.muted, fontSize: 10 },
      axisLabel: baseAxisText(t),
      splitLine: { lineStyle: { color: t.grid, opacity: 0.35 } },
    },
    series: s,
  };
}

export function horizontalBar(
  t: ChartTheme,
  items: { label: string; value: number; color?: string }[],
  opts?: { xName?: string; colorByTone?: boolean; barColor?: string },
): EChartsCoreOption {
  return {
    grid: { left: 8, right: 40, top: 10, bottom: 8, containLabel: true },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: t.card,
      borderColor: t.border,
      textStyle: { color: t.fg, fontSize: 12 },
    },
    xAxis: {
      type: "value",
      name: opts?.xName,
      nameTextStyle: { color: t.muted, fontSize: 10 },
      axisLabel: baseAxisText(t),
      splitLine: { lineStyle: { color: t.grid, opacity: 0.35 } },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: items.map((i) => i.label),
      axisLine: { lineStyle: { color: t.border } },
      axisLabel: { color: t.fg, fontSize: 11 },
    },
    series: [
      {
        type: "bar",
        data: items.map((i) => ({
          value: i.value,
          itemStyle: {
            color: i.color ?? (opts?.colorByTone ? (i.value >= 0 ? t.accent : t.negative) : opts?.barColor ?? t.accent),
            borderRadius: [0, 4, 4, 0],
          },
        })),
        barMaxWidth: 22,
      },
    ],
  };
}
