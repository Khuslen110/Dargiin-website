import {
  forwardRef,
  useEffect,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import { clsx } from "clsx";
import { AlertCircle, ChevronLeft, ChevronRight, Loader2, X } from "lucide-react";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger" | "subtle";
type ButtonSize = "sm" | "md" | "lg";

const buttonVariants: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-acid-500 to-cyan-500 text-white shadow-[0_14px_34px_-18px_rgba(79,70,229,0.9)] hover:from-acid-400 hover:to-cyan-400 focus-visible:ring-acid-400/60 disabled:opacity-60",
  secondary:
    "border border-fg/[0.12] bg-fg/[0.045] text-fg/85 shadow-sm backdrop-blur-xl hover:border-fg/[0.22] hover:bg-fg/[0.08] focus-visible:ring-fg/50",
  ghost:
    "text-fg/60 hover:bg-fg/[0.07] hover:text-fg focus-visible:ring-fg/50",
  danger:
    "bg-red-600/90 text-white shadow-sm hover:bg-red-600 focus-visible:ring-red-400",
  subtle:
    "bg-fg/[0.07] text-fg/85 ring-1 ring-inset ring-fg/[0.08] hover:bg-fg/[0.12] focus-visible:ring-fg/50",
};

const buttonSizes: Record<ButtonSize, string> = {
  sm: "h-8 gap-1.5 px-3 text-xs",
  md: "h-10 gap-2 px-4 text-sm",
  lg: "h-11 gap-2 px-5 text-sm",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      loading,
      disabled,
      icon,
      children,
      ...props
    },
    ref,
  ) => (
    <button
      ref={ref}
      className={clsx(
        "inline-flex items-center justify-center rounded-lg font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-night-950 disabled:cursor-not-allowed disabled:opacity-60",
        buttonVariants[variant],
        buttonSizes[size],
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 size={16} className="animate-spin" /> : icon}
      {children}
    </button>
  ),
);
Button.displayName = "Button";

export const inputClass =
  "w-full rounded-lg border border-fg/[0.11] bg-fg/[0.045] px-3 py-2 text-sm text-fg shadow-sm outline-none backdrop-blur-xl transition placeholder:text-fg/35 hover:border-fg/[0.16] focus:border-acid-400/50 focus:bg-fg/[0.06] focus:ring-2 focus:ring-acid-400/15 disabled:bg-fg/[0.025] disabled:text-fg/45";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input ref={ref} className={clsx(inputClass, className)} {...props} />
  ),
);
Input.displayName = "Input";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, children, ...props }, ref) => (
    <select ref={ref} className={clsx(inputClass, "pr-8", className)} {...props}>
      {children}
    </select>
  ),
);
Select.displayName = "Select";

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => (
  <textarea ref={ref} className={clsx(inputClass, "min-h-24 resize-y", className)} {...props} />
));
Textarea.displayName = "Textarea";

interface FieldProps {
  label: string;
  htmlFor?: string;
  required?: boolean;
  hint?: string;
  error?: string;
  children: ReactNode;
  className?: string;
}

export function Field({
  label,
  htmlFor,
  required,
  hint,
  error,
  children,
  className,
}: FieldProps) {
  return (
    <div className={clsx("space-y-1.5", className)}>
      <label htmlFor={htmlFor} className="flex items-center gap-1 text-sm font-medium text-fg/80">
        {label}
        {required && <span className="text-red-500">*</span>}
      </label>
      {children}
      {hint && !error && <p className="text-xs text-fg/50">{hint}</p>}
      {error && (
        <p className="flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
          <AlertCircle size={13} />
          {error}
        </p>
      )}
    </div>
  );
}

export function Card({
  children,
  className,
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article";
}) {
  return (
    <Tag
      className={clsx(
        "glass-surface rounded-2xl",
        className,
      )}
    >
      {children}
    </Tag>
  );
}

type BadgeTone = "neutral" | "brand" | "success" | "warning" | "danger" | "info";

