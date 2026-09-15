"use client";

// Inline SVG bar/line primitives. No chart library — keeps the bundle
// small and the visual style consistent with the rest of the UI.

type BarRow = { label: string; value: number };

export function HorizontalBars({
  rows,
  color = "#6366f1",
}: {
  rows: BarRow[];
  color?: string;
}) {
  if (rows.length === 0) {
    return <p className="text-xs text-slate-400">No data yet.</p>;
  }
  const max = Math.max(...rows.map((r) => r.value), 1);
  return (
    <ul className="space-y-1.5">
      {rows.map((r) => (
        <li key={r.label} className="grid grid-cols-[minmax(0,7rem)_1fr_auto] items-center gap-3">
          <span className="truncate text-xs font-medium text-slate-700" title={r.label}>
            {r.label}
          </span>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full"
              style={{
                width: `${(r.value / max) * 100}%`,
                background: color,
              }}
            />
          </div>
          <span className="text-xs tabular-nums text-slate-500">{r.value}</span>
        </li>
      ))}
    </ul>
  );
}

export function YearTimeline({
  points,
  color = "#6366f1",
}: {
  points: { year: number; count: number }[];
  color?: string;
}) {
  if (points.length === 0) {
    return <p className="text-xs text-slate-400">No data yet.</p>;
  }
  const w = 480;
  const h = 140;
  const padL = 32;
  const padR = 12;
  const padT = 12;
  const padB = 24;

  const years = points.map((p) => p.year);
  const counts = points.map((p) => p.count);
  const minY = Math.min(...years);
  const maxY = Math.max(...years);
  const maxC = Math.max(...counts, 1);

  // If only one year, render a single centered bar.
  const spanX = Math.max(1, maxY - minY);
  const x = (y: number) => padL + ((y - minY) / spanX) * (w - padL - padR);
  const yFor = (c: number) => padT + (1 - c / maxC) * (h - padT - padB);

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full">
      {/* y-axis grid: 0, mid, max */}
      {[0, Math.round(maxC / 2), maxC].map((v, i) => (
        <g key={i}>
          <line
            x1={padL}
            x2={w - padR}
            y1={yFor(v)}
            y2={yFor(v)}
            stroke="#e2e8f0"
            strokeDasharray="2 3"
          />
          <text x={4} y={yFor(v) + 4} fontSize="10" fill="#94a3b8">
            {v}
          </text>
        </g>
      ))}
      {/* bars */}
      {points.map((p, i) => {
        const cx = x(p.year);
        const barW = Math.max(6, ((w - padL - padR) / (points.length + 1)) * 0.6);
        const y0 = h - padB;
        const y1 = yFor(p.count);
        return (
          <g key={i}>
            <rect
              x={cx - barW / 2}
              y={y1}
              width={barW}
              height={y0 - y1}
              rx="3"
              fill={color}
              opacity="0.85"
            />
            <text
              x={cx}
              y={h - 6}
              textAnchor="middle"
              fontSize="10"
              fill="#64748b"
            >
              {p.year}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
