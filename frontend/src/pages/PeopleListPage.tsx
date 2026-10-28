import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  ArrowDownUp,
  BookUser,
  Download,
  Filter,
  Plus,
  RotateCcw,
  Search,
  Upload,
} from "lucide-react";
import { api, buildQuery, downloadFile } from "../api/client";
import type { Gender, GroupType, Page, PersonStatus, PersonSummary } from "../api/types";
import { useAuth } from "../auth/AuthProvider";
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
import { useToast } from "../components/ui/Toast";
import { GENDER_LABELS, GROUP_LABELS, SORT_OPTIONS, STATUS_LABELS } from "../lib/labels";
import { ParentPicker, type ParentValue } from "../components/people/ParentPicker";
import { formatDateTime, fullName, initials } from "../lib/format";

interface Filters {
  reg_number: string;
  last_name: string;
  first_name: string;
  phone: string;
  district: string;
  khoroo: string;
  address: string;
  job: string;
  gender: "" | Gender;
  age_min: string;
  age_max: string;
  group_type: "" | GroupType;
}

const emptyFilters: Filters = {
  reg_number: "",
  last_name: "",
  first_name: "",
  phone: "",
  district: "",
  khoroo: "",
  address: "",
  job: "",
  gender: "",
  age_min: "",
  age_max: "",
  group_type: "",
};

