"use client";

import { useEffect, useState } from "react";
import { api, AnalystDossierData } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { fmtSigned, toneColor } from "@/lib/format";
import { Bot, Sparkles, Shield, Download, FileText, CheckCircle2, AlertTriangle, Users, Compass } from "lucide-react";

const TOPIC_PRESETS = [
  { id: "inflation", label: "Inflation & Cost of Living" },
  { id: "donald_trump", label: "Donald Trump" },
  { id: "ukraine_war", label: "Ukraine War & NATO Alliance" },
  { id: "china_trade", label: "US-China Trade & Tariffs" },
  { id: "defense_spending", label: "Global Defense Spending" },
  { id: "ai_regulation", label: "AI Safety & Tech Regulation" },
];

export default function AnalystPage() {
  const [topic, setTopic] = useState("inflation");
  const [data, setData] = useState<AnalystDossierData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api<AnalystDossierData>("/api/analyst/dossier", { topic })
      .then((res) => setData(res))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [topic]);

  const handleExportMarkdown = () => {
    if (!data) return;
    const md = `# Institutional Geopolitical Intelligence Dossier: ${data.topic.label}
Generated: ${data.generated_at} | Current Media Tone: ${data.latest_tone > 0 ? "+" : ""}${data.latest_tone}

## Executive Summary (BLUF)
${data.bluf}

## Causal Drivers & Friction Points
${data.drivers.map((d) => `- **${d.title}** [Impact: ${d.impact}]: ${d.description}`).join("\n")}

## Stakeholder Matrix
${data.stakeholders.map((s) => `- **${s.actor}** (Stance: ${s.stance}, Power: ${s.power}): ${s.leverage}`).join("\n")}

## Forward Scenarios (Next 4-6 Weeks)
${data.scenarios.map((sc) => `### ${sc.name} (Projected Tone: ${sc.tone_projection > 0 ? "+" : ""}${sc.tone_projection})\n${sc.description}`).join("\n\n")}

## Key Vulnerabilities & Blindspots
${data.vulnerabilities.map((v) => `- ${v}`).join("\n")}
`;

    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `intelligence_dossier_${data.topic.id}_${data.generated_at}.md`;
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">🧠</span>
            <h1 className="text-2xl font-bold tracking-tight">Autonomous AI Geopolitical Analyst</h1>
          </div>
          <p className="text-sm text-muted">
            Institutional-grade causal synthesis, stakeholder power matrices, and scenario forecasts for strategic decision-makers.
          </p>
        </div>

        {data && (
          <button
            onClick={handleExportMarkdown}
            className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-accent/90 transition-colors"
          >
            <Download size={14} /> Export Memo (.md)
          </button>
        )}
      </div>

      {/* Topic Filter Bar */}
      <Card className="p-4 bg-card border-border/80 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <Bot size={16} className="text-accent shrink-0" />
          <span className="text-xs text-muted font-medium">Topic Dossier:</span>
          <select
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="rounded-lg border border-border bg-card2 px-3 py-1.5 text-xs font-medium focus:border-accent focus:outline-none"
          >
            {TOPIC_PRESETS.map((t) => (
              <option key={t.id} value={t.id}>{t.label}</option>
            ))}
          </select>
        </div>

        {data && (
          <div className="flex items-center gap-2">
            <Badge tone="accent">
              <Sparkles size={11} className="mr-1" />
              {data.source === "gemini_flash_llm" ? "Gemini Flash Intelligence" : "Algorithmic Causal Engine"}
            </Badge>
          </div>
        )}
      </Card>

      {loading && (
        <div className="flex h-72 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Synthesizing intelligence dossier &amp; causal drivers...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Failed to generate analyst dossier: {error}
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6">
          {/* BLUF Executive Summary Card */}
          <Card className="p-5 border-accent/40 bg-accent/5">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-accent">
                <FileText size={14} /> Executive Summary (BLUF)
              </div>
              <div className="text-xs text-muted">Generated: {data.generated_at}</div>
            </div>
            <p className="text-sm font-medium text-foreground leading-relaxed">
              {data.bluf}
            </p>
          </Card>

          {/* Grid: Causal Drivers & Stakeholder Power Matrix */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Causal Drivers */}
            <Card className="p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-foreground">
                <Compass size={14} className="text-accent" /> Causal Friction Drivers
              </div>
              <div className="space-y-2.5">
                {data.drivers.map((d, i) => (
                  <div key={i} className="rounded-lg bg-card2 p-3 border border-border/60 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground">{d.title}</span>
                      <Badge tone={d.impact === "High" ? "negative" : "warning"}>{d.impact} Impact</Badge>
                    </div>
                    <p className="text-xs text-muted leading-snug">{d.description}</p>
                  </div>
                ))}
              </div>
            </Card>

            {/* Stakeholder Matrix */}
            <Card className="p-5 space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-foreground">
                <Users size={14} className="text-accent2" /> Stakeholder Positioning &amp; Leverage
              </div>
              <div className="space-y-2.5">
                {data.stakeholders.map((s, i) => (
                  <div key={i} className="rounded-lg bg-card2 p-3 border border-border/60 space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground">{s.actor}</span>
                      <span className="text-[11px] font-semibold text-accent">{s.stance}</span>
                    </div>
                    <div className="text-xs text-muted">
                      <strong>Leverage:</strong> {s.leverage}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* 3 Scenario Risk Projections */}
          <Card className="p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-sm">Forward Scenario Projections (Next 4–6 Weeks)</h3>
                <div className="text-xs text-muted">Probabilistic outcome models and sentiment tone trajectories</div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {data.scenarios.map((sc, i) => (
                <div key={i} className="rounded-xl bg-card2 p-4 border border-border/70 space-y-2.5 flex flex-col justify-between">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground">{sc.name}</span>
                    </div>
                    <div className="w-full bg-border/50 rounded-full h-1.5">
                      <div
                        className={cx(
                          "h-1.5 rounded-full",
                          i === 0 ? "bg-accent" : i === 1 ? "bg-emerald-400" : "bg-rose-400"
                        )}
                        style={{ width: `${sc.probability}%` }}
                      />
                    </div>
                    <p className="text-xs text-muted leading-relaxed">{sc.description}</p>
                  </div>

                  <div className="pt-2 border-t border-border/50 flex items-center justify-between text-xs">
                    <span className="text-muted">Target Tone:</span>
                    <span className="font-mono font-bold" style={{ color: toneColor(sc.tone_projection) }}>
                      {fmtSigned(sc.tone_projection)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Blindspots & Vulnerabilities */}
          <Card className="p-4 border-amber-500/30 bg-amber-500/5 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-bold text-amber-400">
              <AlertTriangle size={14} /> Strategic Vulnerabilities &amp; Blindspots
            </div>
            <ul className="list-disc list-inside space-y-1 text-xs text-muted pl-1">
              {data.vulnerabilities.map((v, i) => (
                <li key={i}>{v}</li>
              ))}
            </ul>
          </Card>
        </div>
      )}
    </div>
  );
}
