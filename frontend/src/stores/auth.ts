import { type ComputedRef, type Ref } from "vue";
import { defineStore, storeToRefs } from "pinia";
import request, { clearToken, getErrorMessage, getToken, setToken } from "../api/request";
import { resetMyCoursesCache } from "../composables/useMyCourses";
import { resetStudyOverviewCache } from "../composables/useStudyOverview";
import type { TokenResponse, User } from "../types";

export interface AuthReturn {
  user: Ref<User | null>;
  loading: Ref<boolean>;
  authMessage: Ref<string>;
  authError: Ref<string>;
  isAuthenticated: ComputedRef<boolean>;
  can: (permission: string) => boolean;
  fetchProfile: (options?: { silent?: boolean }) => Promise<void>;
  login: (username: string, password: string) => Promise<boolean>;
  loginGuest: () => Promise<boolean>;
  register: (username: string, password: string, inviteCode: string) => Promise<boolean>;
  clearGuestData: () => Promise<boolean>;
  logout: () => void;
  resetFeedback: () => void;
}

const ROLE_PERMISSIONS: Record<string, Set<string>> = {
  student: new Set([
    "course:read",
    "course:create",
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
  return (
    ((data as Record<string, unknown>)?.access_token as string) ||
    ((data as Record<string, unknown>)?.token as string) ||
    ((data as Record<string, unknown>)?.accessToken as string) ||
    ""
  );
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as User | null,
    loading: false,
    authMessage: "",
    authError: "",
    authRevision: 0,
    explicitlyLoggedOut: false,
    // 标记本次会话是否已尝试加载 user profile。
    // router guard 用它避免每次路由切换都调 /auth/me，同时确保首次进入时
    // 即使有旧 token 也会先验证一次：token 可能已过期，不能仅凭 token 放行。
    profileInitialized: false,
  }),
  getters: {
    // 仅当 user 已加载且非空时才算已认证。token 单独存在不能代表会话有效，
    // 因为 token 可能已过期（cookie/localStorage 残留）。
    isAuthenticated: (state) => !!state.user,
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

    async fetchProfile(options: { silent?: boolean } = {}): Promise<void> {
      if (this.explicitlyLoggedOut && !getToken()) {
        this.user = null;
        this.loading = false;
        this.profileInitialized = true;
        return;
      }
      const requestRevision = this.authRevision;
      this.loading = true;
      if (!options.silent) this.resetFeedback();
      try {
        const { data } = await request.get<User>("/auth/me");
        if (requestRevision !== this.authRevision) return;
        if (this.user?.id !== data.id) {
          resetMyCoursesCache();
          resetStudyOverviewCache();
        }
        this.user = data;
      } catch (error: unknown) {
        if (requestRevision !== this.authRevision) return;
        const status = (error as { response?: { status?: number } })?.response?.status;
        const hadActiveSession = Boolean(this.user || getToken());
        if (status === 401) {
          this.user = null;
          resetMyCoursesCache();
          resetStudyOverviewCache();
          clearToken();
        }
        if (!options.silent && (status !== 401 || hadActiveSession)) {
          this.authError = getErrorMessage(error, "获取用户信息失败");
        }
      } finally {
        if (requestRevision === this.authRevision) {
          this.loading = false;
          this.profileInitialized = true;
        }
      }
    },

    async login(username: string, password: string): Promise<boolean> {
      if (!username.trim() || !password) {
        this.authError = "请填写用户名和密码。";
        return false;
      }
      this.loading = true;
      this.authRevision += 1;
      this.explicitlyLoggedOut = false;
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
        if (!this.user) return false;
        this.authMessage = "登录成功。";
        return true;
      } catch (error: unknown) {
        this.authError = getErrorMessage(error, "登录失败");
        return false;
      } finally {
        this.loading = false;
      }
    },

    async loginGuest(): Promise<boolean> {
      this.loading = true;
      this.authRevision += 1;
      this.explicitlyLoggedOut = false;
      this.resetFeedback();
      try {
        let data: TokenResponse;
        try {
          ({ data } = await request.post<TokenResponse>("/auth/guest", {}));
        } catch (error: unknown) {
          const status = (error as { response?: { status?: number } })?.response?.status;
          if (status !== 400 && status !== 422) throw error;
          const nickname = `游客${Math.floor(1000 + Math.random() * 9000)}`;
          ({ data } = await request.post<TokenResponse>("/auth/guest", { nickname }));
        }
        const token = normalizeToken(data);
        if (!token) throw new Error("Guest login did not return a token");
        setToken(token);
        await this.fetchProfile();
        return !!this.user;
      } catch (error: unknown) {
        this.authError = getErrorMessage(error, "暂时无法开始游客试用");
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
      this.authRevision += 1;
      this.explicitlyLoggedOut = true;
      this.profileInitialized = true;
      void request.post("/auth/logout").catch(() => undefined);
      this.user = null;
      clearToken();
      resetMyCoursesCache();
      resetStudyOverviewCache();
      this.resetFeedback();
      this.authMessage = "已退出登录。";
    },

    async clearGuestData(): Promise<boolean> {
      const token = getToken();
      const deletionRequest = request.delete(
        "/auth/guest/me",
        token ? { headers: { Authorization: `Bearer ${token}` } } : undefined,
      );
      this.authRevision += 1;
      this.explicitlyLoggedOut = true;
      this.profileInitialized = true;
      this.user = null;
      clearToken();
      resetMyCoursesCache();
      resetStudyOverviewCache();
      this.resetFeedback();
      this.authMessage = "已退出登录。";
      try {
        await deletionRequest;
        return true;
      } catch (error: unknown) {
        this.authError = getErrorMessage(error, "Unable to clear guest data");
        return false;
      }
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
    loginGuest: store.loginGuest,
    register: store.register,
    clearGuestData: store.clearGuestData,
    logout: store.logout,
    resetFeedback: store.resetFeedback,
  };
}
