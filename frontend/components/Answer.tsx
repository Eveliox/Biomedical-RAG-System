"use client";

import type { Source } from "@/lib/api";

// Turn "text [1] more text [2]" into clickable pill superscripts that scroll
// to the matching entry in the sources list below.
export function AnswerWithCitations({
  answer,
  sources,
}: {
  answer: string;
  sources: Source[];
}) {
  const parts = answer.split(/(\[\d+\])/g);
  return (
    <p className="whitespace-pre-wrap text-[15px] leading-7 text-slate-800">
      {parts.map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/);
        if (!m) return <span key={i}>{part}</span>;
        const n = parseInt(m[1], 10);
        const hasSource = n >= 1 && n <= sources.length;
        return (
          <a
            key={i}
            href={hasSource ? `#src-${n}` : undefined}
            className={
              hasSource
                ? "mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-accentSoft px-1.5 text-[10px] font-semibold text-accent align-super hover:bg-accent hover:text-white"
                : "mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-red-100 px-1.5 text-[10px] font-semibold text-red-600 align-super"
            }
            title={
              hasSource
                ? sources[n - 1].title
                : "citation not in sources — possible hallucination"
            }
          >
            {n}
          </a>
        );
      })}
    </p>
  );
}

export function SourcesList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;
  return (
    <div className="mt-6">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Sources
      </h3>
      <ol className="space-y-2">
        {sources.map((s, i) => (
          <li
            id={`src-${i + 1}`}
            key={s.pmid}
            className="rounded-xl border border-slate-200 bg-white p-3 text-sm shadow-soft"
          >
            <div className="flex items-baseline gap-2">
              <span className="grid h-5 min-w-5 place-items-center rounded-full bg-accentSoft px-1.5 text-[10px] font-semibold text-accent">
                {i + 1}
              </span>
              <a
                href={s.pubmed_url}
                target="_blank"
                rel="noreferrer"
                className="font-medium hover:underline"
              >
                {s.title || `PMID ${s.pmid}`}
              </a>
            </div>
            <p className="mt-1 pl-7 text-xs text-slate-500">
              PMID {s.pmid}
              {s.journal && <> &middot; {s.journal}</>}
              {s.publication_date && <> &middot; {s.publication_date}</>}
              {typeof s.relevance_score === "number" && (
                <> &middot; score {s.relevance_score.toFixed(3)}</>
              )}
            </p>
          </li>
        ))}
      </ol>
    </div>
  );
}
