// Session state for the Library page: the last search query, its results,
// and which PMIDs are checked. Stored in sessionStorage so leaving and
// coming back doesn't wipe your work (but a full tab close is a clean slate).

import type { Paper } from "@/lib/api";

const KEY = "biomed_library_session_v1";

type Snapshot = {
  query: string;
  papers: Paper[];
  selected: string[];
};

export function loadSession(): Snapshot {
  if (typeof window === "undefined") return { query: "", papers: [], selected: [] };
  try {
    const raw = window.sessionStorage.getItem(KEY);
    if (!raw) return { query: "", papers: [], selected: [] };
    return JSON.parse(raw) as Snapshot;
  } catch {
    return { query: "", papers: [], selected: [] };
  }
}

export function saveSession(snap: Snapshot): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(KEY, JSON.stringify(snap));
}
