import { Link } from "react-router-dom";

const POSITIONS: Record<string, { x: number; y: number }> = {
  "Сонгинохайрхан": { x: 22, y: 25 },
  "Хангарьд": { x: 67, y: 20 },
  "Багануур": { x: 87, y: 34 },
  "Чингэлтэй": { x: 46, y: 39 },
  "Баянгол": { x: 28, y: 46 },
  "Сүхбаатар": { x: 60, y: 53 },
  "Баянзүрх": { x: 78, y: 58 },
  "Хан-Уул": { x: 26, y: 70 },
  "Налайх": { x: 66, y: 79 },
};

const FALLBACK = [
  { x: 15, y: 35 },
  { x: 40, y: 18 },
  { x: 84, y: 48 },
  { x: 50, y: 74 },
];

export function DistrictMap({
  items,
  hrefBuilder,
}: {
  items: { name: string; count: number }[];
  hrefBuilder: (name: string) => string;
}) {
  const max = Math.max(1, ...items.map((item) => item.count));
  const center = { x: 50, y: 51 };

  return (
    <div className="glass-surface relative h-[360px] overflow-hidden rounded-2xl">
      <div
        className="absolute inset-0 opacity-[0.55]"
        style={{
          backgroundImage:
            "linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px)",
          backgroundSize: "44px 44px",
        }}
      />
      <div className="absolute -left-20 -top-24 h-72 w-72 rounded-full bg-fg/[0.06] blur-3xl" />
      <div className="absolute -bottom-32 right-0 h-80 w-80 rounded-full bg-fg/[0.035] blur-3xl" />

      <div className="absolute left-5 top-4 z-10">
        <p className="text-[9px] uppercase tracking-[0.24em] text-fg/25">Geographic distribution</p>
        <p className="mt-1 text-xs font-medium text-fg/55">Улаанбаатар хотын зураглал</p>
      </div>
      <div className="absolute right-5 top-4 z-10 rounded-full border border-fg/[0.07] bg-night-900/60 px-2.5 py-1 font-mono text-[9px] text-fg/30">
        47.9188° N · 106.9176° E
      </div>

      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
        <circle cx="50" cy="51" r="34" fill="none" stroke="currentColor" className="text-fg/[0.08]" strokeDasharray="1 3" />
        <circle cx="50" cy="51" r="19" fill="none" stroke="currentColor" className="text-fg/[0.06]" strokeDasharray="1 3" />
        {items.map((item, index) => {
          const pos = POSITIONS[item.name] ?? FALLBACK[index % FALLBACK.length];
          return (
            <path
              key={item.name}
              d={`M ${center.x} ${center.y} Q ${(center.x + pos.x) / 2} ${Math.min(center.y, pos.y) - 8} ${pos.x} ${pos.y}`}
              fill="none"
              stroke={index < 3 ? "rgba(139,92,246,.42)" : "rgba(56,189,248,.24)"}
              strokeWidth="0.18"
              strokeDasharray={index < 3 ? "none" : "0.8 1.4"}
            />
          );
        })}
        <circle cx="50" cy="51" r="0.8" fill="#22d3ee" />
        <circle cx="50" cy="51" r="3.2" fill="none" stroke="rgba(34,211,238,.35)" className="animate-ping" />
      </svg>

      {items.map((item, index) => {
        const pos = POSITIONS[item.name] ?? FALLBACK[index % FALLBACK.length];
        const size = Math.round(58 + (item.count / max) * 42);
        const strength = item.count / max;
        return (
          <Link
            key={item.name}
            to={hrefBuilder(item.name)}
            className="group absolute z-10 -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
          >
            <span
              className="relative flex items-center justify-center rounded-full border backdrop-blur-sm transition duration-300 group-hover:scale-110 group-hover:border-violet-400/60 group-hover:shadow-[0_0_34px_rgba(139,92,246,0.3)]"
              style={{
                width: size,
                height: size,
                borderColor: `rgba(139,92,246,${0.18 + strength * 0.42})`,
                background: `radial-gradient(circle at 35% 28%, rgba(139,92,246,${0.18 + strength * 0.34}), rgba(14,14,16,.9) 66%)`,
              }}
            >
              <span className="absolute inset-2 rounded-full border border-fg/[0.05]" />
              <span className="text-sm font-semibold text-fg">{item.count}</span>
              <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
            </span>
            <span className="absolute left-1/2 top-[calc(100%+6px)] -translate-x-1/2 whitespace-nowrap rounded-full border border-fg/[0.07] bg-night-900/85 px-2 py-0.5 text-[9px] text-fg/55 backdrop-blur-sm transition group-hover:border-acid-300/30 group-hover:text-fg">
              {item.name}
            </span>
          </Link>
        );
      })}

      <div className="absolute bottom-4 left-5 flex items-center gap-3 text-[9px] text-fg/25">
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-acid-400" /> Өндөр бүртгэл
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-clay/60" /> Бусад дүүрэг
        </span>
      </div>
      <div className="absolute bottom-4 right-5 font-mono text-[9px] text-fg/20">
        {items.length} districts · live
      </div>
    </div>
  );
}
