<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Eye, EyeOff } from "@lucide/vue";

import { useAuth } from "../../stores/auth";

const router = useRouter();
const route = useRoute();
const { login, loading, authMessage, authError, resetFeedback } = useAuth();

const form = ref({
  username: "",
  password: "",
});
const showPassword = ref(false);

async function handleLogin() {
  resetFeedback();
  const ok = await login(form.value.username, form.value.password);
  if (!ok) return;

  const redirect = route.query.redirect;
  if (
    redirect
    && typeof redirect === "string"
    && redirect.startsWith("/")
    && !redirect.startsWith("/login")
    && !redirect.startsWith("/register")
  ) {
    router.replace(redirect);
    return;
  }
  router.replace({ name: "home" });
}
</script>

<template>
  <div class="auth-card fade-up d1">
    <p class="auth-brand">学习宝 <span>学习与练习</span></p>
    <div class="auth-tabs">
      <button class="auth-tab active" type="button">登录</button>
      <router-link class="auth-tab" replace to="/register">注册</router-link>
    </div>

    <p v-if="authMessage" class="success-message">{{ authMessage }}</p>
    <p v-if="authError" class="error-message">{{ authError }}</p>

    <div class="auth-heading">
      <h1>登录</h1>
      <p>继续使用你的学习空间</p>
    </div>

    <form @submit.prevent="handleLogin">
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
        {{ loading ? "登录中..." : "登录" }}
      </button>
    </form>
  </div>
</template>

<style scoped>
a.auth-tab {
  text-decoration: none;
  text-align: center;
  cursor: pointer;
}

button.auth-tab {
  font-family: inherit;
  cursor: default;
}

.success-message,
.error-message {
  margin: 0 0 var(--space-3);
  padding: 10px 12px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.5;
}
.auth-card { max-width: 400px; padding: 24px; border-radius: 6px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }
.auth-brand { margin: 0 0 22px; color: var(--text-main); font-size: 15px; font-weight: 800; }
.auth-brand span { margin-left: 6px; color: var(--text-muted); font-size: 12px; font-weight: 600; }
.auth-tabs { margin-bottom: 22px; padding: 0; border-bottom: 1px solid var(--line-soft); border-radius: 0; background: transparent; }
.auth-tab { min-height: 44px; padding: 0 12px; border-radius: 0; }
.auth-tab.active { border-bottom: 2px solid var(--primary); box-shadow: none; }
.auth-heading { margin-bottom: 20px; }
.auth-heading h1 { margin: 0; color: var(--text-main); font-family: var(--font-sans); font-size: 22px; font-weight: 800; }
.auth-heading p { margin: 5px 0 0; color: var(--text-muted); font-size: 13px; }
.auth-field { gap: 7px; margin-bottom: 16px; }
.auth-field label { font-size: 13px; letter-spacing: 0; text-transform: none; }
.auth-field input { height: 48px; border-radius: 5px; }

.auth-field-control {
  position: relative;
}

.auth-field-control input {
  padding-right: 44px;
}

.auth-field-suffix {
  position: absolute;
  right: 6px;
  top: 50%;
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transform: translateY(-50%);
  transition: color var(--ease-out);
  -webkit-tap-highlight-color: transparent;
}

.auth-field-suffix:hover {
  color: var(--text-secondary);
}

/* iOS Safari: prevent zoom-on-focus (input font-size ≥ 16px) */
.auth-field input {
  font-size: 16px;
}
.auth-btn { height: 48px; margin-top: 8px; border-radius: 5px; background: var(--primary); box-shadow: none; }
.auth-btn:hover:not(:disabled) { transform: none; box-shadow: none; background: var(--primary-strong); }
</style>
