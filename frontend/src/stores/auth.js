import { computed, ref } from "vue";
import request, { clearToken, getErrorMessage, getToken, setToken } from "../api/request";

const user = ref(null);
const loading = ref(false);
const authMessage = ref("");
const authError = ref("");

export function useAuth() {
  const isAuthenticated = computed(() => !!getToken());

  function normalizeToken(data) {
    return data?.access_token || data?.token || data?.accessToken || "";
  }

  function resetFeedback() {
    authMessage.value = "";
    authError.value = "";
  }

  async function fetchProfile() {
    if (!getToken()) {
      user.value = null;
      return;
    }
    loading.value = true;
    resetFeedback();
    try {
      const { data } = await request.get("/auth/me");
      user.value = data;
    } catch (error) {
      if (error?.response?.status === 401) {
        user.value = null;
        clearToken();
      }
      authError.value = getErrorMessage(error, "获取用户信息失败");
    } finally {
      loading.value = false;
    }
  }

  async function login(username, password) {
    if (!username.trim() || !password) {
      authError.value = "请填写用户名和密码。";
      return false;
    }
    loading.value = true;
    resetFeedback();
    try {
      const { data } = await request.post("/auth/login", {
        username: username.trim(),
        password,
      });
      const token = normalizeToken(data);
      if (!token) throw new Error("登录成功，但未收到 token");
      setToken(token);
      await fetchProfile();
      authMessage.value = "登录成功。";
      return true;
    } catch (error) {
      authError.value = getErrorMessage(error, "登录失败");
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function register(username, password, inviteCode) {
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
    } catch (error) {
      authError.value = getErrorMessage(error, "注册失败");
      return false;
    } finally {
      loading.value = false;
    }
  }

  function logout() {
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
