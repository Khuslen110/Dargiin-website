import type { GroupType } from "../api/types";

export const GROUP_ORDER: GroupType[] = ["TUMT", "MYANGAT", "ZUUT", "ARAVT", "MEMBER"];

export const NEXT_GROUP_TYPE: Record<GroupType, GroupType | null> = {
  TUMT: "MYANGAT",
  MYANGAT: "ZUUT",
  ZUUT: "ARAVT",
  ARAVT: "MEMBER",
  MEMBER: null,
};

export const PARENT_GROUP_TYPE: Record<GroupType, GroupType | null> = {
  TUMT: null,
  MYANGAT: "TUMT",
  ZUUT: "MYANGAT",
  ARAVT: "ZUUT",
  MEMBER: "ARAVT",
};

export const GROUP_CHART_COLORS: Record<GroupType, string> = {
  TUMT: "#8b5cf6",
  MYANGAT: "#38bdf8",
  ZUUT: "#f59e0b",
  ARAVT: "#fb7185",
  MEMBER: "#94a3b8",
};

export const GROUP_STYLES: Record<
  GroupType,
  { badge: string; card: string; dot: string; rail: string; soft: string }
> = {
  TUMT: {
    badge: "bg-violet-500/10 text-violet-600 ring-violet-500/20 dark:text-violet-300",
    card: "border-violet-500/20 bg-gradient-to-br from-violet-500/[0.1] to-night-800",
    dot: "bg-violet-500",
    rail: "bg-violet-500/70",
    soft: "text-violet-600 dark:text-violet-300",
  },
  MYANGAT: {
    badge: "bg-sky-500/10 text-sky-600 ring-sky-500/20 dark:text-sky-300",
    card: "border-sky-500/20 bg-gradient-to-br from-sky-500/[0.09] to-night-800",
    dot: "bg-sky-500",
    rail: "bg-sky-500/70",
    soft: "text-sky-600 dark:text-sky-300",
  },
  ZUUT: {
    badge: "bg-amber-500/10 text-amber-600 ring-amber-500/20 dark:text-amber-300",
    card: "border-amber-500/20 bg-gradient-to-br from-amber-500/[0.09] to-night-800",
    dot: "bg-amber-500",
    rail: "bg-amber-500/70",
    soft: "text-amber-600 dark:text-amber-300",
  },
  ARAVT: {
    badge: "bg-rose-500/10 text-rose-600 ring-rose-500/20 dark:text-rose-300",
    card: "border-rose-500/20 bg-gradient-to-br from-rose-500/[0.09] to-night-800",
    dot: "bg-rose-500",
    rail: "bg-rose-500/70",
    soft: "text-rose-600 dark:text-rose-300",
  },
  MEMBER: {
    badge: "bg-fg/[0.05] text-fg/60 ring-fg/[0.1]",
    card: "border-fg/[0.08] bg-gradient-to-br from-fg/[0.035] to-night-800",
    dot: "bg-fg/35",
    rail: "bg-fg/25",
    soft: "text-fg/55",
  },
};
