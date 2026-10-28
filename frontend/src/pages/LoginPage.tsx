import { useEffect, useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Eye, EyeOff, LockKeyhole, Network, ShieldCheck, Users } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";
import { ApiError } from "../api/client";
import { Button, Field, Input } from "../components/ui";
import { ThemeToggle } from "../components/ui/ThemeToggle";

export default function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string } | null)?.from ?? "/";

  useEffect(() => {
    if (user) navigate(from, { replace: true });
  }, [user, from, navigate]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(username.trim(), password);
      navigate(from, { replace: true });
    } catch (caught) {
      if (caught instanceof ApiError) setError(caught.message);
      else setError("Нэвтрэх үед алдаа гарлаа. Дахин оролдоно уу.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen bg-night-950 text-fg lg:grid-cols-[1.05fr_1fr]">
      <section className="relative hidden overflow-hidden p-12 text-fg lg:flex lg:flex-col lg:justify-between">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            backgroundImage:
              "radial-gradient(circle at 18% 18%, rgba(139,92,246,0.22), transparent 44%), radial-gradient(circle at 82% 72%, rgba(34,211,238,0.14), transparent 44%)",
          }}
        />
        <div className="absolute inset-0 opacity-[0.045]" aria-hidden>
          <svg width="100%" height="100%">
            <defs>
              <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
                <path d="M 48 0 L 0 0 0 48" fill="none" stroke="white" strokeWidth="1" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        <div className="relative">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 text-sm font-bold text-white shadow-[0_10px_28px_-12px_rgba(124,58,237,0.9)]">
              ИБ
            </span>
            <div>
              <p className="text-sm font-semibold">Иргэдийн нэгдсэн бүртгэл</p>
              <p className="text-xs text-fg/40">Хүн амын бүртгэлийн удирдлагын систем</p>
            </div>
          </div>
        </div>

        <div className="relative max-w-lg">
          <h1 className="text-4xl font-semibold leading-tight tracking-tight text-fg">
            Бүртгэл бүр тодорхой,
            <br />
            харьяалал бүр <span className="bg-gradient-to-r from-violet-500 to-cyan-500 bg-clip-text text-transparent dark:from-violet-300 dark:to-cyan-300">нэгдсэн</span>.
          </h1>
          <p className="mt-4 text-sm leading-7 text-fg/45">
            Иргэдийн мэдээлэл, Түмт–Мянгат–Зуут–Аравт бүтэц, хандах эрхийг нэг
            аюулгүй системд удирдана.
          </p>

          <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
            {[
              { icon: Users, label: "500,000 хүртэл бүртгэл" },
              { icon: Network, label: "Харьяаллын бүтэц" },
              { icon: ShieldCheck, label: "Эрх, аудитын хяналт" },
            ].map((item) => (
              <div
                key={item.label}
                className="glass-soft rounded-xl px-3 py-3"
              >
                <item.icon size={18} className="text-acid-300" />
                <p className="mt-2 text-xs leading-5 text-fg/55">{item.label}</p>
              </div>
            ))}
          </div>
        </div>

        <p className="relative text-xs text-fg/50">
          Зөвхөн эрх бүхий хэрэглэгч нэвтрэх боломжтой. Бүх үйлдэл аудитлагдана.
        </p>
      </section>

      <section className="relative flex items-center justify-center overflow-hidden border-l border-fg/[0.06] px-5 py-10 sm:px-10">
        <div className="absolute right-5 top-5 z-10">
          <ThemeToggle />
        </div>
        <div className="pointer-events-none absolute -right-32 top-0 h-96 w-96 rounded-full bg-violet-500/[0.14] blur-[110px]" />
        <div className="pointer-events-none absolute -bottom-40 -left-20 h-96 w-96 rounded-full bg-cyan-500/[0.1] blur-[110px]" />
        <div className="glass-surface relative w-full max-w-sm rounded-3xl p-6 sm:p-8">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 text-sm font-bold text-white shadow-[0_10px_28px_-12px_rgba(124,58,237,0.9)]">
              ИБ
            </span>
            <div>
              <p className="text-sm font-semibold text-fg">Иргэдийн бүртгэл</p>
              <p className="text-xs text-fg/50">Нэгдсэн удирдлагын систем</p>
            </div>
          </div>

          <div className="mb-7">
            <p className="text-xs font-medium uppercase tracking-wider text-acid-300">
              Нэвтрэх
            </p>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight text-fg">
              Системд тавтай морил
            </h2>
            <p className="mt-1 text-sm text-fg/50">
              Хэрэглэгчийн нэр, нууц үгээ оруулна уу.
            </p>
          </div>

          {error && (
            <div
              className="mb-5 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2.5 text-sm text-red-300"
              role="alert"
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label="Хэрэглэгчийн нэр" htmlFor="username" required>
              <Input
                id="username"
                name="username"
                autoComplete="username"
                autoFocus
                required
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="жишээ: bat.erdene"
              />
            </Field>

            <Field label="Нууц үг" htmlFor="password" required>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder="Нууц үгээ оруулна уу"
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-fg/40 hover:text-fg/70"
                  aria-label={showPassword ? "Нууц үг нуух" : "Нууц үг харах"}
                >
                  {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </Field>

            <Button type="submit" size="lg" loading={submitting} className="w-full">
              {submitting ? "Нэвтэрч байна…" : "Нэвтрэх"}
            </Button>
          </form>

          <div className="mt-6 flex items-start gap-2 rounded-lg bg-fg/[0.03] px-3 py-2.5 text-xs leading-5 text-fg/50">
            <LockKeyhole size={15} className="mt-0.5 shrink-0" />
            <p>
              Нэвтрэлт нь аюулгүй cookie болон CSRF хамгаалалтад суурилна. Нэг
              сесс 8 цаг үргэлжилнэ.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
