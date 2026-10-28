import { useEffect, useRef, useState, type ReactNode } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  BookUser,
  ChevronDown,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Menu,
  Network,
  ShieldCheck,
  Upload,
  UserCog,
  X,
} from "lucide-react";
import { clsx } from "clsx";
import { api } from "../../api/client";
import type { NotificationList } from "../../api/types";
import { useAuth } from "../../auth/AuthProvider";
import { Badge, Button } from "../ui";
import { ThemeToggle } from "../ui/ThemeToggle";
import { formatDateTime, fullName } from "../../lib/format";
import { ROLE_LABELS } from "../../lib/labels";

const navItems = [
  { to: "/", label: "Хяналтын самбар", icon: LayoutDashboard, end: true },
  { to: "/people", label: "Иргэдийн бүртгэл", icon: BookUser },
  { to: "/structure", label: "Бүтцийн харагдац", icon: Network },
  { to: "/imports", label: "Импорт", icon: Upload, admin: true },
  { to: "/users", label: "Хэрэглэгчид", icon: UserCog, admin: true },
  { to: "/audit", label: "Аудитын мөр", icon: ClipboardList, admin: true },
];

export function AppShell({ children }: { children?: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  if (!user) return null;

  const visibleNav = navItems.filter((item) => {
    if (item.admin && !user.is_admin) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-night-950 text-fg">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0"
        style={{
          backgroundImage:
            "radial-gradient(circle at 72% -8%, rgba(139,92,246,0.13), transparent 36%), radial-gradient(circle at 8% 105%, rgba(34,211,238,0.09), transparent 34%)",
        }}
      />
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-fg/[0.08] bg-night-950/75 text-fg/70 backdrop-blur-2xl transition-transform lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-fg/[0.08] px-5">
          <a href="/" className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 text-sm font-bold text-white shadow-[0_8px_24px_-10px_rgba(124,58,237,0.9)]">
              ИБ
            </span>
            <span>
              <span className="block text-sm font-semibold text-fg">Иргэдийн бүртгэл</span>
              <span className="block text-[11px] text-fg/40">Нэгдсэн удирдлага</span>
            </span>
          </a>
          <button
            type="button"
            className="rounded p-1 text-fg/30 lg:hidden"
            onClick={() => setMobileOpen(false)}
            aria-label="Цэс хаах"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {visibleNav.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition",
                    isActive
                      ? "bg-acid-400/[0.08] font-medium text-acid-200 ring-1 ring-inset ring-acid-400/15"
                      : "text-fg/45 hover:bg-fg/[0.04] hover:text-fg/85",
                  )
                }
              >
                <Icon size={18} />
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="border-t border-fg/[0.08] p-4">
          <p className="text-[11px] uppercase tracking-wider text-fg/50">Хандах хүрээ</p>
          <p className="mt-1 text-xs leading-5 text-fg/40">
            {user.is_admin ? "Бүх бүртгэл" : user.leader_person ? fullName(user.leader_person) : "Харьяалалгүй"}
          </p>
          <div className="mt-3 flex items-center gap-1.5 text-[11px] text-fg/40">
            <ShieldCheck size={13} />
            {user.role === "ADMIN"
              ? "Админ эрх"
              : user.role === "MEMBER"
                ? "Гишүүний эрх"
                : "Удирдагчийн эрх"}
          </div>
        </div>
      </aside>

      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-night-950/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden
        />
      )}

      <div className="relative lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-fg/[0.08] bg-night-950/55 px-4 text-fg backdrop-blur-2xl sm:px-6">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="rounded-lg p-2 text-fg/55 hover:bg-fg/[0.06] lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Цэс нээх"
            >
              <Menu size={20} />
            </button>
            <HeaderTitle dark />
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <NotificationMenu dark />
            <ProfileMenu
              dark
              onLogout={async () => {
                await logout();
                navigate("/login", { replace: true });
              }}
            />
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1480px] px-4 py-6 sm:px-6 lg:px-8">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  );
}

function HeaderTitle({ dark = false }: { dark?: boolean }) {
  const { pathname } = useLocation();
  const map: Record<string, string> = {
    "/": "Хяналтын самбар",
    "/people": "Иргэдийн бүртгэл",
    "/structure": "Бүтцийн харагдац",
    "/people/new": "Шинэ иргэн бүртгэх",
    "/imports": "Импорт",
    "/users": "Хэрэглэгчдийн удирдлага",
    "/audit": "Аудитын мөр",
    "/profile": "Миний бүртгэл",
  };
  const title =
    map[pathname] ??
    (pathname.includes("/people/") ? "Иргэний дэлгэрэнгүй" : "Иргэдийн бүртгэл");
  return (
    <h1
      className={clsx(
        "text-sm font-semibold sm:text-base",
        dark ? "text-fg" : "text-fg/80",
      )}
    >
      {title}
    </h1>
  );
}

