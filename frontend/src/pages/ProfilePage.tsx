import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { KeyRound, LockKeyhole, LogOut, ShieldCheck, UserCog } from "lucide-react";
import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthProvider";
import { Badge, Button, Card, Field, Input } from "../components/ui";
import { PageHeader } from "../components/layout/AppShell";
import { useToast } from "../components/ui/Toast";
import { ROLE_LABELS } from "../lib/labels";
import { fullName } from "../lib/format";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!user) return null;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (newPassword.length < 10) {
      setError("Шинэ нууц үг 10-аас доошгүй тэмдэгт байна.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Шинэ нууц үг болон давталт таарахгүй байна.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast("Нууц үг амжилттай солигдлоо.", "success");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Нууц үг солиход алдаа гарлаа.");
    } finally {
      setSubmitting(false);
    }
  }

  const permissionLabels: Array<[keyof typeof user.permissions, string]> = [
    ["can_edit", "Бүртгэл засах"],
    ["can_import", "Импорт хийх"],
    ["can_export", "Экспорт хийх"],
    ["can_view_sensitive", "Мэдрэмжтэй мэдээлэл харах"],
    ["can_delete", "Бүртгэл устгах"],
    ["can_manage_users", "Хэрэглэгч удирдах"],
  ];

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        eyebrow="Миний бүртгэл"
        title={user.full_name}
        description={`@${user.username} · ${ROLE_LABELS[user.role]}`}
        actions={
          <Button
            variant="secondary"
            icon={<LogOut size={16} />}
            onClick={() => {
              void logout().then(() => navigate("/login", { replace: true }));
            }}
          >
            Гарах
          </Button>
        }
      />

      <div className="grid gap-5 md:grid-cols-[1fr_1.1fr]">
        <div className="space-y-5">
          <Card className="p-5">
            <div className="flex items-center gap-3">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-acid-400/[0.07] text-base font-semibold text-acid-300">
                {user.full_name.charAt(0).toUpperCase()}
              </span>
              <div>
                <p className="text-sm font-semibold text-fg">{user.full_name}</p>
                <p className="text-xs text-fg/50">@{user.username}</p>
              </div>
            </div>
            <dl className="mt-5 space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <dt className="text-fg/50">Эрх</dt>
                <dd><Badge tone={user.is_admin ? "brand" : "neutral"}>{ROLE_LABELS[user.role]}</Badge></dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-fg/50">Хандах хүрээ</dt>
                <dd className="text-right text-fg/80">
                  {user.is_admin ? "Бүх бүртгэл" : user.leader_person ? fullName(user.leader_person) : "Харьяалалгүй"}
                </dd>
              </div>
            </dl>
          </Card>

          <Card className="p-5">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-fg">
              <ShieldCheck size={16} className="text-acid-300" /> Миний эрхүүд
            </h3>
            <ul className="mt-3 space-y-2">
              {permissionLabels.map(([key, label]) => {
                const enabled = user.is_admin || user.permissions[key];
                return (
                  <li key={key} className="flex items-center justify-between text-xs">
                    <span className={enabled ? "text-fg/70" : "text-fg/40"}>{label}</span>
                    <Badge tone={enabled ? "success" : "neutral"}>{enabled ? "Тийм" : "Үгүй"}</Badge>
                  </li>
                );
              })}
            </ul>
          </Card>
        </div>

        <Card className="p-5 sm:p-6">
          <div className="flex items-center gap-2">
            <KeyRound size={17} className="text-acid-300" />
            <h3 className="text-sm font-semibold text-fg">Нууц үг солих</h3>
          </div>
          <p className="mt-1 text-xs text-fg/50">Аюулгүй байдлын үүднээс 10-аас доошгүй тэмдэгт ашиглана уу.</p>

          {error && (
            <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <Field label="Одоогийн нууц үг" htmlFor="current-password" required>
              <Input
                id="current-password"
                type="password"
                autoComplete="current-password"
                required
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
              />
            </Field>
            <Field label="Шинэ нууц үг" htmlFor="new-password" required>
              <Input
                id="new-password"
                type="password"
                autoComplete="new-password"
                required
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
              />
            </Field>
            <Field label="Шинэ нууц үг давтах" htmlFor="confirm-password" required>
              <Input
                id="confirm-password"
                type="password"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
              />
            </Field>

            <div className="flex items-start gap-2 rounded-lg bg-fg/[0.03] px-3 py-2.5 text-xs leading-5 text-fg/50">
              <LockKeyhole size={14} className="mt-0.5 shrink-0" />
              Нууц үг солигдсоны дараа бусад төхөөрөмж дээрх сессүүд хаагдана.
            </div>

            <Button type="submit" loading={submitting} icon={<UserCog size={16} />}>
              Нууц үг солих
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
