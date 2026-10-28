import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import LoginPage from "./LoginPage";
import { AuthProvider } from "../auth/AuthProvider";
import { ToastProvider } from "../components/ui/Toast";
import { ThemeProvider } from "../theme/ThemeProvider";
import type { CurrentUser } from "../api/types";

const user: CurrentUser = {
  id: 1,
  username: "admin",
  full_name: "Систем Админ",
  role: "ADMIN",
  is_admin: true,
  permissions: {
    can_edit: true,
    can_import: true,
    can_export: true,
    can_view_sensitive: true,
    can_delete: true,
    can_manage_users: true,
    can_add_child: true,
  },
  leader_person: null,
  leader_group_type: null,
  next_group_type: null,
};

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/" element={<div>Хяналтын самбар</div>} />
            </Routes>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </MemoryRouter>,
  );
}

describe("LoginPage", () => {
  afterEach(() => vi.restoreAllMocks());

  it("logs in and redirects to the dashboard", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/me")) {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "Нэвтрээгүй." }), { status: 401 }),
        );
      }
      return Promise.resolve(
        new Response(JSON.stringify({ user, csrf_token: "csrf" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    renderLogin();
    await userEvent.type(screen.getByLabelText(/Хэрэглэгчийн нэр/), "admin");
    await userEvent.type(screen.getByPlaceholderText("Нууц үгээ оруулна уу"), "AdminDemo2026");
    await userEvent.click(screen.getByRole("button", { name: "Нэвтрэх" }));

    await waitFor(() => expect(screen.getByText("Хяналтын самбар")).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("shows the server error message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/auth/me")) {
          return Promise.resolve(new Response("{}", { status: 401 }));
        }
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "Нэр эсвэл нууц үг буруу." }), {
            status: 401,
            headers: { "Content-Type": "application/json" },
          }),
        );
      }),
    );

    renderLogin();
    await userEvent.type(screen.getByLabelText(/Хэрэглэгчийн нэр/), "admin");
    await userEvent.type(screen.getByPlaceholderText("Нууц үгээ оруулна уу"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: "Нэвтрэх" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Нэр эсвэл нууц үг буруу.");
  });
});
