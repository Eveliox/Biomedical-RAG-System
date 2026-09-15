// Thin typed client for the FastAPI backend.
// Keeping every fetch call here means components stay UI-focused and
// changing the API surface touches exactly one file.

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Paper = {
  pmid: string;
  title: string;
  abstract: string;
  authors: string[];
  journal: string;
  publication_date: string;
  doi: string | null;
  pubmed_url: string;
};

export type SearchResponse = {
  query: string;
  papers: Paper[];
};

export type IngestResponse = {
  ingested: string[];
  skipped: string[];
  failed: string[];
  chunk_count: number;
};

export type Source = {
  pmid: string;
  title: string;
  journal: string;
  publication_date: string;
  pubmed_url: string;
  relevance_score: number | null;
};

export type AskResponse = {
  question: string;
  answer: string;
  sources: Source[];
};

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${detail || res.statusText}`);
  }
  return (await res.json()) as T;
}

export type SearchFilters = {
  yearFrom?: number | null;
  yearTo?: number | null;
  articleType?: string | null;
};

export async function searchPapers(
  q: string,
  limit = 10,
  filters: SearchFilters = {},
): Promise<SearchResponse> {
  const url = new URL(`${BASE}/api/search`);
  url.searchParams.set("q", q);
  url.searchParams.set("limit", String(limit));
  if (filters.yearFrom) url.searchParams.set("year_from", String(filters.yearFrom));
  if (filters.yearTo) url.searchParams.set("year_to", String(filters.yearTo));
  if (filters.articleType) url.searchParams.set("article_type", filters.articleType);
  return jsonOrThrow<SearchResponse>(await fetch(url.toString()));
}

export async function ingestPapers(pmids: string[]): Promise<IngestResponse> {
  return jsonOrThrow<IngestResponse>(
    await fetch(`${BASE}/api/papers/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pmids }),
    }),
  );
}

export type LibraryStats = {
  paper_count: number;
  chunk_count: number;
  journal_count: number;
  top_journals: { journal: string; count: number }[];
  year_min: number | null;
  year_max: number | null;
};

export async function getLibraryStats(): Promise<LibraryStats> {
  return jsonOrThrow<LibraryStats>(await fetch(`${BASE}/api/library/stats`));
}

export async function askQuestion(question: string, top_k = 6): Promise<AskResponse> {
  return jsonOrThrow<AskResponse>(
    await fetch(`${BASE}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k }),
    }),
  );
}

export type StreamEvent =
  | { type: "sources"; sources: Source[] }
  | { type: "token"; content: string }
  | { type: "done" }
  | { type: "error"; message: string };

export async function askQuestionStream(
  question: string,
  top_k: number,
  handlers: {
    onSources?: (sources: Source[]) => void;
    onToken?: (chunk: string) => void;
    onDone?: () => void;
    onError?: (message: string) => void;
    signal?: AbortSignal;
  },
): Promise<void> {
  const res = await fetch(`${BASE}/api/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k }),
    signal: handlers.signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // NDJSON: split on newlines, keep the last partial line for next round.
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      let ev: StreamEvent;
      try {
        ev = JSON.parse(trimmed) as StreamEvent;
      } catch {
        continue;
      }
      if (ev.type === "sources") handlers.onSources?.(ev.sources);
      else if (ev.type === "token") handlers.onToken?.(ev.content);
      else if (ev.type === "done") handlers.onDone?.();
      else if (ev.type === "error") handlers.onError?.(ev.message);
    }
  }
}
