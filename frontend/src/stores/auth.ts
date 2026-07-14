import { type ComputedRef, type Ref } from "vue";
import { defineStore, storeToRefs } from "pinia";
import request, { clearToken, getErrorMessage, getToken, setToken } from "../api/request";
import type { TokenResponse, User } from "../types";

export interface AuthReturn {
  user: Ref<User | null>;
  loading: Ref<boolean>;
  authMessage: Ref<string>;
  authError: Ref<string>;
  isAuthenticated: ComputedRef<boolean>;
  can: (permission: string) => boolean;
  fetchProfile: () => Promise<void>;
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, password: string, inviteCode: string) => Promise<boolean>;
  logout: () => void;
  resetFeedback: () => void;
}

const ROLE_PERMISSIONS: Record<string, Set<string>> = {
  student: new Set([
    "course:read",
    "course:create",
    "exam:take",
    "exam:view_result",
    "exam:view_leaderboard",
    "practice:random",
    "practice:submit",
    "wrongbook:read",
    "chat:use",
    "import:use",
  ]),
  teacher: new Set([
    "course:read",
    "course:create",
    "course:edit",
    "course:publish",
    "exam:create",
    "exam:publish",
    "exam:take",
    "exam:view_result",
    "exam:view_leaderboard",
    "practice:random",
    "practice:submit",
    "wrongbook:read",
    "chat:use",
    "import:use",
  ]),
  admin: new Set(["*"]),
};

function normalizeToken(data: TokenResponse | Record<string, unknown> | undefined): string {
  if (!data) return "";
  return (data as Record<string, unknown>)?.access_token as string
    || (data as Record<string, unknown>)?.token as string
    || (data as Record<string, unknown>)?.accessToken as string
    || "";
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as User | null,
    loading: false,
    authMessage: "",
    authError: "",
  }),
  getters: {
    isAuthenticated: () => !!getToken(),
    role: (state) => state.user?.role || "student",
    permissions: (state) => state.user?.permissions || [],
    can: (state) => {
      return (permission: string): boolean => {
        const explicit = state.user?.permissions || [];
        if (explicit.includes(permission) || explicit.includes("*")) return true;
        const role = state.user?.role || "student";
        const rolePerms = ROLE_PERMISSIONS[role] || ROLE_PERMISSIONS.student;
        return rolePerms.has("*") || rolePerms.has(permission);
      };
    },
  },
  actions: {
    resetFeedback(): void {
      this.authMessage = "";
      this.authError = "";
    },

    async fetchProfile(): Promise<void> {
      if (!getToken()) {
        this.user = null;
        return;
      }
      this.loading = true;
      this.resetFeedback();
      try {
        const { data } = await request.get<User>("/auth/me");
        this.user = data;
      } catch (error: unknown) {
        if ((error as { response?: { status?: number } })?.response?.status === 401) {
          this.user = null;
          clearToken();
        }
        this.authError = getErrorMessage(error, "获取用户信息失败");
      } finally {
        this.loading = false;
      }
    },

    async login(username: string, password: string): Promise<boolean> {
      if (!username.trim() || !password) {
        this.authError = "请填写用户名和密码。";
        return false;
      }
      this.loading = true;
      this.resetFeedback();
      try {
        const { data } = await request.post<TokenResponse>("/auth/login", {
          username: username.trim(),
          password,
        });
        const token = normalizeToken(data);
        if (!token) throw new Error("登录成功，但没有收到 token");
        setToken(token);
        await this.fetchProfile();
        this.authMessage = "登录成功。";
        return true;
      } catch (error: unknown) {
        this.authError = getErrorMessage(error, "登录失败");
        return false;
      } finally {
        this.loading = false;
      }
    },

    async register(username: string, password: string, inviteCode: string): Promise<boolean> {
      if (!username.trim() || !password || !inviteCode.trim()) {
        this.authError = "注册时请填写用户名、密码和邀请码。";
        return false;
      }
      this.loading = true;
      this.resetFeedback();
      try {
        await request.post("/auth/register", {
          username: username.trim(),
          password,
          invite_code: inviteCode.trim(),
        });
        this.authMessage = "注册成功，请使用新账号登录。";
        return true;
      } catch (error: unknown) {
        this.authError = getErrorMessage(error, "注册失败");
        return false;
      } finally {
        this.loading = false;
      }
    },

    logout(): void {
      clearToken();
      this.user = null;
      this.resetFeedback();
      this.authMessage = "已退出登录。";
    },
  },
});

export function useAuth(): AuthReturn {
  const store = useAuthStore();
  const refs = storeToRefs(store);
  return {
    user: refs.user,
    loading: refs.loading,
    authMessage: refs.authMessage,
    authError: refs.authError,
    isAuthenticated: refs.isAuthenticated as ComputedRef<boolean>,
    can: store.can,
    fetchProfile: store.fetchProfile,
    login: store.login,
    register: store.register,
    logout: store.logout,
    resetFeedback: store.resetFeedback,
  };
}
