"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ingestPapers,
  searchPapers,
  type IngestResponse,
  type Paper,
} from "@/lib/api";
import {
  clearHistory,
  deleteEntry as deleteEntryFn,
  loadHistory,
  type HistoryEntry,
} from "@/lib/history";
import { Sidebar } from "@/components/Sidebar";
import { IconSearch } from "@/components/Icons";
import { useRouter } from "next/navigation";

export default function LibraryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const [query, setQuery] = useState("");
  const [papers, setPapers] = useState<Paper[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestResult, setIngestResult] = useState<IngestResponse | null>(null);

  const selectedList = useMemo(() => Array.from(selected), [selected]);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  async function onSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearchLoading(true);
    setSearchError(null);
    try {
      const res = await searchPapers(query.trim(), 15);
      setPapers(res.papers);
      setSelected(new Set());
      setIngestResult(null);
    } catch (err) {
      setSearchError(err instanceof Error ? err.message : "Search failed");
      setPapers([]);
    } finally {
      setSearchLoading(false);
    }
  }

  function toggle(pmid: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(pmid)) next.delete(pmid);
      else next.add(pmid);
      return next;
    });
  }

  async function onIngest() {
    if (selectedList.length === 0) return;
    setIngestLoading(true);
    setIngestResult(null);
    try {
      const res = await ingestPapers(selectedList);
      setIngestResult(res);
      setSelected(new Set());
    } catch (err) {
      setIngestResult({
        ingested: [],
        skipped: [],
        failed: selectedList,
        chunk_count: 0,
      });
      console.error(err);
    } finally {
      setIngestLoading(false);
    }
  }

  return (
    <div className="flex h-screen">
      <Sidebar
        history={history}
        activeId={null}
        onSelect={(id) => {
          // Send them back to the Ask page with that entry active. Simplest:
          // just navigate — the ask page reloads history from localStorage.
          router.push("/");
          setTimeout(() => {
            // hint the ask page which one to open via hash
            window.location.hash = `q=${id}`;
          }, 0);
        }}
        onDelete={(id) => setHistory(deleteEntryFn(id))}
        onClear={() => {
          clearHistory();
          setHistory([]);
        }}
        onNew={() => router.push("/")}
      />

      <div className="thin-scroll flex-1 overflow-y-auto px-8 py-10">
        <div className="mx-auto max-w-4xl">
          <header className="mb-8">
            <h2 className="text-3xl font-semibold tracking-tight text-ink">Library</h2>
            <p className="mt-1 text-sm text-slate-500">
              Search PubMed and ingest papers into your knowledge base. Ingested papers become searchable by meaning on the Ask page.
            </p>
          </header>

          <section className="mb-8">
            <form
              onSubmit={onSearch}
              className="flex items-center gap-3 rounded-full border border-slate-200 bg-white px-4 py-2 shadow-soft focus-within:border-accent"
            >
              <IconSearch className="h-4 w-4 text-slate-400" />
              <input
                className="flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
                placeholder="Search PubMed — e.g. pancreatic cancer BRCA2"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button
                type="submit"
                disabled={searchLoading || !query.trim()}
                className="rounded-full bg-accent px-4 py-1.5 text-sm font-medium text-white shadow-sm hover:opacity-90 disabled:opacity-40"
              >
                {searchLoading ? "Searching…" : "Search"}
              </button>
            </form>
            {searchError && (
              <p className="mt-2 text-sm text-red-600">{searchError}</p>
            )}
          </section>

          {papers.length > 0 && (
            <section>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-medium text-ink">
                  Results <span className="text-slate-400">({papers.length})</span>
                </h3>
                <button
                  onClick={onIngest}
                  disabled={ingestLoading || selectedList.length === 0}
                  className="rounded-full bg-ink px-4 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
                >
                  {ingestLoading
                    ? "Ingesting…"
                    : `Ingest ${selectedList.length} selected`}
                </button>
              </div>

              {ingestResult && (
                <div className="mb-4 rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-700 shadow-soft">
                  Ingested <b className="text-accent">{ingestResult.ingested.length}</b> new,
                  skipped <b>{ingestResult.skipped.length}</b> already-indexed,
                  failed <b>{ingestResult.failed.length}</b>.
                  Stored <b>{ingestResult.chunk_count}</b> chunks.
                </div>
              )}

              <ul className="space-y-3">
                {papers.map((p, i) => (
                  <li
                    key={p.pmid}
                    className="rounded-2xl border border-slate-200 bg-white p-4 shadow-soft"
                  >
                    <label className="flex cursor-pointer items-start gap-3">
                      <input
                        type="checkbox"
                        checked={selected.has(p.pmid)}
                        onChange={() => toggle(p.pmid)}
                        className="mt-1 h-4 w-4 accent-[color:theme(colors.accent)]"
                      />
                      <div className="flex-1">
                        <div className="flex items-baseline justify-between gap-4">
                          <h4 className="text-sm font-semibold">
                            {i + 1}. {p.title || "(untitled)"}
                          </h4>
                          <span className="whitespace-nowrap text-xs text-slate-500">
                            PMID {p.pmid}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-slate-500">
                          {p.authors.slice(0, 4).join(", ")}
                          {p.authors.length > 4 ? " et al." : ""}
                          {p.journal && <> &middot; <em>{p.journal}</em></>}
                          {p.publication_date && <> &middot; {p.publication_date}</>}
                        </p>
                        {p.abstract && (
                          <p className="mt-2 line-clamp-3 text-sm text-slate-700">
                            {p.abstract}
                          </p>
                        )}
                        <a
                          href={p.pubmed_url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-2 inline-block text-xs font-medium text-accent hover:underline"
                        >
                          View on PubMed →
                        </a>
                      </div>
                    </label>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {papers.length === 0 && !searchLoading && (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white/50 p-10 text-center">
              <p className="text-sm text-slate-500">
                No results yet. Try searching PubMed above.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
