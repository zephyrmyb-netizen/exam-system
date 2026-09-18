import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const requestGet = vi.hoisted(() => vi.fn());

vi.mock("./api/request", () => ({
  default: { get: requestGet },
  getToken: () => "",
  clearToken: vi.fn(),
  setToken: vi.fn(),
  getErrorMessage: vi.fn(),
}));

import router from "./router";

describe("anonymous route guards", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    requestGet.mockReset();
  });

  it("checks the HttpOnly Cookie session before redirecting an anonymous visitor", async () => {
    requestGet.mockRejectedValue({ response: { status: 401 } });
    await router.push("/");
    await router.isReady();

    expect(router.currentRoute.value.name).toBe("login");
    expect(requestGet).toHaveBeenCalledWith("/auth/me");
  });

  it("restores a protected route when only the HttpOnly Cookie session remains", async () => {
    requestGet.mockResolvedValue({
      data: { id: 7, username: "cookie-user", display_name: "", is_guest: false, role: "student", permissions: [] },
    });

    await router.push("/courses");

    expect(router.currentRoute.value.name).toBe("courses");
    expect(requestGet).toHaveBeenCalledWith("/auth/me");
  });

  it("shows the login route without requesting the profile when no token exists", async () => {
    await router.push("/login");

    expect(router.currentRoute.value.name).toBe("login");
    expect(requestGet).not.toHaveBeenCalled();
  });
});
