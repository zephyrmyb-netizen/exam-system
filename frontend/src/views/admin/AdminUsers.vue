<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RefreshCw } from "@lucide/vue";

import { listAdminUsers, updateAdminUserRole, type AdminUser } from "@/api/admin";
import { getErrorMessage } from "@/api/request";

const users = ref<AdminUser[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

async function fetchUsers() {
  loading.value = true;
  errorMessage.value = "";
  try {
    const data = await listAdminUsers();
    users.value = data.items || [];
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "用户列表加载失败");
  } finally {
    loading.value = false;
  }
}

async function changeRole(user: AdminUser, role: string) {
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const updated = await updateAdminUserRole(user.id, role);
    user.role = updated.role;
    successMessage.value = `已将 ${user.username} 设置为 ${updated.role}`;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "角色修改失败");
  }
}

function onRoleChange(user: AdminUser, event: Event) {
  changeRole(user, (event.target as HTMLSelectElement).value);
}

onMounted(fetchUsers);
</script>

<template>
  <section class="admin-users-page">
    <div class="section-heading row-heading">
      <div>
        <h2>用户角色</h2>
        <p>调整学生、教师和管理员身份。</p>
      </div>
      <button class="refresh-button" type="button" :disabled="loading" @click="fetchUsers">
        <RefreshCw :size="16" />
        刷新
      </button>
    </div>

    <p v-if="loading" class="info-message">正在加载用户...</p>
    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    <p v-if="successMessage" class="success-message">{{ successMessage }}</p>

    <article v-for="user in users" :key="user.id" class="user-row">
      <div>
        <strong>{{ user.username }}</strong>
        <span>ID {{ user.id }} · {{ user.role }}</span>
      </div>
      <select :value="user.role" @change="onRoleChange(user, $event)">
        <option value="student">student</option>
        <option value="teacher">teacher</option>
        <option value="admin">admin</option>
      </select>
    </article>
  </section>
</template>

<style scoped>
.admin-users-page { display: grid; gap: var(--space-3); }
.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 38px;
  padding: 0 12px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-full);
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
  font-weight: 900;
}
.user-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 132px;
  gap: var(--space-2);
  align-items: center;
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: 18px;
  background: var(--surface);
}
.user-row div { display: grid; gap: 2px; min-width: 0; }
.user-row strong { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--text-main); }
.user-row span { color: var(--text-muted); font-size: var(--text-xs); font-weight: 800; }
.user-row select {
  min-height: 40px;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  background: var(--surface-soft);
  color: var(--text-main);
  font: inherit;
  font-weight: 850;
}
</style>
