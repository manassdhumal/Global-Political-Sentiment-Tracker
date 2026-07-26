"use client";

import { useEffect, useState } from "react";
import { api } from "./api";

export function useApi<T>(
  path: string | null,
  params?: Record<string, string | number | boolean | undefined | null>,
) {
  const [data, setData] = useState<T | undefined>();
  const [error, setError] = useState<string | undefined>();
  const [loading, setLoading] = useState<boolean>(!!path);
  const key = path ? path + JSON.stringify(params ?? {}) : null;

  useEffect(() => {
    if (!path) { setLoading(false); return; }
    let alive = true;
    setLoading(true); setError(undefined);
    api<T>(path, params)
      .then((d) => { if (alive) { setData(d); setLoading(false); } })
      .catch((e) => { if (alive) { setError(String(e?.message ?? e)); setLoading(false); } });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return { data, error, loading };
}
