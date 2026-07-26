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
        <p><b className="text-foreground">Open-ended topics:</b> any topic is a query. Trending and Browse rank a curated catalog, but the &ldquo;Analyze a topic&rdquo; page runs the same analysis on <b>anything you type</b> — on demand.</p>
        <p><b className="text-foreground">Media:</b> coverage is pulled from GDELT, cleaned, and rolled up to weekly tone (volume-weighted across countries).</p>
        <p><b className="text-foreground">Public:</b> social posts are fetched per topic, each post&apos;s text scored by the model, then aggregated weekly (author handles hashed for privacy).</p>
        <p><b className="text-foreground">History:</b> each topic&apos;s series runs from when it first appeared (its &ldquo;inception&rdquo;), so timelines can span years and vary in length by topic.</p>
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
        The browse catalog is curated in <code>config/topics.yaml</code>, but the system is
        <b> open-ended</b> — any topic can be analysed on demand, across <b>{config?.countries.length ?? "…"}</b> countries.
      </p>
    </div>
  );
}
