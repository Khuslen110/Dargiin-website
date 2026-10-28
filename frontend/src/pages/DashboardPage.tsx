import { useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { clsx } from "clsx";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  Bell,
  BookUser,
  CalendarDays,
  ChevronRight,
  ClipboardList,
  Layers,
  Loader2,
  MapPin,
  Network,
  Plus,
  Sparkles,
  Trash2,
  TrendingUp,
  UserCheck,
  UserRound,
  Users,
} from "lucide-react";
import { api } from "../api/client";
import type { DashboardStats } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { AgeBars, DailyTrend, DonutChart, HorizontalBars } from "../components/charts/DistributionCharts";
import { DistrictMap } from "../components/charts/DistrictMap";
import { AUDIT_ACTION_LABELS, GENDER_LABELS, GROUP_LABELS } from "../lib/labels";
import { GROUP_CHART_COLORS } from "../lib/groups";
import { formatDateTime, formatNumber, fullName, initials } from "../lib/format";

const GENDER_COLORS: Record<string, string> = {
  MALE: "#8b5cf6",
  FEMALE: "#fb7185",
  OTHER: "#38bdf8",
};

const SECTIONS = [
  { id: "overview", label: "Тойм" },
  { id: "demographics", label: "Хүн амын бүтэц" },
  { id: "geography", label: "Газар зүй" },
  { id: "activity", label: "Идэвх" },
];

