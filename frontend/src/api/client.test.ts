import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, buildQuery } from "./client";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("api client", () => {
  beforeEach(() => {
    document.cookie = "pr_csrf=token-123";
  });

  afterEach(() => {
    vi.restoreAllMocks();
    document.cookie = "pr_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  });

  it("adds CSRF header and JSON body to mutations", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await api.post("/people", { first_name: "Сүх" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/people");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("token-123");
    expect(init.body).toBe(JSON.stringify({ first_name: "Сүх" }));
  });

  it("does not send CSRF header on GET", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    vi.stubGlobal("fetch", fetchMock);

    await api.get("/people");

    const [, init] = fetchMock.mock.calls[0];
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBeNull();
  });

  it("throws ApiError with server fields", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(
          {
            detail: "Регистр давхцаж байна.",
            code: "DUPLICATE_REG_NUMBER",
            fields: { reg_number: "Давхцсан." },
          },
          409,
        ),
      ),
    );

    await expect(api.post("/people", {})).rejects.toMatchObject({
      status: 409,
      code: "DUPLICATE_REG_NUMBER",
      fields: { reg_number: "Давхцсан." },
    });
    await expect(api.post("/people", {})).rejects.toBeInstanceOf(ApiError);
  });

  it("omits empty query values", () => {
    expect(buildQuery({ page: 2, search: "", empty: null, status: undefined })).toBe("?page=2");
  });
});
