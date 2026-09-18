<script setup lang="ts">
import { onMounted, ref } from "vue";
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

onMounted(() => resetFeedback());

async function handleRegister() {
  resetFeedback();
  const ok = await register(form.value.username, form.value.password, form.value.inviteCode);
  if (ok) router.replace({ name: "login" });
}
</script>

<template>
  <div class="auth-card fade-up d1">
    <header class="auth-hero">
      <p class="auth-brand">学习宝</p>
      <h1>创建测试账号</h1>
      <p>使用邀请码注册，之后可在多台设备继续学习。</p>
    </header>

    <p v-if="authMessage" class="success-message feedback-message" role="status">{{ authMessage }}</p>
    <p v-if="authError" class="error-message feedback-message" role="alert">{{ authError }}</p>

    <form class="auth-form" @submit.prevent="handleRegister">
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
        <input id="register-invite" v-model="form.inviteCode" type="text" autocomplete="off" placeholder="输入邀请码" />
        <p class="invite-hint">邀请码请向测试管理员获取。</p>
      </div>

      <button class="auth-btn" type="submit" :disabled="loading">
        {{ loading ? "正在注册…" : "注册账号" }}
      </button>
    </form>

    <p class="auth-link-row">已有账号？<router-link replace to="/login">返回登录</router-link></p>
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
  line-height: 1.55;
}

.feedback-message {
  margin: 0 0 16px;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
}

.auth-form,
.auth-field,
.auth-field-control {
  min-width: 0;
}

.auth-field {
  display: flex;
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

.invite-hint {
  margin: 0;
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.55;
}

.auth-btn {
  box-sizing: border-box;
  width: 100%;
  min-height: 48px;
  margin-top: 4px;
  border: none;
  border-radius: 12px;
  background: var(--primary);
  color: #ffffff;
  font: inherit;
  font-weight: 800;
  transition:
    background-color var(--ease-feedback),
    opacity var(--ease-feedback);
}

.auth-btn:hover:not(:disabled),
.auth-btn:active:not(:disabled) {
  background: var(--primary-strong);
}

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
