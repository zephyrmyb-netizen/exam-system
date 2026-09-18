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