const badgeTones: Record<BadgeTone, string> = {
  neutral: "bg-fg/[0.055] text-fg/70 ring-fg/[0.1]",
  brand: "bg-violet-500/10 text-violet-600 ring-violet-500/20 dark:text-violet-300",
  success: "bg-emerald-500/10 text-emerald-600 ring-emerald-500/20 dark:text-emerald-300",
  warning: "bg-amber-500/10 text-amber-600 ring-amber-500/20 dark:text-amber-300",
  danger: "bg-red-500/10 text-red-600 ring-red-500/20 dark:text-red-300",
  info: "bg-sky-500/10 text-sky-600 ring-sky-500/20 dark:text-sky-300",
};

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        badgeTones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <div className={clsx("flex items-center justify-center py-16", className)}>
      <Loader2 className="h-6 w-6 animate-spin text-acid-400" />
      <span className="sr-only">Ачаалж байна</span>
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      {icon && (
        <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-fg/[0.03] text-fg/40">
          {icon}
        </div>
      )}
      <h3 className="text-sm font-semibold text-fg">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-fg/50">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-red-500/20 bg-red-500/10 px-6 py-10 text-center">
      <AlertCircle className="mb-2 h-6 w-6 text-red-500" />
      <p className="text-sm text-red-300">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-3" onClick={onRetry}>
          Дахин оролдох
        </Button>
      )}
    </div>
  );
}

export function Modal({
  open,
  onClose,
  title,
  description,
  children,
  footer,
  size = "md",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg" | "xl";
}) {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = "";
    };
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-night-950/70 backdrop-blur-[2px]"
        onClick={onClose}
        aria-hidden
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className={clsx(
          "glass-overlay relative w-full overflow-hidden rounded-2xl shadow-pop animate-fade-in",
          size === "sm" && "max-w-md",
          size === "md" && "max-w-xl",
          size === "lg" && "max-w-3xl",
          size === "xl" && "max-w-6xl",
        )}
      >
        <div className="flex items-start justify-between gap-4 border-b border-fg/[0.07] px-6 py-4">
          <div>
            <h2 className="text-base font-semibold text-fg">{title}</h2>
            {description && <p className="mt-0.5 text-sm text-fg/50">{description}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-fg/40 transition hover:bg-fg/[0.06] hover:text-fg/70"
            aria-label="Хаах"
          >
            <X size={18} />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto px-6 py-4">{children}</div>
        {footer && (
          <div className="flex flex-wrap items-center justify-end gap-2 border-t border-fg/[0.07] bg-fg/[0.025] px-6 py-3 backdrop-blur-xl">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

export function Pagination({
  page,
  totalPages,
  total,
  onChange,
}: {
  page: number;
  totalPages: number;
  total: number;
  onChange: (page: number) => void;
}) {
  if (totalPages <= 1) {
    return (
      <div className="flex items-center justify-between px-1 text-xs text-fg/50">
        <span>Нийт {total.toLocaleString("mn-MN")} бичлэг</span>
      </div>
    );
  }
  const pages: number[] = [];
  const start = Math.max(1, page - 1);
  const end = Math.min(totalPages, start + 2);
  for (let index = start; index <= end; index += 1) pages.push(index);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-1 text-sm">
      <span className="text-xs text-fg/50">
        Нийт {total.toLocaleString("mn-MN")} бичлэг · {page}/{totalPages} хуудас
      </span>
      <div className="flex items-center gap-1">
        <Button
          variant="secondary"
          size="sm"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          aria-label="Өмнөх хуудас"
        >
          <ChevronLeft size={15} />
        </Button>
        {start > 1 && (
          <>
            <Button variant="ghost" size="sm" onClick={() => onChange(1)}>
              1
            </Button>
            {start > 2 && <span className="px-1 text-fg/40">…</span>}
          </>
        )}
        {pages.map((item) => (
          <Button
            key={item}
            variant={item === page ? "primary" : "ghost"}
            size="sm"
            onClick={() => onChange(item)}
          >
            {item}
          </Button>
        ))}
        {end < totalPages && (
          <>
            {end < totalPages - 1 && <span className="px-1 text-fg/40">…</span>}
            <Button variant="ghost" size="sm" onClick={() => onChange(totalPages)}>
              {totalPages}
            </Button>
          </>
        )}
        <Button
          variant="secondary"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          aria-label="Дараагийн хуудас"
        >
          <ChevronRight size={15} />
        </Button>
      </div>
    </div>
  );
}
