"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getLibraryInsights, type LibraryInsights } from "@/lib/api";
import {
  clearHistory,
  deleteEntry as deleteEntryFn,
  loadHistory,
  type HistoryEntry,
} from "@/lib/history";
import { Sidebar } from "@/components/Sidebar";
import { HorizontalBars, YearTimeline } from "@/components/Charts";
import { useRouter } from "next/navigation";

export default function InsightsPage() {
  const router = useRouter();
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [insights, setInsights] = useState<LibraryInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setHistory(loadHistory());
    getLibraryInsights()
      .then(setInsights)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex h-screen">
      <Sidebar
        history={history}
        activeId={null}
        onSelect={() => router.push("/")}
        onDelete={(id) => setHistory(deleteEntryFn(id))}
        onClear={() => {
          clearHistory();
          setHistory([]);
        }}
        onNew={() => router.push("/")}
      />

      <div className="thin-scroll flex-1 overflow-y-auto px-8 py-10">
        <div className="mx-auto max-w-5xl">
          <header className="mb-8">
            <h2 className="text-3xl font-semibold tracking-tight text-ink">
              Insights
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Aggregate view over the papers you&apos;ve ingested. Gene detection is a curated allowlist —{" "}
              <Link href="/library" className="text-accent hover:underline">
                add more papers
              </Link>{" "}
              to see richer patterns.
            </p>
          </header>

          {loading && <InsightsSkeleton />}
          {error && (
            <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </p>
          )}
          {insights && <InsightsBody data={insights} />}
        </div>
      </div>
    </div>
  );
}

function InsightsBody({ data }: { data: LibraryInsights }) {
  const empty =
    data.papers_per_year.length === 0 &&
    data.top_genes.length === 0 &&
    data.top_journals.length === 0;

  if (empty) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white/60 p-10 text-center">
        <p className="text-sm text-slate-600">
          Your library is empty.{" "}
          <Link href="/library" className="font-medium text-accent hover:underline">
            Ingest some papers
          </Link>{" "}
          first — insights populate as your corpus grows.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card title="Papers per year" span="lg:col-span-2">
        <YearTimeline points={data.papers_per_year} />
      </Card>

      <Card title="Most-mentioned genes">
        <HorizontalBars
          color="#10b981"
          rows={data.top_genes.map((g) => ({ label: g.name, value: g.count }))}
        />
        <p className="mt-3 text-[11px] text-slate-400">
          Detected from a curated symbol allowlist. Counts are mentions across
          all chunks (a paper can contribute more than one).
        </p>
      </Card>

      <Card title="Top journals">
        <HorizontalBars
          rows={data.top_journals.map((j) => ({ label: j.name, value: j.count }))}
        />
      </Card>

      <Card title="Top authors" span="lg:col-span-2">
        <HorizontalBars
          color="#f59e0b"
          rows={data.top_authors.map((a) => ({ label: a.name, value: a.count }))}
        />
      </Card>
    </div>
  );
}

function Card({
  title,
  children,
  span = "",
}: {
  title: string;
  children: React.ReactNode;
  span?: string;
}) {
  return (
    <div className={`${span} rounded-2xl border border-slate-200 bg-white p-5 shadow-soft`}>
      <h3 className="mb-4 text-xs font-semibold uppercase tracking-wider text-slate-500">
        {title}
      </h3>
      {children}
    </div>
  );
}

function InsightsSkeleton() {
  return (
    <div className="grid animate-pulse grid-cols-1 gap-6 lg:grid-cols-2">
      <div className="h-40 rounded-2xl bg-white shadow-soft lg:col-span-2" />
      <div className="h-64 rounded-2xl bg-white shadow-soft" />
      <div className="h-64 rounded-2xl bg-white shadow-soft" />
    </div>
  );
}
