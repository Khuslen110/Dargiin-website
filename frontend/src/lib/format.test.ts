import { describe, expect, it } from "vitest";
import { formatDateOnly, fullName, initials, maskPhone } from "./format";

describe("format helpers", () => {
  it("formats date-only strings without timezone shifts", () => {
    expect(formatDateOnly("1990-01-01")).toBe("1990.01.01");
    expect(formatDateOnly(null)).toBe("—");
  });

  it("builds full names and initials", () => {
    const person = { last_name: "Бат", first_name: "Сүх" };
    expect(fullName(person)).toBe("Бат Сүх");
    expect(initials(person)).toBe("БС");
  });

  it("keeps already masked phones", () => {
    expect(maskPhone("99112233")).toBe("••••••2233");
    expect(maskPhone("••••••2233")).toBe("••••••2233");
    expect(maskPhone(null)).toBe("—");
  });
});
