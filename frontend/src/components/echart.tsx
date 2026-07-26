"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import { useTheme } from "next-themes";

export interface ChartTheme {
  fg: string; muted: string; border: string; card: string; card2: string;
  accent: string; accent2: string; positive: string; negative: string;
  grid: string;
}

/** Resolve current CSS-variable colors (re-runs when the theme changes). */
export function useChartTheme(): ChartTheme {
  const { resolvedTheme } = useTheme();
  // read fresh each render; resolvedTheme in deps of callers triggers recompute
  const v = (n: string, fb: string) =>
    (typeof window !== "undefined"
      ? getComputedStyle(document.documentElement).getPropertyValue(n).trim()
      : "") || fb;
  void resolvedTheme;
  return {
    fg: v("--foreground", "#e7ebf3"),
    muted: v("--muted", "#8b93a7"),
    border: v("--border", "#242d3d"),
    card: v("--card", "#141a24"),
    card2: v("--card-2", "#1b2230"),
    accent: v("--accent", "#4f8cff"),
    accent2: v("--accent-2", "#a78bfa"),
    positive: v("--positive", "#34d399"),
    negative: v("--negative", "#f87171"),
    grid: v("--border", "#242d3d"),
  };
}

export function EChart({
  option, height = 360, className, onReady,
}: {
  option: echarts.EChartsCoreOption;
  height?: number | string;
  className?: string;
  onReady?: (chart: echarts.ECharts) => void;
}) {
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    if (!el.current) return;
    chart.current = echarts.init(el.current, undefined, { renderer: "canvas" });
    onReady?.(chart.current);
    const ro = new ResizeObserver(() => chart.current?.resize());
    ro.observe(el.current);
    return () => { ro.disconnect(); chart.current?.dispose(); chart.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    chart.current?.setOption(option, true);
  }, [option, resolvedTheme]);

  return <div ref={el} style={{ height, width: "100%" }} className={className} />;
}
