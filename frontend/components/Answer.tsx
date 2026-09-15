"use client";

import type { Source } from "@/lib/api";
import { GENE_REGEX, isGeneSymbol } from "@/lib/genes";

// Render an answer with two enhancements:
//   1. Citation pills:  [1] → clickable superscript that scrolls to source
//   2. Gene highlights: KRAS / TP53 / etc. get a subtle pill styling.
//
// Both stack — a gene symbol next to a citation still renders correctly.

export function AnswerWithCitations({
  answer,
  sources,
}: {
  answer: string;
  sources: Source[];
}) {
  // First split on citations (they never overlap with gene tokens).
  const citParts = answer.split(/(\[\d+\])/g);
  return (
    <p className="whitespace-pre-wrap text-[15px] leading-7 text-slate-800">
      {citParts.map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/);
        if (m) {
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
        }
        return <HighlightGenes key={i} text={part} />;
      })}
    </p>
  );
}

export function HighlightGenes({ text }: { text: string }) {
  if (!text) return null;
  const pieces = text.split(GENE_REGEX);
  return (
    <>
      {pieces.map((piece, i) => {
        if (isGeneSymbol(piece)) {
          return (
            <span
              key={i}
              className="rounded bg-emerald-50 px-1 py-0.5 font-mono text-[13px] font-semibold text-emerald-700"
              title="Detected gene symbol"
            >
              {piece}
            </span>
          );
        }
        return <span key={i}>{piece}</span>;
      })}
    </>
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
                <HighlightGenes text={s.title || `PMID ${s.pmid}`} />
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
