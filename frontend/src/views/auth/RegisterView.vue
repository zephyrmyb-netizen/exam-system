<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { Eye, EyeOff, KeyRound, Lock, User } from "@lucide/vue";

import { useAuth } from "../../stores/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";

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
  <Card class="auth-form-section">
    <CardHeader class="p-0 pb-5">
      <CardTitle class="text-3xl">注册账号</CardTitle>
      <p class="auth-desc">输入邀请码后即可注册，注册成功后返回登录。</p>
    </CardHeader>

    <CardContent class="p-0">
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
            class="text-input has-left-icon has-right-icon"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="new-password"
            placeholder="设置密码"
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

        <p class="invite-hint">邀请码由管理员配置在 backend/.env 的 INVITE_CODE。</p>

        <Button class="full-button" type="submit" :disabled="loading">
          {{ loading ? "注册中..." : "注册账号" }}
        </Button>
      </form>
    </CardContent>

    <CardFooter class="justify-center p-0 pt-5">
      <p class="auth-switch">
        已有账号？
        <router-link :to="{ name: 'login' }">去登录</router-link>
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

.invite-hint {
  margin: var(--space-1) 0 0;
  color: var(--text-muted);
  font-size: var(--text-xs);
  line-height: 1.6;
  text-align: center;
}
</style>
