"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, apiPost } from "@/lib/api";
import { Card, Badge, PageHeader, cx } from "@/components/ui";
import { fmtSigned, toneColor } from "@/lib/format";
import {
  Bookmark,
  Bell,
  Plus,
  Trash2,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Layers,
  ArrowUpRight,
  Sliders,
  CheckCircle,
} from "lucide-react";

interface WatchlistMember {
  id: string;
  label: string;
  category: string;
  latest_tone: number;
  delta_tone: number;
  volume: number;
  volatility_4w: number;
  status: string;
}

interface AlertItem {
  id: string;
  topic_id: string;
  topic_label: string;
  watchlist_name?: string;
  type: string;
  severity: string;
  message: string;
  timestamp: string;
  value: number;
}

interface WatchlistData {
  id: string;
  name: string;
  description: string;
  color: string;
  basket_tone: number;
  total_volume: number;
  member_count: number;
  members: WatchlistMember[];
  active_alerts: AlertItem[];
}

export default function WatchlistsPage() {
  const [watchlists, setWatchlists] = useState<WatchlistData[]>([]);
  const [activeWlId, setActiveWlId] = useState<string>("geopolitical_flashpoints");
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api<WatchlistData[]>("/api/watchlists"),
      api<AlertItem[]>("/api/watchlists/alerts"),
    ])
      .then(([wlRes, alertsRes]) => {
        setWatchlists(wlRes);
        setAlerts(alertsRes);
        if (wlRes.length > 0 && !activeWlId) {
          setActiveWlId(wlRes[0].id);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const activeWl = watchlists.find((w) => w.id === activeWlId) || watchlists[0];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">💼</span>
            <h1 className="text-2xl font-bold tracking-tight">Custom Portfolios &amp; Alert Center</h1>
          </div>
          <p className="text-sm text-muted">
            Group global narratives into custom monitoring baskets, track aggregate sentiment elasticity, and trigger real-time alerts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge tone="accent">
            <Bell size={12} className="mr-1" /> {alerts.length} Active Triggers
          </Badge>
        </div>
      </div>

      {/* Active Alerts Banner */}
      {alerts.length > 0 && (
        <Card className="p-4 border-amber-500/40 bg-amber-500/5 space-y-2.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-amber-400">
              <AlertTriangle size={14} /> Active Threshold Alerts ({alerts.length})
            </div>
            <span className="text-[11px] text-muted">Auto-refreshed</span>
          </div>

          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {alerts.slice(0, 4).map((a) => (
              <div key={a.id} className="rounded-lg bg-card2 p-2.5 border border-border/70 flex items-start gap-2.5">
                <span className="flex h-2 w-2 relative mt-1 shrink-0">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                </span>
                <div className="space-y-0.5 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-foreground truncate">{a.topic_label}</span>
                    <span className="text-[10px] text-muted font-mono shrink-0">{a.timestamp}</span>
                  </div>
                  <p className="text-xs text-muted leading-tight">{a.message}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Portfolio Selector Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {watchlists.map((wl) => {
          const active = wl.id === activeWlId;
          return (
            <button
              key={wl.id}
              onClick={() => setActiveWlId(wl.id)}
              className={cx(
                "inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-semibold transition-all shrink-0",
                active
                  ? "border-accent bg-accent/15 text-accent shadow-sm"
                  : "border-border bg-card text-muted hover:border-border/80 hover:text-foreground"
              )}
            >
              <Bookmark size={14} style={{ color: wl.color }} />
              <span>{wl.name}</span>
              <span
                className="font-mono text-[11px] px-1.5 py-0.5 rounded-md bg-card2"
                style={{ color: toneColor(wl.basket_tone) }}
              >
                {fmtSigned(wl.basket_tone)}
              </span>
            </button>
          );
        })}
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center rounded-xl border border-border bg-card">
          <div className="text-sm text-muted animate-pulse">Evaluating portfolio basket telemetry &amp; alert triggers...</div>
        </div>
      )}

      {/* Selected Watchlist Details */}
      {activeWl && !loading && (
        <div className="space-y-6">
          {/* Basket Overview KPI Card */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card className="p-4 space-y-1">
              <div className="text-xs text-muted font-medium">Aggregated Basket Tone</div>
              <div className="text-2xl font-bold font-mono" style={{ color: toneColor(activeWl.basket_tone) }}>
                {fmtSigned(activeWl.basket_tone)}
              </div>
              <div className="text-[11px] text-muted">Average sentiment across {activeWl.member_count} topics</div>
            </Card>

            <Card className="p-4 space-y-1">
              <div className="text-xs text-muted font-medium">Aggregate Weekly Media Volume</div>
              <div className="text-2xl font-bold font-mono text-foreground">
                {activeWl.total_volume.toLocaleString()}
              </div>
              <div className="text-[11px] text-muted">Total tracked articles across global outlets</div>
            </Card>

            <Card className="p-4 space-y-1">
              <div className="text-xs text-muted font-medium">Active Alert Triggers</div>
              <div className="text-2xl font-bold font-mono text-amber-400">
                {activeWl.active_alerts.length}
              </div>
              <div className="text-[11px] text-muted">Threshold triggers requiring analyst review</div>
            </Card>
          </div>

          {/* Members Table */}
          <Card className="overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-foreground">{activeWl.name} — Asset Breakdown</h3>
                <p className="text-xs text-muted">{activeWl.description}</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-card2 text-muted uppercase tracking-wider font-semibold border-b border-border">
                  <tr>
                    <th className="px-4 py-3">Topic / Entity</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3 text-right">Latest Tone</th>
                    <th className="px-4 py-3 text-right">1-Week Δ</th>
                    <th className="px-4 py-3 text-right">4W Volatility (σ)</th>
                    <th className="px-4 py-3 text-right">Est. Volume</th>
                    <th className="px-4 py-3 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {activeWl.members.map((m) => (
                    <tr key={m.id} className="hover:bg-card2/50 transition-colors">
                      <td className="px-4 py-3.5 font-semibold text-foreground">
                        <Link href={`/topic?id=${m.id}`} className="hover:text-accent flex items-center gap-1.5">
                          {m.label} <ArrowUpRight size={12} className="text-muted" />
                        </Link>
                      </td>
                      <td className="px-4 py-3.5 capitalize text-muted">{m.category.replace("_", " ")}</td>
                      <td className="px-4 py-3.5 text-right font-mono font-bold" style={{ color: toneColor(m.latest_tone) }}>
                        {fmtSigned(m.latest_tone)}
                      </td>
                      <td className="px-4 py-3.5 text-right font-mono" style={{ color: toneColor(m.delta_tone) }}>
                        {fmtSigned(m.delta_tone)}
                      </td>
                      <td className="px-4 py-3.5 text-right font-mono text-muted">{m.volatility_4w}</td>
                      <td className="px-4 py-3.5 text-right font-mono text-muted">{m.volume.toLocaleString()}</td>
                      <td className="px-4 py-3.5 text-center">
                        <Link
                          href={`/timeseries?topic=${m.id}`}
                          className="inline-flex items-center gap-1 rounded bg-card2 px-2 py-1 text-[11px] font-medium text-accent hover:bg-accent/15"
                        >
                          Econometrics
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
