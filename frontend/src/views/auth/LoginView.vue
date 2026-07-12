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
    <div class="auth-tabs">
      <button class="auth-tab active" type="button">登录</button>
      <router-link class="auth-tab" replace to="/register">注册</router-link>
    </div>

    <p v-if="authMessage" class="success-message">{{ authMessage }}</p>
    <p v-if="authError" class="error-message">{{ authError }}</p>

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
  margin-bottom: var(--space-3);
}

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
  width: 36px;
  height: 36px;
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
</style>
