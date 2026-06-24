import axios from "axios";

const TOKEN_KEY = "exam_system_token";
const AUTH_EVENT = "exam-system-auth-change";
let memoryToken = "";

function getDefaultApiBaseUrl() {
  const { protocol, hostname } = window.location;
  if (hostname && hostname !== "localhost" && hostname !== "127.0.0.1") {
    return `${protocol}//${hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
}

function emitAuthChange(detail) {
  window.dispatchEvent(new CustomEvent(AUTH_EVENT, { detail }));
}

export function getToken() {
  try {
    return window.localStorage.getItem(TOKEN_KEY) || memoryToken || "";
  } catch {
    return memoryToken || "";
  }
}

export function setToken(token) {
  memoryToken = token || "";
  try {
    if (token) {
      window.localStorage.setItem(TOKEN_KEY, token);
    } else {
      window.localStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // Some embedded browsers can block localStorage. Keep the token in memory
    // for the current session so the app remains usable.
  }
  emitAuthChange({ token: token || "" });
}

export function clearToken() {
  memoryToken = "";
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // localStorage may be unavailable in restrictive webviews.
  }
  emitAuthChange({ token: "" });
}

export function getAuthEventName() {
  return AUTH_EVENT;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || getDefaultApiBaseUrl();

const request = axios.create({
  baseURL: API_BASE_URL,
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
  (error) => {
    if (error?.response?.status === 401) {
      clearToken();
      error.userMessage = "登录状态已失效，请重新登录。";
      return Promise.reject(error);
    }

    if (!error.response && error.code === "ERR_NETWORK") {
      error.userMessage = "网络连接失败，请检查后端服务或网络后重试。";
      return Promise.reject(error);
    }

    if (error.code === "ECONNABORTED") {
      error.userMessage = "请求超时，请稍后重试。";
      return Promise.reject(error);
    }

    return Promise.reject(error);
  }
);

export function getErrorMessage(error, fallback = "请求失败，请稍后重试") {
  if (error?.userMessage) return error.userMessage;
  if (error?.authMessage) return error.authMessage;

  const status = error?.response?.status;
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item?.msg) return item.msg;
        if (item?.message) return item.message;
        return JSON.stringify(item);
      })
      .join("；");
  }

  if (status) {
    const statusMessages = {
      400: "请求参数有误，请检查输入。",
      403: "没有权限执行此操作。",
      404: "请求的资源不存在。",
      409: "数据冲突，请刷新后重试。",
      422: "请求数据格式有误，请检查输入。",
      429: "请求过于频繁，请稍后重试。",
      500: "服务器内部错误，请稍后重试。",
      502: "AI 服务暂时不可用，请稍后重试。",
      503: "服务暂时不可用，请稍后重试。",
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