function peopleHref(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  return `/people?${search.toString()}`;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [section, setSection] = useState("overview");
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardStats>("/dashboard"),
  });

  if (isLoading) {
    return (
      <div className="flex min-h-[70vh] flex-col items-center justify-center gap-3 text-fg/40">
        <Loader2 size={24} className="animate-spin text-acid-400" />
        <p className="text-xs uppercase tracking-[0.24em]">Аналитик ачаалж байна</p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="glass-soft flex min-h-[70vh] flex-col items-center justify-center rounded-3xl text-center">
        <p className="text-sm text-fg/70">Хяналтын самбарыг ачаалж чадсангүй.</p>
        <button
          type="button"
          onClick={() => void refetch()}
          className="mt-4 rounded-full bg-gradient-to-r from-acid-500 to-cyan-500 px-4 py-2 text-xs font-semibold text-white shadow-[0_14px_34px_-18px_rgba(79,70,229,0.9)] transition hover:from-acid-400 hover:to-cyan-400"
        >
          Дахин оролдох
        </button>
      </div>
    );
  }

  const activeRatio = data.total_people > 0 ? (data.active_people / data.total_people) * 100 : 0;
  const genderTotal = data.gender_counts.reduce((sum, item) => sum + item.count, 0);
  const ageTotal = data.age_counts.reduce((sum, item) => sum + item.count, 0);
  const groupTotal = data.group_counts.reduce((sum, item) => sum + item.count, 0);
  const trendTotal = data.daily_registrations.reduce((sum, item) => sum + item.count, 0);
  const trendMax = Math.max(1, ...data.daily_registrations.map((item) => item.count));
  const today = new Date().toLocaleDateString("mn-MN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });

  return (
    <div className="space-y-4 pb-8">
      <section className="glass-surface relative overflow-hidden rounded-[28px] animate-rise">
        <div
          className="pointer-events-none absolute inset-0 opacity-60"
          style={{
            backgroundImage:
              "linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px)",
            backgroundSize: "72px 72px",
            maskImage: "linear-gradient(to bottom, black, transparent 82%)",
          }}
        />
        <div className="pointer-events-none absolute -right-28 -top-40 h-[420px] w-[420px] rounded-full bg-violet-500/[0.16] blur-[110px]" />
        <div className="pointer-events-none absolute -bottom-44 left-1/4 h-80 w-80 rounded-full bg-cyan-500/[0.1] blur-[100px]" />
        <div className="pointer-events-none absolute inset-0 dashboard-noise opacity-[0.035] mix-blend-soft-light" />

        <div className="relative px-5 pb-5 pt-5 sm:px-7 sm:pb-6 sm:pt-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-2 rounded-full border border-acid-400/20 bg-acid-400/[0.06] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-acid-300">
                <span className="h-1.5 w-1.5 rounded-full bg-acid-400 shadow-[0_0_10px_rgba(129,140,248,0.9)]" />
                Live analytics
              </span>
              <span className="hidden rounded-full border border-fg/[0.07] bg-fg/[0.03] px-3 py-1.5 text-[10px] text-fg/40 sm:inline-flex">
                {data.scope_label}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-2 rounded-full border border-fg/[0.07] bg-fg/[0.035] px-3 py-1.5 text-[10px] text-fg/45">
                <CalendarDays size={12} /> {today}
              </span>
              <span className="inline-flex items-center gap-2 rounded-full border border-fg/[0.07] bg-fg/[0.035] px-3 py-1.5 text-[10px] text-fg/45">
                <Bell size={12} /> {data.unread_notifications}
              </span>
            </div>
          </div>

          <div className="mt-7 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-[10px] font-medium uppercase tracking-[0.34em] text-fg/30">
                Иргэдийн нэгдсэн бүртгэл · 2026
              </p>
              <h1 className="mt-2 text-[2.55rem] font-semibold leading-[0.98] tracking-[-0.055em] text-fg sm:text-6xl">
                Хүн амын
                <br />
                <span className="bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent dark:from-violet-300 dark:to-cyan-300">аналитик.</span>
              </h1>
              <p className="mt-4 max-w-xl text-sm leading-6 text-fg/40">
                Хүйс, нас, газар зүй болон шатлын бүтцийг нэг дор харж, диаграм дээр дарж
                шууд шүүлттэй жагсаалт руу шилжинэ.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Link
                to="/structure"
                className="inline-flex h-10 items-center gap-2 rounded-full border border-fg/[0.09] bg-fg/[0.03] px-4 text-xs font-medium text-fg/65 transition hover:border-fg/20 hover:bg-fg/[0.06] hover:text-fg"
              >
                <Network size={15} /> Бүтэц харах
              </Link>
              {user?.permissions.can_edit && (
                <button
                  type="button"
                  onClick={() => navigate("/people/new")}
                  className="inline-flex h-10 items-center gap-2 rounded-full bg-gradient-to-r from-acid-500 to-cyan-500 px-4 text-xs font-semibold text-white shadow-[0_14px_34px_-18px_rgba(79,70,229,0.9)] transition hover:from-acid-400 hover:to-cyan-400 hover:shadow-[0_0_30px_rgba(99,102,241,0.35)]"
                >
                  <Plus size={15} /> Иргэн бүртгэх
                </button>
              )}
            </div>
          </div>

          <div className="mt-7 flex flex-wrap items-center justify-between gap-3 border-t border-fg/[0.06] pt-4">
            <nav className="flex flex-wrap gap-1 rounded-full border border-fg/[0.06] bg-fg/[0.035] p-1">
              {SECTIONS.map((item) => (
                <a
                  key={item.id}
                  href={`#${item.id}`}
                  onClick={() => setSection(item.id)}
                  className={clsx(
                    "rounded-full px-3 py-1.5 text-[11px] font-medium transition",
                    section === item.id
                      ? "bg-fg/[0.09] text-fg"
                      : "text-fg/35 hover:text-fg/70",
                  )}
                >
                  {item.label}
                </a>
              ))}
            </nav>
            <div className="flex items-center gap-4 text-[10px] text-fg/25">
              <span className="hidden items-center gap-1.5 sm:flex">
                <Sparkles size={11} className="text-acid-400" /> Бодит цагийн өгөгдөл
              </span>
              <span className="font-mono">v2.6 / 500k ready</span>
            </div>
          </div>
        </div>
      </section>

      <section id="overview" className="grid scroll-mt-24 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Нийт бүртгэл"
          value={data.total_people}
          hint={`${formatNumber(data.active_people)} идэвхтэй`}
          icon={<Users size={16} />}
          accent="acid"
          aside={<MiniRing value={activeRatio} />}
        />
        <MetricCard
          label="Идэвхтэй"
          value={data.active_people}
          hint={`${activeRatio.toFixed(0)}% нийт бүртгэлээс`}
          icon={<UserCheck size={16} />}
          accent="clay"
          footer={
            <div className="mt-4 h-1 overflow-hidden rounded-full bg-fg/[0.06]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-teal-400 to-teal-500"
                style={{ width: `${Math.min(100, activeRatio)}%` }}
              />
            </div>
          }
        />
        <MetricCard
          label="Өнөөдөр"
          value={data.created_today}
          hint={`Сүүлийн 7 хоногт +${formatNumber(data.created_last_7_days)}`}
          icon={<TrendingUp size={16} />}
          accent="acid"
          footer={<SparkBars values={data.daily_registrations.map((item) => item.count)} />}
        />
        <MetricCard
          label="Устгасан"
          value={data.deleted_people}
          hint={`${data.pending_imports} хүлээгдэж буй импорт`}
          icon={<Trash2 size={16} />}
          accent="brass"
        />
      </section>

      <section id="demographics" className="grid scroll-mt-24 gap-4 xl:grid-cols-12">
        <Panel className="xl:col-span-4">
          <PanelTitle
            eyebrow="Gender balance"
            title="Хүйсийн тэнцвэр"
            description="Идэвхтэй бүртгэлийн харьцаа"
            icon={<UserRound size={14} />}
            action={<ArrowUpRight size={15} className="text-fg/20" />}
          />
          <div className="mt-4">
            <DonutChart
              centerLabel="идэвхтэй"
              centerValue={genderTotal}
              showLabels
              segments={data.gender_counts.map((item) => ({
                label: GENDER_LABELS[item.gender],
                value: item.count,
                color: GENDER_COLORS[item.gender],
                href: peopleHref({ gender: item.gender }),
              }))}
            />
          </div>
        </Panel>

        <Panel className="xl:col-span-5">
          <div className="flex items-start justify-between">
            <PanelTitle
              eyebrow="Age architecture"
              title="Насны бүтэц"
              description="Насны бүлгээр хуваасан идэвхтэй бүртгэл"
              icon={<CalendarDays size={14} />}
            />
            <div className="text-right">
              <p className="text-2xl font-semibold tracking-[-0.04em] text-fg">
                {formatNumber(ageTotal)}
              </p>
              <p className="text-[9px] uppercase tracking-[0.18em] text-fg/25">Нийт</p>
            </div>
          </div>
          <AgeBars
            buckets={data.age_counts}
            ageHref={(min, max) => peopleHref({ age_min: min ?? undefined, age_max: max ?? undefined })}
          />
          <p className="mt-1 flex items-center gap-1.5 border-t border-fg/[0.06] pt-3 text-[10px] text-fg/25">
            <ArrowUpRight size={11} /> Багана дээр дарж тухайн насны бүлгийг шүүнэ
          </p>
        </Panel>

        <Panel className="xl:col-span-3">
          <PanelTitle
            eyebrow="Hierarchy"
            title="Шатлын бүтэц"
            description="Түмтээс гишүүн хүртэл"
            icon={<Layers size={14} />}
          />
          <div className="mt-3">
            <DonutChart
              centerLabel="идэвхтэй"
              centerValue={groupTotal}
              segments={data.group_counts.map((item) => ({
                label: GROUP_LABELS[item.group_type],
                value: item.count,
                color: GROUP_CHART_COLORS[item.group_type],
                href: peopleHref({ group_type: item.group_type }),
              }))}
            />
          </div>
        </Panel>
      </section>

      <section id="geography" className="grid scroll-mt-24 gap-4 xl:grid-cols-12">
        <div className="xl:col-span-8">
          <DistrictMap
            items={data.district_counts}
            hrefBuilder={(name) => peopleHref({ district: name })}
          />
        </div>
        <Panel className="xl:col-span-4">
          <PanelTitle
            eyebrow="Khoroo density"
            title="Хорооны нягтшил"
            description="Хамгийн олон бүртгэлтэй хороонууд"
            icon={<MapPin size={14} />}
            action={
              <Link
                to={peopleHref({})}
                className="inline-flex items-center gap-1 text-[10px] font-medium text-acid-300/80 transition hover:text-acid-200"
              >
                Бүгд <ChevronRight size={12} />
              </Link>
            }
          />
          <div className="mt-3">
            <HorizontalBars
              items={data.khoroo_counts}
              hrefBuilder={(name) => peopleHref({ khoroo: name })}
              color="bg-gradient-to-r from-acid-500 to-acid-300"
            />
          </div>
        </Panel>
      </section>

      <section className="grid gap-4 xl:grid-cols-12">
        <Panel className="xl:col-span-7">
          <div className="flex items-start justify-between">
            <PanelTitle
              eyebrow="Registration velocity"
              title="Бүртгэлийн динамик"
              description="Сүүлийн 7 хоногийн шинэ бүртгэл"
              icon={<Activity size={14} />}
            />
            <span className="rounded-full border border-fg/[0.07] bg-fg/[0.03] px-2.5 py-1 font-mono text-[9px] text-fg/30">
              7D
            </span>
          </div>
          <div className="mt-4">
            <DailyTrend items={data.daily_registrations} total={trendTotal} max={trendMax} />
          </div>
        </Panel>

        <Panel id="activity" className="scroll-mt-24 xl:col-span-5">
          <PanelTitle
            eyebrow="System activity"
            title="Сүүлийн үйлдэл"
            description="Бүртгэлийн аудитын урсгал"
            icon={<ClipboardList size={14} />}
            action={
              user?.is_admin ? (
                <Link
                  to="/audit"
                  className="inline-flex items-center gap-1 text-[10px] font-medium text-acid-300/80 transition hover:text-acid-200"
                >
                  Аудит <ChevronRight size={12} />
                </Link>
              ) : undefined
            }
          />
          <ol className="relative mt-4 space-y-1">
            <span className="absolute bottom-3 left-[13px] top-3 w-px bg-fg/[0.06]" />
            {data.recent_actions.slice(0, 6).map((item, index) => (
              <li key={item.id} className="relative flex gap-3 rounded-xl px-1 py-2">
                <span
                  className={clsx(
                    "relative z-10 mt-0.5 flex h-[27px] w-[27px] shrink-0 items-center justify-center rounded-full border",
                    index === 0
                      ? "border-acid-400/40 bg-acid-400/10 text-acid-300"
                      : "border-fg/[0.08] bg-night-800 text-fg/30",
                  )}
                >
                  <span className={clsx("h-1.5 w-1.5 rounded-full", index === 0 ? "bg-acid-400" : "bg-fg/30")} />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-medium text-fg/65">
                    {item.actor?.full_name ?? "Систем"} ·{" "}
                    <span className="text-fg/40">{AUDIT_ACTION_LABELS[item.action] ?? item.action}</span>
                  </p>
                  <p className="mt-1 font-mono text-[9px] text-fg/20">{formatDateTime(item.created_at)}</p>
                </div>
              </li>
            ))}
            {data.recent_actions.length === 0 && (
              <li className="py-10 text-center text-xs text-fg/25">Үйлдэл бүртгэгдээгүй.</li>
            )}
          </ol>
        </Panel>
      </section>

      <Panel>
        <div className="flex items-center justify-between border-b border-fg/[0.06] px-5 py-4">
          <PanelTitle
            eyebrow="Latest records"
            title="Сүүлд бүртгэсэн иргэд"
            description="Таны хүрээний хамгийн сүүлийн бүртгэлүүд"
            icon={<BookUser size={14} />}
          />
          <Link
            to="/people"
            className="inline-flex items-center gap-1.5 rounded-full border border-fg/[0.08] bg-fg/[0.03] px-3 py-1.5 text-[10px] font-medium text-fg/50 transition hover:border-fg/20 hover:text-fg"
          >
            Бүгдийг харах <ArrowRight size={12} />
          </Link>
        </div>
        {data.recent_people.length === 0 ? (
          <div className="px-5 py-12 text-center text-xs text-fg/30">Бүртгэл байхгүй.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left">
              <thead>
                <tr className="text-[9px] uppercase tracking-[0.18em] text-fg/20">
                  <th className="px-5 py-3 font-medium">Иргэн</th>
                  <th className="px-4 py-3 font-medium">Регистр</th>
                  <th className="px-4 py-3 font-medium">Байршил</th>
                  <th className="px-4 py-3 font-medium">Шатлал</th>
                  <th className="px-5 py-3 text-right font-medium">Огноо</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_people.map((person) => (
                  <tr key={person.id} className="group border-t border-fg/[0.05] transition hover:bg-fg/[0.03]">
                    <td className="px-5 py-3">
                      <Link to={`/people/${person.id}`} className="flex items-center gap-3">
                        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-fg/[0.08] bg-fg/[0.04] text-[10px] font-semibold text-fg/55">
                          {initials(person)}
                        </span>
                        <span className="min-w-0">
                          <span className="block truncate text-xs font-medium text-fg/75 group-hover:text-fg">
                            {fullName(person)}
                          </span>
                          <span className="mt-0.5 block text-[10px] text-fg/25">
                            {person.age !== null ? `${person.age} нас` : "Нас тодорхойгүй"}
                            <span className="text-fg/15"> · {GENDER_LABELS[person.gender]}</span>
                          </span>
                        </span>
                      </Link>
                    </td>
                    <td className="px-4 py-3 font-mono text-[10px] text-fg/40">{person.reg_number}</td>
                    <td className="px-4 py-3 text-[11px] text-fg/45">
                      {person.district ?? "—"}
                      <span className="text-fg/20"> · {person.khoroo ?? "—"}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className="inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[9px]"
                        style={{
                          borderColor: `${GROUP_CHART_COLORS[person.group_type]}33`,
                          color: GROUP_CHART_COLORS[person.group_type],
                          backgroundColor: `${GROUP_CHART_COLORS[person.group_type]}0d`,
                        }}
                      >
                        <span
                          className="h-1 w-1 rounded-full"
                          style={{ backgroundColor: GROUP_CHART_COLORS[person.group_type] }}
                        />
                        {GROUP_LABELS[person.group_type]}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-right font-mono text-[9px] text-fg/25">
                      {formatDateTime(person.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}

function Panel({
  children,
  className,
  id,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section
      id={id}
      className={clsx(
        "glass-surface relative overflow-hidden rounded-2xl p-5 animate-rise",
        className,
      )}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-fg/[0.14] to-transparent" />
      {children}
    </section>
  );
}

function PanelTitle({
  eyebrow,
  title,
  description,
  icon,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  icon?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="flex items-start gap-2.5">
        {icon && (
          <span className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-lg border border-acid-400/15 bg-acid-400/[0.07] text-acid-300">
            {icon}
          </span>
        )}
        <div>
          <p className="text-[8px] font-semibold uppercase tracking-[0.22em] text-fg/20">{eyebrow}</p>
          <h3 className="mt-1 text-sm font-semibold tracking-[-0.01em] text-fg">{title}</h3>
          <p className="mt-0.5 text-[10px] text-fg/30">{description}</p>
        </div>
      </div>
      {action}
    </div>
  );
}

function MetricCard({
  label,
  value,
  hint,
  icon,
  accent,
  aside,
  footer,
}: {
  label: string;
  value: number;
  hint: string;
  icon: ReactNode;
  accent: "acid" | "clay" | "brass";
  aside?: ReactNode;
  footer?: ReactNode;
}) {
  const tones = {
    acid: "border-violet-500/20 bg-violet-500/10 text-violet-600 dark:text-violet-300",
    clay: "border-teal-500/20 bg-teal-500/10 text-teal-600 dark:text-teal-300",
    brass: "border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-300",
  };
  return (
    <Panel className="p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[9px] font-medium uppercase tracking-[0.18em] text-fg/25">{label}</p>
          <p className="mt-2 text-3xl font-semibold tracking-[-0.045em] text-fg">
            {formatNumber(value)}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span className={clsx("flex h-8 w-8 items-center justify-center rounded-lg border", tones[accent])}>
            {icon}
          </span>
          {aside}
        </div>
      </div>
      <p className="mt-2 text-[10px] text-fg/28">{hint}</p>
      {footer}
    </Panel>
  );
}

function MiniRing({ value }: { value: number }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="relative h-10 w-10">
      <svg viewBox="0 0 40 40" className="h-full w-full -rotate-90">
        <circle cx="20" cy="20" r="16" fill="none" stroke="currentColor" strokeWidth="3" className="text-fg/[0.1]" />
        <circle
          cx="20"
          cy="20"
          r="16"
          fill="none"
          stroke="#818cf8"
          strokeWidth="3"
          pathLength={100}
          strokeDasharray={`${clamped} ${100 - clamped}`}
          strokeLinecap="round"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center font-mono text-[8px] text-fg/45">
        {clamped.toFixed(0)}
      </span>
    </div>
  );
}

function SparkBars({ values }: { values: number[] }) {
  const max = Math.max(1, ...values);
  return (
    <div className="mt-4 flex h-7 items-end gap-1">
      {values.map((value, index) => (
        <span
          key={index}
          className={clsx(
            "flex-1 rounded-sm transition-all",
            index === values.length - 1 ? "bg-acid-400" : "bg-acid-400/25",
          )}
          style={{ height: `${Math.max(8, (value / max) * 100)}%` }}
        />
      ))}
    </div>
  );
}
