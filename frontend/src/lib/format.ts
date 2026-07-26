// Small formatting + tone helpers shared across pages.

export function fmtSigned(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return (v >= 0 ? "+" : "") + v.toFixed(digits);
}

export function fmtNum(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toLocaleString();
}

export function toneLabel(v: number | null | undefined): string {
  if (v === null || v === undefined) return "no data";
  if (v >= 5) return "positive";
  if (v <= -5) return "negative";
  return "neutral";
}

// CSS-variable-driven colors (resolved at call time so they follow the theme).
export function cssVar(name: string): string {
  if (typeof window === "undefined") return "";
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function toneColor(v: number | null | undefined): string {
  if (v === null || v === undefined) return cssVar("--muted") || "#8b93a7";
  return v >= 0 ? cssVar("--accent") || "#4f8cff" : cssVar("--negative") || "#f87171";
}
