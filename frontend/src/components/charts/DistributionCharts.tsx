import { Link } from "react-router-dom";
import { clsx } from "clsx";

export interface ChartSegment {
  label: string;
  value: number;
  color: string;
  href?: string;
}

const CARD_HOVER = "transition hover:bg-fg/[0.05]";

export function DonutChart({
  segments,
  centerLabel,
  centerValue,
  emptyText = "Мэдээлэл байхгүй",
  showLabels = false,
}: {
  segments: ChartSegment[];
  centerLabel: string;
  centerValue: number;
  emptyText?: string;
  showLabels?: boolean;
}) {
  const visible = segments.filter((segment) => segment.value > 0);
  const total = visible.reduce((sum, segment) => sum + segment.value, 0);
  let cursor = 0;
  const labels: { x: number; y: number; value: number; color: string }[] = [];

  return (
    <div>
      <div className="relative mx-auto h-56 w-full max-w-64">
        <svg viewBox="0 0 240 240" className="h-full w-full">
          <circle cx="120" cy="120" r="78" fill="none" stroke="currentColor" strokeWidth="18" className="text-fg/[0.08]" />
          <circle cx="120" cy="120" r="101" fill="none" stroke="currentColor" strokeWidth="1" className="text-fg/[0.05]" />
          <circle cx="120" cy="120" r="54" fill="none" stroke="currentColor" strokeWidth="1" className="text-fg/[0.05]" />
          {total > 0 &&
            visible.map((segment) => {
              const length = (segment.value / total) * 100;
              const offset = -cursor;
              const mid = cursor + length / 2;
              cursor += length;
              if (showLabels && length >= 7) {
                const angle = (mid / 100) * Math.PI * 2 - Math.PI / 2;
                labels.push({
                  x: 120 + Math.cos(angle) * 105,
                  y: 120 + Math.sin(angle) * 105,
                  value: Math.round(length),
                  color: segment.color,
                });
              }
              return (
                <g key={segment.label} className="drop-shadow-[0_0_10px_rgba(99,102,241,0.18)]">
                  <circle
                    cx="120"
                    cy="120"
                    r="78"
                    fill="none"
                    stroke={segment.color}
                    strokeWidth="18"
                    pathLength={100}
                    strokeDasharray={`${Math.max(length - 0.5, 0.2)} ${100 - Math.max(length - 0.5, 0.2)}`}
                    strokeDashoffset={offset}
                    transform="rotate(-90 120 120)"
                    strokeLinecap="butt"
                    className="transition-all duration-700"
                  >
                    <title>{`${segment.label}: ${segment.value}`}</title>
                  </circle>
                </g>
              );
            })}
          {labels.map((label) => (
            <g key={`${label.x}-${label.y}`}>
              <circle cx={label.x} cy={label.y} r="15" className="fill-night-800 stroke-fg/15" strokeWidth="1" />
              <text
                x={label.x}
                y={label.y + 3.5}
                textAnchor="middle"
                className="fill-fg text-[10px] font-semibold"
              >
                {label.value}%
              </text>
            </g>
          ))}
          <text x="120" y="116" textAnchor="middle" className="fill-fg text-[25px] font-semibold tracking-tight">
            {total > 0 ? centerValue.toLocaleString("mn-MN") : "—"}
          </text>
          <text x="120" y="136" textAnchor="middle" className="fill-fg/45 text-[9px] uppercase tracking-[0.16em]">
            {centerLabel}
          </text>
        </svg>
      </div>
      <div className="mt-2 space-y-0.5">
        {segments.map((segment) => {
          const percent = total > 0 ? (segment.value / total) * 100 : 0;
          const row = (
            <>
              <span className="flex min-w-0 items-center gap-2.5">
                <span
                  className="h-2 w-2 shrink-0 rounded-full shadow-[0_0_10px_currentColor]"
                  style={{ backgroundColor: segment.color, color: segment.color }}
                />
                <span className="truncate text-xs font-medium text-fg/65">{segment.label}</span>
              </span>
              <span className="flex items-center gap-3 text-xs">
                <span className="font-mono text-[10px] text-fg/30">{percent.toFixed(0)}%</span>
                <span className="w-12 text-right font-semibold text-fg">
                  {segment.value.toLocaleString("mn-MN")}
                </span>
              </span>
            </>
          );
          return segment.href && segment.value > 0 ? (
            <Link
              key={segment.label}
              to={segment.href}
              className={clsx("flex items-center justify-between gap-2 rounded-lg px-2 py-1.5", CARD_HOVER)}
            >
              {row}
            </Link>
          ) : (
            <div key={segment.label} className="flex items-center justify-between gap-2 px-2 py-1.5">
              {row}
            </div>
          );
        })}
        {visible.length === 0 && <p className="py-2 text-center text-xs text-fg/30">{emptyText}</p>}
      </div>
    </div>
  );
}

