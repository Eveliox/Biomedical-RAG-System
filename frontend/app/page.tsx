"use client";

import { useState } from "react";
import { searchPapers, type Paper } from "@/lib/api";

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchPapers(query.trim(), 10);
      setPapers(res.papers);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
      setPapers([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
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
            disabled={loading || !query.trim()}
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white shadow-sm hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </form>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-medium">
          Retrieved Papers {papers.length > 0 && <span className="text-slate-400">({papers.length})</span>}
        </h2>
        {papers.length === 0 && !loading && (
          <p className="text-sm text-slate-500">
            No results yet. Try a query above.
          </p>
        )}
        <ul className="space-y-4">
          {papers.map((p, i) => (
            <li key={p.pmid} className="rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-baseline justify-between gap-4">
                <h3 className="text-sm font-semibold">
                  {i + 1}. {p.title || "(untitled)"}
                </h3>
                <span className="whitespace-nowrap text-xs text-slate-500">PMID {p.pmid}</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                {p.authors.slice(0, 4).join(", ")}
                {p.authors.length > 4 ? " et al." : ""}
                {p.journal && <> &middot; <em>{p.journal}</em></>}
                {p.publication_date && <> &middot; {p.publication_date}</>}
              </p>
              {p.abstract && (
                <p className="mt-2 line-clamp-4 text-sm text-slate-700">{p.abstract}</p>
              )}
              <a
                href={p.pubmed_url}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-block text-xs font-medium text-accent hover:underline"
              >
                View on PubMed →
              </a>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
