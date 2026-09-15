"use client";

import { useMemo, useState } from "react";
import {
  askQuestion,
  ingestPapers,
  searchPapers,
  type AskResponse,
  type IngestResponse,
  type Paper,
} from "@/lib/api";
import { AnswerWithCitations, SourcesList } from "@/components/Answer";

export default function HomePage() {
  // --- search state ---
  const [query, setQuery] = useState("");
  const [papers, setPapers] = useState<Paper[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // --- selection + ingestion state ---
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [ingestLoading, setIngestLoading] = useState(false);
  const [ingestResult, setIngestResult] = useState<IngestResponse | null>(null);

  // --- ask state ---
  const [question, setQuestion] = useState("");
  const [askLoading, setAskLoading] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<AskResponse | null>(null);

  const selectedList = useMemo(() => Array.from(selected), [selected]);

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
      next.has(pmid) ? next.delete(pmid) : next.add(pmid);
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

  async function onAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    setAskLoading(true);
    setAskError(null);
    setAnswer(null);
    try {
      const res = await askQuestion(question.trim(), 6);
      setAnswer(res);
    } catch (err) {
      setAskError(err instanceof Error ? err.message : "Ask failed");
    } finally {
      setAskLoading(false);
    }
  }

  return (
    <div className="space-y-10">
      {/* --------------- Search --------------- */}
      <section>
        <h2 className="mb-3 text-lg font-medium">Search PubMed</h2>
        <form onSubmit={onSearch} className="flex gap-2">
          <input
            className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent"
            placeholder="e.g. pancreatic cancer BRCA2"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="submit"
            disabled={searchLoading || !query.trim()}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white shadow-sm hover:opacity-90 disabled:opacity-50"
          >
            {searchLoading ? "Searching…" : "Search"}
          </button>
        </form>
        {searchError && <p className="mt-2 text-sm text-red-600">{searchError}</p>}
      </section>

      {/* --------------- Results + Ingest --------------- */}
      {papers.length > 0 && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-medium">
              Results <span className="text-slate-400">({papers.length})</span>
            </h2>
            <button
              onClick={onIngest}
              disabled={ingestLoading || selectedList.length === 0}
              className="rounded-md bg-ink px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
            >
              {ingestLoading
                ? "Ingesting…"
                : `Ingest ${selectedList.length} selected`}
            </button>
          </div>

          {ingestResult && (
            <div className="mb-4 rounded-md border border-slate-200 bg-white p-3 text-xs text-slate-700">
              Ingested <b>{ingestResult.ingested.length}</b> new,
              skipped <b>{ingestResult.skipped.length}</b> already-indexed,
              failed <b>{ingestResult.failed.length}</b>.
              Stored <b>{ingestResult.chunk_count}</b> chunks.
            </div>
          )}

          <ul className="space-y-3">
            {papers.map((p, i) => (
              <li
                key={p.pmid}
                className="rounded-md border border-slate-200 bg-white p-4 shadow-sm"
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
                      <h3 className="text-sm font-semibold">
                        {i + 1}. {p.title || "(untitled)"}
                      </h3>
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

      {/* --------------- Ask --------------- */}
      <section>
        <h2 className="mb-3 text-lg font-medium">Ask the Literature</h2>
        <form onSubmit={onAsk} className="flex flex-col gap-2 sm:flex-row">
          <input
            className="flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm outline-none focus:border-accent focus:ring-1 focus:ring-accent"
            placeholder="e.g. What genes are commonly associated with pancreatic cancer?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button
            type="submit"
            disabled={askLoading || !question.trim()}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white shadow-sm hover:opacity-90 disabled:opacity-50"
          >
            {askLoading ? "Thinking…" : "Ask"}
          </button>
        </form>
        {askError && <p className="mt-2 text-sm text-red-600">{askError}</p>}

        {answer && (
          <div className="mt-4 space-y-2">
            <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <AnswerWithCitations answer={answer.answer} sources={answer.sources} />
            </div>
            <div>
              <h3 className="mb-2 mt-4 text-sm font-medium text-slate-600">Sources</h3>
              <SourcesList sources={answer.sources} />
            </div>
            <p className="pt-4 text-xs italic text-slate-500">
              This tool summarizes biomedical literature and is not a substitute for
              professional medical advice.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
