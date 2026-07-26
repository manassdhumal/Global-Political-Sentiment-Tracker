"use client";

import { useEffect, useState } from "react";
import { Field, Select } from "./ui";

/** Manages a [from, to] week window, defaulting to the full available range. */
export function useWindow(weeks: string[] | undefined) {
  const [w0, setW0] = useState<string>("");
  const [w1, setW1] = useState<string>("");
  useEffect(() => {
    if (weeks && weeks.length) {
      setW0((p) => p || weeks[0]);
      setW1((p) => p || weeks[weeks.length - 1]);
    }
  }, [weeks]);
  return { w0, w1, setW0, setW1 };
}

export function WindowControls({
  weeks, w0, w1, setW0, setW1,
}: {
  weeks: string[] | undefined;
  w0: string; w1: string;
  setW0: (v: string) => void; setW1: (v: string) => void;
}) {
  if (!weeks || !weeks.length) return null;
  const opts = weeks.map((w) => ({ value: w, label: w }));
  return (
    <>
      <Field label="From"><Select value={w0} onChange={setW0} options={opts} className="min-w-32" /></Field>
      <Field label="To"><Select value={w1} onChange={setW1} options={opts} className="min-w-32" /></Field>
    </>
  );
}
