"use client";

import { useEffect, useState } from "react";
import { api, apiPost, AnalystDossierData, AnalystQAResponse } from "@/lib/api";
import { Card, Badge, cx } from "@/components/ui";
import { fmtSigned, toneColor } from "@/lib/format";
import {
  Bot,
  Sparkles,
  Shield,
  Download,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Users,
  Compass,
  Send,
  Sliders,
  TrendingUp,
  MessageSquare,
  HelpCircle,
  Briefcase,
  Globe2,
} from "lucide-react";

const TOPIC_PRESETS = [
  { id: "inflation", label: "Inflation & Cost of Living" },
  { id: "donald_trump", label: "Donald Trump" },
  { id: "ukraine_war", label: "Ukraine War & NATO Alliance" },
  { id: "china_trade", label: "US-China Trade & Tariffs" },
  { id: "defense_spending", label: "Global Defense Spending" },
  { id: "ai_regulation", label: "AI Safety & Tech Regulation" },
];

const ARCHETYPES = [
  { id: "executive", label: "Executive C-Suite", icon: Briefcase, desc: "Governance, reputation & regulatory timelines" },
  { id: "hedge_fund", label: "Macro Hedge Fund", icon: TrendingUp, desc: "Cross-asset spillovers, FX/rates & tail risks" },
  { id: "diplomatic", label: "Diplomatic Strategy", icon: Globe2, desc: "Treaties, sanctions contagion & alliances" },
];

