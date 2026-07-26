"use client";

import { createContext, useContext } from "react";
import { AppConfig } from "@/lib/api";
import { useApi } from "@/lib/useApi";

interface ConfigCtx {
  config?: AppConfig;
  loading: boolean;
  error?: string;
  entityName: (id: string) => string;
  countryName: (gdelt: string) => string;
  entityOptions: (opts?: { includeAll?: boolean }) => { value: string; label: string }[];
}

const Ctx = createContext<ConfigCtx | null>(null);

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const { data: config, loading, error } = useApi<AppConfig>("/api/config");

  const entityName = (id: string) =>
    config?.entities.find((e) => e.id === id)?.name ?? id;
  const countryName = (g: string) =>
    config?.countries.find((c) => c.gdelt === g)?.name ?? g;
  const entityOptions = (opts?: { includeAll?: boolean }) => {
    const base = (config?.entities ?? []).map((e) => ({ value: e.id, label: e.name }));
    return opts?.includeAll ? [{ value: "__all__", label: "All entities (combined)" }, ...base] : base;
  };

  return (
    <Ctx.Provider value={{ config, loading, error, entityName, countryName, entityOptions }}>
      {children}
    </Ctx.Provider>
  );
}

export function useConfig(): ConfigCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error("useConfig must be used within ConfigProvider");
  return c;
}
