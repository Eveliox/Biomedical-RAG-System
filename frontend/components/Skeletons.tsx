"use client";

// Shimmer placeholders shown while the backend is thinking.
// Better UX than a spinner: users see roughly what's about to appear.

export function PaperResultSkeleton() {
  return (
    <div className="animate-pulse rounded-2xl border border-slate-200 bg-white p-4 shadow-soft">
      <div className="flex items-start gap-3">
        <div className="mt-1 h-4 w-4 rounded bg-slate-200" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-3/4 rounded bg-slate-200" />
          <div className="h-3 w-1/2 rounded bg-slate-100" />
          <div className="mt-3 space-y-1.5">
            <div className="h-3 w-full rounded bg-slate-100" />
            <div className="h-3 w-11/12 rounded bg-slate-100" />
            <div className="h-3 w-4/5 rounded bg-slate-100" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function PaperResultsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <ul className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <li key={i}>
          <PaperResultSkeleton />
        </li>
      ))}
    </ul>
  );
}

export function AnswerSkeleton() {
  return (
    <div className="space-y-6">
      <div className="animate-pulse rounded-2xl bg-white p-5 shadow-soft">
        <div className="h-3 w-16 rounded bg-slate-200" />
        <div className="mt-3 h-4 w-3/4 rounded bg-slate-100" />
      </div>
      <div className="animate-pulse rounded-2xl bg-white p-5 shadow-soft">
        <div className="h-3 w-16 rounded bg-slate-200" />
        <div className="mt-3 space-y-2">
          <div className="h-3 w-full rounded bg-slate-100" />
          <div className="h-3 w-11/12 rounded bg-slate-100" />
          <div className="h-3 w-10/12 rounded bg-slate-100" />
          <div className="h-3 w-9/12 rounded bg-slate-100" />
          <div className="h-3 w-11/12 rounded bg-slate-100" />
        </div>
        <div className="mt-6">
          <div className="h-3 w-12 rounded bg-slate-200" />
          <div className="mt-3 space-y-2">
            <div className="h-10 rounded-xl bg-slate-100" />
            <div className="h-10 rounded-xl bg-slate-100" />
            <div className="h-10 rounded-xl bg-slate-100" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function IngestProgressSkeleton({ count }: { count: number }) {
  return (
    <div className="animate-pulse rounded-xl border border-slate-200 bg-white p-3 text-xs shadow-soft">
      <div className="flex items-center gap-2">
        <div className="h-3 w-3 rounded-full bg-accent" />
        <span className="text-slate-600">
          Ingesting {count} paper{count === 1 ? "" : "s"}
          <span className="ml-1 inline-block">…</span>
        </span>
      </div>
      <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-slate-100">
        <div className="h-full w-1/3 animate-[shimmer_1.4s_infinite] rounded-full bg-accent" />
      </div>
    </div>
  );
}
