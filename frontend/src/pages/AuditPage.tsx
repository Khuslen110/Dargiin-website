import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ClipboardList, Filter, RotateCcw, Search } from "lucide-react";
import { api, buildQuery } from "../api/client";
import type { AuditItem, Page } from "../api/types";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Pagination,
  Select,
  Spinner,
} from "../components/ui";
import { PageHeader } from "../components/layout/AppShell";
import { AUDIT_ACTION_LABELS, AUDIT_ENTITY_LABELS } from "../lib/labels";
import { formatDateTime } from "../lib/format";

export default function AuditPage() {
  const [action, setAction] = useState("");
  const [entityType, setEntityType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [applied, setApplied] = useState({ action: "", entityType: "", dateFrom: "", dateTo: "" });
  const [page, setPage] = useState(1);

  const params = {
    action: applied.action || undefined,
    entity_type: applied.entityType || undefined,
    date_from: applied.dateFrom
      ? new Date(`${applied.dateFrom}T00:00:00+08:00`).toISOString()
      : undefined,
    date_to: applied.dateTo
      ? new Date(`${applied.dateTo}T23:59:59+08:00`).toISOString()
      : undefined,
    page,
    page_size: 20,
  };

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["audit", params],
    queryFn: () => api.get<Page<AuditItem>>(`/audit${buildQuery(params)}`),
  });

  function apply() {
    setApplied({ action, entityType, dateFrom, dateTo });
    setPage(1);
  }

  function reset() {
    setAction("");
    setEntityType("");
    setDateFrom("");
    setDateTo("");
    setApplied({ action: "", entityType: "", dateFrom: "", dateTo: "" });
    setPage(1);
  }

  return (
    <div>
      <PageHeader
        eyebrow="Хяналт"
        title="Аудитын мөр"
        description="Системд хийгдсэн бүх мэдээлэл өөрчлөх, нэвтрэх, импорт, экспортын үйлдлийн бүртгэл."
      />

      <Card className="p-4 sm:p-5">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            apply();
          }}
          className="grid gap-3 md:grid-cols-2 xl:grid-cols-5"
        >
          <Field label="Үйлдэл" htmlFor="audit-action">
            <Select id="audit-action" value={action} onChange={(event) => setAction(event.target.value)}>
              <option value="">Бүгд</option>
              {Object.entries(AUDIT_ACTION_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </Select>
          </Field>
          <Field label="Объект" htmlFor="audit-entity">
            <Select id="audit-entity" value={entityType} onChange={(event) => setEntityType(event.target.value)}>
              <option value="">Бүгд</option>
              {Object.entries(AUDIT_ENTITY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </Select>
          </Field>
          <Field label="Эхлэх огноо" htmlFor="audit-from">
            <Input id="audit-from" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          </Field>
          <Field label="Дуусах огноо" htmlFor="audit-to">
            <Input id="audit-to" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </Field>
          <div className="flex items-end gap-2">
            <Button type="submit" icon={<Search size={16} />} className="flex-1">Шүүх</Button>
            <Button type="button" variant="ghost" icon={<RotateCcw size={15} />} onClick={reset}>Цэвэрлэх</Button>
          </div>
        </form>
      </Card>

      <Card className="mt-4 overflow-hidden">
        {isLoading ? (
          <Spinner />
        ) : isError ? (
          <ErrorState message="Аудитын мөрийг ачаалж чадсангүй." onRetry={() => void refetch()} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState icon={<ClipboardList size={22} />} title="Бичлэг олдсонгүй" description="Сонгосон шүүлтэд тохирох үйлдэл байхгүй." />
        ) : (
          <>
            <div className={`overflow-x-auto ${isFetching ? "opacity-60" : ""}`}>
              <table className="w-full min-w-[820px] text-left text-sm">
                <thead className="border-b border-fg/[0.07] bg-fg/[0.04] text-xs uppercase tracking-wide text-fg/50">
                  <tr>
                    <th className="px-5 py-3 font-medium">Хугацаа</th>
                    <th className="px-4 py-3 font-medium">Хэрэглэгч</th>
                    <th className="px-4 py-3 font-medium">Үйлдэл</th>
                    <th className="px-4 py-3 font-medium">Объект</th>
                    <th className="px-5 py-3 font-medium">Дэлгэрэнгүй</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr key={item.id} className="border-b border-fg/[0.04] last:border-0 hover:bg-fg/[0.03]">
                      <td className="whitespace-nowrap px-5 py-3 text-xs text-fg/50">{formatDateTime(item.created_at)}</td>
                      <td className="px-4 py-3">
                        <p className="text-xs font-medium text-fg/80">{item.actor?.full_name ?? "Систем"}</p>
                        {item.actor && <p className="text-[11px] text-fg/40">@{item.actor.username}</p>}
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={actionTone(item.action)}>
                          {AUDIT_ACTION_LABELS[item.action] ?? item.action}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-fg/60">
                        {item.entity_type ? AUDIT_ENTITY_LABELS[item.entity_type] ?? item.entity_type : "—"}
                        {item.entity_id !== null && <span className="ml-1 font-mono text-fg/40">#{item.entity_id}</span>}
                      </td>
                      <td className="max-w-xs px-5 py-3">
                        <MetadataView metadata={item.metadata} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-fg/[0.07] px-4 py-3">
              <Pagination page={data.page} totalPages={data.total_pages} total={data.total} onChange={setPage} />
            </div>
          </>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-[11px] text-fg/40">
        <Filter size={12} /> Аудитын мөр өөрчлөгдөх, устгах боломжгүй.
      </p>
    </div>
  );
}

function actionTone(action: string) {
  if (action.includes("DELETE") || action.includes("PURGE") || action.includes("FAILED")) return "danger" as const;
  if (action.includes("CREATE") || action.includes("LOGIN_SUCCESS") || action.includes("COMPLETE")) return "success" as const;
  if (action.includes("UPDATE") || action.includes("CHANGE") || action.includes("EXPORT") || action.includes("IMPORT")) return "info" as const;
  return "neutral" as const;
}

function MetadataView({ metadata }: { metadata: Record<string, unknown> }) {
  const entries = Object.entries(metadata ?? {}).filter(([, value]) => value !== null && value !== undefined);
  if (entries.length === 0) return <span className="text-xs text-fg/40">—</span>;

  const labels: Record<string, string> = {
    format: "Формат",
    rows: "Мөр",
    filename: "Файл",
    imported: "Оруулсан",
    invalid: "Алдаа",
    group_type: "Бүлэг",
    relationship: "Харьяалал",
    changes: "Өөрчлөлт",
    reason: "Шалтгаан",
    scope: "Хүрээ",
  };

  return (
    <div className="flex flex-wrap gap-1">
      {entries.slice(0, 4).map(([key, value]) => {
        const display =
          typeof value === "object"
            ? JSON.stringify(value)
            : String(value);
        return (
          <span
            key={key}
            className="inline-flex max-w-full items-center gap-1 rounded bg-fg/[0.03] px-1.5 py-0.5 text-[11px] text-fg/60 ring-1 ring-inset ring-fg/[0.07]"
            title={`${key}: ${display}`}
          >
            <span className="text-fg/40">{labels[key] ?? key}:</span>
            <span className="truncate">{display}</span>
          </span>
        );
      })}
      {entries.length > 4 && <span className="text-[11px] text-fg/40">+{entries.length - 4}</span>}
    </div>
  );
}
