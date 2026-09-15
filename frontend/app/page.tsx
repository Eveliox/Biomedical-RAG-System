"use client";

import { useEffect, useRef, useState } from "react";
import { askQuestion } from "@/lib/api";
import {
  addEntry,
  deleteEntry as deleteEntryFn,
  clearHistory,
  loadHistory,
  newId,
  type HistoryEntry,
} from "@/lib/history";
import { AnswerWithCitations, SourcesList } from "@/components/Answer";
import { Sidebar } from "@/components/Sidebar";
import { IconArrowUp } from "@/components/Icons";
import { LibraryStatsCard } from "@/components/LibraryStatsCard";

const EXAMPLES = [
  "Which genes are commonly mutated in pancreatic cancer?",
  "What molecular markers predict poor prognosis in glioblastoma?",
  "What are common resistance mechanisms to anti-PD-1 therapy?",
];

export default function AskPage() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [active, setActive] = useState<HistoryEntry | null>(null);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  }, [active]);

  async function submit(qText: string) {
    const q = qText.trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    try {
      const res = await askQuestion(q, 6);
      const entry: HistoryEntry = {
        id: newId(),
        question: q,
        answer: res.answer,
        sources: res.sources,
        createdAt: Date.now(),
      };
      const next = addEntry(entry);
      setHistory(next);
      setActive(entry);
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ask failed");
    } finally {
      setLoading(false);
    }
  }

  function onSelect(id: string) {
    const found = history.find((h) => h.id === id) ?? null;
    setActive(found);
  }

  function onDelete(id: string) {
    const next = deleteEntryFn(id);
    setHistory(next);
    if (active?.id === id) setActive(null);
  }

  function onClear() {
    clearHistory();
    setHistory([]);
    setActive(null);
  }

  function onNew() {
    setActive(null);
    setQuestion("");
    setError(null);
  }

  return (
    <div className="flex h-screen">
      <Sidebar
        history={history}
        activeId={active?.id ?? null}
        onSelect={onSelect}
        onDelete={onDelete}
        onClear={onClear}
        onNew={onNew}
      />

      <div className="flex flex-1 flex-col">
        <div
          ref={scrollRef}
          className="thin-scroll flex-1 overflow-y-auto px-8 py-10"
        >
          <div className="mx-auto max-w-3xl">
            {!active ? (
              <EmptyState
                onExample={(q) => {
                  setQuestion(q);
                  submit(q);
                }}
              />
            ) : (
              <ActiveThread
                entry={active}
                loading={loading}
              />
            )}
            {loading && !active && (
              <p className="mt-6 text-sm text-slate-500">Thinking…</p>
            )}
            {error && (
              <p className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </p>
            )}
          </div>
        </div>

        <div className="border-t border-slate-200 bg-white px-8 py-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit(question);
            }}
            className="mx-auto flex max-w-3xl items-center gap-3 rounded-full border border-slate-200 bg-white px-5 py-2 shadow-soft focus-within:border-accent"
          >
            <input
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
              placeholder="Ask the literature…"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="grid h-8 w-8 place-items-center rounded-full bg-accent text-white transition disabled:opacity-40"
              aria-label="Send"
            >
              <IconArrowUp className="h-4 w-4" />
            </button>
          </form>
          <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] italic text-slate-400">
            This tool summarizes biomedical literature and is not a substitute for
            professional medical advice.
          </p>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onExample }: { onExample: (q: string) => void }) {
  return (
    <div className="pt-16 text-center">
      <h2 className="text-3xl font-semibold tracking-tight text-ink">
        Ask the literature.
      </h2>
      <p className="mt-2 text-sm text-slate-500">
        Grounded answers from PubMed papers you&apos;ve ingested. Start with an example or type your own.
      </p>
      <LibraryStatsCard />

      <div className="mx-auto mt-8 grid max-w-2xl gap-3 sm:grid-cols-3">
        {EXAMPLES.map((q) => (
          <button
            key={q}
            onClick={() => onExample(q)}
            className="rounded-xl border border-slate-200 bg-white p-4 text-left text-sm text-slate-700 shadow-soft hover:border-accent hover:text-ink"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function ActiveThread({
  entry,
  loading,
}: {
  entry: HistoryEntry;
  loading: boolean;
}) {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-white p-5 shadow-soft">
        <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-accent">
          Question
        </p>
        <p className="text-[15px] leading-6 text-ink">{entry.question}</p>
      </div>

      <div className="rounded-2xl bg-white p-5 shadow-soft">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-accent">
          Answer
        </p>
        {loading ? (
          <p className="text-sm text-slate-500">Thinking…</p>
        ) : (
          <AnswerWithCitations answer={entry.answer} sources={entry.sources} />
        )}
        <SourcesList sources={entry.sources} />
      </div>
    </div>
  );
}
