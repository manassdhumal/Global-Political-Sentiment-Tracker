"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Bell, AlertTriangle, ArrowRight } from "lucide-react";
import { cx } from "@/components/ui";

interface AlertItem {
  id: string;
  topic_id: string;
  topic_label: string;
  watchlist_name?: string;
  type: string;
  severity: string;
  message: string;
  timestamp: string;
}

export function NotificationBell() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api<AlertItem[]>("/api/watchlists/alerts")
      .then((res) => setAlerts(res))
      .catch(() => {});

    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setOpen(!open)}
        className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-muted hover:border-border/80 hover:text-foreground transition-colors"
        title="Active Threshold Alerts"
      >
        <Bell size={16} />
        {alerts.length > 0 && (
          <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-sm">
            {alerts.length}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl border border-border bg-card shadow-2xl p-3 z-50 space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-border">
            <div className="flex items-center gap-1.5 text-xs font-bold text-foreground">
              <AlertTriangle size={14} className="text-amber-400" />
              <span>Active Threshold Alerts</span>
            </div>
            <span className="text-[10px] font-mono text-muted bg-card2 px-1.5 py-0.5 rounded">
              {alerts.length} unread
            </span>
          </div>

          <div className="max-h-72 overflow-y-auto space-y-1.5 divide-y divide-border/40">
            {alerts.length === 0 ? (
              <div className="py-6 text-center text-xs text-muted">No active threshold alerts.</div>
            ) : (
              alerts.map((a) => (
                <div key={a.id} className="pt-1.5 first:pt-0 space-y-0.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-foreground truncate">{a.topic_label}</span>
                    <span className="text-[10px] text-muted font-mono">{a.timestamp}</span>
                  </div>
                  <p className="text-[11px] text-muted leading-tight">{a.message}</p>
                </div>
              ))
            )}
          </div>

          <div className="pt-2 border-t border-border">
            <Link
              href="/watchlists"
              onClick={() => setOpen(false)}
              className="flex items-center justify-between text-xs font-medium text-accent hover:underline"
            >
              <span>Manage Portfolios &amp; Rules</span>
              <ArrowRight size={12} />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