export function HorizontalBars({
  items,
  emptyText = "Мэдээлэл байхгүй",
  hrefBuilder,
  color = "bg-gradient-to-r from-fg/60 to-fg",
}: {
  items: { name: string; count: number; href?: string }[];
  emptyText?: string;
  hrefBuilder?: (name: string) => string;
  color?: string;
}) {
  const max = Math.max(1, ...items.map((item) => item.count));
  if (items.length === 0) {
    return <p className="py-8 text-center text-xs text-fg/30">{emptyText}</p>;
  }
  return (
    <div className="space-y-1">
      {items.map((item, index) => {
        const href = item.href ?? hrefBuilder?.(item.name);
        const body = (
          <div className="flex items-center gap-3 rounded-xl px-2 py-2">
            <span className="w-4 shrink-0 font-mono text-[10px] text-fg/20">{String(index + 1).padStart(2, "0")}</span>
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline justify-between gap-2">
                <span className="truncate text-xs font-medium text-fg/65">{item.name}</span>
                <span className="shrink-0 text-[11px] font-semibold text-fg">
                  {item.count.toLocaleString("mn-MN")}
                </span>
              </div>
              <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-fg/[0.06]">
                <div
                  className={clsx("h-full rounded-full transition-all duration-700", color)}
                  style={{ width: `${Math.max(5, (item.count / max) * 100)}%` }}
                />
              </div>
            </div>
          </div>
        );
        return href ? (
          <Link key={item.name} to={href} className={clsx("block rounded-xl", CARD_HOVER)}>
            {body}
          </Link>
        ) : (
          <div key={item.name}>{body}</div>
        );
      })}
    </div>
  );
}

export function AgeBars({
  buckets,
  ageHref,
}: {
  buckets: { label: string; count: number; min_age: number | null; max_age: number | null }[];
  ageHref: (min: number | null, max: number | null) => string;
}) {
  const max = Math.max(1, ...buckets.map((bucket) => bucket.count));
  return (
    <div className="flex min-h-56 items-end gap-1.5 pt-2 sm:gap-2.5">
      {buckets.map((bucket) => {
        const height = bucket.count > 0 ? Math.max(7, (bucket.count / max) * 100) : 2;
        const href = bucket.min_age === null ? undefined : ageHref(bucket.min_age, bucket.max_age);
        const isUnknown = bucket.min_age === null;
        const body = (
          <div className="group flex h-full w-full flex-col items-center justify-end gap-2">
            <span className="text-[10px] font-semibold text-fg/55 transition group-hover:text-acid-300">
              {bucket.count.toLocaleString("mn-MN")}
            </span>
            <div
              className={clsx(
                "relative w-full max-w-14 rounded-full border transition-all duration-500",
                isUnknown
                  ? "border-fg/[0.06] bg-fg/[0.08]"
                  : "border-acid-300/10 bg-gradient-to-t from-acid-600/25 via-acid-500/70 to-acid-300 group-hover:shadow-[0_0_28px_rgba(99,102,241,0.28)]",
              )}
              style={{ height: `${height}%` }}
              title={`${bucket.label}: ${bucket.count}`}
            >
              {!isUnknown && (
                <span className="absolute inset-x-2 top-2 h-px rounded bg-fg/60 opacity-70" />
              )}
            </div>
            <span className="whitespace-nowrap text-[9px] text-fg/30 sm:text-[10px]">{bucket.label}</span>
          </div>
        );
        return href && bucket.count > 0 ? (
          <Link key={bucket.label} to={href} className={clsx("flex h-52 flex-1 items-end rounded-xl px-1", CARD_HOVER)}>
            {body}
          </Link>
        ) : (
          <div key={bucket.label} className="flex h-52 flex-1 items-end px-1">
            {body}
          </div>
        );
      })}
    </div>
  );
}

