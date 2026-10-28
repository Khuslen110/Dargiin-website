import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Pagination } from "./index";

describe("Pagination", () => {
  it("renders total and navigates pages", async () => {
    const onChange = vi.fn();
    render(<Pagination page={2} totalPages={4} total={80} onChange={onChange} />);

    expect(screen.getByText(/Нийт 80 бичлэг/)).toBeInTheDocument();
    await userEvent.click(screen.getByLabelText("Дараагийн хуудас"));
    expect(onChange).toHaveBeenCalledWith(3);
    await userEvent.click(screen.getByLabelText("Өмнөх хуудас"));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("hides navigation for a single page", () => {
    render(<Pagination page={1} totalPages={1} total={5} onChange={() => undefined} />);
    expect(screen.queryByLabelText("Дараагийн хуудас")).not.toBeInTheDocument();
  });
});
