import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const mocks = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
  delete: vi.fn(),
  getToken: vi.fn(),
  setToken: vi.fn(),
  clearToken: vi.fn(),
}));

vi.mock("../../api/request", () => ({
  default: {
    post: mocks.post,
    get: mocks.get,
    delete: mocks.delete,
  },
  getToken: mocks.getToken,
  setToken: mocks.setToken,
  clearToken: mocks.clearToken,
  getErrorMessage: () => "请求失败",
}));

import { useAuthStore } from "../auth";

describe("guest authentication", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mocks.post.mockReset().mockResolvedValue({ data: { access_token: "guest-token", token: "guest-token" } });
    mocks.get.mockReset().mockResolvedValue({
      data: {
        id: 12,
        username: "guest_1234",
        display_name: "游客1234",
        is_guest: true,
        role: "student",
        permissions: [],
      },
    });
    mocks.setToken.mockReset();
    mocks.clearToken.mockReset();
    mocks.delete.mockReset().mockResolvedValue({ status: 204 });
    mocks.getToken.mockReset().mockReturnValue("");
  });

  it("starts an isolated guest session without a nickname", async () => {
    const store = useAuthStore();

    await expect(store.loginGuest()).resolves.toBe(true);

    expect(mocks.post).toHaveBeenCalledWith("/auth/guest", {});
    expect(mocks.setToken).toHaveBeenCalledWith("guest-token");
    expect(store.user?.display_name).toBe("游客1234");
  });

  it("retries once with an automatic nickname for an older beta backend", async () => {
    const store = useAuthStore();
    mocks.post
      .mockRejectedValueOnce({ response: { status: 422 } })
      .mockResolvedValueOnce({ data: { access_token: "guest-token", token: "guest-token" } });

    await expect(store.loginGuest()).resolves.toBe(true);

    expect(mocks.post).toHaveBeenNthCalledWith(1, "/auth/guest", {});
    expect(mocks.post).toHaveBeenNthCalledWith(2, "/auth/guest", {
      nickname: expect.stringMatching(/^游客\d{4}$/),
    });
  });

  it("does not show an expired-session error while silently checking a first visit", async () => {
    const store = useAuthStore();
    mocks.get.mockRejectedValueOnce({ response: { status: 401 } });

    await store.fetchProfile({ silent: true });

    expect(store.authError).toBe("");
  });

  it("does not restore a profile request that completed after logout", async () => {
    const store = useAuthStore();
    let resolveProfile!: (value: { data: Record<string, unknown> }) => void;
    mocks.get.mockImplementationOnce(
      () =>
        new Promise<{ data: Record<string, unknown> }>((resolve) => {
          resolveProfile = resolve;
        }),
    );

    const pendingProfile = store.fetchProfile();
    store.logout();
    resolveProfile({
      data: {
        id: 12,
        username: "guest_1234",
        display_name: "游客1234",
        is_guest: true,
        role: "student",
        permissions: [],
      },
    });
    await pendingProfile;

    expect(store.user).toBeNull();
  });

  it("does not restore a session from a stale cookie after logout", async () => {
    const store = useAuthStore();
    store.logout();
    mocks.get.mockResolvedValueOnce({
      data: {
        id: 12,
        username: "guest_1234",
        display_name: "游客1234",
        is_guest: true,
        role: "student",
        permissions: [],
      },
    });

    await store.fetchProfile({ silent: true });

    expect(store.user).toBeNull();
    expect(mocks.get).not.toHaveBeenCalled();
  });

  it("signs out locally before the guest-data deletion request finishes", async () => {
    const store = useAuthStore();
    let finishDeletion!: (value: { status: number }) => void;
    mocks.getToken.mockReturnValue("guest-token");
    mocks.delete.mockImplementationOnce(
      () =>
        new Promise<{ status: number }>((resolve) => {
          finishDeletion = resolve;
        }),
    );
    store.user = {
      id: 12,
      username: "guest_1234",
      display_name: "游客1234",
      is_guest: true,
      role: "student",
      permissions: [],
    };

    const deletion = store.clearGuestData();

    expect(store.user).toBeNull();
    expect(mocks.clearToken).toHaveBeenCalled();
    expect(mocks.delete).toHaveBeenCalledWith("/auth/guest/me", {
      headers: { Authorization: "Bearer guest-token" },
    });

    finishDeletion({ status: 204 });
    await expect(deletion).resolves.toBe(true);
  });
});

describe("credential login", () => {
  const profile = {
    data: {
      id: 7,
      username: "student",
      display_name: "学生",
      is_guest: false,
      role: "student",
      permissions: [],
    },
  };

  beforeEach(() => {
    setActivePinia(createPinia());
    mocks.post.mockReset();
    mocks.get.mockReset();
    mocks.setToken.mockReset();
    mocks.clearToken.mockReset();
    mocks.getToken.mockReset().mockReturnValue("");
  });

  it("logs in with trimmed credentials, stores the token and loads the profile", async () => {
    mocks.post.mockResolvedValue({ data: { access_token: "user-token" } });
    mocks.get.mockResolvedValue(profile);
    const store = useAuthStore();

    await expect(store.login("  student  ", "secret")).resolves.toBe(true);

    expect(mocks.post).toHaveBeenCalledWith("/auth/login", { username: "student", password: "secret" });
    expect(mocks.setToken).toHaveBeenCalledWith("user-token");
    expect(store.user?.username).toBe("student");
    expect(store.authMessage).toBe("登录成功。");
  });

  it("does not store anything and reports an error when the response has no token", async () => {
    mocks.post.mockResolvedValue({ data: { detail: "ok" } });
    const store = useAuthStore();

    await expect(store.login("student", "secret")).resolves.toBe(false);

    expect(mocks.setToken).not.toHaveBeenCalled();
    expect(mocks.get).not.toHaveBeenCalled();
    expect(store.authError).toBeTruthy();
  });

  it("rejects a wrong password without storing a token", async () => {
    mocks.post.mockRejectedValue({ response: { status: 401, data: { detail: "用户名或密码错误" } } });
    const store = useAuthStore();

    await expect(store.login("student", "wrong")).resolves.toBe(false);

    expect(mocks.setToken).not.toHaveBeenCalled();
    expect(store.authError).toBeTruthy();
    expect(store.user).toBeNull();
  });

  it("validates empty input before any request", async () => {
    const store = useAuthStore();

    await expect(store.login("   ", "")).resolves.toBe(false);

    expect(mocks.post).not.toHaveBeenCalled();
    expect(store.authError).toBe("请填写用户名和密码。");
  });

  it("does not report a logged-in user when the profile fails right after a token", async () => {
    mocks.post.mockResolvedValue({ data: { token: "user-token" } });
    mocks.get.mockRejectedValue({ response: { status: 401 } });
    const store = useAuthStore();

    await expect(store.login("student", "secret")).resolves.toBe(false);

    expect(mocks.setToken).toHaveBeenCalledWith("user-token");
    expect(store.user).toBeNull();
  });
});
