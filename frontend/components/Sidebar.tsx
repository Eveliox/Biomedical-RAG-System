"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { HistoryEntry } from "@/lib/history";
import {
  IconDna,
  IconLibrary,
  IconMessage,
  IconPlus,
  IconTrash,
  IconUser,
} from "@/components/Icons";

function IconChart({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 20h16" />
      <path d="M7 20V10" />
      <path d="M12 20V4" />
      <path d="M17 20v-7" />
    </svg>
  );
}

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
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="grid h-8 w-8 place-items-center rounded-md bg-ink text-white">
          <IconDna className="h-4 w-4" />
        </div>
        <h1 className="text-sm font-semibold tracking-wide text-ink">
          Biomed&nbsp;RAG
        </h1>
      </div>

      <div className="px-4">
        <button
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-full bg-accent px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:opacity-90"
        >
          <IconPlus className="h-4 w-4" />
          New question
        </button>
        <p className="mt-2 text-center text-[10px] uppercase tracking-wider text-slate-400">
          <kbd className="rounded border border-slate-200 bg-white px-1 py-0.5 text-[10px] text-slate-500">
            Ctrl
          </kbd>{" "}
          +{" "}
          <kbd className="rounded border border-slate-200 bg-white px-1 py-0.5 text-[10px] text-slate-500">
            K
          </kbd>{" "}
          quick search
        </p>
      </div>

      <div className="mt-6 flex items-center justify-between px-5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
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
              <button
                onClick={() => onSelect(h.id)}
                className="flex-1 truncate text-left"
                title={h.question}
              >
                {h.question}
              </button>
              <button
                onClick={() => onDelete(h.id)}
                className="text-slate-400 opacity-0 transition group-hover:opacity-100 hover:text-red-500"
                aria-label="Delete"
                title="Delete"
              >
                <IconTrash />
              </button>
            </div>
          );
        })}
      </nav>

      <div className="mt-auto border-t border-slate-200 p-3">
        <Link
          href="/"
          className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
            pathname === "/"
              ? "bg-white text-ink shadow-soft"
              : "text-slate-700 hover:bg-white/60"
          }`}
        >
          <IconMessage />
          <span className="flex-1">Ask</span>
        </Link>
        <Link
          href="/library"
          className={`mt-1 flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
            pathname === "/library"
              ? "bg-white text-ink shadow-soft"
              : "text-slate-700 hover:bg-white/60"
          }`}
        >
          <IconLibrary />
          <span className="flex-1">Library</span>
          <span className="text-[10px] uppercase tracking-wider text-slate-400">Papers</span>
        </Link>
        <Link
          href="/insights"
          className={`mt-1 flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
            pathname === "/insights"
              ? "bg-white text-ink shadow-soft"
              : "text-slate-700 hover:bg-white/60"
          }`}
        >
          <IconChart />
          <span className="flex-1">Insights</span>
        </Link>
        <div className="mt-3 flex items-center gap-2 rounded-md px-3 py-2 text-xs text-slate-500">
          <div className="grid h-7 w-7 place-items-center rounded-full bg-slate-200 text-slate-500">
            <IconUser className="h-4 w-4" />
          </div>
          <span>Researcher</span>
        </div>
      </div>
    </aside>
  );
}
