"use client";

import { useConfig } from "@/components/config-context";
import { Card, PageHeader, Banner } from "@/components/ui";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card className="p-5">
      <h2 className="mb-2 text-sm font-semibold">{title}</h2>
      <div className="space-y-2 text-sm text-muted">{children}</div>
    </Card>
  );
}

export default function MethodologyPage() {
  const { config } = useConfig();
  return (
    <div className="space-y-6">
      <PageHeader title="Methodology & limitations" subtitle="What this tool measures — and what it does not." />

      {config?.synthetic && <Banner>⚠ This instance runs on synthetic (fabricated) demo data — a stand-in for live feeds. The numbers are not real coverage.</Banner>}

      <Section title="What this measures — and what it does not">
        <p>Two independent signals, both on a <b>−100 … +100</b> scale:</p>
        <p><b className="text-foreground">Media sentiment</b> — the tone of news <i>coverage</i> (GDELT), i.e. how positively or negatively outlets write about a subject.</p>
        <p><b className="text-foreground">Public / social sentiment</b> — model-scored posts from social platforms (Reddit, Bluesky), scored with a RoBERTa sentiment model.</p>
        <p className="text-foreground">Neither is representative public opinion. Media tone reflects editorial framing; social sentiment reflects vocal, non-representative users. The <b>gap</b> between them is the interesting signal — not a poll.</p>
      </Section>

      <Section title="How a score is built">
        <p><b className="text-foreground">Media:</b> coverage is pulled from GDELT, cleaned (dedup, country/date normalization), and rolled up to <b>entity × country × ISO-week</b>, volume-weighted.</p>
        <p><b className="text-foreground">Public:</b> posts are fetched per entity, each post&apos;s text is scored by the model, then aggregated to <b>entity × source × week</b> (author handles are hashed for privacy).</p>
      </Section>

      <Section title="Data-integrity signals (shown throughout)">
        <p><b className="text-foreground">Source diversity</b> — distinct outlets / authors behind a weekly score. More is more robust.</p>
        <p><b className="text-foreground">Low-confidence flag</b> — weeks with too few articles/posts or a single source. GDELT and social coverage are genuinely sparse for smaller countries and languages.</p>
      </Section>

      <Section title="Known limitations">
        <p>• <b className="text-foreground">Coverage/posts ≠ opinion.</b> Both signals are shaped by who publishes, not a representative public.</p>
        <p>• <b className="text-foreground">Selection &amp; outlet bias</b> is not corrected for.</p>
        <p>• <b className="text-foreground">Translation artifacts</b> — non-English coverage is machine-processed; tone can shift.</p>
        <p>• <b className="text-foreground">Sarcasm &amp; irony</b> are frequently misread by tone models.</p>
        <p>• <b className="text-foreground">Correlation ≠ causation</b> — event-impact deltas show tone moved around a date, not that the event caused it.</p>
        <p>• <b className="text-foreground">Forecasts are indicative</b> — short, noisy series; always read the confidence interval.</p>
      </Section>

      <p className="text-xs text-muted">
        Currently tracking <b>{config?.entities.length ?? "…"}</b> entities across <b>{config?.countries.length ?? "…"}</b> countries.
        The watchlist is fully config-driven (<code>config/watchlist.yaml</code>).
      </p>
    </div>
  );
}
