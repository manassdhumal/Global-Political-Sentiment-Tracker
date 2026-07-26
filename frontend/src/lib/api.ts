// Typed client for the FastAPI backend.
// Base URL overridable via NEXT_PUBLIC_API_BASE (defaults to localhost:8000).

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export async function api<T = unknown>(
  path: string,
  params?: Record<string, string | number | boolean | undefined | null>,
): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch {}
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function apiPost<T = unknown>(path: string, body: unknown): Promise<T> {
  const res = await fetch(new URL(path, API_BASE).toString(), {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch {}
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export function reportUrl(p: {
  scope: string; id: string; w0?: string; w1?: string; format: "markdown" | "pdf";
}): string {
  const url = new URL("/api/report", API_BASE);
  url.searchParams.set("scope", p.scope);
  url.searchParams.set("id", p.id);
  url.searchParams.set("format", p.format);
  if (p.w0) url.searchParams.set("w0", p.w0);
  if (p.w1) url.searchParams.set("w1", p.w1);
  return url.toString();
}

// ---- Shared config types ----
export interface Country { gdelt: string; iso3: string; name: string; }
export interface Entity {
  id: string; name: string; type: string;
  home_country: string | null; aliases: string[];
}
export interface AppConfig {
  measures: string;
  tone_range: [number, number];
  synthetic: boolean;
  window: { start: string | null; end: string | null };
  weeks: string[];
  countries: Country[];
  entities: Entity[];
}
