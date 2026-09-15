"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { HistoryEntry } from "@/lib/history";

type Props = {
  history: HistoryEntry[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onClear: () => void;
  onNew: () => void;
};

export function Sidebar({
  history,
  activeId,
  onSelect,
  onDelete,
  onClear,
  onNew,
}: Props) {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-72 flex-col border-r border-slate-200 bg-sidebar">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="grid h-8 w-8 place-items-center rounded-md bg-accent text-xs font-bold text-white">
          Bx
        </div>
        <h1 className="text-sm font-semibold tracking-wide text-ink">
          BIOMED RAG
        </h1>
      </div>

      <div className="px-4">
        <button
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-full bg-accent px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:opacity-90"
        >
          <span className="text-lg leading-none">+</span> New question
        </button>
      </div>

      <div className="mt-6 flex items-center justify-between px-5 text-xs font-medium uppercase tracking-wider text-slate-500">
        <span>Your questions</span>
        {history.length > 0 && (
          <button
            onClick={onClear}
            className="text-[10px] font-medium text-accent hover:underline"
          >
            Clear all
          </button>
        )}
      </div>

      <nav className="thin-scroll mt-2 flex-1 space-y-1 overflow-y-auto px-2 pb-4">
        {history.length === 0 && (
          <p className="px-3 py-4 text-xs text-slate-500">
            Your past questions will appear here.
          </p>
        )}
        {history.map((h) => {
          const isActive = h.id === activeId;
          return (
            <div
              key={h.id}
              className={`group flex items-center gap-2 rounded-md px-3 py-2 text-sm ${
                isActive
                  ? "bg-white text-ink shadow-soft"
                  : "text-slate-700 hover:bg-white/60"
              }`}
            >
              <span className="text-slate-400">◦</span>
              <button
                onClick={() => onSelect(h.id)}
                className="flex-1 truncate text-left"
                title={h.question}
              >
                {h.question}
              </button>
              <button
                onClick={() => onDelete(h.id)}
                className="opacity-0 transition group-hover:opacity-100"
                aria-label="Delete"
                title="Delete"
              >
                <span className="text-xs text-slate-400 hover:text-red-500">×</span>
              </button>
            </div>
          );
        })}
      </nav>

      <div className="mt-auto border-t border-slate-200 p-3">
        <Link
          href="/library"
          className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
            pathname === "/library"
              ? "bg-white text-ink shadow-soft"
              : "text-slate-700 hover:bg-white/60"
          }`}
        >
          <span>📚</span>
          <span className="flex-1">Library</span>
          <span className="text-xs text-slate-400">Manage papers</span>
        </Link>
        <Link
          href="/"
          className={`mt-1 flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
            pathname === "/"
              ? "bg-white text-ink shadow-soft"
              : "text-slate-700 hover:bg-white/60"
          }`}
        >
          <span>💬</span>
          <span className="flex-1">Ask</span>
        </Link>
        <div className="mt-3 flex items-center gap-2 rounded-md px-3 py-2 text-xs text-slate-500">
          <div className="grid h-6 w-6 place-items-center rounded-full bg-slate-200 text-[10px] font-semibold text-slate-600">
            YOU
          </div>
          <span>Researcher</span>
        </div>
      </div>
    </aside>
  );
}
