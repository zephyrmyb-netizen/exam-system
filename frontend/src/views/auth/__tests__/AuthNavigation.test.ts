import { flushPromises, mount } from "@vue/test-utils";
import { reactive } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LoginView from "../LoginView.vue";
import RegisterView from "../RegisterView.vue";

const mocks = vi.hoisted(() => ({
  replace: vi.fn(),
  login: vi.fn(),
  register: vi.fn(),
}));

const route = reactive({ query: {} as Record<string, string> });

vi.mock("vue-router", () => ({
  useRouter: () => ({ replace: mocks.replace }),
  useRoute: () => route,
}));

vi.mock("../../../stores/auth", () => ({
  useAuth: () => ({
    login: mocks.login,
    register: mocks.register,
    loading: false,
    authMessage: "",
    authError: "",
    resetFeedback: vi.fn(),
  }),
}));

describe("authentication navigation", () => {
  beforeEach(() => {
    mocks.replace.mockReset();
    mocks.login.mockReset().mockResolvedValue(true);
    mocks.register.mockReset().mockResolvedValue(true);
    route.query = {};
  });

  it("replaces to a safe redirect after login", async () => {
    route.query = { redirect: "/courses/7" };
    const wrapper = mount(LoginView, { global: { stubs: { RouterLink: true } } });

    await wrapper.get("#login-username").setValue("student");
    await wrapper.get("#login-password").setValue("password");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(mocks.replace).toHaveBeenCalledWith("/courses/7");
  });

  it("replaces to login after registration", async () => {
    const wrapper = mount(RegisterView, { global: { stubs: { RouterLink: true } } });

    expect(wrapper.findAll(".auth-tab")).toHaveLength(2);
    expect(wrapper.get("#register-invite").attributes("id")).toBe("register-invite");
    await wrapper.get("#register-username").setValue("student");
    await wrapper.get("#register-password").setValue("password");
    await wrapper.get("#register-invite").setValue("invite");
    await wrapper.get("form").trigger("submit");
    await flushPromises();

    expect(mocks.replace).toHaveBeenCalledWith({ name: "login" });
  });
});
