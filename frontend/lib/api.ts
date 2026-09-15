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

export async function searchPapers(q: string, limit = 10): Promise<SearchResponse> {
  const url = new URL(`${BASE}/api/search`);
  url.searchParams.set("q", q);
  url.searchParams.set("limit", String(limit));
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

export async function askQuestion(question: string, top_k = 6): Promise<AskResponse> {
  return jsonOrThrow<AskResponse>(
    await fetch(`${BASE}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k }),
    }),
  );
}
