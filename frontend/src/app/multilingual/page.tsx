"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { Card, Badge, PageHeader, cx } from "@/components/ui";
import { fmtSigned, toneColor } from "@/lib/format";
import { Languages, Globe, Scale, ArrowRight, MessageSquareQuote, Newspaper, Compass } from "lucide-react";

interface SphereItem {
  code: string;
  name: string;
  region: string;
  color: string;
  outlets: string[];
  tone: number;
  headline: string;
  framing: string;
}

interface MultilingualResp {
  topic: {
    id: string;
    label: string;
    category: string;
  };
  base_tone: number;
  disparity_spread: number;
  disparity_tier: string;
  spheres: SphereItem[];
  max_sphere: string;
  min_sphere: string;
}

const PRESET_TOPICS = [
  { id: "us_china", label: "US–China Competition" },
  { id: "ukraine_war", label: "War in Ukraine" },
  { id: "middle_east", label: "Israel-Gaza Conflict" },
  { id: "taiwan", label: "Taiwan Strait Security" },
  { id: "trade_tariffs", label: "Trade & Tariffs" },
  { id: "ai_regulation", label: "AI Governance" },
];

export default function MultilingualPage() {
  const [topicId, setTopicId] = useState<string>("us_china");
  const { data, loading, error, reload } = useApi<MultilingualResp>(
    `/api/multilingual/matrix?topic=${topicId}`
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌐</span>
            <h1 className="text-2xl font-bold tracking-tight">Cross-Cultural Media Framing</h1>
          </div>
          <p className="text-sm text-muted">
            Analyze how 8 major world language ecosystems frame identical geopolitical crises, revealing cultural framing divides.
          </p>
        </div>

        {data && (
          <div className="flex items-center gap-2">
            <Badge tone={data.disparity_spread > 2.5 ? "negative" : "accent"}>
              <Scale size={12} className="mr-1" /> Disparity: {data.disparity_spread} pts
            </Badge>
          </div>
        )}
      </div>

      {/* Preset Topic Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {PRESET_TOPICS.map((pt) => {
          const active = pt.id === topicId;
          return (
            <button
              key={pt.id}
              onClick={() => setTopicId(pt.id)}
              className={cx(
                "rounded-xl border px-3.5 py-2 text-xs font-semibold transition-all shrink-0",
                active
                  ? "border-accent bg-accent/15 text-accent shadow-sm"
                  : "border-border bg-card text-muted hover:border-border/80 hover:text-foreground"
              )}
            >
              {pt.label}
            </button>
          );
        })}
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Synthesizing cross-lingual narrative matrices across 8 language spheres...</div>
        </div>
      )}

      {data && !loading && (
        <div className="space-y-6">
          {/* Executive Overview KPI Cards */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card className="p-4 space-y-1">
              <div className="text-xs text-muted font-medium">Cross-Lingual Disparity Spread</div>
              <div className="text-2xl font-bold font-mono text-accent">
                {data.disparity_spread} pts
              </div>
              <div className="text-[11px] text-muted">{data.disparity_tier}</div>
            </Card>

            <Card className="p-4 space-y-1">
              <div className="text-xs text-muted font-medium">Most Favorable Sphere</div>
              <div className="text-base font-bold text-emerald-400 truncate">
                {data.max_sphere}
              </div>
              <div className="text-[11px] text-muted">Highest relative narrative tone</div>
            </Card>

            <Card className="p-4 space-y-1">
              <div className="text-xs text-muted font-medium">Most Critical Sphere</div>
              <div className="text-base font-bold text-rose-400 truncate">
                {data.min_sphere}
              </div>
              <div className="text-[11px] text-muted">Lowest relative narrative tone</div>
            </Card>
          </div>

          {/* Cross-Lingual Spheres Grid */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {data.spheres.map((s) => (
              <Card key={s.code} className="p-4 space-y-3 border-l-4" style={{ borderLeftColor: s.color }}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
                      <Globe size={14} style={{ color: s.color }} />
                      {s.name}
                    </h4>
                    <span className="text-[11px] text-muted">{s.region}</span>
                  </div>
                  <div
                    className="font-mono text-xs font-bold px-2 py-1 rounded-md bg-card2"
                    style={{ color: toneColor(s.tone) }}
                  >
                    {fmtSigned(s.tone)} tone
                  </div>
                </div>

                <div className="rounded-lg bg-card2 p-3 space-y-2 text-xs">
                  <div className="flex items-start gap-2">
                    <Newspaper size={13} className="text-accent shrink-0 mt-0.5" />
                    <div>
                      <div className="text-[10px] uppercase font-bold text-muted tracking-wider">Representative Framing</div>
                      <p className="text-foreground italic mt-0.5">&ldquo;{s.headline}&rdquo;</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-2 pt-1 border-t border-border/50">
                    <Compass size={13} className="text-muted shrink-0 mt-0.5" />
                    <div>
                      <div className="text-[10px] uppercase font-bold text-muted tracking-wider">Geopolitical Lens</div>
                      <p className="text-muted mt-0.5">{s.framing}</p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-muted pt-1">
                  <span className="truncate">Tracked: {s.outlets.slice(0, 3).join(", ")}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