export function DailyTrend({
  items,
  total,
  max: providedMax,
}: {
  items: { date: string; count: number }[];
  total: number;
  max?: number;
}) {
  const width = 640;
  const height = 190;
  const padX = 20;
  const padTop = 22;
  const padBottom = 28;
  const max = providedMax ?? Math.max(1, ...items.map((item) => item.count));
  const stepX = items.length > 1 ? (width - padX * 2) / (items.length - 1) : 0;
  const points = items.map((item, index) => ({
    x: padX + index * stepX,
    y: padTop + (1 - item.count / max) * (height - padTop - padBottom),
    ...item,
  }));
  const line = points.map((point) => `${point.x},${point.y}`).join(" ");
  const area = `M ${points[0]?.x ?? padX},${height - padBottom} L ${line.replaceAll(",", " ")} L ${points.at(-1)?.x ?? width - padX},${height - padBottom} Z`;
  const weekdays = ["Ням", "Дав", "Мяг", "Лха", "Пүр", "Баа", "Бям"];

  return (
    <div>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-3xl font-semibold tracking-[-0.04em] text-fg">
            {total.toLocaleString("mn-MN")}
          </p>
          <p className="mt-1 text-[11px] text-fg/35">Сүүлийн 7 хоногийн шинэ бүртгэл</p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full border border-acid-400/20 bg-acid-400/[0.07] px-3 py-1.5 text-[10px] font-medium text-acid-300">
          <span className="h-1.5 w-1.5 rounded-full bg-acid-400 shadow-[0_0_8px_rgba(34,211,238,0.75)]" />
          Өдрийн дээд {max}
        </div>
      </div>
      <div className="mt-3">
        <svg viewBox={`0 0 ${width} ${height}`} className="h-48 w-full overflow-visible">
          <defs>
            <linearGradient id="trend-area" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#818cf8" stopOpacity="0.28" />
              <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
            </linearGradient>
            <linearGradient id="trend-line" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="60%" stopColor="#a78bfa" />
              <stop offset="100%" stopColor="#22d3ee" />
            </linearGradient>
            <filter id="trend-glow">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          {[0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={ratio}
              x1={padX}
              x2={width - padX}
              y1={padTop + (1 - ratio) * (height - padTop - padBottom)}
              y2={padTop + (1 - ratio) * (height - padTop - padBottom)}
              stroke="currentColor" className="text-fg/[0.06]"
              strokeDasharray="3 8"
            />
          ))}
          <path d={area} fill="url(#trend-area)" />
          <polyline
            points={line}
            fill="none"
            stroke="url(#trend-line)"
            strokeWidth="2.5"
            strokeLinejoin="round"
            strokeLinecap="round"
            filter="url(#trend-glow)"
          />
          {points.map((point, index) => {
            const date = new Date(`${point.date}T00:00:00`);
            const isToday = index === points.length - 1;
            return (
              <g key={point.date}>
                <circle
                  cx={point.x}
                  cy={point.y}
                  r={isToday ? 6 : 3.5}
                  fill={isToday ? "#22d3ee" : "#18181b"}
                  stroke={isToday ? "#67e8f9" : "#a78bfa"}
                  strokeWidth="2"
                >
                  <title>{`${point.date}: ${point.count}`}</title>
                </circle>
                <text
                  x={point.x}
                  y={height - 9}
                  textAnchor="middle"
                  className="fill-fg/40 text-[9px]"
                >
                  {weekdays[date.getDay()]}
                </text>
                <text
                  x={point.x}
                  y={height + 5}
                  textAnchor="middle"
                  className="fill-fg/25 text-[8px]"
                >
                  {point.date.slice(8, 10)}.{point.date.slice(5, 7)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
