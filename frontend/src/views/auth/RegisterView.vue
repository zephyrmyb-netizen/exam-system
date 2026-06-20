<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuth } from "../../stores/auth";
import { Eye, EyeOff, User, Lock, KeyRound } from "@lucide/vue";

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
    router.push({ name: "login" });
  }
}
</script>

<template>
  <section class="auth-form-section">
    <h2>注册账号</h2>
    <p class="auth-desc">需要邀请码才能注册，注册后自动跳转登录。</p>

    <p v-if="authMessage" class="success-message">{{ authMessage }}</p>
    <p v-if="authError" class="error-message">{{ authError }}</p>

    <form class="stack" @submit.prevent="handleRegister">
      <div class="input-with-icon">
        <User class="input-icon" :size="18" />
        <input
          id="register-username"
          v-model="form.username"
          class="text-input has-left-icon"
          type="text"
          autocomplete="username"
          placeholder="设置用户名"
        />
      </div>

      <div class="input-with-icon">
        <Lock class="input-icon" :size="18" />
        <input
          id="register-password"
          v-model="form.password"
          class="text-input has-left-icon"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="new-password"
          placeholder="设置密码"
        />
        <button
          type="button"
          class="input-suffix"
          tabindex="-1"
          @click="showPassword = !showPassword"
        >
          <EyeOff v-if="showPassword" :size="17" />
          <Eye v-else :size="17" />
        </button>
      </div>

      <div class="input-with-icon">
        <KeyRound class="input-icon" :size="18" />
        <input
          id="register-invite"
          v-model="form.inviteCode"
          class="text-input has-left-icon"
          type="text"
          autocomplete="off"
          placeholder="邀请码"
        />
      </div>

      <!-- 邀请码提示 -->
      <p class="invite-hint">
        💡 开发邀请码：<code>dev-invite</code>（默认）
      </p>

      <button class="primary-button full-button" type="submit" :disabled="loading">
        {{ loading ? "注册中..." : "注册账号" }}
      </button>
    </form>

    <p class="auth-switch">
      已有账号？
      <router-link :to="{ name: 'login' }">去登录</router-link>
    </p>
  </section>
</template>

<style scoped>
.input-with-icon {
  position: relative;
  display: grid;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-placeholder);
  z-index: 1;
  pointer-events: none;
}

.text-input.has-left-icon {
  padding-left: 42px;
}

.input-suffix {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: color var(--ease-out);
}

.input-suffix:hover {
  color: var(--text-secondary);
}

.invite-hint {
  margin: var(--space-1) 0 0;
  text-align: center;
  font-size: var(--text-xs);
  color: var(--text-muted);
  line-height: 1.6;
}

.invite-hint code {
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  background: var(--amber-soft);
  color: var(--amber);
  font-size: 0.85em;
  font-weight: 700;
}
</style>
