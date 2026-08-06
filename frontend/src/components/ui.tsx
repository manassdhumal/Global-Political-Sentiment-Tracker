"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown, Check } from "lucide-react";

export function cx(...c: (string | false | null | undefined)[]) {
  return c.filter(Boolean).join(" ");
}

export const DISCLAIMER =
  "Scores are media / social sentiment — coverage tone and vocal social posts, " +
  "not representative public opinion. Thin coverage is flagged low-confidence.";

export function Card({ className, style, children }: { className?: string; style?: React.CSSProperties; children: React.ReactNode }) {
  return (
    <div className={cx("rounded-xl border border-border bg-card", className)} style={style}>
      {children}
    </div>
  );
}

export function PageHeader({
  title, subtitle, children,
}: { title: string; subtitle?: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 max-w-3xl text-sm text-muted">{subtitle}</p>}
      </div>
      {children && <div className="flex flex-wrap items-end gap-3">{children}</div>}
    </div>
  );
}

export function StatTile({
  label, value, sub, accent,
}: { label: string; value: React.ReactNode; sub?: React.ReactNode; accent?: string }) {
  return (
    <Card className="p-4">
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 text-2xl font-semibold tnum" style={accent ? { color: accent } : undefined}>
        {value}
      </div>
      {sub !== undefined && <div className="mt-0.5 text-xs text-muted tnum">{sub}</div>}
    </Card>
  );
}

export function Field({
  label, hint, children,
}: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-xs font-medium text-muted">{label}</span>
      {children}
      {hint && <span className="text-[11px] text-muted">{hint}</span>}
    </label>
  );
}

const controlCls =
  "h-9 rounded-lg border border-border bg-card px-3 text-sm text-foreground outline-none focus:border-accent/60 focus:ring-2 focus:ring-accent/20";

export function Select({
  value, onChange, options, className,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  className?: string;
}) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} className={cx(controlCls, "min-w-40 pr-8", className)}>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

export function Segmented({
  options, value, onChange,
}: { options: { value: string; label: string }[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="inline-flex rounded-lg border border-border bg-card p-0.5">
      {options.map((o) => (
        <button
          key={o.value}
          onClick={() => onChange(o.value)}
          className={cx(
            "rounded-md px-3 py-1.5 text-sm transition-colors",
            value === o.value ? "bg-accent text-white" : "text-muted hover:text-foreground",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function MultiSelect({
  options, value, onChange, placeholder = "Select…", maxLabel = 2,
}: {
  options: { value: string; label: string }[];
  value: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
  maxLabel?: number;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);
  const toggle = (v: string) =>
    onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  const labelText =
    value.length === 0 ? placeholder
      : value.length <= maxLabel
        ? options.filter((o) => value.includes(o.value)).map((o) => o.label).join(", ")
        : `${value.length} selected`;

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen((o) => !o)} className={cx(controlCls, "flex min-w-48 items-center justify-between gap-2")}>
        <span className="truncate text-left">{labelText}</span>
        <ChevronDown size={15} className="shrink-0 text-muted" />
      </button>
      {open && (
        <div className="absolute z-30 mt-1 max-h-72 w-64 overflow-auto rounded-lg border border-border bg-card p-1 shadow-xl">
          {options.map((o) => {
            const on = value.includes(o.value);
            return (
              <button
                key={o.value}
                onClick={() => toggle(o.value)}
                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-card2"
              >
                <span className={cx("flex h-4 w-4 items-center justify-center rounded border", on ? "border-accent bg-accent text-white" : "border-border")}>
                  {on && <Check size={12} />}
                </span>
                <span className="truncate">{o.label}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function Badge({ children, tone = "muted" }: { children: React.ReactNode; tone?: "muted" | "accent" | "warning" | "positive" | "negative" }) {
  const map: Record<string, string> = {
    muted: "border-border text-muted",
    accent: "border-accent/40 text-accent",
    warning: "border-warning/40 text-warning",
    positive: "border-positive/40 text-positive",
    negative: "border-negative/40 text-negative",
  };
  return <span className={cx("inline-flex items-center rounded-full border px-2 py-0.5 text-[11px]", map[tone])}>{children}</span>;
}

export function Banner({ children, tone = "warning" }: { children: React.ReactNode; tone?: "warning" | "accent" }) {
  const cls = tone === "warning"
    ? "border-warning/30 bg-warning/10 text-warning"
    : "border-accent/30 bg-accent/10 text-accent";
  return <div className={cx("rounded-lg border px-3 py-2 text-sm", cls)}>{children}</div>;
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-10 text-sm text-muted">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-accent" />
      {label ?? "Loading…"}
    </div>
  );
}

export function EmptyState({ title, hint, onRetry }: { title: string; hint?: string; onRetry?: () => void }) {
  return (
    <div className="rounded-xl border border-dashed border-border p-8 text-center">
      <p className="text-sm font-medium">{title}</p>
      {hint && <p className="mt-1 text-sm text-muted">{hint}</p>}
      {onRetry && (
        <button onClick={onRetry} className="mt-3 rounded-lg border border-border px-3 py-1.5 text-sm text-muted hover:border-accent/50 hover:text-foreground">
          Retry
        </button>
      )}
    </div>
  );
}

/** Pulsing placeholder block. */
export function Skeleton({ className }: { className?: string }) {
  return <div className={cx("animate-pulse rounded-lg bg-card2", className)} />;
}

/** A grid of card-shaped skeletons (matches TopicCard layout). */
export function CardGridSkeleton({ n = 6 }: { n?: number }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: n }).map((_, i) => (
        <Card key={i} className="p-4">
          <div className="flex items-start justify-between">
            <div className="space-y-2"><Skeleton className="h-4 w-32" /><Skeleton className="h-3 w-16" /></div>
            <Skeleton className="h-6 w-12" />
          </div>
          <Skeleton className="mt-3 h-10 w-full" />
          <Skeleton className="mt-2 h-3 w-24" />
        </Card>
      ))}
    </div>
  );
}

/** A few stacked stat-tile + chart skeletons (matches a detail page). */
export function DetailSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-20" />)}
      </div>
      <Skeleton className="h-80 w-full" />
      <div className="grid gap-4 lg:grid-cols-2"><Skeleton className="h-64" /><Skeleton className="h-64" /></div>
    </div>
  );
}
