import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Pencil, Plus, Search, UserCog } from "lucide-react";
import { api, ApiError, buildQuery } from "../api/client";
import type {
  Page,
  ParentCandidate,
  Role,
  UserCreatePayload,
  UserListItem,
  UserUpdatePayload,
} from "../api/types";
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
  Select,
  Spinner,
} from "../components/ui";
import { PageHeader } from "../components/layout/AppShell";
import { useToast } from "../components/ui/Toast";
import { GROUP_LABELS, ROLE_LABELS } from "../lib/labels";
import { formatDateTime, fullName } from "../lib/format";
import { LeaderPicker } from "../components/people/LeaderPicker";

interface FormState {
  username: string;
  full_name: string;
  password: string;
  role: Role;
  is_active: boolean;
  leader: ParentCandidate | null;
}

const emptyForm: FormState = {
  username: "",
  full_name: "",
  password: "",
  role: "LEADER",
  is_active: true,
  leader: null,
};

export default function UsersPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<UserListItem | null>(null);
  const [resetUser, setResetUser] = useState<UserListItem | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [newPassword, setNewPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const usersQuery = useQuery({
    queryKey: ["users", search, page],
    queryFn: () => api.get<Page<UserListItem>>(`/users${buildQuery({ search, page, page_size: 20 })}`),
  });

  useEffect(() => {
    if (createOpen) {
      setForm(emptyForm);
      setErrors({});
    }
  }, [createOpen]);

  useEffect(() => {
    if (editUser) {
      setForm({
        username: editUser.username,
        full_name: editUser.full_name,
        password: "",
        role: editUser.role,
        is_active: editUser.is_active,
        leader: editUser.leader_person,
      });
      setErrors({});
    }
  }, [editUser]);

  const createMutation = useMutation({
    mutationFn: (payload: UserCreatePayload) => api.post<UserListItem>("/users", payload),
    onSuccess: async () => {
      setCreateOpen(false);
      toast("Хэрэглэгч амжилттай үүслээ.", "success");
      await queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error) => handleError(error, "Хэрэглэгч үүсгэхэд алдаа гарлаа."),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UserUpdatePayload }) =>
      api.patch<UserListItem>(`/users/${id}`, payload),
    onSuccess: async () => {
      setEditUser(null);
      toast("Хэрэглэгчийн мэдээлэл шинэчлэгдлээ.", "success");
      await queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error) => handleError(error, "Хэрэглэгч засахад алдаа гарлаа."),
  });

  const resetMutation = useMutation({
    mutationFn: ({ id, password }: { id: number; password: string }) =>
      api.post(`/users/${id}/reset-password`, { new_password: password }),
    onSuccess: () => {
      setResetUser(null);
      setNewPassword("");
      toast("Нууц үг амжилттай шинэчлэгдлээ.", "success");
    },
    onError: (error) => handleError(error, "Нууц үг шинэчлэхэд алдаа гарлаа."),
  });

  function handleError(error: unknown, fallback: string) {
    if (error instanceof ApiError) {
      setErrors(error.fields);
      toast(error.message, "error");
    } else {
      toast(fallback, "error");
    }
  }

  function updateRole(role: Role) {
    setForm({
      ...form,
      role,
      ...(role === form.role ? {} : { leader: null }),
      ...(role === "ADMIN" ? { leader: null } : {}),
    });
  }

  function validateLeader(): boolean {
    if (form.role === "ADMIN") return true;
    if (!form.leader) {
      setErrors({
        leader_person_id:
          form.role === "MEMBER"
            ? "Гишүүнээ сонгоно уу."
            : "Удирдах хүнээ сонгоно уу.",
      });
      return false;
    }
    return true;
  }

  function submitCreate() {
    setErrors({});
    if (!validateLeader()) return;
    if (form.password.length < 10) {
      setErrors({ password: "Нууц үг 10-аас доошгүй тэмдэгт байна." });
      return;
    }
    createMutation.mutate({
      username: form.username,
      full_name: form.full_name,
      password: form.password,
      role: form.role,
      leader_person_id: form.role === "ADMIN" ? null : (form.leader?.id ?? null),
    });
  }

  function submitEdit() {
    if (!editUser) return;
    setErrors({});
    if (!validateLeader()) return;
    updateMutation.mutate({
      id: editUser.id,
      payload: {
        full_name: form.full_name,
        role: form.role,
        is_active: form.is_active,
        leader_person_id: form.role === "ADMIN" ? null : (form.leader?.id ?? null),
      },
    });
  }

  return (
    <div>
      <PageHeader
        eyebrow="Хандах эрх"
        title="Хэрэглэгчдийн удирдлага"
        description="Админ бүх бүртгэлийг, удирдагч зөвхөн өөрийн модны бүртгэлийг удирдана."
        actions={
          <Button icon={<Plus size={16} />} onClick={() => setCreateOpen(true)}>
            Хэрэглэгч нэмэх
          </Button>
        }
      />

      <Card className="p-4">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            setSearch(searchInput);
            setPage(1);
          }}
          className="flex flex-col gap-2 sm:flex-row"
        >
          <Input
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Нэр эсвэл хэрэглэгчийн нэрээр хайх…"
            aria-label="Хэрэглэгч хайх"
          />
          <Button type="submit" icon={<Search size={16} />}>Хайх</Button>
        </form>
      </Card>

      <Card className="mt-4 overflow-hidden">
        {usersQuery.isLoading ? (
          <Spinner />
        ) : usersQuery.isError ? (
          <ErrorState message="Хэрэглэгчдийн жагсаалтыг ачаалж чадсангүй." onRetry={() => void usersQuery.refetch()} />
        ) : !usersQuery.data || usersQuery.data.items.length === 0 ? (
          <EmptyState icon={<UserCog size={22} />} title="Хэрэглэгч олдсонгүй" description="Шинэ хэрэглэгч нэмж эхэлнэ үү." />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[820px] text-left text-sm">
                <thead className="border-b border-fg/[0.07] bg-fg/[0.04] text-xs uppercase tracking-wide text-fg/50">
                  <tr>
                    <th className="px-5 py-3 font-medium">Хэрэглэгч</th>
                    <th className="px-4 py-3 font-medium">Эрх</th>
                    <th className="px-4 py-3 font-medium">Удирдах хүн</th>
                    <th className="px-4 py-3 font-medium">Хандах хүрээ</th>
                    <th className="px-4 py-3 font-medium">Төлөв</th>
                    <th className="px-4 py-3 font-medium">Үүсгэсэн</th>
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody>
                  {usersQuery.data.items.map((item) => (
                    <tr key={item.id} className="border-b border-fg/[0.04] last:border-0 hover:bg-fg/[0.03]">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-fg/[0.06] text-xs font-semibold text-fg/70">
                            {item.full_name.charAt(0).toUpperCase()}
                          </span>
                          <div>
                            <p className="font-medium text-fg">{item.full_name}</p>
                            <p className="text-[11px] text-fg/50">@{item.username}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={item.role === "ADMIN" ? "brand" : "neutral"}>
                          {ROLE_LABELS[item.role]}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-fg/60">
                        {item.leader_person ? (
                          <div className="flex flex-col gap-1">
                            <span className="font-medium text-fg/80">{fullName(item.leader_person)}</span>
                            <Badge tone="brand">{GROUP_LABELS[item.leader_person.group_type]}</Badge>
                          </div>
                        ) : (
                          <span className="text-fg/40">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs text-fg/60">
                        {item.role === "ADMIN"
                          ? "Бүх бүртгэл"
                          : item.role === "MEMBER"
                            ? "Нэг аравтын гишүүд"
                            : item.leader_person
                              ? "Удирдах хүний мод"
                              : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <Badge tone={item.is_active ? "success" : "danger"}>
                          {item.is_active ? "Идэвхтэй" : "Идэвхгүй"}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-xs text-fg/50">{formatDateTime(item.created_at)}</td>
                      <td className="px-5 py-3">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="sm" icon={<Pencil size={14} />} onClick={() => setEditUser(item)}>
                            Засах
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<KeyRound size={14} />}
                            onClick={() => {
                              setResetUser(item);
                              setNewPassword("");
                              setErrors({});
                            }}
                          >
                            Нууц үг
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="border-t border-fg/[0.07] px-4 py-3">
              <Pagination
                page={usersQuery.data.page}
                totalPages={usersQuery.data.total_pages}
                total={usersQuery.data.total}
                onChange={setPage}
              />
            </div>
          </>
        )}
      </Card>

      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Шинэ хэрэглэгч"
        description="Хэрэглэгчийн нэвтрэх мэдээлэл, эрх, удирдах хүнийг тохируулна."
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setCreateOpen(false)}>Болих</Button>
            <Button loading={createMutation.isPending} onClick={submitCreate}>Үүсгэх</Button>
          </>
        }
      >
        <form onSubmit={(event) => { event.preventDefault(); submitCreate(); }} className="space-y-5">
          <div className="rounded-xl border border-acid-400/15 bg-acid-400/[0.05] px-3 py-2.5 text-xs leading-relaxed text-fg/60">
            <span className="font-medium text-acid-300">Нэвтрэх мэдээлэл:</span> доор өгсөн нэр, нууц үгээр
            хэрэглэгч <span className="font-mono text-fg/80">/login</span> хуудаснаас нэвтэрнэ.
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field
              label="Нэвтрэх нэр"
              htmlFor="new-username"
              required
              error={errors.username}
              hint="Жишээ: bat.erdene"
            >
              <Input
                id="new-username"
                value={form.username}
                onChange={(event) => setForm({ ...form, username: event.target.value })}
                placeholder="bat.erdene"
                autoComplete="off"
              />
            </Field>
            <Field label="Бүтэн нэр" htmlFor="new-fullname" required error={errors.full_name}>
              <Input
                id="new-fullname"
                value={form.full_name}
                onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                placeholder="Бат Эрдэнэ"
              />
            </Field>
            <Field
              label="Нэвтрэх нууц үг"
              htmlFor="new-password"
              required
              error={errors.password}
              hint="10-аас доошгүй тэмдэгт. Хадгалсны дараа дахин харах боломжгүй."
            >
              <Input
                id="new-password"
                type="password"
                value={form.password}
                onChange={(event) => setForm({ ...form, password: event.target.value })}
                autoComplete="new-password"
              />
            </Field>
            <Field label="Эрх" htmlFor="new-role">
              <Select
                id="new-role"
                value={form.role}
                onChange={(event) => updateRole(event.target.value as Role)}
              >
                <option value="LEADER">Удирдагч</option>
                <option value="MEMBER">Гишүүн</option>
                <option value="ADMIN">Админ</option>
              </Select>
            </Field>
          </div>

          <Field
            label={form.role === "MEMBER" ? "Холбох гишүүн" : "Удирдах хүн"}
            required={form.role !== "ADMIN"}
            error={errors.leader_person_id}
            hint={
              form.role === "ADMIN"
                ? "Админд удирдах хүн шаардлагагүй."
                : form.role === "MEMBER"
                  ? "Гишүүн зөвхөн өөрийн аравтын гишүүдийг харна."
                  : "Удирдагч зөвхөн энэ хүн болон түүний доорх бүх бүртгэлийг харж, засна."
            }
          >
            <LeaderPicker
              value={form.leader}
              onChange={(leader) => setForm({ ...form, leader })}
              disabled={form.role === "ADMIN"}
              mode={form.role === "MEMBER" ? "member" : "leader"}
            />
          </Field>

          {form.role === "LEADER" && form.leader && (
            <div className="rounded-lg border border-acid-400/15 bg-acid-400/[0.06] px-3 py-2 text-xs text-acid-300">
              {fullName(form.leader)} · {GROUP_LABELS[form.leader.group_type]} — хандах хүрээ автоматаар
              энэ хүний мод болно.
            </div>
          )}

          {form.role === "MEMBER" && form.leader && (
            <div className="rounded-lg border border-sky-400/15 bg-sky-400/[0.06] px-3 py-2 text-xs text-sky-300">
              {fullName(form.leader)} · {GROUP_LABELS[form.leader.group_type]} — зөвхөн нэг
              аравтын гишүүдийн нэр, утас, хаягийг харна.
            </div>
          )}

          {form.role === "ADMIN" && (
            <div className="rounded-lg border border-fg/[0.08] bg-fg/[0.03] px-3 py-2 text-xs text-fg/50">
              Админ бүх бүртгэл, импорт, экспорт, аудитыг бүрэн удирдана.
            </div>
          )}
        </form>
      </Modal>

      <Modal
        open={editUser !== null}
        onClose={() => setEditUser(null)}
        title={`${editUser?.full_name ?? ""} · засах`}
        description={`@${editUser?.username ?? ""}`}
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditUser(null)}>Болих</Button>
            <Button loading={updateMutation.isPending} onClick={submitEdit}>Хадгалах</Button>
          </>
        }
      >
        <form onSubmit={(event) => { event.preventDefault(); submitEdit(); }} className="space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-fg/[0.08] bg-fg/[0.03] px-3 py-2.5">
            <div>
              <p className="text-[11px] uppercase tracking-wide text-fg/40">Нэвтрэх нэр</p>
              <p className="font-mono text-sm text-fg/80">@{editUser?.username}</p>
            </div>
            <p className="text-xs text-fg/45">Нууц үгийг жагсаалтын “Нууц үг” товчоор шинэчилнэ.</p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Бүтэн нэр" htmlFor="edit-fullname" required error={errors.full_name}>
              <Input
                id="edit-fullname"
                value={form.full_name}
                onChange={(event) => setForm({ ...form, full_name: event.target.value })}
              />
            </Field>
            <Field label="Эрх" htmlFor="edit-role">
              <Select
                id="edit-role"
                value={form.role}
                onChange={(event) => updateRole(event.target.value as Role)}
              >
                <option value="LEADER">Удирдагч</option>
                <option value="MEMBER">Гишүүн</option>
                <option value="ADMIN">Админ</option>
              </Select>
            </Field>
          </div>

          <Field
            label={form.role === "MEMBER" ? "Холбох гишүүн" : "Удирдах хүн"}
            required={form.role !== "ADMIN"}
            error={errors.leader_person_id}
            hint={
              form.role === "ADMIN"
                ? "Админд удирдах хүн шаардлагагүй."
                : form.role === "MEMBER"
                  ? "Гишүүн зөвхөн өөрийн аравтын гишүүдийг харна."
                  : undefined
            }
          >
            <LeaderPicker
              value={form.leader}
              onChange={(leader) => setForm({ ...form, leader })}
              disabled={form.role === "ADMIN"}
              mode={form.role === "MEMBER" ? "member" : "leader"}
            />
          </Field>

          <label className="flex items-center gap-2 text-sm text-fg/70">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
              className="h-4 w-4 rounded border-fg/[0.16] text-acid-400 focus:ring-acid-400"
            />
            Бүртгэл идэвхтэй
          </label>
        </form>
      </Modal>

      <Modal
        open={resetUser !== null}
        onClose={() => setResetUser(null)}
        title="Нууц үг шинэчлэх"
        description={`${resetUser?.full_name ?? ""} (@${resetUser?.username ?? ""})`}
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setResetUser(null)}>Болих</Button>
            <Button
              disabled={newPassword.length < 10}
              loading={resetMutation.isPending}
              onClick={() => resetUser && resetMutation.mutate({ id: resetUser.id, password: newPassword })}
            >
              Хадгалах
            </Button>
          </>
        }
      >
        <Field label="Шинэ нууц үг" htmlFor="reset-password" required hint="10-аас доошгүй тэмдэгт">
          <Input
            id="reset-password"
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            autoComplete="new-password"
          />
        </Field>
        <p className="mt-3 text-xs text-fg/50">
          Хадгалсны дараа хэрэглэгчийн бүх идэвхтэй сесс хаагдана.
        </p>
      </Modal>
    </div>
  );
}
