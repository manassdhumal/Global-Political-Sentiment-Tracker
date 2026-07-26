"use client";

import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { reportUrl } from "@/lib/api";
import { useConfig } from "@/components/config-context";
import { useWindow, WindowControls } from "@/components/controls";
import { Card, PageHeader, Segmented, Select, Field, Spinner, DISCLAIMER } from "@/components/ui";

export default function ReportsPage() {
  const { config } = useConfig();
  const { w0, w1, setW0, setW1 } = useWindow(config?.weeks);
  const [scope, setScope] = useState("entity");
  const [id, setId] = useState("");
  const [md, setMd] = useState("");
  const [loading, setLoading] = useState(false);

  const options = scope === "entity"
    ? (config?.entities ?? []).map((e) => ({ value: e.id, label: e.name }))
    : (config?.countries ?? []).map((c) => ({ value: c.gdelt, label: c.name }));
  const curId = id || options[0]?.value || "";

  useEffect(() => { setId(""); }, [scope]);

  useEffect(() => {
    if (!curId || !w0 || !w1) return;
    setLoading(true);
    fetch(reportUrl({ scope, id: curId, w0, w1, format: "markdown" }))
      .then((r) => r.text()).then(setMd).catch(() => setMd("Failed to load preview."))
      .finally(() => setLoading(false));
  }, [scope, curId, w0, w1]);

  return (
    <div className="space-y-6">
      <PageHeader title="Exportable reports" subtitle="A shareable media-sentiment summary for an entity or country — as Markdown or PDF.">
        <Field label="Scope"><Segmented value={scope} onChange={setScope} options={[{ value: "entity", label: "Entity" }, { value: "country", label: "Country" }]} /></Field>
        <Field label={scope === "entity" ? "Entity" : "Country"}><Select value={curId} onChange={setId} options={options} /></Field>
        <WindowControls weeks={config?.weeks} w0={w0} w1={w1} setW0={setW0} setW1={setW1} />
      </PageHeader>

      <div className="flex flex-wrap gap-3">
        <a href={reportUrl({ scope, id: curId, w0, w1, format: "markdown" })}
          className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2 text-sm hover:border-accent/50">
          <Download size={15} /> Download Markdown
        </a>
        <a href={reportUrl({ scope, id: curId, w0, w1, format: "pdf" })}
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white">
          <Download size={15} /> Download PDF
        </a>
      </div>

      <Card className="p-4">
        <div className="mb-2 text-sm font-medium">Preview</div>
        {loading ? <Spinner /> : <pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap font-mono text-xs text-foreground/90">{md}</pre>}
      </Card>
      <p className="text-xs text-muted">{DISCLAIMER}</p>
    </div>
  );
}
