import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronsUpDown, Search, X } from "lucide-react";
import { api, buildQuery } from "../../api/client";
import type { ParentCandidate } from "../../api/types";
import { GROUP_LABELS } from "../../lib/labels";
import { fullName } from "../../lib/format";
import { Badge, Input } from "../ui";

export function LeaderPicker({
  value,
  onChange,
  disabled,
  mode = "leader",
}: {
  value: ParentCandidate | null;
  onChange: (value: ParentCandidate | null) => void;
  disabled?: boolean;
  mode?: "leader" | "member";
}) {
  const isMember = mode === "member";
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  const { data = [], isFetching } = useQuery({
    queryKey: ["account-person-candidates", mode, search],
    queryFn: () =>
      api.get<ParentCandidate[]>(
        `/users/${isMember ? "member-candidates" : "leader-candidates"}${buildQuery({ search, limit: 30 })}`,
      ),
    enabled: open && !disabled,
  });

  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setOpen((current) => !current)}
          className="flex min-h-10 flex-1 items-center justify-between gap-2 rounded-lg border border-fg/[0.11] bg-fg/[0.045] px-3 py-2 text-left text-sm shadow-sm backdrop-blur-xl transition hover:border-fg/[0.18] focus:border-fg/30 focus:outline-none focus:ring-2 focus:ring-fg/15 disabled:bg-fg/[0.025] disabled:text-fg/45"
          aria-haspopup="listbox"
          aria-expanded={open}
        >
          {value ? (
            <span className="flex min-w-0 items-center gap-2">
              <span className="truncate font-medium text-fg">{fullName(value)}</span>
              <span className="shrink-0 font-mono text-[11px] text-fg/50">{value.reg_number}</span>
              <Badge tone="brand">{GROUP_LABELS[value.group_type]}</Badge>
            </span>
          ) : (
            <span className="text-fg/40">
              {isMember ? "Гишүүнээ сонгоно уу" : "Удирдах хүнээ сонгоно уу"}
            </span>
          )}
          <ChevronsUpDown size={15} className="shrink-0 text-fg/40" />
        </button>
        {value && !disabled && (
          <button
            type="button"
            onClick={() => onChange(null)}
            className="rounded-md p-2 text-fg/40 hover:bg-fg/[0.06] hover:text-fg/70"
            aria-label={isMember ? "Гишүүнийг цэвэрлэх" : "Удирдах хүнийг цэвэрлэх"}
          >
            <X size={15} />
          </button>
        )}
      </div>

      {open && (
        <div className="glass-overlay absolute z-20 mt-1 w-full overflow-hidden rounded-xl shadow-pop">
          <div className="flex items-center gap-2 border-b border-fg/[0.07] px-3 py-2">
            <Search size={15} className="text-fg/40" />
            <Input
              autoFocus
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Нэр эсвэл регистрээр хайх…"
              className="h-8 border-0 p-0 shadow-none focus:ring-0"
            />
          </div>
          <ul role="listbox" className="max-h-64 overflow-y-auto py-1 scrollbar-thin">
            {isFetching && data.length === 0 && (
              <li className="px-3 py-4 text-center text-xs text-fg/50">Хайж байна…</li>
            )}
            {!isFetching && data.length === 0 && (
              <li className="px-3 py-4 text-center text-xs text-fg/50">
                {isMember
                  ? "Гишүүн бүртгэл олдсонгүй."
                  : "Удирдагч болох бүртгэл олдсонгүй."}
              </li>
            )}
            {data.map((candidate) => {
              const selected = candidate.id === value?.id;
              return (
                <li key={candidate.id} role="option" aria-selected={selected}>
                  <button
                    type="button"
                    onClick={() => {
                      onChange(candidate);
                      setOpen(false);
                      setSearch("");
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-fg/[0.03]"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium text-fg/80">{fullName(candidate)}</p>
                      <p className="font-mono text-[11px] text-fg/50">{candidate.reg_number}</p>
                    </div>
                    <Badge tone="brand">{GROUP_LABELS[candidate.group_type]}</Badge>
                    {selected && <Check size={15} className="text-acid-400" />}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
