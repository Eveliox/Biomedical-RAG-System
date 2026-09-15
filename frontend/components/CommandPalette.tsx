"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { searchPapers, type Paper } from "@/lib/api";
import { IconSearch } from "@/components/Icons";

// Cmd/Ctrl-K palette to search PubMed without leaving the Ask page.
// Debounces input and keeps the last 6 results in-view.

const OPEN_KEY = "k";

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global keyboard trigger.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const mod = e.metaKey || e.ctrlKey;
      if (mod && e.key.toLowerCase() === OPEN_KEY) {
        e.preventDefault();
        setOpen((v) => !v);
        return;
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 0);
    else {
      setQ("");
      setResults([]);
    }
  }, [open]);

  // Debounced search.
  useEffect(() => {
    if (!q.trim()) {
      setResults([]);
      return;
    }
    let cancelled = false;
    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await searchPapers(q.trim(), 6);
        if (!cancelled) setResults(res.papers);
      } catch {
        if (!cancelled) setResults([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 350);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [q]);

  const hasResults = useMemo(() => results.length > 0, [results]);
  if (!open) return null;

  function goToLibrary() {
    setOpen(false);
    router.push(`/library?q=${encodeURIComponent(q)}`);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center bg-slate-900/40 p-4 pt-32 backdrop-blur-sm"
      onClick={() => setOpen(false)}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
      >
        <div className="flex items-center gap-3 border-b border-slate-100 px-4 py-3">
          <IconSearch className="h-4 w-4 text-slate-400" />
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
            placeholder="Search PubMed…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && q.trim()) goToLibrary();
            }}
          />
          <kbd className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 text-[10px] text-slate-500">
            Esc
          </kbd>
        </div>

        <div className="max-h-96 overflow-y-auto">
          {loading && (
            <p className="px-4 py-6 text-center text-xs text-slate-400">Searching…</p>
          )}
          {!loading && !hasResults && q.trim() && (
            <p className="px-4 py-6 text-center text-xs text-slate-400">
              No results.
            </p>
          )}
          {!loading && !q.trim() && (
            <p className="px-4 py-6 text-center text-xs text-slate-400">
              Type to search PubMed. Enter opens the full Library page.
            </p>
          )}
          <ul>
            {results.map((p) => (
              <li key={p.pmid}>
                <button
                  onClick={goToLibrary}
                  className="w-full border-t border-slate-100 px-4 py-3 text-left hover:bg-slate-50"
                >
                  <div className="text-sm font-medium text-ink line-clamp-1">
                    {p.title}
                  </div>
                  <div className="mt-0.5 text-xs text-slate-500">
                    PMID {p.pmid}
                    {p.journal && <> &middot; {p.journal}</>}
                    {p.publication_date && <> &middot; {p.publication_date}</>}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50 px-4 py-2 text-[10px] uppercase tracking-wider text-slate-500">
          <span>Enter → open in Library</span>
          <span>
            <kbd className="mr-1 rounded border border-slate-200 bg-white px-1 py-0.5 text-[10px]">
              Ctrl
            </kbd>
            <kbd className="rounded border border-slate-200 bg-white px-1 py-0.5 text-[10px]">
              K
            </kbd>
            &nbsp;to toggle
          </span>
        </div>
      </div>
    </div>
  );
}
