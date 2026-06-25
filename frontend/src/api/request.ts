import axios, { type AxiosError } from "axios";

const TOKEN_KEY = "exam_system_token";
const AUTH_EVENT = "exam-system-auth-change";
let memoryToken = "";

function getDefaultApiBaseUrl(): string {
  const { hostname } = window.location;
  if (hostname && hostname !== "localhost" && hostname !== "127.0.0.1") {
    // Production: use relative path (nginx proxies to backend on same origin)
    return "";
  }
  return "http://127.0.0.1:8000";
}

function emitAuthChange(detail: Record<string, string>): void {
  window.dispatchEvent(new CustomEvent(AUTH_EVENT, { detail }));
}

export function getToken(): string {
  try {
    return window.localStorage.getItem(TOKEN_KEY) || memoryToken || "";
  } catch {
    return memoryToken || "";
  }
}

export function setToken(token: string): void {
  memoryToken = token || "";
  try {
    if (token) {
      window.localStorage.setItem(TOKEN_KEY, token);
    } else {
      window.localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // localStorage unavailable in some mobile WebViews — memory token suffices
  }
  emitAuthChange({ token: token || "" });
}

export function clearToken(): void {
  memoryToken = "";
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // localStorage unavailable — memory token already cleared
  }
  emitAuthChange({ token: "" });
}

export function getAuthEventName(): string {
  return AUTH_EVENT;
}

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL || getDefaultApiBaseUrl();

const request = axios.create({
  baseURL: API_BASE_URL || undefined,
  timeout: 15000,
});

request.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

request.interceptors.response.use(
  (response) => response,
  (error: AxiosError & { userMessage?: string }) => {
    if (error?.response?.status === 401) {
      clearToken();
      error.userMessage = "登录状态已失效，请重新登录。";
      return Promise.reject(error);
    }

    if (!error.response && (error as any).code === "ERR_NETWORK") {
      error.userMessage = "网络连接失败，请检查后端服务或网络后重试。";
      return Promise.reject(error);
    }

    if ((error as any).code === "ECONNABORTED") {
      error.userMessage = "请求超时，请稍后重试。";
      return Promise.reject(error);
    }

    return Promise.reject(error);
  },
);

export function getErrorMessage(error: any, fallback = "请求失败，请稍后重试"): string {
  if (error?.userMessage) return error.userMessage;
  if (error?.authMessage) return error.authMessage;

  const status = error?.response?.status as number | undefined;
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item: any) => {
        if (typeof item === "string") return item;
        if (item?.msg) return item.msg;
        if (item?.message) return item.message;
        return JSON.stringify(item);
      })
      .join("；");
  }

  if (status) {
    const statusMessages: Record<number, string> = {
      400: "请求参数有误，请检查输入。",
      403: "没有权限执行此操作。",
      404: "请求的资源不存在。",
      409: "数据冲突，请刷新后重试。",
      422: "请求数据格式有误，请检查输入。",
      429: "请求过于频繁，请稍后重试。",
      500: "服务器内部错误，请稍后重试。",
      502: "AI 服务暂时不可用，请稍后重试。",
      503: "服务暂时不可用，请稍后重试。",
      504: "AI 调用超时，请稍后重试或拆分文档后再导入。",
    };
    if (statusMessages[status]) {
      return `${statusMessages[status]}（${status}）`;
    }
    return `请求失败（${status}），请稍后重试。`;
  }

  if (error?.message) {
    return `${fallback}：${error.message}`;
  }

  return fallback;
}

export default request;
