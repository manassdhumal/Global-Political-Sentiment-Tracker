"use client";

import { useMemo, useState } from "react";
import type { EChartsCoreOption } from "echarts";
import { apiPost } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { EChart, useChartTheme } from "@/components/echart";
import { horizontalBar } from "@/components/charts";
import { Card, PageHeader, Select, Field, Spinner, EmptyState, Badge, DISCLAIMER, cx } from "@/components/ui";
import { fmtSigned } from "@/lib/format";

interface Contribution { token: string; start: number; end: number; delta: number; }
interface Aspect { name: string; entity_id: string | null; tracked: boolean; score: number; label: string; mentions: number; snippet: string; current_trend: number | null; delta_vs_trend: number | null; }
interface Analysis {
  backend: string; used_spacy: boolean; overall_score: number; overall_label: string;
  contributions: Contribution[]; aspects: Aspect[]; emotions: Record<string, number>; notes: string[];
}

const EXAMPLE = "I really admire how Narendra Modi handled the summit — it was a triumph. But rising inflation and the cost-of-living crisis are causing real anger and hardship. Donald Trump gave a controversial speech that sparked outrage and backlash.";

export default function AnalyzePage() {
  const { data: backends } = useApi<{ available: string[] }>("/api/sentiment-backends");
  const [text, setText] = useState(EXAMPLE);
  const [backend, setBackend] = useState("");
  const [res, setRes] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const t = useChartTheme();

  const run = async () => {
    if (!text.trim()) return;
    setLoading(true); setErr(null);
    try {
      const r = await apiPost<Analysis>("/api/analyze-text", { text, backend: backend || null });
      setRes(r);
    } catch (e) { setErr(String((e as Error).message ?? e)); }
    finally { setLoading(false); }
  };

  const gauge = useMemo<EChartsCoreOption>(() => {
    const v = res?.overall_score ?? 0;
    return {
      series: [{
        type: "gauge", min: -100, max: 100, radius: "95%", center: ["50%", "60%"],
        progress: { show: false },
        axisLine: { lineStyle: { width: 14, color: [[0.475, t.negative], [0.525, t.muted], [1, t.accent]] } },
        pointer: { itemStyle: { color: v >= 0 ? t.accent : t.negative } },
        axisTick: { show: false }, splitLine: { length: 10, lineStyle: { color: t.border } },
        axisLabel: { color: t.muted, fontSize: 9, distance: 14 },
        detail: { valueAnimation: true, formatter: (x: number) => (x >= 0 ? "+" : "") + x.toFixed(1), color: v >= 0 ? t.accent : t.negative, fontSize: 26, offsetCenter: [0, "40%"] },
        data: [{ value: v }],
      }],
    };
  }, [res, t]);

  const emotionOption = useMemo(() => {
    if (!res || !Object.keys(res.emotions).length) return null;
    const items = Object.entries(res.emotions).map(([k, v]) => ({ label: k, value: v }));
    return horizontalBar(t, items, { xName: "share", barColor: t.accent2 });
  }, [res, t]);

  const highlighted = useMemo(() => {
    if (!res) return null;
    const spans = [...res.contributions].sort((a, b) => a.start - b.start);
    const out: React.ReactNode[] = []; let cur = 0;
    spans.forEach((c, i) => {
      if (c.start < cur) return;
      if (c.start > cur) out.push(<span key={`p${i}`}>{text.slice(cur, c.start)}</span>);
      const alpha = Math.min(0.85, Math.abs(c.delta) / 10 + 0.15);
      const rgb = c.delta > 0 ? "79,140,255" : "248,113,113";
      out.push(<span key={`h${i}`} title={fmtSigned(c.delta)} style={{ background: `rgba(${rgb},${alpha})`, borderRadius: 3, padding: "0 2px" }}>{text.slice(c.start, c.end)}</span>);
      cur = c.end;
    });
    out.push(<span key="end">{text.slice(cur)}</span>);
    return out;
  }, [res, text]);

  return (
    <div className="space-y-6">
      <PageHeader title="Analyze your own text" subtitle="Runs the shared sentiment/entity model on text you paste — same −100…+100 scale. Measures the sentiment of the text, not truth.">
        <Field label="Engine"><Select value={backend} onChange={setBackend} options={[{ value: "", label: "Default" }, ...((backends?.available ?? []).map((b) => ({ value: b, label: b })))]} /></Field>
      </PageHeader>

      <Card className="p-4">
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={5}
          className="w-full resize-y rounded-lg border border-border bg-background p-3 text-sm outline-none focus:border-accent/60"
          placeholder="Paste text about political figures, parties or issues…" />
        <div className="mt-3 flex items-center gap-3">
          <button onClick={run} disabled={loading || !text.trim()}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
            {loading ? "Analyzing…" : "Analyze"}
          </button>
          {res && <span className="text-xs text-muted">engine: <code>{res.backend}</code>{res.used_spacy ? " · spaCy" : ""}</span>}
        </div>
      </Card>

      {loading && <Spinner label="Running the sentiment model…" />}
      {err && <EmptyState title="Analysis failed" hint={err} />}

      {res && !loading && (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="p-4">
              <div className="mb-1 text-sm font-medium">Overall sentiment</div>
              <EChart height={220} option={gauge} />
              <div className="text-center text-sm text-muted">{res.overall_label}</div>
            </Card>
            <Card className="p-4">
              <div className="mb-2 text-sm font-medium">What drove the score</div>
              <div className="leading-8 text-sm">{highlighted}</div>
              <div className="mt-2 text-xs text-muted">Blue = pushed positive, red = negative (hover a word for its impact).</div>
            </Card>
          </div>

          <Card className="p-4">
            <div className="mb-2 text-sm font-medium">Per-entity sentiment (aspect-based) vs live trend</div>
            {res.aspects.length === 0 ? <div className="text-sm text-muted">No entities detected.</div>
              : <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="text-left text-xs text-muted">
                      <tr><th className="py-1 pr-4">Entity</th><th className="py-1 pr-4">Your text</th><th className="py-1 pr-4">Current trend</th><th className="py-1 pr-4">Δ</th><th className="py-1">Mentions</th></tr>
                    </thead>
                    <tbody>
                      {res.aspects.map((a) => (
                        <tr key={a.name} className="border-t border-border">
                          <td className="py-1.5 pr-4">{a.name}{!a.tracked && <Badge tone="muted">untracked</Badge>}</td>
                          <td className="py-1.5 pr-4 tnum" style={{ color: a.score >= 0 ? t.accent : t.negative }}>{fmtSigned(a.score)}</td>
                          <td className="py-1.5 pr-4 tnum text-muted">{a.current_trend != null ? fmtSigned(a.current_trend) : "—"}</td>
                          <td className="py-1.5 pr-4 tnum">{a.delta_vs_trend != null ? fmtSigned(a.delta_vs_trend) : "—"}</td>
                          <td className="py-1.5 tnum text-muted">{a.mentions}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>}
          </Card>

          {emotionOption && (
            <Card className="p-4">
              <div className="mb-1 text-sm font-medium">Emotion breakdown <span className="text-xs font-normal text-muted">(indicative, keyword-based)</span></div>
              <EChart height={Math.max(160, Object.keys(res.emotions).length * 30)} option={emotionOption} />
            </Card>
          )}
          {res.notes.map((n, i) => <p key={i} className="text-xs text-muted">ℹ {n}</p>)}
          <p className="text-xs text-muted">{DISCLAIMER}</p>
        </>
      )}
    </div>
  );
}
