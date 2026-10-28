import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CalendarDays,
  ChevronRight,
  CircleAlert,
  Clock,
  Edit3,
  History,
  KeyRound,
  MapPin,
  Network,
  Phone,
  RotateCcw,
  ShieldAlert,
  Trash2,
  Upload,
  UserPlus,
  UserRound,
  Users,
  Briefcase,
  Building2,
} from "lucide-react";
import { api } from "../api/client";
import type {
  AuditItem,
  Page,
  PersonAccountState,
  PersonDetail,
  PersonSummary,
} from "../api/types";
import { useAuth } from "../auth/AuthProvider";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Input,
  Modal,
  Pagination,
  Spinner,
} from "../components/ui";
import { PageHeader } from "../components/layout/AppShell";
import { useToast } from "../components/ui/Toast";
import {
  AUDIT_ACTION_LABELS,
  GENDER_LABELS,
  GROUP_LABELS,
  ROLE_LABELS,
  STATUS_LABELS,
} from "../lib/labels";
import { formatDate, formatDateTime, fullName, initials } from "../lib/format";

export default function PersonDetailPage() {
  const { personId } = useParams();
  const id = Number(personId);
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [purgeOpen, setPurgeOpen] = useState(false);
  const [confirmReg, setConfirmReg] = useState("");
  const [memberPage, setMemberPage] = useState(1);
  const [accountOpen, setAccountOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const [accountUsername, setAccountUsername] = useState("");
  const [accountPassword, setAccountPassword] = useState("");
  const [accountFormError, setAccountFormError] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [resetFormError, setResetFormError] = useState("");

  const detailQuery = useQuery({
    queryKey: ["person", id],
    queryFn: () => api.get<PersonDetail>(`/people/${id}`),
    enabled: Number.isFinite(id),
  });

  const membersQuery = useQuery({
    queryKey: ["person-members", id, memberPage],
    queryFn: () => api.get<Page<PersonSummary>>(`/people/${id}/members?page=${memberPage}&page_size=10`),
    enabled: Number.isFinite(id) && detailQuery.data?.full_profile === true,
  });

  const historyQuery = useQuery({
    queryKey: ["person-history", id],
    queryFn: () => api.get<AuditItem[]>(`/people/${id}/history?limit=20`),
    enabled: Number.isFinite(id) && detailQuery.data?.full_profile === true,
  });

  const accountQuery = useQuery({
    queryKey: ["person-account", id],
    queryFn: () => api.get<PersonAccountState>(`/people/${id}/account`),
    enabled:
      Number.isFinite(id) &&
      detailQuery.data?.permissions.can_manage_account === true,
  });

  const invalidate = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["person", id] }),
      queryClient.invalidateQueries({ queryKey: ["person-members", id] }),
      queryClient.invalidateQueries({ queryKey: ["person-history", id] }),
      queryClient.invalidateQueries({ queryKey: ["person-account", id] }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
    ]);
  };

  const remove = useMutation({
    mutationFn: () => api.delete(`/people/${id}`),
    onSuccess: async () => {
      setDeleteOpen(false);
      toast("Бүртгэл устгагдлаа. Устгасан бүртгэлээс сэргээх боломжтой.", "success");
      await invalidate();
      navigate("/people");
    },
    onError: (error) => toast(error instanceof Error ? error.message : "Устгахад алдаа гарлаа.", "error"),
  });

  const restore = useMutation({
    mutationFn: () => api.post<PersonDetail>(`/people/${id}/restore`),
    onSuccess: async () => {
      toast("Бүртгэл амжилттай сэргээгдлээ.", "success");
      await invalidate();
    },
    onError: (error) => toast(error instanceof Error ? error.message : "Сэргээхэд алдаа гарлаа.", "error"),
  });

  const createAccount = useMutation({
    mutationFn: () =>
      api.post(`/people/${id}/account`, {
        username: accountUsername.trim(),
        password: accountPassword,
      }),
    onSuccess: async () => {
      setAccountOpen(false);
      setAccountUsername("");
      setAccountPassword("");
      toast("Нэвтрэх эрх амжилттай үүслээ.", "success");
      await queryClient.invalidateQueries({ queryKey: ["person-account", id] });
      await queryClient.invalidateQueries({ queryKey: ["users"] });
      await queryClient.invalidateQueries({ queryKey: ["person-history", id] });
    },
    onError: (error) =>
      toast(error instanceof Error ? error.message : "Нэвтрэх эрх үүсгэхэд алдаа гарлаа.", "error"),
  });

  const resetAccountPassword = useMutation({
    mutationFn: () =>
      api.post(`/people/${id}/account/reset-password`, {
        new_password: newPassword,
      }),
    onSuccess: async () => {
      setResetOpen(false);
      setNewPassword("");
      toast("Нууц үг солигдож, хуучин сессүүд хаагдлаа.", "success");
      await queryClient.invalidateQueries({ queryKey: ["person-account", id] });
      await queryClient.invalidateQueries({ queryKey: ["person-history", id] });
    },
    onError: (error) =>
      toast(error instanceof Error ? error.message : "Нууц үг солиход алдаа гарлаа.", "error"),
  });

  function submitAccount() {
    setAccountFormError("");
    if (accountUsername.trim().length < 3) {
      setAccountFormError("Хэрэглэгчийн нэр 3-аас доошгүй тэмдэгт байна.");
      return;
    }
    if (accountPassword.length < 10) {
      setAccountFormError("Нууц үг 10-аас доошгүй тэмдэгт байна.");
      return;
    }
    createAccount.mutate();
  }

  function submitReset() {
    setResetFormError("");
    if (newPassword.length < 10) {
      setResetFormError("Нууц үг 10-аас доошгүй тэмдэгт байна.");
      return;
    }
    resetAccountPassword.mutate();
  }

  const purge = useMutation({
    mutationFn: () => api.post(`/people/${id}/purge`, { confirm_reg_number: confirmReg }),
    onSuccess: async () => {
      setPurgeOpen(false);
      toast("Бүртгэл бүр мөсөн устгагдлаа.", "success");
      await queryClient.invalidateQueries({ queryKey: ["people"] });
      navigate("/people");
    },
    onError: (error) => toast(error instanceof Error ? error.message : "Бүр мөсөн устгахад алдаа гарлаа.", "error"),
  });

  if (detailQuery.isLoading) return <Spinner />;
  if (detailQuery.isError || !detailQuery.data) {
    return (
      <ErrorState
        message="Иргэний бүртгэл олдсонгүй эсвэл хандах эрх танд байхгүй."
        onRetry={() => void detailQuery.refetch()}
      />
    );
  }

  const person = detailQuery.data;
  const isDeleted = person.status === "DELETED";
  const fullProfile = person.full_profile;
  const path = person.path.length > 0 ? person.path : [];

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-1 text-xs text-fg/50">
        <Link to="/people" className="hover:text-acid-300">Иргэдийн бүртгэл</Link>
        {path.map((item) => (
          <span key={item.id} className="flex items-center gap-1">
            <ChevronRight size={12} />
            <Link to={`/people/${item.id}`} className="hover:text-acid-300">
              {fullName(item)}
            </Link>
          </span>
        ))}
      </div>

      {isDeleted && (
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 backdrop-blur-xl dark:text-amber-300">
          <span className="flex items-center gap-2">
            <CircleAlert size={17} />
            Энэ бүртгэл устгагдсан төлөвтэй байна{person.deleted_at ? ` · ${formatDateTime(person.deleted_at)}` : ""}.
          </span>
          {person.permissions.can_restore && (
            <Button size="sm" variant="secondary" icon={<RotateCcw size={14} />} loading={restore.isPending} onClick={() => restore.mutate()}>
              Сэргээх
            </Button>
          )}
        </div>
      )}

      <PageHeader
        title={fullName(person)}
        description={
          fullProfile
            ? `${person.reg_number} · ${GROUP_LABELS[person.group_type]} · ${person.district ?? "Дүүрэг тодорхойгүй"}`
            : `${GROUP_LABELS[person.group_type]} · ${person.district ?? "Дүүрэг тодорхойгүй"} · Хязгаарлагдмал харагдац`
        }
        actions={
          <>
            <Button variant="ghost" icon={<ArrowLeft size={16} />} onClick={() => navigate("/people")}>
              Буцах
            </Button>
            {user?.is_admin && !isDeleted && person.group_type !== "MEMBER" && (
              <Button
                variant="secondary"
                icon={<Upload size={16} />}
                onClick={() =>
                  navigate(
                    `/imports?${new URLSearchParams({
                      parent_id: String(person.id),
                      parent_reg: person.reg_number,
                      parent_last: person.last_name,
                      parent_first: person.first_name,
                      parent_group: person.group_type,
                    }).toString()}`,
                  )
                }
              >
                Доор нь импортлох
              </Button>
            )}
            {person.permissions.can_edit && !isDeleted && (
              <Button variant="secondary" icon={<Edit3 size={16} />} onClick={() => navigate(`/people/${person.id}/edit`)}>
                Засах
              </Button>
            )}
            {person.permissions.can_delete && !isDeleted && (
              <Button variant="danger" icon={<Trash2 size={16} />} onClick={() => setDeleteOpen(true)}>
                Устгах
              </Button>
            )}
            {user?.is_admin && isDeleted && (
              <Button variant="danger" icon={<ShieldAlert size={16} />} onClick={() => setPurgeOpen(true)}>
                Бүр мөсөн устгах
              </Button>
            )}
          </>
        }
      />

      <div className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
        <div className="space-y-5">
          <Card className="p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="flex items-center gap-4">
                <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-acid-400/[0.07] text-lg font-semibold text-acid-300">
                  {initials(person)}
                </span>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-lg font-semibold text-fg">{fullName(person)}</h3>
                    <Badge tone={isDeleted ? "danger" : "success"}>{STATUS_LABELS[person.status]}</Badge>
                  </div>
                  <p className="mt-1 font-mono text-xs text-fg/50">
                    {fullProfile ? person.reg_number : "Хязгаарлагдмал мэдээлэл"}
                  </p>
                </div>
              </div>
              <Badge tone="brand">{GROUP_LABELS[person.group_type]}</Badge>
            </div>

            <dl className="mt-6 grid gap-4 sm:grid-cols-2">
              {fullProfile && (
                <InfoItem icon={<UserRound size={15} />} label="Хүйс" value={GENDER_LABELS[person.gender]} />
              )}
              {fullProfile && (
                <InfoItem
                  icon={<CalendarDays size={15} />}
                  label="Төрсөн огноо"
                  value={person.birth_date ? `${formatDate(person.birth_date)}${person.age !== null ? ` · ${person.age} нас` : ""}` : "—"}
                />
              )}
              <InfoItem icon={<Phone size={15} />} label="Утас" value={person.phone ?? "—"} mono />
              <InfoItem icon={<MapPin size={15} />} label="Хаяг" value={person.address ?? (person.permissions.can_view_sensitive ? "—" : "Харах эрхгүй")} />
              <InfoItem icon={<Building2 size={15} />} label="Дүүрэг, хороо" value={[person.district, person.khoroo].filter(Boolean).join(", ") || "—"} />
              {fullProfile && (
                <InfoItem icon={<Briefcase size={15} />} label="Ажил" value={person.job ?? "—"} />
              )}
              <InfoItem icon={<Network size={15} />} label="Бүлгийн төрөл" value={GROUP_LABELS[person.group_type]} />
              {fullProfile && (
                <InfoItem icon={<Users size={15} />} label="Шууд гишүүн" value={`${person.direct_member_count} бүртгэл`} />
              )}
            </dl>

            {fullProfile && person.parent && (
              <div className="mt-5 rounded-lg border border-fg/[0.07] bg-fg/[0.04] px-4 py-3">
                <p className="text-[11px] font-medium uppercase tracking-wide text-fg/40">Харьяалагдах бүртгэл</p>
                <Link to={`/people/${person.parent.id}`} className="mt-1 flex items-center gap-2 text-sm font-medium text-acid-300 hover:underline">
                  {fullName(person.parent)} <span className="font-mono text-xs text-fg/50">{person.parent.reg_number}</span>
                </Link>
              </div>
            )}
          </Card>

          {fullProfile && (
          <Card className="overflow-hidden">
            <div className="flex items-center justify-between border-b border-fg/[0.07] px-5 py-4">
              <div className="flex items-center gap-2">
                <Users size={16} className="text-acid-300" />
                <h3 className="text-sm font-semibold text-fg">Шууд харьяалах гишүүд</h3>
              </div>
              <div className="flex items-center gap-2">
                <Badge>{person.direct_member_count}</Badge>
                {person.direct_member_count > 0 && (
                  <Link
                    to={`/people?${new URLSearchParams({
                      under_person_id: String(person.id),
                      under_reg: person.reg_number,
                      under_last: person.last_name,
                      under_first: person.first_name,
                    }).toString()}`}
                    className="text-xs font-medium text-acid-300 hover:underline"
                  >
                    Бүх доорх бүртгэл
                  </Link>
                )}
              </div>
            </div>
            {membersQuery.isLoading ? (
              <Spinner className="py-10" />
            ) : !membersQuery.data || membersQuery.data.items.length === 0 ? (
              <EmptyState title="Гишүүн бүртгэгдээгүй" description="Энэ бүртгэлийн доор шууд харьяалах иргэн байхгүй." />
            ) : (
              <>
                <ul className="divide-y divide-fg/[0.04]">
                  {membersQuery.data.items.map((member) => (
                    <li key={member.id}>
                      <Link to={`/people/${member.id}`} className="flex items-center gap-3 px-5 py-3 hover:bg-fg/[0.04]">
                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-fg/[0.06] text-[11px] font-semibold text-fg/70">
                          {initials(member)}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-fg/80">{fullName(member)}</p>
                          <p className="font-mono text-[11px] text-fg/50">{member.reg_number}</p>
                        </div>
                        <Badge tone="brand">{GROUP_LABELS[member.group_type]}</Badge>
                        <ChevronRight size={15} className="text-fg/30" />
                      </Link>
                    </li>
                  ))}
                </ul>
                <div className="border-t border-fg/[0.07] px-4 py-3">
                  <Pagination
                    page={membersQuery.data.page}
                    totalPages={membersQuery.data.total_pages}
                    total={membersQuery.data.total}
                    onChange={setMemberPage}
                  />
                </div>
              </>
            )}
          </Card>
          )}
        </div>

        {fullProfile && (
        <div className="space-y-5">
          {person.permissions.can_manage_account && (
            <Card className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-fg">
                  <KeyRound size={16} className="text-acid-300" /> Нэвтрэх эрх
                </h3>
                {accountQuery.data?.account && (
                  <Badge tone={accountQuery.data.account.is_active ? "success" : "danger"}>
                    {accountQuery.data.account.is_active ? "Идэвхтэй" : "Идэвхгүй"}
                  </Badge>
                )}
              </div>
              {accountQuery.isLoading ? (
                <Spinner className="py-6" />
              ) : accountQuery.isError ? (
                <p className="py-4 text-xs text-red-400">Нэвтрэх эрхийн мэдээлэл ачаалж чадсангүй.</p>
              ) : accountQuery.data?.account ? (
                <>
                  <dl className="mt-4 space-y-2 text-xs">
                    <div className="flex justify-between gap-3">
                      <dt className="text-fg/50">Хэрэглэгчийн нэр</dt>
                      <dd className="font-mono text-fg/80">{accountQuery.data.account.username}</dd>
                    </div>
                    <div className="flex justify-between gap-3">
                      <dt className="text-fg/50">Эрх</dt>
                      <dd className="text-fg/80">{ROLE_LABELS[accountQuery.data.account.role]}</dd>
                    </div>
                    <div className="flex justify-between gap-3">
                      <dt className="text-fg/50">Үүссэн</dt>
                      <dd className="text-right text-fg/70">
                        {formatDateTime(accountQuery.data.account.created_at)}
                      </dd>
                    </div>
                  </dl>
                  <Button
                    className="mt-4 w-full"
                    variant="secondary"
                    icon={<KeyRound size={15} />}
                    onClick={() => {
                      setResetOpen(true);
                      setNewPassword("");
                      setResetFormError("");
                    }}
                  >
                    Нууц үг солих
                  </Button>
                </>
              ) : (
                <>
                  <p className="mt-3 text-xs leading-5 text-fg/50">
                    Энэ хүнд нэвтрэх эрх үүсээгүй байна. Хэрэглэгчийн нэр, анхны нууц үг өгч
                    системд нэвтрэх боломж олгоно.
                  </p>
                  <Button
                    className="mt-4 w-full"
                    icon={<UserPlus size={15} />}
                    onClick={() => {
                      setAccountOpen(true);
                      setAccountUsername("");
                      setAccountPassword("");
                      setAccountFormError("");
                    }}
                  >
                    Нэвтрэх эрх үүсгэх
                  </Button>
                </>
              )}
            </Card>
          )}

          <Card className="p-5">
            <div className="flex items-center gap-2">
              <History size={16} className="text-acid-300" />
              <h3 className="text-sm font-semibold text-fg">Өөрчлөлтийн түүх</h3>
            </div>
            {historyQuery.isLoading ? (
              <Spinner className="py-10" />
            ) : !historyQuery.data || historyQuery.data.length === 0 ? (
              <p className="py-8 text-center text-xs text-fg/50">Түүх байхгүй.</p>
            ) : (
              <ol className="mt-4 space-y-4">
                {historyQuery.data.map((item) => (
                  <li key={item.id} className="relative flex gap-3 pb-1">
                    <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-acid-400 ring-4 ring-acid-400/10" />
                    <div>
                      <p className="text-xs font-medium text-fg/80">
                        {AUDIT_ACTION_LABELS[item.action] ?? item.action}
                      </p>
                      <p className="mt-0.5 text-[11px] text-fg/50">
                        {item.actor?.full_name ?? "Систем"} · {formatDateTime(item.created_at)}
                      </p>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </Card>

          <Card className="p-5">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-fg">
              <Clock size={16} className="text-acid-300" /> Системийн мэдээлэл
            </h3>
            <dl className="mt-3 space-y-2 text-xs">
              <div className="flex justify-between gap-3">
                <dt className="text-fg/50">Бүртгэсэн</dt>
                <dd className="text-right text-fg/70">{formatDateTime(person.created_at)}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-fg/50">Сүүлд өөрчилсөн</dt>
                <dd className="text-right text-fg/70">{formatDateTime(person.updated_at)}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-fg/50">Бүртгэсэн хэрэглэгч</dt>
                <dd className="text-right text-fg/70">{person.created_by?.full_name ?? "—"}</dd>
              </div>
            </dl>
          </Card>
        </div>
        )}
      </div>

      <Modal
        open={accountOpen}
        onClose={() => {
          setAccountOpen(false);
          setAccountFormError("");
        }}
        title="Нэвтрэх эрх үүсгэх"
        description="Энэ хүн системд нэвтрэх боломжтой болно. Эрх нь бүлгийн төрлөөр автоматаар тодорхойлогдоно."
        footer={
          <>
            <Button variant="secondary" onClick={() => setAccountOpen(false)}>Болих</Button>
            <Button
              loading={createAccount.isPending}
              icon={<UserPlus size={15} />}
              onClick={submitAccount}
            >
              Үүсгэх
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <Field label="Хэрэглэгчийн нэр" htmlFor="person-account-username" required hint="3–64 тэмдэгт, латин жижиг үсэг/тоо">
            <Input
              id="person-account-username"
              value={accountUsername}
              onChange={(event) => {
                setAccountUsername(event.target.value);
                setAccountFormError("");
              }}
              autoComplete="off"
              placeholder="bat.erdene"
            />
          </Field>
          <Field label="Анхны нууц үг" htmlFor="person-account-password" required hint="10-аас доошгүй тэмдэгт, үсэг болон тоо агуулна">
            <Input
              id="person-account-password"
              type="password"
              value={accountPassword}
              onChange={(event) => {
                setAccountPassword(event.target.value);
                setAccountFormError("");
              }}
              autoComplete="new-password"
            />
          </Field>
          {accountFormError && <p className="text-xs text-rose-400">{accountFormError}</p>}
          <p className="rounded-lg border border-fg/[0.08] bg-fg/[0.03] px-3 py-2 text-xs leading-5 text-fg/50">
            Оноох эрх: <span className="font-medium text-fg/80">{ROLE_LABELS[person.group_type === "MEMBER" ? "MEMBER" : "LEADER"]}</span>
            {" · "}энэ хүний харьяаллд тохируулна.
          </p>
        </div>
      </Modal>

      <Modal
        open={resetOpen}
        onClose={() => {
          setResetOpen(false);
          setResetFormError("");
        }}
        title="Нууц үг солих"
        description="Шинэ нууц үг өгсний дараа энэ хэрэглэгчийн бүх идэвхтэй сесс хаагдана."
        footer={
          <>
            <Button variant="secondary" onClick={() => setResetOpen(false)}>Болих</Button>
            <Button
              loading={resetAccountPassword.isPending}
              icon={<KeyRound size={15} />}
              onClick={submitReset}
            >
              Солих
            </Button>
          </>
        }
      >
        <Field label="Шинэ нууц үг" htmlFor="person-account-new-password" required hint="10-аас доошгүй тэмдэгт, үсэг болон тоо агуулна">
          <Input
            id="person-account-new-password"
            type="password"
            value={newPassword}
            onChange={(event) => {
              setNewPassword(event.target.value);
              setResetFormError("");
            }}
            autoComplete="new-password"
          />
        </Field>
        {resetFormError && <p className="mt-2 text-xs text-rose-400">{resetFormError}</p>}
      </Modal>

      <Modal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        title="Бүртгэлийг устгах уу?"
        description="Устгасан бүртгэл дата баазад хадгалагдаж, дараа нь сэргээх боломжтой."
        footer={
          <>
            <Button variant="secondary" onClick={() => setDeleteOpen(false)}>Болих</Button>
            <Button variant="danger" loading={remove.isPending} onClick={() => remove.mutate()}>
              Устгах
            </Button>
          </>
        }
      >
        <p className="text-sm leading-6 text-fg/60">
          <span className="font-medium text-fg">{fullName(person)}</span> ({person.reg_number}) иргэний
          бүртгэлийг устгах гэж байна. Хэрэв доор нь харьяалах гишүүн байгаа бол эхлээд тэдгээрийн
          харьяаллыг шилжүүлнэ үү.
        </p>
      </Modal>

      <Modal
        open={purgeOpen}
        onClose={() => setPurgeOpen(false)}
        title="Бүр мөсөн устгах"
        description="Энэ үйлдлийг буцаах боломжгүй."
        footer={
          <>
            <Button variant="secondary" onClick={() => setPurgeOpen(false)}>Болих</Button>
            <Button
              variant="danger"
              loading={purge.isPending}
              disabled={confirmReg.trim().toUpperCase() !== person.reg_number}
              onClick={() => purge.mutate()}
            >
              Бүр мөсөн устгах
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-sm leading-6 text-fg/60">
            Баталгаажуулахын тулд <span className="font-mono font-semibold text-fg">{person.reg_number}</span>{" "}
            регистрийн дугаарыг дахин оруулна уу.
          </p>
          <Field label="Регистрийн дугаар" htmlFor="confirm-reg">
            <Input
              id="confirm-reg"
              value={confirmReg}
              onChange={(event) => setConfirmReg(event.target.value)}
              placeholder={person.reg_number}
              autoComplete="off"
            />
          </Field>
        </div>
      </Modal>
    </div>
  );
}

function InfoItem({
  icon,
  label,
  value,
  mono,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-fg/40">
        {icon}
        {label}
      </dt>
      <dd className={`mt-1 text-sm text-fg/80 ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}
