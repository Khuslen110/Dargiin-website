import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ChevronRight, Layers3, Network, Plus, Users } from "lucide-react";
import { clsx } from "clsx";
import { api } from "../api/client";
import type { HierarchyNode, Page } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import { Button, Card, EmptyState, ErrorState, Spinner } from "../components/ui";
import { PageHeader } from "../components/layout/AppShell";
import { GROUP_LABELS } from "../lib/labels";
import { GROUP_ORDER, GROUP_STYLES } from "../lib/groups";
import { fullName, initials } from "../lib/format";

export default function StructurePage() {
  const { user } = useAuth();
  const rootsQuery = useQuery({
    queryKey: ["hierarchy-roots"],
    queryFn: () => api.get<HierarchyNode[]>("/hierarchy/roots"),
  });
  const roots = rootsQuery.data ?? [];

  return (
    <div>
      <PageHeader
        eyebrow="Харьяалал"
        title="Бүтцийн харагдац"
        description="Түмт–Мянгат–Зуут–Аравт–Гишүүн шатлалыг өнгөт модоор харна. Зангилаа дээр дарж шууд доорх бүтцийг дэлгэнэ."
        actions={
          user?.permissions.can_edit ? (
            <Link to="/people/new">
              <Button icon={<Plus size={16} />}>Шинэ бүртгэл</Button>
            </Link>
          ) : undefined
        }
      />

      <div className="mb-5 grid gap-3 sm:grid-cols-3">
        <StatCard icon={<Network size={16} />} label="Үндсэн бүтэц" value={roots.length} />
        <StatCard icon={<Layers3 size={16} />} label="Шатлалын түвшин" value={5} />
        <StatCard
          icon={<Users size={16} />}
          label="Таны шатлал"
          value={
            user?.is_admin
              ? "Бүх бүтэц"
              : user?.leader_group_type
                ? `${GROUP_LABELS[user.leader_group_type]}${user.next_group_type ? ` → ${GROUP_LABELS[user.next_group_type]}` : ""}`
                : "—"
          }
          compact
        />
      </div>

      <Card className="mb-5 p-4 sm:p-5">
        <div className="flex flex-wrap items-center gap-2">
          <span className="mr-1 text-xs font-medium text-fg/50">Шатлалын өнгө:</span>
          {GROUP_ORDER.map((group, index) => (
            <span key={group} className="flex items-center gap-1.5">
              {index > 0 && <ChevronRight size={12} className="text-fg/30" />}
              <span
                className={clsx(
                  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ring-1 ring-inset",
                  GROUP_STYLES[group].badge,
                )}
              >
                <span className={clsx("h-1.5 w-1.5 rounded-full", GROUP_STYLES[group].dot)} />
                {GROUP_LABELS[group]}
              </span>
            </span>
          ))}
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="flex items-center justify-between gap-3 border-b border-fg/[0.07] px-5 py-4">
          <div className="flex items-center gap-2">
            <Network size={16} className="text-acid-300" />
            <h3 className="text-sm font-semibold text-fg">
              {user?.is_admin ? "Үндсэн бүтэцүүд" : "Таны хандах бүтэц"}
            </h3>
          </div>
          {rootsQuery.isFetching && <span className="text-[11px] text-fg/40">Шинэчилж байна…</span>}
        </div>
        {rootsQuery.isLoading ? (
          <Spinner />
        ) : rootsQuery.isError ? (
          <ErrorState message="Бүтцийг ачаалж чадсангүй." onRetry={() => void rootsQuery.refetch()} />
        ) : roots.length === 0 ? (
          <EmptyState
            icon={<Network size={22} />}
            title="Бүтэц үүсээгүй"
            description="Харьяалалгүй (үндсэн) бүртгэл байхгүй байна."
          />
        ) : (
          <div className="space-y-4 bg-gradient-to-b from-fg/[0.04] to-night-850 p-3 sm:p-5">
            {roots.map((root) => (
              <TreeNode key={root.id} node={root} level={0} defaultOpen />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  compact = false,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  compact?: boolean;
}) {
  return (
    <Card className="flex items-center gap-3 px-4 py-3">
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-acid-400/[0.07] text-acid-300">
        {icon}
      </span>
      <div className="min-w-0">
        <p className="text-[11px] font-medium uppercase tracking-wide text-fg/40">{label}</p>
        <p className={clsx("truncate font-semibold text-fg", compact ? "text-sm" : "text-lg")}>
          {value}
        </p>
      </div>
    </Card>
  );
}

function TreeNode({
  node,
  level,
  defaultOpen = false,
}: {
  node: HierarchyNode;
  level: number;
  defaultOpen?: boolean;
}) {
  const memberCount = node.direct_member_count ?? 0;
  const [open, setOpen] = useState(defaultOpen && memberCount > 0);
  const style = GROUP_STYLES[node.group_type];

  const membersQuery = useQuery({
    queryKey: ["tree-members", node.id],
    queryFn: () =>
      api.get<Page<HierarchyNode>>(`/people/${node.id}/members?page=1&page_size=100`),
    enabled: open,
  });

  return (
    <div className={clsx(level > 0 && "relative pl-5 sm:pl-7")}>
      {level > 0 && (
        <>
          <span className="absolute left-0 top-1/2 h-px w-4 bg-fg/[0.1] sm:w-5" />
          <span className="absolute bottom-0 left-0 top-0 w-px bg-fg/[0.1]" />
        </>
      )}
      <div
        className={clsx(
          "group flex items-center gap-2 rounded-xl border px-2.5 py-2 shadow-sm transition hover:shadow-md sm:gap-3 sm:px-3",
          style.card,
          level === 0 && "sm:px-4 sm:py-3",
        )}
      >
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          disabled={memberCount === 0}
          className={clsx(
            "flex h-6 w-6 shrink-0 items-center justify-center rounded-md text-fg/40 transition",
            memberCount > 0 ? "hover:bg-fg/10 hover:text-fg/80" : "opacity-0",
          )}
          aria-label={open ? "Хураах" : "Дэлгэх"}
          aria-expanded={open}
        >
          <ChevronRight size={15} className={clsx("transition-transform", open && "rotate-90")} />
        </button>
        <span
          className={clsx(
            "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ring-2 ring-fg sm:h-9 sm:w-9",
            style.badge,
          )}
        >
          {initials(node)}
        </span>
        <Link to={`/people/${node.id}`} className="min-w-0 flex-1">
          <span className="block truncate text-sm font-semibold text-fg hover:text-acid-300 hover:underline">
            {fullName(node)}
          </span>
          <span className="block font-mono text-[11px] text-fg/40">{node.reg_number}</span>
        </Link>
        <span className={clsx("hidden rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset sm:inline-flex", style.badge)}>
          {GROUP_LABELS[node.group_type]}
        </span>
        <span className="flex items-center gap-1 rounded-full bg-fg/[0.05] px-2 py-0.5 text-[11px] text-fg/50 ring-1 ring-inset ring-fg/[0.07]">
          <Users size={11} /> {memberCount}
        </span>
      </div>

      {open && (
        <div className="mt-2 space-y-2 pl-5 sm:pl-8">
          {membersQuery.isLoading && (
            <p className="rounded-lg bg-fg/[0.05] px-3 py-2 text-xs text-fg/40">Ачаалж байна…</p>
          )}
          {membersQuery.data?.items.map((member) => (
            <TreeNode key={member.id} node={member} level={level + 1} />
          ))}
          {membersQuery.data && membersQuery.data.items.length === 0 && (
            <p className="rounded-lg bg-fg/[0.05] px-3 py-2 text-xs text-fg/40">Гишүүн байхгүй.</p>
          )}
        </div>
      )}
    </div>
  );
}