function NotificationMenu({ dark = false }: { dark?: boolean }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get<NotificationList>("/notifications?limit=10"),
    refetchInterval: 60_000,
  });

  const markAll = useMutation({
    mutationFn: () => api.post("/notifications/read-all"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const unread = data?.unread_count ?? 0;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={clsx(
          "relative rounded-lg p-2 transition",
          dark
            ? "text-fg/60 hover:bg-fg/10 hover:text-fg"
            : "text-fg/50 hover:bg-fg/[0.06] hover:text-fg/80",
        )}
        aria-label="Мэдэгдэл"
        aria-expanded={open}
      >
        <Bell size={19} />
        {unread > 0 && (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-fg">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>
      {open && (
        <div className="glass-overlay absolute right-0 top-12 w-[min(22rem,calc(100vw-2rem))] overflow-hidden rounded-xl shadow-pop animate-fade-in">
          <div className="flex items-center justify-between border-b border-fg/[0.07] px-4 py-3">
            <h3 className="text-sm font-semibold text-fg">Мэдэгдэл</h3>
            {unread > 0 && (
              <button
                type="button"
                onClick={() => markAll.mutate()}
                className="text-xs font-medium text-acid-300 hover:underline"
              >
                Бүгдийг уншсан
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {!data || data.items.length === 0 ? (
              <p className="px-4 py-10 text-center text-sm text-fg/50">Мэдэгдэл байхгүй.</p>
            ) : (
              data.items.map((item) => (
                <div
                  key={item.id}
                  className={clsx(
                    "border-b border-fg/[0.04] px-4 py-3 last:border-0",
                    !item.read_at && "bg-acid-400/[0.04]",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium text-fg/80">{item.title}</p>
                    {!item.read_at && <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-acid-400" />}
                  </div>
                  <p className="mt-0.5 text-xs leading-5 text-fg/50">{item.body}</p>
                  <p className="mt-1 text-[11px] text-fg/40">{formatDateTime(item.created_at)}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ProfileMenu({
  onLogout,
  dark = false,
}: {
  onLogout: () => Promise<void>;
  dark?: boolean;
}) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!open) return;
    const handler = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  if (!user) return null;

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={clsx(
          "flex items-center gap-2 rounded-lg px-2 py-1.5 transition",
          dark ? "hover:bg-fg/10" : "hover:bg-fg/[0.06]",
        )}
        aria-expanded={open}
      >
        <span
          className={clsx(
            "flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold",
            dark ? "bg-acid-400 text-night-950" : "bg-night-700 text-fg",
          )}
        >
          {user.full_name.charAt(0).toUpperCase()}
        </span>
        <span className="hidden text-left sm:block">
          <span className={clsx("block text-xs font-semibold", dark ? "text-fg" : "text-fg")}>
            {user.full_name}
          </span>
          <span className={clsx("block text-[11px]", dark ? "text-fg/40" : "text-fg/50")}>
            @{user.username}
          </span>
        </span>
        <ChevronDown size={15} className={clsx("hidden sm:block", dark ? "text-fg/35" : "text-fg/40")} />
      </button>
      {open && (
        <div className="glass-overlay absolute right-0 top-12 w-64 overflow-hidden rounded-xl shadow-pop animate-fade-in">
          <div className="border-b border-fg/[0.07] px-4 py-3">
            <p className="text-sm font-semibold text-fg">{user.full_name}</p>
            <div className="mt-1 flex items-center gap-2">
              <Badge tone={user.is_admin ? "brand" : "neutral"}>
                {ROLE_LABELS[user.role]}
              </Badge>
              <span className="truncate text-[11px] text-fg/40">
                {user.is_admin ? "Бүх бүртгэл" : user.leader_person ? fullName(user.leader_person) : "Харьяалалгүй"}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              navigate("/profile");
            }}
            className="flex w-full items-center gap-2 px-4 py-2.5 text-sm text-fg/70 hover:bg-fg/[0.03]"
          >
            <UserCog size={16} /> Миний бүртгэл
          </button>
          <button
            type="button"
            onClick={() => void onLogout()}
            className="flex w-full items-center gap-2 border-t border-fg/[0.04] px-4 py-2.5 text-sm text-red-300 hover:bg-red-500/10"
          >
            <LogOut size={16} /> Гарах
          </button>
        </div>
      )}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  actions,
  eyebrow,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  eyebrow?: string;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow && (
          <p className="mb-1 text-xs font-medium uppercase tracking-wider text-acid-300">
            {eyebrow}
          </p>
        )}
        <h2 className="text-xl font-semibold tracking-tight text-fg sm:text-2xl">{title}</h2>
        {description && <p className="mt-1 max-w-2xl text-sm text-fg/50">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export { Button };