export default function AnalystPage() {
  const [topic, setTopic] = useState("inflation");
  const [archetype, setArchetype] = useState("executive");
  const [data, setData] = useState<AnalystDossierData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dynamic Scenario Tuning State
  const [customProbabilities, setCustomProbabilities] = useState<number[]>([60, 25, 15]);

  // Q&A Terminal State
  const [question, setQuestion] = useState("");
  const [qaLoading, setQaLoading] = useState(false);
  const [qaHistory, setQaHistory] = useState<AnalystQAResponse[]>([]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api<AnalystDossierData>("/api/analyst/dossier", { topic, archetype })
      .then((res) => {
        setData(res);
        if (res.scenarios) {
          setCustomProbabilities(res.scenarios.map((s) => s.probability));
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [topic, archetype]);

  const handleAskQuestion = async (qText?: string) => {
    const query = qText || question;
    if (!query.trim()) return;

    setQaLoading(true);
    try {
      const res = await apiPost<AnalystQAResponse>("/api/analyst/qa", {
        topic,
        question: query,
        archetype,
      });
      setQaHistory((prev) => [res, ...prev]);
      if (!qText) setQuestion("");
    } catch (err: any) {
      console.error(err);
    } finally {
      setQaLoading(false);
    }
  };

  const handleExportMarkdown = () => {
    if (!data) return;
    const md = `# Institutional Geopolitical Intelligence Dossier: ${data.topic.label}
Archetype: ${archetype.toUpperCase()} | Generated: ${data.generated_at} | Current Media Tone: ${data.latest_tone > 0 ? "+" : ""}${data.latest_tone}

## Executive Summary (BLUF)
${data.bluf}

## Causal Drivers & Friction Points
${data.drivers.map((d) => `- **${d.title}** [Impact: ${d.impact}]: ${d.description}`).join("\n")}

## Stakeholder Matrix
${data.stakeholders.map((s) => `- **${s.actor}** (Stance: ${s.stance}, Power: ${s.power}): ${s.leverage}`).join("\n")}

## Forward Scenarios (Next 4-6 Weeks)
${data.scenarios.map((sc, i) => `### ${sc.name} (Probability: ${customProbabilities[i]}%, Projected Tone: ${sc.tone_projection > 0 ? "+" : ""}${sc.tone_projection})\n${sc.description}`).join("\n\n")}

## Key Vulnerabilities & Blindspots
${data.vulnerabilities.map((v) => `- ${v}`).join("\n")}
`;

    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `intelligence_dossier_${data.topic.id}_${archetype}.md`;
    a.click();
  };

  // Calculate Weighted Projected Tone based on scenario sliders
  const totalProb = customProbabilities.reduce((a, b) => a + b, 0) || 100;
  const weightedProjectedTone = data && data.scenarios
    ? customProbabilities.reduce((acc, p, i) => acc + ((p / totalProb) * (data.scenarios[i]?.tone_projection || 0)), 0)
    : 0;

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
            Institutional-grade causal synthesis, archetype customization, and real-time intelligence Q&amp;A.
          </p>
        </div>

        {data && (
          <div className="flex items-center gap-2">
            <a
              href={`/api/export/pdf/dossier?topic=${topic}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-card2 px-3.5 py-1.5 text-xs font-semibold text-foreground shadow-sm hover:border-accent hover:text-accent transition-colors"
            >
              <FileText size={14} className="text-rose-400" /> Export PDF Dossier
            </a>
            <button
              onClick={handleExportMarkdown}
              className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-accent/90 transition-colors"
            >
              <Download size={14} /> Export Memo (.md)
            </button>
          </div>
        )}
      </div>

      {/* Control Strip: Topic + Archetype Selector */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="p-4 bg-card border-border/80 flex items-center gap-3">
          <Bot size={18} className="text-accent shrink-0" />
          <div className="flex-1">
            <div className="text-[10px] text-muted font-bold uppercase">Topic Dossier</div>
            <select
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full rounded-md border border-border bg-card2 px-2.5 py-1 text-xs font-semibold focus:border-accent focus:outline-none mt-0.5"
            >
              {TOPIC_PRESETS.map((t) => (
                <option key={t.id} value={t.id}>{t.label}</option>
              ))}
            </select>
          </div>
        </Card>

        {/* Archetype Selector Tabs */}
        <Card className="lg:col-span-2 p-2 bg-card flex items-center gap-2 overflow-x-auto">
          {ARCHETYPES.map((arc) => {
            const Icon = arc.icon;
            const isSelected = archetype === arc.id;
            return (
              <button
                key={arc.id}
                onClick={() => setArchetype(arc.id)}
                className={cx(
                  "flex flex-1 items-center gap-2 rounded-lg px-3 py-2 text-left transition-all",
                  isSelected
                    ? "bg-accent text-white shadow-sm"
                    : "bg-card2 text-muted hover:text-foreground hover:bg-card border border-border/50"
                )}
              >
                <Icon size={16} className={isSelected ? "text-white" : "text-accent"} />
                <div className="min-w-0">
                  <div className="text-xs font-bold truncate">{arc.label}</div>
                  <div className={cx("text-[10px] truncate", isSelected ? "text-white/80" : "text-muted")}>
                    {arc.desc}
                  </div>
                </div>
              </button>
            );
          })}
        </Card>
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Generating causal intelligence dossier for {archetype}...</div>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-400">
          Analyst engine error: {error}
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6">
          {/* BLUF Hero Banner */}
          <Card className="p-6 border-accent/40 bg-accent/5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-accent">
                <Sparkles size={16} /> Bottom Line Up Front (BLUF) · {archetype.toUpperCase()} PERSPECTIVE
              </div>
              <Badge tone="accent">Net Tone: {fmtSigned(data.latest_tone)}</Badge>
            </div>
            <p className="text-base font-medium leading-relaxed text-foreground">
              {data.bluf}
            </p>
            {data.rag_sources && data.rag_sources.length > 0 && (
              <div className="mt-4 border-t border-accent/20 pt-3">
                <div className="flex items-center gap-1.5 text-xs font-bold text-accent mb-2">
                  <Bot size={14} /> Retrieved Factual Context (RAG)
                </div>
                <ul className="list-disc pl-5 text-[11px] text-muted space-y-1">
                  {data.rag_sources.map((src, i) => (
                    <li key={i}>{src}</li>
                  ))}
                </ul>
              </div>
            )}
          </Card>

          {/* Grid: Drivers & Stakeholders */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Drivers */}
            <Card className="p-5 space-y-4">
              <div className="flex items-center gap-2 text-sm font-bold border-b border-border pb-3">
                <AlertTriangle size={16} className="text-amber-400" />
                <span>Causal Drivers &amp; Narrative Pressures</span>
              </div>
              <div className="space-y-3">
                {data.drivers.map((d, i) => (
                  <div key={i} className="rounded-lg border border-border bg-card2 p-3 text-xs space-y-1">
                    <div className="flex items-center justify-between font-semibold">
                      <span className="text-foreground">{d.title}</span>
                      <Badge tone={d.impact === "High" ? "negative" : "warning"}>{d.impact} Impact</Badge>
                    </div>
                    <p className="text-muted leading-relaxed">{d.description}</p>
                  </div>
                ))}
              </div>
            </Card>

            {/* Stakeholders */}
            <Card className="p-5 space-y-4">
              <div className="flex items-center gap-2 text-sm font-bold border-b border-border pb-3">
                <Users size={16} className="text-blue-400" />
                <span>Primary Stakeholder Power Matrix</span>
              </div>
              <div className="space-y-3">
                {data.stakeholders.map((s, i) => (
                  <div key={i} className="rounded-lg border border-border bg-card2 p-3 text-xs space-y-1">
                    <div className="flex items-center justify-between font-semibold">
                      <span className="text-foreground">{s.actor}</span>
                      <div className="flex items-center gap-1.5">
                        <Badge tone="muted">Power: {s.power}</Badge>
                        <Badge tone="accent">{s.stance}</Badge>
                      </div>
                    </div>
                    <p className="text-muted leading-relaxed"><strong>Leverage:</strong> {s.leverage}</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Dynamic Scenario Projections with Tuning Sliders */}
          <Card className="p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-3">
              <div>
                <h3 className="font-bold text-base flex items-center gap-2">
                  <Compass size={16} className="text-emerald-400" /> Forward Scenarios &amp; Dynamic Sensitivity Tuner
                </h3>
                <p className="text-xs text-muted">Adjust scenario probability weights to compute expected narrative glidepaths.</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted">Weighted Tone:</span>
                <span className="text-sm font-bold font-mono" style={{ color: toneColor(weightedProjectedTone) }}>
                  {fmtSigned(weightedProjectedTone, 2)}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {data.scenarios.map((sc, i) => {
                const prob = customProbabilities[i] ?? sc.probability;
                return (
                  <div key={i} className="rounded-xl border border-border bg-card2 p-4 space-y-3 flex flex-col justify-between">
                    <div className="space-y-1.5">
                      <div className="flex items-start justify-between">
                        <h4 className="font-bold text-xs text-foreground leading-snug">{sc.name}</h4>
                        <span className="text-xs font-bold font-mono" style={{ color: toneColor(sc.tone_projection) }}>
                          {fmtSigned(sc.tone_projection)}
                        </span>
                      </div>
                      <p className="text-xs text-muted leading-relaxed">{sc.description}</p>
                    </div>

                    <div className="space-y-1.5 pt-2 border-t border-border/50">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="text-muted">Probability Weight:</span>
                        <span className="font-bold font-mono text-accent">{prob}%</span>
                      </div>
                      <input
                        type="range"
                        min={0}
                        max={100}
                        value={prob}
                        onChange={(e) => {
                          const newProb = parseInt(e.target.value, 10);
                          const next = [...customProbabilities];
                          next[i] = newProb;
                          setCustomProbabilities(next);
                        }}
                        className="w-full h-1.5 bg-card rounded-lg appearance-none cursor-pointer accent-accent"
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* INTERACTIVE "ASK THE ANALYST" TERMINAL */}
          <Card className="p-5 space-y-4 border-accent/40 bg-card">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2 text-sm font-bold text-foreground">
                <MessageSquare size={16} className="text-accent" />
                <span>Interactive &quot;Ask the Analyst&quot; Intelligence Terminal</span>
              </div>
              <Badge tone="accent">Context: {data.topic.label} · {archetype.toUpperCase()}</Badge>
            </div>

            {/* Quick Prompt Chips */}
            <div className="flex flex-wrap gap-2">
              {[
                "What are the direct cross-asset market implications?",
                "How will key voter demographics react over the next 30 days?",
                "What is the probability of a tail-risk escalation?",
              ].map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => handleAskQuestion(chip)}
                  className="rounded-full border border-border bg-card2 px-3 py-1 text-[11px] text-muted hover:text-foreground hover:border-accent transition-colors"
                >
                  💡 {chip}
                </button>
              ))}
            </div>

            {/* Input Form */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleAskQuestion();
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder={`Ask the ${archetype} analyst anything about ${data.topic.label}...`}
                className="flex-1 rounded-lg border border-border bg-card2 px-3.5 py-2 text-xs focus:border-accent focus:outline-none"
              />
              <button
                type="submit"
                disabled={qaLoading || !question.trim()}
                className="flex items-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-xs font-semibold text-white shadow hover:bg-accent/90 disabled:opacity-50 transition-all"
              >
                {qaLoading ? <Sparkles size={13} className="animate-spin" /> : <Send size={13} />}
                <span>Inquire</span>
              </button>
            </form>

            {/* Q&A Stream History */}
            {qaHistory.length > 0 && (
              <div className="space-y-3 pt-2">
                {qaHistory.map((item, idx) => (
                  <div key={idx} className="rounded-xl border border-border bg-card2 p-4 space-y-2.5">
                    <div className="flex items-center justify-between text-xs font-semibold text-accent">
                      <span>Q: {item.question}</span>
                      <span className="text-[10px] text-muted font-mono">Confidence: {Math.round(item.confidence_score * 100)}%</span>
                    </div>
                    <p className="text-xs text-foreground leading-relaxed bg-card p-3 rounded-lg border border-border/50">
                      {item.answer}
                    </p>
                    {item.key_takeaways && item.key_takeaways.length > 0 && (
                      <div className="space-y-1 text-xs">
                        <span className="text-[10px] uppercase font-bold text-muted">Key Strategic Takeaways:</span>
                        <ul className="list-disc list-inside text-muted text-[11px] space-y-0.5">
                          {item.key_takeaways.map((point, pIdx) => (
                            <li key={pIdx}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {item.rag_sources && item.rag_sources.length > 0 && (
                      <div className="space-y-1 text-xs pt-1 border-t border-border/50">
                        <span className="text-[10px] uppercase font-bold text-accent">Retrieved RAG Sources:</span>
                        <ul className="list-disc list-inside text-muted text-[11px] space-y-0.5">
                          {item.rag_sources.map((point, pIdx) => (
                            <li key={pIdx}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