export default function PeopleListPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const initialUnderId = Number(searchParams.get("under_person_id")) || null;
  const initialUnder = initialUnderId
    ? {
        id: initialUnderId,
        reg_number: searchParams.get("under_reg") ?? "",
        last_name: searchParams.get("under_last") ?? "",
        first_name: searchParams.get("under_first") ?? "",
      }
    : null;
  const initialGroup = searchParams.get("group_type") ?? "";
  const initialGender = searchParams.get("gender") ?? "";
  const initialFilters: Filters = {
    ...emptyFilters,
    reg_number: searchParams.get("reg_number") ?? "",
    last_name: searchParams.get("last_name") ?? "",
    first_name: searchParams.get("first_name") ?? "",
    phone: searchParams.get("phone") ?? "",
    district: searchParams.get("district") ?? "",
    khoroo: searchParams.get("khoroo") ?? "",
    address: searchParams.get("address") ?? "",
    job: searchParams.get("job") ?? "",
    age_min: searchParams.get("age_min") ?? "",
    age_max: searchParams.get("age_max") ?? "",
    gender: initialGender in GENDER_LABELS ? (initialGender as Gender) : "",
    group_type: initialGroup in GROUP_LABELS ? (initialGroup as GroupType) : "",
  };
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [applied, setApplied] = useState<Filters>(initialFilters);
  const [status, setStatus] = useState<PersonStatus>("ACTIVE");
  const [sort, setSort] = useState("created_at");
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [underPerson, setUnderPerson] = useState<ParentValue | null>(initialUnder);
  const [appliedUnder, setAppliedUnder] = useState<ParentValue | null>(initialUnder);
  const [directOnly, setDirectOnly] = useState(searchParams.get("direct_only") === "1");
  const [exporting, setExporting] = useState<"csv" | "xlsx" | null>(null);

  const query = {
    ...applied,
    group_type: applied.group_type || undefined,
    gender: applied.gender || undefined,
    age_min: applied.age_min ? Number(applied.age_min) : undefined,
    age_max: applied.age_max ? Number(applied.age_max) : undefined,
    under_person_id: appliedUnder?.id,
    direct_only: directOnly || undefined,
    status,
    sort,
    order,
    page,
    page_size: 20,
  };

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["people", query],
    queryFn: () => api.get<Page<PersonSummary>>(`/people${buildQuery(query)}`),
    placeholderData: keepPreviousData,
  });

  function apply(event?: FormEvent) {
    event?.preventDefault();
    setApplied(filters);
    setAppliedUnder(underPerson);
    setPage(1);
  }

  function reset() {
    setFilters(emptyFilters);
    setApplied(emptyFilters);
    setUnderPerson(null);
    setAppliedUnder(null);
    setDirectOnly(false);
    setPage(1);
  }

  async function handleExport(format: "csv" | "xlsx") {
    setExporting(format);
    try {
      await downloadFile(
        `/exports/people${buildQuery({
          ...applied,
          group_type: applied.group_type || undefined,
          gender: applied.gender || undefined,
          age_min: applied.age_min ? Number(applied.age_min) : undefined,
          age_max: applied.age_max ? Number(applied.age_max) : undefined,
          under_person_id: appliedUnder?.id,
          direct_only: directOnly || undefined,
          fmt: format,
        })}`,
      );
      toast("Экспортын файл татагдлаа.", "success");
    } catch (error) {
      toast(error instanceof Error ? error.message : "Экспорт хийхэд алдаа гарлаа.", "error");
    } finally {
      setExporting(null);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Бүртгэл"
        title="Иргэдийн бүртгэл"
        description="Регистр, нэр, хаяг, ажил, хүйс, нас болон харьяаллаар нарийвчлан хайна."
        actions={
          <>
            {user?.is_admin && (
              <Button variant="secondary" icon={<Upload size={16} />} onClick={() => navigate("/imports")}>
                Импорт
              </Button>
            )}
            {user?.is_admin && (
              <div className="flex items-center">
                <Button
                  variant="secondary"
                  icon={<Download size={16} />}
                  loading={exporting !== null}
                  onClick={() => void handleExport("csv")}
                  className="rounded-r-none"
                >
                  Экспорт
                </Button>
                <Select
                  aria-label="Экспортын формат"
                  className="h-10 w-[4.6rem] rounded-l-none border-l-0 px-2 text-xs"
                  value=""
                  disabled={exporting !== null}
                  onChange={(event) => {
                    const value = event.target.value as "csv" | "xlsx";
                    if (value) void handleExport(value);
                  }}
                >
                  <option value="">CSV</option>
                  <option value="xlsx">XLSX</option>
                </Select>
              </div>
            )}
            {user?.permissions.can_edit && (
              <Button icon={<Plus size={16} />} onClick={() => navigate("/people/new")}>
                Шинэ бүртгэл
              </Button>
            )}
          </>
        }
      />

      <Card className="p-4 sm:p-5">
        <form onSubmit={apply} className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <Field label="Регистрийн дугаар" htmlFor="f-reg">
            <Input
              id="f-reg"
              value={filters.reg_number}
              onChange={(event) => setFilters({ ...filters, reg_number: event.target.value })}
              placeholder="УБ12345678"
            />
          </Field>
          <Field label="Овог" htmlFor="f-last">
            <Input
              id="f-last"
              value={filters.last_name}
              onChange={(event) => setFilters({ ...filters, last_name: event.target.value })}
              placeholder="Овгийн эхний үсэг"
            />
          </Field>
          <Field label="Нэр" htmlFor="f-first">
            <Input
              id="f-first"
              value={filters.first_name}
              onChange={(event) => setFilters({ ...filters, first_name: event.target.value })}
              placeholder="Нэрийн эхний үсэг"
            />
          </Field>
          <Field label="Бүлгийн төрөл" htmlFor="f-group">
            <Select
              id="f-group"
              value={filters.group_type}
              onChange={(event) =>
                setFilters({ ...filters, group_type: event.target.value as Filters["group_type"] })
              }
            >
              <option value="">Бүгд</option>
              {Object.entries(GROUP_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </Select>
          </Field>
          <Field label="Хүйс" htmlFor="f-gender">
            <Select
              id="f-gender"
              value={filters.gender}
              onChange={(event) => setFilters({ ...filters, gender: event.target.value as Filters["gender"] })}
            >
              <option value="">Бүгд</option>
              {Object.entries(GENDER_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </Select>
          </Field>
          <Field label="Нас (доод хязгаар)" htmlFor="f-age-min">
            <Input
              id="f-age-min"
              type="number"
              min={0}
              max={120}
              value={filters.age_min}
              onChange={(event) => setFilters({ ...filters, age_min: event.target.value })}
              placeholder="18"
            />
          </Field>
          <Field label="Нас (дээд хязгаар)" htmlFor="f-age-max">
            <Input
              id="f-age-max"
              type="number"
              min={0}
              max={120}
              value={filters.age_max}
              onChange={(event) => setFilters({ ...filters, age_max: event.target.value })}
              placeholder="65"
            />
          </Field>
          <Field label="Дүүрэг" htmlFor="f-district">
            <Input
              id="f-district"
              value={filters.district}
              onChange={(event) => setFilters({ ...filters, district: event.target.value })}
              placeholder="Хан-Уул"
            />
          </Field>
          <Field label="Хороо" htmlFor="f-khoroo">
            <Input
              id="f-khoroo"
              value={filters.khoroo}
              onChange={(event) => setFilters({ ...filters, khoroo: event.target.value })}
              placeholder="1-р хороо"
            />
          </Field>
          <Field label="Ажил" htmlFor="f-job">
            <Input
              id="f-job"
              value={filters.job}
              onChange={(event) => setFilters({ ...filters, job: event.target.value })}
              placeholder="Инженер"
            />
          </Field>
          <Field label="Хаяг" htmlFor="f-address">
            <Input
              id="f-address"
              value={filters.address}
              onChange={(event) => setFilters({ ...filters, address: event.target.value })}
              placeholder="Хаягийн хэсэг"
            />
          </Field>
          {user?.permissions.can_view_sensitive && (
            <Field label="Утас" htmlFor="f-phone">
              <Input
                id="f-phone"
                value={filters.phone}
                onChange={(event) => setFilters({ ...filters, phone: event.target.value })}
                placeholder="99112233"
              />
            </Field>
          )}
          <div className="md:col-span-2 xl:col-span-4">
            <Field
              label="Харьяаллаар шүүх"
              hint="Сонгосон хүн болон түүний бүх доорх бүртгэлийг харуулна. Зөвхөн шууд доорхыг харах бол чагтлана."
            >
              <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
                <ParentPicker
                  value={underPerson}
                  onChange={(value) => {
                    setUnderPerson(value);
                    if (!value) setDirectOnly(false);
                  }}
                  placeholder="Хүн сонгоод түүний хүрээг шүүх…"
                />
                <label className="flex items-center gap-2 rounded-lg border border-fg/[0.1] bg-fg/[0.045] px-3 text-xs text-fg/70 backdrop-blur-xl">
                  <input
                    type="checkbox"
                    checked={directOnly}
                    disabled={!underPerson}
                    onChange={(event) => setDirectOnly(event.target.checked)}
                    className="h-4 w-4 rounded border-fg/[0.16] text-acid-400 focus:ring-acid-400"
                  />
                  Зөвхөн шууд доорх
                </label>
              </div>
            </Field>
          </div>
          <div className="flex items-end gap-2 md:col-span-2 xl:col-span-4">
            <Button type="submit" icon={<Search size={16} />} className="sm:w-auto">
              Хайх
            </Button>
            <Button type="button" variant="ghost" icon={<RotateCcw size={15} />} onClick={reset}>
              Цэвэрлэх
            </Button>
            {appliedUnder && (
              <Badge tone="brand">Хүрээ: {fullName(appliedUnder)}</Badge>
            )}
            {appliedUnder && directOnly && <Badge tone="neutral">Шууд доорх</Badge>}
            {isFetching && <span className="text-xs text-fg/40">Шинэчилж байна…</span>}
          </div>
        </form>
      </Card>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
        <div className="inline-flex rounded-lg border border-fg/[0.1] bg-fg/[0.045] p-1 shadow-sm backdrop-blur-xl">
          {(user?.is_admin ? (["ACTIVE", "DELETED"] as PersonStatus[]) : (["ACTIVE"] as PersonStatus[])).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => {
                setStatus(value);
                setPage(1);
              }}
              className={
                status === value
                  ? "rounded-md bg-night-700 px-3 py-1.5 text-xs font-medium text-fg"
                  : "rounded-md px-3 py-1.5 text-xs font-medium text-fg/50 hover:text-fg/80"
              }
            >
              {value === "ACTIVE" ? "Идэвхтэй" : "Устгасан"}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <ArrowDownUp size={15} className="text-fg/40" />
          <Select
            aria-label="Эрэмбэлэх талбар"
            value={sort}
            onChange={(event) => {
              setSort(event.target.value);
              setPage(1);
            }}
            className="h-9 w-auto text-xs"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Эрэмбэлэх чиглэл"
            value={order}
            onChange={(event) => {
              setOrder(event.target.value as "asc" | "desc");
              setPage(1);
            }}
            className="h-9 w-auto text-xs"
          >
            <option value="desc">Буурах</option>
            <option value="asc">Өсөх</option>
          </Select>
        </div>
      </div>

      <Card className="mt-3 overflow-hidden">
        {isLoading ? (
          <Spinner />
        ) : isError ? (
          <ErrorState message="Бүртгэлийг ачаалж чадсангүй." onRetry={() => void refetch()} />
        ) : !data || data.items.length === 0 ? (
          <EmptyState
            icon={<BookUser size={22} />}
            title="Бүртгэл олдсонгүй"
            description={
              status === "DELETED"
                ? "Устгасан бүртгэл байхгүй байна."
                : "Хайлтын нөхцөлд тохирох иргэн байхгүй. Шүүлтээ өөрчилж үзнэ үү."
            }
            action={
              user?.permissions.can_edit && status === "ACTIVE" ? (
                <Button size="sm" icon={<Plus size={15} />} onClick={() => navigate("/people/new")}>
                  Шинэ бүртгэл
                </Button>
              ) : undefined
            }
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[820px] text-left text-sm">
                <thead className="border-b border-fg/[0.07] bg-fg/[0.04] text-xs uppercase tracking-wide text-fg/50">
                  <tr>
                    <th className="px-5 py-3 font-medium">Иргэн</th>
                    <th className="px-4 py-3 font-medium">Бүлэг</th>
                    <th className="px-4 py-3 font-medium">Байршил</th>
                    <th className="px-4 py-3 font-medium">Утас</th>
                    <th className="px-4 py-3 font-medium">Бүртгэсэн</th>
                    {status === "DELETED" && <th className="px-4 py-3 font-medium">Төлөв</th>}
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody className={isFetching ? "opacity-60 transition-opacity" : ""}>
                  {data.items.map((person) => (
                    <tr key={person.id} className="border-b border-fg/[0.04] last:border-0 hover:bg-fg/[0.03]">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-acid-400/[0.07] text-xs font-semibold text-acid-300">
                            {initials(person)}
                          </span>
                          <div>
                            <Link
                              to={`/people/${person.id}`}
                              className="font-medium text-fg hover:text-acid-300 hover:underline"
                            >
                              {fullName(person)}
                            </Link>
                            <p className="mt-0.5 font-mono text-[11px] text-fg/50">{person.reg_number}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone="brand">{GROUP_LABELS[person.group_type]}</Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-fg/60">
                        {person.district ?? "—"}
                        {person.khoroo ? `, ${person.khoroo}` : ""}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-fg/60">{person.phone ?? "—"}</td>
                      <td className="px-4 py-3 text-xs text-fg/50">
                        {person.full_profile ? formatDateTime(person.created_at) : "—"}
                      </td>
                      {status === "DELETED" && (
                        <td className="px-4 py-3">
                          <Badge tone="danger">{STATUS_LABELS[person.status]}</Badge>
                        </td>
                      )}
                      <td className="px-5 py-3 text-right">
                        <Button variant="ghost" size="sm" onClick={() => navigate(`/people/${person.id}`)}>
                          Дэлгэрэнгүй
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-fg/[0.07] px-4 py-3">
              <Pagination
                page={data.page}
                totalPages={data.total_pages}
                total={data.total}
                onChange={setPage}
              />
            </div>
          </>
        )}
      </Card>

      <p className="mt-3 flex items-center gap-1.5 text-[11px] text-fg/40">
        <Filter size={12} />
        Утасны дугаар нь хандах эрхгүй хэрэглэгчид автоматаар нууцлагдана.
      </p>
    </div>
  );
}
