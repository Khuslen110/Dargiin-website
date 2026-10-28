import { useRef, useState, type DragEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import {
  CheckCircle2,
  Download,
  FileSpreadsheet,
  FileText,
  History,
  Table2,
  Upload,
  Users,
  XCircle,
} from "lucide-react";
import { api, downloadFile } from "../api/client";
import type { GroupType, ImportJob, ImportPreview, Page } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Spinner,
} from "../components/ui";
import { PageHeader } from "../components/layout/AppShell";
import { ImportGuideModal } from "../components/imports/ImportGuideModal";
import { ParentPicker, type ParentValue } from "../components/people/ParentPicker";
import { useToast } from "../components/ui/Toast";
import { GROUP_LABELS, IMPORT_STATUS_LABELS } from "../lib/labels";
import { NEXT_GROUP_TYPE } from "../lib/groups";
import { formatDateTime, formatNumber, fullName } from "../lib/format";

export default function ImportPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [searchParams] = useSearchParams();
  const [parent, setParent] = useState<ParentValue | null>(() => {
    const id = Number(searchParams.get("parent_id"));
    const regNumber = searchParams.get("parent_reg");
    if (!Number.isFinite(id) || !regNumber) return null;
    return {
      id,
      reg_number: regNumber,
      last_name: searchParams.get("parent_last") ?? "",
      first_name: searchParams.get("parent_first") ?? "",
      group_type: (searchParams.get("parent_group") as GroupType | null) ?? undefined,
    };
  });
  const [dragging, setDragging] = useState(false);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [completed, setCompleted] = useState<ImportJob | null>(null);
  const [guideOpen, setGuideOpen] = useState(false);
  const [page, setPage] = useState(1);

  const jobsQuery = useQuery({
    queryKey: ["imports", page],
    queryFn: () => api.get<Page<ImportJob>>(`/imports?page=${page}&page_size=10`),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      if (parent) form.append("parent_id", String(parent.id));
      return api.upload<ImportPreview>("/imports/preview", form);
    },
    onSuccess: (result) => {
      setPreview(result);
      setCompleted(null);
      toast("Файл шалгагдаж, урьдчилсан үр дүн гарлаа.", "success");
      void queryClient.invalidateQueries({ queryKey: ["imports"] });
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : "Файл уншихад алдаа гарлаа.", "error");
    },
  });

  const confirmMutation = useMutation({
    mutationFn: (jobId: string) => api.post<ImportJob>(`/imports/${jobId}/confirm`),
    onSuccess: (job) => {
      setCompleted(job);
      setPreview(null);
      toast(
        `Импорт дууслаа. ${formatNumber(job.imported_rows)} бүртгэл` +
          (job.accounts_created > 0 ? `, ${formatNumber(job.accounts_created)} хэрэглэгч` : "") +
          " нэмэгдлээ.",
        "success",
      );
      void queryClient.invalidateQueries({ queryKey: ["imports"] });
      void queryClient.invalidateQueries({ queryKey: ["people"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (error) => {
      toast(error instanceof Error ? error.message : "Импорт хийхэд алдаа гарлаа.", "error");
    },
  });

  function selectFile(file: File | undefined) {
    if (!file) return;
    setCompleted(null);
    uploadMutation.mutate(file);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files[0]);
  }

  function changeParent(value: ParentValue | null) {
    if (value && (!value.group_type || !NEXT_GROUP_TYPE[value.group_type])) {
      toast("Гишүүн төрөлтэй хүний доор бүртгэл оруулах боломжгүй.", "error");
      return;
    }
    setParent(value);
    setPreview(null);
    setCompleted(null);
  }

  if (!user?.is_admin) {
    return <ErrorState message="Импорт хийх эрх танд байхгүй." />;
  }

  const nextGroupType = parent?.group_type ? NEXT_GROUP_TYPE[parent.group_type] : null;

  return (
    <div>
      <PageHeader
        eyebrow="Өгөгдөл шилжүүлэх"
        title="Импорт"
        description="CSV эсвэл XLSX файлаас иргэдийн бүртгэлийг урьдчилан шалгаж, баталгаажуулсны дараа оруулна."
        actions={
          <>
            <Button
              variant="secondary"
              icon={<Table2 size={16} />}
              onClick={() => setGuideOpen(true)}
            >
              Хэрхэн бөглөх вэ?
            </Button>
            <Button
              icon={<Download size={16} />}
              onClick={() => void downloadFile("/imports/template").catch((error: Error) => toast(error.message, "error"))}
            >
              Загвар татах
            </Button>
          </>
        }
      />

      <div className="grid gap-5 xl:grid-cols-[1.35fr_1fr]">
        <div className="space-y-5">
          <Card className="p-5">
            <div className="mb-5 rounded-xl border border-fg/[0.08] bg-fg/[0.03] p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-start gap-2.5">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-acid-500/10 text-acid-300 ring-1 ring-inset ring-acid-500/20">
                    <Users size={15} />
                  </span>
                  <div>
                    <p className="text-xs font-semibold text-fg/80">Харьяалагдах хүн</p>
                    <p className="mt-0.5 text-[11px] leading-5 text-fg/50">
                      {parent
                        ? `${fullName(parent)}-ийн шууд доор ${nextGroupType ? GROUP_LABELS[nextGroupType] : "доорх"} бүртгэл нэмэгдэнэ.`
                        : "Сонговол файлын бүх мөр тухайн хүний шууд доор нэмэгдэнэ. Сонгохгүй бол зөвхөн Түмт (үндсэн) бүртгэл оруулна."}
                    </p>
                  </div>
                </div>
                {parent && (
                  <Button variant="ghost" size="sm" onClick={() => changeParent(null)}>
                    Цэвэрлэх
                  </Button>
                )}
              </div>
              <div className="mt-3">
                <ParentPicker
                  value={parent}
                  onChange={changeParent}
                  placeholder="Харьяалагдах хүнээ сонгох…"
                />
              </div>
              {parent && !nextGroupType && (
                <p className="mt-2 text-[11px] text-red-400">
                  Гишүүн төрөлтэй хүний доор бүртгэл нэмэх боломжгүй.
                </p>
              )}
            </div>
            <div
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={handleDrop}
              className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-12 text-center transition ${
                dragging ? "border-acid-400/50 bg-acid-400/[0.06]" : "border-fg/[0.1] bg-fg/[0.03]"
              }`}
            >
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-night-800 text-acid-300 shadow-sm">
                <Upload size={21} />
              </span>
              <p className="mt-4 text-sm font-medium text-fg/80">
                Файлаа энд чирж тавих эсвэл сонгоно уу
              </p>
              <p className="mt-1 text-xs text-fg/50">CSV, XLSX · дээд хэмжээ 10 MB · 50,000 хүртэл мөр</p>
              <input
                ref={inputRef}
                type="file"
                accept=".csv,.xlsx"
                className="hidden"
                onChange={(event) => {
                  selectFile(event.target.files?.[0]);
                  event.target.value = "";
                }}
              />
              <Button
                className="mt-4"
                variant="secondary"
                loading={uploadMutation.isPending}
                onClick={() => inputRef.current?.click()}
              >
                Файл сонгох
              </Button>
            </div>

            <div className="mt-4 grid gap-2 text-xs text-fg/50 sm:grid-cols-2">
              <p className="flex items-center gap-2">
                <FileText size={14} className="text-fg/40" />
                CSV файл UTF-8 кодчилолтой байна.
              </p>
              <p className="flex items-center gap-2">
                <FileSpreadsheet size={14} className="text-fg/40" />
                Эхний мөр нь баганын нэр байна.
              </p>
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-acid-500/20 bg-acid-500/[0.06] px-4 py-3">
              <div className="flex items-start gap-2.5">
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-acid-500/10 text-acid-300 ring-1 ring-inset ring-acid-500/20">
                  <Table2 size={15} />
                </span>
                <div>
                  <p className="text-xs font-medium text-fg/80">Анх удаа оруулж байна уу?</p>
                  <p className="mt-0.5 text-[11px] leading-5 text-fg/45">
                    Баганын загвар, жишээ мөрийг хуулж Excel эсвэл Google Sheets-д paste хийнэ.
                  </p>
                </div>
              </div>
              <Button variant="secondary" size="sm" onClick={() => setGuideOpen(true)}>
                Загвар харах
              </Button>
            </div>
          </Card>

          {uploadMutation.isPending && (
            <Card className="p-5">
              <Spinner className="py-8" />
              <p className="text-center text-xs text-fg/50">Файлыг шалгаж байна…</p>
            </Card>
          )}

          {preview && (
            <Card className="overflow-hidden">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-fg/[0.07] px-5 py-4">
                <div>
                  <h3 className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">Урьдчилсан үр дүн</h3>
                  <p className="mt-0.5 text-xs text-fg/50">
                    {preview.filename}
                    {parent && ` · ${fullName(parent)}-ийн доор`}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone="success">{formatNumber(preview.valid_rows)} зөв</Badge>
                  <Badge tone={preview.invalid_rows > 0 ? "danger" : "neutral"}>
                    {formatNumber(preview.invalid_rows)} алдаа
                  </Badge>
                </div>
              </div>
              <div className="grid grid-cols-2 divide-x divide-fg/[0.06] border-b border-fg/[0.07] text-center sm:grid-cols-4">
                <Stat label="Нийт мөр" value={preview.total_rows} />
                <Stat label="Оруулах" value={preview.valid_rows} tone="text-emerald-600 dark:text-emerald-300" />
                <Stat label="Хэрэглэгч" value={preview.accounts_planned} tone="text-sky-600 dark:text-sky-300" />
                <Stat label="Алдаатай" value={preview.invalid_rows} tone="text-red-300" />
              </div>

              {preview.errors.length > 0 && (
                <div className="max-h-64 overflow-y-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="sticky top-0 bg-fg/[0.03] text-fg/50">
                      <tr>
                        <th className="px-5 py-2 font-medium">Мөр</th>
                        <th className="px-3 py-2 font-medium">Талбар</th>
                        <th className="px-3 py-2 font-medium">Алдаа</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-fg/[0.04]">
                      {preview.errors.map((error, index) => (
                        <tr key={`${error.row}-${index}`}>
                          <td className="px-5 py-2 font-mono text-fg/60">{error.row}</td>
                          <td className="px-3 py-2 text-fg/60">{error.field ?? "—"}</td>
                          <td className="px-3 py-2 text-red-300">{error.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-fg/[0.07] bg-fg/[0.03] px-5 py-3">
                <p className="text-xs text-fg/50">
                  {preview.can_confirm
                    ? "Зөв мөрүүд л орох болно. Нууц үг бүхий мөрүүдэд нэвтрэх хэрэглэгч автоматаар үүснэ."
                    : "Оруулах боломжтой мөр байхгүй."}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Download size={14} />}
                    onClick={() => void downloadFile(`/imports/${preview.job_id}/errors.csv`).catch((error: Error) => toast(error.message, "error"))}
                  >
                    Алдааны тайлан
                  </Button>
                  <Button
                    size="sm"
                    disabled={!preview.can_confirm}
                    loading={confirmMutation.isPending}
                    onClick={() => confirmMutation.mutate(preview.job_id)}
                  >
                    Баталгаажуулж оруулах
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {completed && (
            <Card className="border-emerald-500/20 bg-emerald-500/10 p-5">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="mt-0.5 h-5 w-5 text-emerald-600 dark:text-emerald-300" />
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">Импорт амжилттай дууслаа</h3>
                  <p className="mt-1 text-xs leading-5 text-emerald-700/80 dark:text-emerald-300/80">
                    {completed.filename} файлаас {formatNumber(completed.imported_rows)} бүртгэл
                    {completed.accounts_created > 0
                      ? `, ${formatNumber(completed.accounts_created)} нэвтрэх хэрэглэгч`
                      : ""}{" "}
                    нэмэгдлээ.
                    {completed.invalid_rows > 0 &&
                      ` ${formatNumber(completed.invalid_rows)} мөр алдаатай байсан тул ороогүй.`}
                  </p>
                  {completed.invalid_rows > 0 && (
                    <button
                      type="button"
                      onClick={() => void downloadFile(`/imports/${completed.id}/errors.csv`)}
                      className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-emerald-700 hover:underline dark:text-emerald-300"
                    >
                      <Download size={13} /> Алдааны тайлан татах
                    </button>
                  )}
                </div>
              </div>
            </Card>
          )}
        </div>

        <Card className="overflow-hidden self-start">
          <div className="flex items-center gap-2 border-b border-fg/[0.07] px-5 py-4">
            <History size={16} className="text-acid-300" />
            <h3 className="text-sm font-semibold text-emerald-700 dark:text-emerald-300">Импортын түүх</h3>
          </div>
          {jobsQuery.isLoading ? (
            <Spinner className="py-10" />
          ) : jobsQuery.isError ? (
            <ErrorState message="Импортын түүхийг ачаалж чадсангүй." onRetry={() => void jobsQuery.refetch()} />
          ) : !jobsQuery.data || jobsQuery.data.items.length === 0 ? (
            <EmptyState title="Импорт хийгдээгүй" description="Эхний файлаа оруулж эхэлнэ үү." />
          ) : (
            <>
              <ul className="divide-y divide-fg/[0.04]">
                {jobsQuery.data.items.map((job) => (
                  <li key={job.id} className="px-5 py-3">
                    <div className="flex items-start justify-between gap-2">
                      <p className="truncate text-xs font-medium text-fg/80">{job.filename}</p>
                      <StatusBadge status={job.status} />
                    </div>
                    <p className="mt-1 text-[11px] text-fg/50">
                      {formatDateTime(job.created_at)} · {formatNumber(job.imported_rows)} оруулсан
                      {job.invalid_rows > 0 ? ` · ${formatNumber(job.invalid_rows)} алдаа` : ""}
                    </p>
                  </li>
                ))}
              </ul>
              {jobsQuery.data.total_pages > 1 && (
                <div className="flex items-center justify-between border-t border-fg/[0.07] px-4 py-2 text-xs">
                  <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                    Өмнөх
                  </Button>
                  <span className="text-fg/50">
                    {page}/{jobsQuery.data.total_pages}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={page >= jobsQuery.data.total_pages}
                    onClick={() => setPage(page + 1)}
                  >
                    Дараах
                  </Button>
                </div>
              )}
            </>
          )}
        </Card>
      </div>

      <div className="mt-5 flex flex-wrap items-start justify-between gap-3 rounded-xl border border-fg/[0.08] bg-fg/[0.035] px-5 py-4 text-xs leading-6 text-fg/50 backdrop-blur-xl">
        <div className="max-w-4xl">
          <p className="mb-1 font-medium text-fg/70">Файлын бүтэц</p>
          <p>
            Баганын нэр: Регистрийн дугаар, Овог, Нэр, Хүйс, Төрсөн огноо, Утас, Дүүрэг, Хороо,
            Хаяг, Ажил, Бүлгийн төрөл, Хэрэглэгчийн нэр, Нууц үг. Хүйс: Эрэгтэй/Эмэгтэй/Бусад,
            Бүлэг: Түмт/Мянгат/Зуут/Аравт/Гишүүн. Харьяалагдах хүнийг энэ хуудаснаас сонгоно.
            Хэрэглэгчийн нэр, нууц үг хоосон бол зөвхөн хүн бүртгэгдэнэ.
          </p>
        </div>
        <Button variant="ghost" size="sm" icon={<Table2 size={14} />} onClick={() => setGuideOpen(true)}>
          Дэлгэрэнгүй заавар
        </Button>
      </div>

      <ImportGuideModal open={guideOpen} onClose={() => setGuideOpen(false)} parent={parent} />
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="px-3 py-3">
      <p className={`text-lg font-semibold ${tone ?? "text-fg"}`}>{formatNumber(value)}</p>
      <p className="text-[11px] text-fg/50">{label}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: ImportJob["status"] }) {
  const tone = {
    COMPLETED: "success",
    FAILED: "danger",
    PROCESSING: "info",
    PREVIEWED: "neutral",
  } as const;
  const Icon = status === "COMPLETED" ? CheckCircle2 : status === "FAILED" ? XCircle : undefined;
  return (
    <Badge tone={tone[status]}>
      {Icon && <Icon size={11} className="mr-1" />}
      {IMPORT_STATUS_LABELS[status]}
    </Badge>
  );
}
