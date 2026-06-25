import { computed, ref, type Ref, type ComputedRef } from "vue";
import request, { clearToken, getErrorMessage, getToken, setToken } from "../api/request";
import type { User, TokenResponse } from "../types";

const user = ref<User | null>(null);
const loading = ref<boolean>(false);
const authMessage = ref<string>("");
const authError = ref<string>("");

export interface AuthReturn {
  user: Ref<User | null>;
  loading: Ref<boolean>;
  authMessage: Ref<string>;
  authError: Ref<string>;
  isAuthenticated: ComputedRef<boolean>;
  fetchProfile: () => Promise<void>;
  login: (username: string, password: string) => Promise<boolean>;
  register: (username: string, password: string, inviteCode: string) => Promise<boolean>;
  logout: () => void;
  resetFeedback: () => void;
}

export function useAuth(): AuthReturn {
  const isAuthenticated = computed<boolean>(() => !!getToken());

  function normalizeToken(data: TokenResponse | Record<string, unknown> | undefined): string {
    if (!data) return "";
    return (data as Record<string, unknown>)?.access_token as string
      || (data as Record<string, unknown>)?.token as string
      || (data as Record<string, unknown>)?.accessToken as string
      || "";
  }

  function resetFeedback(): void {
    authMessage.value = "";
    authError.value = "";
  }

  async function fetchProfile(): Promise<void> {
    if (!getToken()) {
      user.value = null;
      return;
    }
    loading.value = true;
    resetFeedback();
    try {
      const { data } = await request.get<User>("/auth/me");
      user.value = data;
    } catch (error: unknown) {
      if ((error as { response?: { status?: number } })?.response?.status === 401) {
        user.value = null;
        clearToken();
      }
      authError.value = getErrorMessage(error, "获取用户信息失败");
    } finally {
      loading.value = false;
    }
  }

  async function login(username: string, password: string): Promise<boolean> {
    if (!username.trim() || !password) {
      authError.value = "请填写用户名和密码。";
      return false;
    }
    loading.value = true;
    resetFeedback();
    try {
      const { data } = await request.post<TokenResponse>("/auth/login", {
        username: username.trim(),
        password,
      });
      const token = normalizeToken(data);
      if (!token) throw new Error("登录成功，但未收到 token");
      setToken(token);
      await fetchProfile();
      authMessage.value = "登录成功。";
      return true;
    } catch (error: unknown) {
      authError.value = getErrorMessage(error, "登录失败");
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function register(username: string, password: string, inviteCode: string): Promise<boolean> {
    if (!username.trim() || !password || !inviteCode.trim()) {
      authError.value = "注册时请填写用户名、密码和邀请码。";
      return false;
    }
    loading.value = true;
    resetFeedback();
    try {
      await request.post("/auth/register", {
        username: username.trim(),
        password,
        invite_code: inviteCode.trim(),
      });
      authMessage.value = "注册成功，请使用新账号登录。";
      return true;
    } catch (error: unknown) {
      authError.value = getErrorMessage(error, "注册失败");
      return false;
    } finally {
      loading.value = false;
    }
  }

  function logout(): void {
    clearToken();
    user.value = null;
    resetFeedback();
    authMessage.value = "已退出登录。";
  }

  return {
    user,
    loading,
    authMessage,
    authError,
    isAuthenticated,
    fetchProfile,
    login,
    register,
    logout,
    resetFeedback,
  };
}
