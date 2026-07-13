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
    <p class="auth-brand">学习宝 <span>学习与练习</span></p>
    <div class="auth-tabs">
      <router-link class="auth-tab" replace to="/login">登录</router-link>
      <button class="auth-tab active" type="button">注册</button>
    </div>

    <p v-if="authMessage" class="success-message">{{ authMessage }}</p>
    <p v-if="authError" class="error-message">{{ authError }}</p>

    <div class="auth-heading">
      <h1>注册</h1>
      <p>创建账号，开始整理你的学习内容</p>
    </div>

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

.invite-hint {
  margin: var(--space-1) 0 0;
  color: var(--text-muted);
  font-size: var(--text-xs);
  line-height: 1.6;
  text-align: left;
}

/* iOS Safari: prevent zoom-on-focus (input font-size ≥ 16px) */
.auth-field input {
  font-size: 16px;
}
.auth-btn { height: 48px; margin-top: 8px; border-radius: 5px; background: var(--primary); box-shadow: none; }
.auth-btn:hover:not(:disabled) { transform: none; box-shadow: none; background: var(--primary-strong); }
</style>
