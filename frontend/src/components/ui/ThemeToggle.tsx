import { Moon, Sun } from "lucide-react";
import { clsx } from "clsx";
import { useTheme } from "../../theme/ThemeProvider";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? "Цайвар горимд шилжих" : "Харанхуй горимд шилжих"}
      title={isDark ? "Цайвар горим" : "Харанхуй горим"}
      className={clsx(
        "inline-flex h-9 w-9 items-center justify-center rounded-full border border-fg/[0.1] bg-fg/[0.04] text-fg/60 backdrop-blur-xl transition hover:border-fg/20 hover:bg-fg/[0.08] hover:text-fg",
        className,
      )}
    >
      {isDark ? <Sun size={17} /> : <Moon size={17} />}
    </button>
  );
}
