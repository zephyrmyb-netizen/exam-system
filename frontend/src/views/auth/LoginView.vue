<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Eye, EyeOff } from "@lucide/vue";

import { useAuth } from "../../stores/auth";

const router = useRouter();
const route = useRoute();
const { login, loginGuest, loading, authMessage, authError, resetFeedback } = useAuth();

const form = ref({
  username: "",
  password: "",
});
const showPassword = ref(false);
const isBetaBuild = import.meta.env.VITE_APP_ENV === "beta";

async function handleLogin() {
  resetFeedback();
  const ok = await login(form.value.username, form.value.password);
  if (!ok) return;

  const redirect = route.query.redirect;
  if (
    redirect &&
    typeof redirect === "string" &&
    redirect.startsWith("/") &&
    !redirect.startsWith("/login") &&
    !redirect.startsWith("/register")
  ) {
    router.replace(redirect);
    return;
  }
  router.replace({ name: "home" });
}

async function handleGuestLogin() {
  resetFeedback();
  if (await loginGuest()) router.replace({ name: "home" });
}
</script>

<template>
  <div class="auth-card fade-up d1">
    <header class="auth-hero">
      <p class="auth-brand">学习宝</p>
      <h1>{{ isBetaBuild ? "欢迎使用学习宝" : "欢迎回来" }}</h1>
      <p>轻松整理和练习题目</p>
      <span v-if="isBetaBuild" class="beta-badge">Beta 测试版</span>
    </header>

    <p v-if="authMessage" class="success-message feedback-message" role="status">{{ authMessage }}</p>
    <p v-if="authError" class="error-message feedback-message" role="alert">{{ authError }}</p>

    <section v-if="isBetaBuild" class="quick-entry" aria-labelledby="quick-entry-title">
      <h2 id="quick-entry-title">先试试看</h2>
      <p id="quick-entry-note">无需注册，点击即可进入；测试数据会保存在当前设备。</p>
      <button class="guest-btn" type="button" :disabled="loading" @click="handleGuestLogin">
        {{ loading ? "正在进入…" : "立即试用" }}
      </button>
    </section>

    <div v-if="isBetaBuild" class="auth-divider"><span>已有账号</span></div>

    <form class="auth-form" @submit.prevent="handleLogin">
      <div class="auth-field">
        <label for="login-username">用户名</label>
        <input
          id="login-username"
          v-model="form.username"
          type="text"
          autocomplete="username"
          placeholder="请输入用户名"
        />
      </div>

      <div class="auth-field">
        <label for="login-password">密码</label>
        <div class="auth-field-control">
          <input
            id="login-password"
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="请输入密码"
          />
          <button
            type="button"
            class="auth-field-suffix"
            tabindex="-1"
            aria-label="切换密码显示"
            @click="showPassword = !showPassword"
          >
            <EyeOff v-if="showPassword" :size="17" />
            <Eye v-else :size="17" />
          </button>
        </div>
      </div>

      <button class="auth-btn" type="submit" :disabled="loading">
        {{ loading ? "正在登录…" : "登录" }}
      </button>
    </form>

    <p class="auth-link-row">没有账号？<router-link replace to="/register">使用邀请码注册</router-link></p>
  </div>
</template>

<style scoped>
.auth-card {
  box-sizing: border-box;
  width: min(100%, 420px);
  max-width: 420px;
  padding: 28px 24px;
  border-radius: 20px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
}

.auth-hero {
  margin-bottom: 24px;
  text-align: center;
}

.auth-brand {
  margin: 0 0 8px;
  color: var(--primary-strong);
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.auth-hero h1 {
  margin: 0;
  color: var(--text-main);
  font-size: 24px;
  font-weight: 800;
}

.auth-hero > p:not(.auth-brand) {
  margin: 8px 0 0;
  color: var(--text-muted);
  font-size: 14px;
}

.beta-badge {
  display: inline-flex;
  margin-top: 12px;
  padding: 4px 9px;
  border-radius: 999px;
  background: var(--primary-soft);
  color: var(--primary-strong);
  font-size: 12px;
  font-weight: 800;
}

.feedback-message {
  margin: 0 0 16px;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
}

.quick-entry {
  display: grid;
  gap: 10px;
  padding: 18px;
  border: 1px solid var(--line-accent);
  border-radius: 16px;
  background: var(--primary-soft);
}

.quick-entry h2 {
  margin: 0;
  color: var(--text-main);
  font-size: 16px;
}

.quick-entry p {
  margin: 0;
  color: var(--text-muted);
  font-size: 13px;
  line-height: 1.55;
}

.guest-btn,
.auth-btn {
  box-sizing: border-box;
  width: 100%;
  min-height: 48px;
  border-radius: 12px;
  font: inherit;
  font-weight: 800;
  transition:
    background-color var(--ease-feedback),
    transform var(--ease-press),
    opacity var(--ease-feedback);
}

.guest-btn {
  border: none;
  background: var(--primary);
  color: #ffffff;
}

.guest-btn:hover:not(:disabled),
.guest-btn:active:not(:disabled) {
  background: var(--primary-strong);
}

.auth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 24px 0 18px;
  color: var(--text-muted);
  font-size: 13px;
}

.auth-divider::before,
.auth-divider::after {
  height: 1px;
  flex: 1;
  background: var(--line-soft);
  content: "";
}

.auth-form {
  min-width: 0;
}

.auth-field {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 7px;
  margin-bottom: 16px;
}

.auth-field label {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 700;
}

.auth-field-control {
  position: relative;
  min-width: 0;
}

.auth-field input {
  box-sizing: border-box;
  display: block;
  width: 100%;
  max-width: 100%;
  height: 48px;
  min-width: 0;
  padding: 0 13px;
  border-radius: 12px;
  font-size: 16px;
}

.auth-field-control input {
  padding-right: 52px;
}

.auth-field-suffix {
  position: absolute;
  top: 50%;
  right: 4px;
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transform: translateY(-50%);
}

.auth-field-suffix:hover,
.auth-field-suffix:active {
  color: var(--text-secondary);
}

.auth-btn {
  margin-top: 4px;
  border: none;
  background: var(--primary);
  color: #ffffff;
}

.auth-btn:hover:not(:disabled),
.auth-btn:active:not(:disabled) {
  background: var(--primary-strong);
}

.guest-btn:disabled,
.auth-btn:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.auth-link-row {
  margin: 20px 0 0;
  color: var(--text-muted);
  font-size: 14px;
  text-align: center;
}

.auth-link-row a {
  margin-left: 4px;
  color: var(--primary-strong);
  font-weight: 800;
  text-decoration: none;
}

@media (max-width: 360px) {
  .auth-card {
    padding: 24px 18px;
  }
}
</style>
