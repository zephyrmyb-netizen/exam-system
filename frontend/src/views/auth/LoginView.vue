<script setup lang="ts">
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Eye, EyeOff, Lock, User } from "@lucide/vue";

import { useAuth } from "../../stores/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

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
    router.push(redirect);
    return;
  }
  router.push({ name: "home" });
}
</script>

<template>
  <Card class="auth-form-section">
    <CardHeader class="p-0 pb-5">
      <CardTitle class="text-3xl">登录账号</CardTitle>
      <p class="auth-desc">使用你的账号登录，开始刷题复习。</p>
    </CardHeader>

    <CardContent class="p-0">
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
            class="text-input has-left-icon has-right-icon"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="请输入密码"
          />
          <button
            type="button"
            class="input-suffix"
            tabindex="-1"
            aria-label="切换密码显示"
            @click="showPassword = !showPassword"
          >
            <EyeOff v-if="showPassword" :size="17" />
            <Eye v-else :size="17" />
          </button>
        </div>

        <Button class="full-button" type="submit" :disabled="loading">
          {{ loading ? "登录中..." : "登录" }}
        </Button>
      </form>
    </CardContent>

    <CardFooter class="flex-col p-0 pt-5">
      <p class="auth-switch">
        还没有账号？
        <router-link :to="{ name: 'register' }">去注册</router-link>
      </p>
    </CardFooter>
  </Card>
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
  z-index: 1;
  color: var(--text-placeholder);
  pointer-events: none;
  transform: translateY(-50%);
}

.text-input.has-left-icon {
  padding-left: 42px;
}

.text-input.has-right-icon {
  padding-right: 46px;
}

.input-suffix {
  position: absolute;
  right: 10px;
  top: 50%;
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transform: translateY(-50%);
  transition: color var(--ease-out);
}

.input-suffix:hover {
  color: var(--text-secondary);
}
</style>
