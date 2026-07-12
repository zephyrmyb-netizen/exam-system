<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { Eye, EyeOff } from "@lucide/vue";

import { useAuth } from "../../stores/auth";

const router = useRouter();
const { register, loading, authMessage, authError, resetFeedback } = useAuth();

const form = ref({
  username: "",
  password: "",
  inviteCode: "",
});
const showPassword = ref(false);

async function handleRegister() {
  resetFeedback();
  const ok = await register(form.value.username, form.value.password, form.value.inviteCode);
  if (ok) {
    router.replace({ name: "login" });
  }
}
</script>

<template>
  <div class="auth-card fade-up d1">
    <div class="auth-tabs">
      <router-link class="auth-tab" replace to="/login">登录</router-link>
      <button class="auth-tab active" type="button">注册</button>
    </div>

    <p v-if="authMessage" class="success-message">{{ authMessage }}</p>
    <p v-if="authError" class="error-message">{{ authError }}</p>

    <form @submit.prevent="handleRegister">
      <div class="auth-field">
        <label for="register-username">用户名</label>
        <input
          id="register-username"
          v-model="form.username"
          type="text"
          autocomplete="username"
          placeholder="设置用户名"
        />
      </div>

      <div class="auth-field">
        <label for="register-password">密码</label>
        <div class="auth-field-control">
          <input
            id="register-password"
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            placeholder="设置密码"
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

      <div class="auth-field">
        <label for="register-invite">邀请码</label>
        <input
          id="register-invite"
          v-model="form.inviteCode"
          type="text"
          autocomplete="off"
          placeholder="输入邀请码"
        />
      </div>

      <p class="invite-hint">邀请码由管理员配置在 backend/.env 的 INVITE_CODE。</p>

      <button class="auth-btn" type="submit" :disabled="loading">
        {{ loading ? "注册中..." : "注册账号" }}
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

.invite-hint {
  margin: var(--space-1) 0 0;
  color: var(--text-muted);
  font-size: var(--text-xs);
  line-height: 1.6;
  text-align: center;
}

/* iOS Safari: prevent zoom-on-focus (input font-size ≥ 16px) */
.auth-field input {
  font-size: 16px;
}
</style>
