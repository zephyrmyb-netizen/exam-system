<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuth } from "../../stores/auth";
import { Eye, EyeOff, User, Lock } from "@lucide/vue";

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
  if (ok) {
    const redirect = route.query.redirect;
    // 安全校验：仅接受相对路径，且不跳转到游客页面
    if (redirect && typeof redirect === "string" && redirect.startsWith("/") && !redirect.startsWith("/login") && !redirect.startsWith("/register")) {
      router.push(redirect);
    } else {
      router.push({ name: "home" });
    }
  }
}
</script>

<template>
  <section class="auth-form-section">
    <h2>登录账号</h2>
    <p class="auth-desc">使用你的账号登录，开始练习复习。</p>

    <p v-if="authMessage" class="success-message">{{ authMessage }}</p>
    <p v-if="authError" class="error-message">{{ authError }}</p>

    <form class="stack" @submit.prevent="handleLogin">
      <div class="input-with-icon">
        <User class="input-icon" :size="18" />
        <input
          id="login-username"
          v-model="form.username"
          class="text-input has-left-icon"
          type="text"
          autocomplete="username"
          placeholder="请输入用户名"
        />
      </div>

      <div class="input-with-icon">
        <Lock class="input-icon" :size="18" />
        <input
          id="login-password"
          v-model="form.password"
          class="text-input has-left-icon"
          :type="showPassword ? 'text' : 'password'"
          autocomplete="current-password"
          placeholder="请输入密码"
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

      <button class="primary-button full-button" type="submit" :disabled="loading">
        {{ loading ? "登录中..." : "登 录" }}
      </button>
    </form>

    <!-- 邀请码提示 -->
    <p class="invite-hint">
      💡 首次使用？请向管理员获取邀请码，然后<router-link :to="{ name: 'register' }">去注册</router-link>。
    </p>

    <p class="auth-switch">
      还没有账号？
      <router-link :to="{ name: 'register' }">去注册</router-link>
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

.invite-hint a {
  color: var(--primary);
  font-weight: 700;
  text-decoration: none;
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
