"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getLibraryStats, type LibraryStats } from "@/lib/api";

export function LibraryStatsCard() {
  const [stats, setStats] = useState<LibraryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getLibraryStats()
      .then((s) => !cancelled && setStats(s))
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="mx-auto mt-8 max-w-2xl animate-pulse rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
        <div className="h-4 w-32 rounded bg-slate-200" />
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="h-8 rounded bg-slate-200" />
          <div className="h-8 rounded bg-slate-200" />
          <div className="h-8 rounded bg-slate-200" />
        </div>
      </div>
    );
  }

  if (error || !stats) return null;

  if (stats.paper_count === 0) {
    return (
      <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-dashed border-slate-300 bg-white/60 p-5 text-center">
        <p className="text-sm text-slate-600">
          Your library is empty.{" "}
          <Link
            href="/library"
            className="font-medium text-accent hover:underline"
          >
            Head to Library
          </Link>{" "}
          to search PubMed and ingest papers before asking questions.
        </p>
      </div>
    );
  }

  const range =
    stats.year_min && stats.year_max
      ? stats.year_min === stats.year_max
        ? `${stats.year_min}`
        : `${stats.year_min}–${stats.year_max}`
      : "—";

  return (
    <div className="mx-auto mt-8 max-w-2xl rounded-2xl border border-slate-200 bg-white p-5 shadow-soft">
      <div className="flex items-baseline justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Your library
        </h3>
        <Link
          href="/library"
          className="text-xs font-medium text-accent hover:underline"
        >
          Manage papers →
        </Link>
      </div>

      <div className="mt-3 grid grid-cols-3 divide-x divide-slate-200 text-center">
        <Stat label="Papers" value={stats.paper_count.toLocaleString()} />
        <Stat label="Chunks" value={stats.chunk_count.toLocaleString()} />
        <Stat label="Years" value={range} />
      </div>

      {stats.top_journals.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-1.5">
          {stats.top_journals.map((j) => (
            <span
              key={j.journal}
              className="rounded-full bg-accentSoft px-2.5 py-0.5 text-[11px] font-medium text-accent"
              title={`${j.count} paper${j.count === 1 ? "" : "s"}`}
            >
              {j.journal}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-2">
      <div className="text-xl font-semibold text-ink">{value}</div>
      <div className="mt-0.5 text-[11px] uppercase tracking-wider text-slate-500">
        {label}
      </div>
    </div>
  );
}
