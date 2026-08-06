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

export function briefingUrl(topic: string, format: "markdown" | "html" | "pdf" = "markdown"): string {
  const url = new URL("/api/briefing", API_BASE);
  url.searchParams.set("topic", topic);
  url.searchParams.set("format", format);
  return url.toString();
}

// ---- New Intelligence APIs ----

export interface WorldCountrySentiment {
  iso3: string;
  gdelt: string;
  name: string;
  flag: string;
  groups: string[];
  leaders: string[];
  latest_tone: number;
  public_sentiment: number;
  gap: number;
  movement: number;
  volume: number;
  is_hotspot: boolean;
  status_label: string;
  spark: number[];
}

export interface WorldMapData {
  region: string;
  summary: {
    country_count: number;
    hotspot_count: number;
    global_avg_tone: number;
    total_articles: number;
  };
  countries: WorldCountrySentiment[];
}

export interface SimulationResult {
  topic: { id: string; label: string; category: string };
  event: {
    type: string;
    label: string;
    magnitude: number;
    description: string;
    category: string;
  };
  metrics: {
    initial_tone: number;
    peak_delta: number;
    max_divergence_gap: number;
    recovery_weeks: number;
    volume_surge_pct: number;
    severity_assessment: string;
  };
  simulation: {
    dates: string[];
    baseline_media: number[];
    baseline_public: number[];
    shocked_media: number[];
    shocked_public: number[];
    shocked_upper: number[];
    shocked_lower: number[];
  };
}

export interface NetworkGraphData {
  nodes: {
    id: string;
    name: string;
    category: string;
    latest_tone: number;
    volume: number;
    symbolSize: number;
    cluster_id: number;
    cluster_name: string;
    itemStyle: { color: string };
  }[];
  links: {
    source: string;
    target: string;
    source_label: string;
    target_label: string;
    value: number;
    weight: number;
    relationship: string;
    lineStyle: {
      width: number;
      color: string;
      opacity: number;
      type: string;
    };
  }[];
  clusters: { id: number; name: string; color: string }[];
  summary: {
    node_count: number;
    link_count: number;
    min_correlation_threshold: number;
  };
}

export interface PollingComparisonData {
  entity: {
    id: string;
    label: string;
    title: string;
    country: string;
    flag: string;
    pollsters: string[];
  };
  latest: {
    approval_pct: number;
    disapproval_pct: number;
    net_approval: number;
    media_tone: number;
    media_bias_index: number;
    correlation_r: number;
    verdict: string;
    verdict_code: string;
  };
  series: {
    date: string;
    approval_pct: number;
    disapproval_pct: number;
    net_approval: number;
    media_tone: number;
    bias_gap: number;
    pollster: string;
  }[];
}

export interface EconometricData {
  topic: { id: string; label: string; category: string };
  dates: string[];
  raw_tone: number[];
  hp_decomposition: {
    cycle: number[];
    trend: number[];
    smoothness_lambda: number;
    cyclical_variance_pct: number;
  };
  stationarity: {
    is_stationary: boolean;
    adf_statistic: number;
    p_value: number;
    critical_values: Record<string, number>;
    interpretation: string;
  };
  structural_breaks: {
    date: string;
    index: number;
    magnitude: number;
    t_statistic: number;
    type: string;
    pre_mean: number;
    post_mean: number;
  }[];
  volatility: {
    series: number[];
    current_volatility: number;
    mean_volatility: number;
    regime: string;
  };
}

export interface MarketSpilloverData {
  topic: { id: string; label: string; category: string };
  asset: {
    id: string;
    name: string;
    symbol: string;
    category: string;
    unit: string;
    base_price: number;
    volatility: number;
    geopolitical_sensitivity: string;
    description: string;
  };
  metrics: {
    correlation_r: number;
    spillover_beta: number;
    contagion_score: number;
    granger_causality: {
      causality_detected: boolean;
      optimal_lag_weeks: number;
      f_statistic: number;
      p_value: number;
      verdict: string;
    };
    latest_price: number;
    latest_tone: number;
  };
  series: {
    date: string;
    price: number;
    return_pct: number;
    sentiment_tone: number;
  }[];
}

export interface PolarizationData {
  topic: { id: string; label: string; category: string };
  summary: {
    latest_polarization_spread: number;
    mean_polarization_spread: number;
    polarization_tier: string;
    tier_code: string;
  };
  spectra: {
    id: string;
    name: string;
    color: string;
    outlets: string[];
    latest_tone: number;
    movement: number;
    volume: number;
    keywords: string[];
    series: number[];
  }[];
  timeline: {
    date: string;
    spread: number;
    left_tone: number;
    right_tone: number;
  }[];
}

export interface AnalystDossierData {
  topic: { id: string; label: string; category: string };
  latest_tone: number;
  generated_at: string;
  bluf: string;
  drivers: { title: string; impact: string; description: string }[];
  stakeholders: { actor: string; stance: string; power: string; leverage: string }[];
  scenarios: { name: string; probability: number; tone_projection: number; description: string }[];
  vulnerabilities: string[];
  source: string;
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
