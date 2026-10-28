const dateTimeFormatter = new Intl.DateTimeFormat("mn-MN", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  timeZone: "Asia/Ulaanbaatar",
});

const dateFormatter = new Intl.DateTimeFormat("mn-MN", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  timeZone: "Asia/Ulaanbaatar",
});

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  return dateTimeFormatter.format(new Date(value));
}

export function formatDateOnly(value: string | null | undefined): string {
  if (!value) return "—";
  const [year, month, day] = value.split("-");
  if (!year || !month || !day) return value;
  return `${year}.${month}.${day}`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return formatDateOnly(value);
  return dateFormatter.format(new Date(value));
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("mn-MN").format(value);
}

export function fullName(person: { last_name: string; first_name: string }): string {
  return `${person.last_name} ${person.first_name}`.trim();
}

export function initials(person: { last_name: string; first_name: string }): string {
  return `${person.last_name.charAt(0)}${person.first_name.charAt(0)}`.toUpperCase();
}

export function maskPhone(phone: string | null): string {
  if (!phone) return "—";
  if (phone.includes("•")) return phone;
  const digits = phone.replace(/^\+/, "");
  if (digits.length <= 4) return "••••";
  return `••••••${digits.slice(-4)}`;
}
