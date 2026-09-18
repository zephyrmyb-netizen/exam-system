<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { BookOpen, ChevronRight, Copy } from "@lucide/vue";

import { useAuthStore } from "../stores/auth";
import request, { getErrorMessage } from "../api/request";

const router = useRouter();
const auth = useAuthStore();

type StudyGroup = {
  id: number;
  name: string;
  invite_code: string;
  member_count: number;
  owner_id: number;
};

type GroupResources = {
  courses: Array<{ id: number; name: string; question_count: number }>;
  exams: Array<{ id: number; title: string; share_code?: string }>;
};

const groups = ref<StudyGroup[]>([]);
const groupName = ref("");
const inviteCode = ref("");
const errorMessage = ref("");
const successMessage = ref("");
const loading = ref(false);
const saving = ref(false);
const resourcesLoading = ref(false);
let resourceGeneration = 0;
const groupResources = ref<GroupResources | null>(null);
const shareGroupId = ref<number | null>(null);
const selectedGroup = computed(() => groups.value.find((group) => group.id === shareGroupId.value) || null);

const canShare = computed(() => selectedGroup.value?.owner_id === auth.user?.id);

function clearMessages() {
  errorMessage.value = "";
  successMessage.value = "";
}

async function loadGroups() {
  loading.value = true;
  try {
    const { data } = await request.get<StudyGroup[]>("/study-groups/mine");
    groups.value = data;
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "加载小组失败");
  } finally {
    loading.value = false;
  }
}

async function createGroup() {
  if (saving.value) return;
  const name = groupName.value.trim();
  if (!name) {
    errorMessage.value = "请输入小组名称。";
    return;
  }
  clearMessages();
  saving.value = true;
  try {
    await request.post("/study-groups/", { name });
    groupName.value = "";
    successMessage.value = "小组已创建。";
    await loadGroups();
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "创建小组失败");
  } finally {
    saving.value = false;
  }
}

async function joinGroup() {
  if (saving.value) return;
  const code = inviteCode.value.trim();
  if (!code) {
    errorMessage.value = "请输入邀请码。";
    return;
  }
  clearMessages();
  saving.value = true;
  try {
    await request.post(`/study-groups/join/${encodeURIComponent(code)}`);
    inviteCode.value = "";
    successMessage.value = "已加入小组。";
    await loadGroups();
  } catch (error) {
    errorMessage.value = getErrorMessage(error, "加入小组失败");
  } finally {
    saving.value = false;
  }
}

async function loadGroupResources(groupId: number) {
  const generation = ++resourceGeneration;
  shareGroupId.value = groupId;
  groupResources.value = null;
  resourcesLoading.value = true;
  clearMessages();
  try {
    const { data } = await request.get<GroupResources>(`/study-groups/${groupId}/resources`);
    if (generation === resourceGeneration) groupResources.value = data;
  } catch (error) {
    if (generation === resourceGeneration) errorMessage.value = getErrorMessage(error, "加载小组资源失败");
  } finally {
    if (generation === resourceGeneration) resourcesLoading.value = false;
  }
}

function selectGroup() {
  if (!shareGroupId.value) {
    resourceGeneration += 1;
    groupResources.value = null;
    resourcesLoading.value = false;
    return;
  }
  void loadGroupResources(shareGroupId.value);
}

async function copyInviteCode(code: string) {
  clearMessages();
  try {
    await navigator.clipboard.writeText(code);
    successMessage.value = "邀请码已复制。";
  } catch {
    window.prompt("请复制邀请码", code);
  }
}

function chooseResource(kind: "course" | "exam") {
  if (!shareGroupId.value) {
    errorMessage.value = "请先从上方选择一个小组。";
    return;
  }
  router.replace({
    name: kind === "course" ? "courses" : "exams",
    query: { share_group: String(shareGroupId.value), from: "study-groups" },
  });
}

onMounted(() => void loadGroups());
</script>

<template>
  <section class="groups-page" data-reference-page="study-groups">
    <p v-if="errorMessage" class="status-banner status-banner--error" role="alert">{{ errorMessage }}</p>
    <p v-if="successMessage" class="status-banner status-banner--success" role="status">{{ successMessage }}</p>

    <section class="groups-card groups-card--forms">
      <form @submit.prevent="createGroup">
        <label>创建小组<input v-model="groupName" maxlength="100" placeholder="例如：高数冲刺组" required /></label>
        <button type="submit" :disabled="saving || !groupName.trim()">创建小组</button>
      </form>
      <form @submit.prevent="joinGroup">
        <label
          >加入小组<input
            v-model="inviteCode"
            maxlength="16"
            placeholder="输入邀请码"
            autocapitalize="characters"
            required
        /></label>
        <button type="submit" :disabled="saving || !inviteCode.trim()">加入小组</button>
      </form>
    </section>

    <section class="groups-card">
      <div class="section-heading">
        <div>
          <h2>我的小组</h2>
          <p>选择小组后可查看共享资源，也会自动带入共享表单。</p>
        </div>
        <span>{{ loading ? "加载中…" : `${groups.length} 个` }}</span>
      </div>
      <p v-if="!loading && !groups.length" class="empty-state">还没有小组。创建一个，或让朋友把邀请码发给你。</p>
      <div v-else class="group-list">
        <article
          v-for="group in groups"
          :key="group.id"
          class="group-item"
          :class="{ 'is-selected': group.id === shareGroupId }"
        >
          <div>
            <h3>{{ group.name }}</h3>
            <p>
              {{ group.owner_id === auth.user?.id ? "我创建的" : "我加入的" }} · {{ group.member_count }} 人 · 邀请码
              {{ group.invite_code }}
            </p>
          </div>
          <div class="group-item__actions">
            <button type="button" class="secondary-button" @click="copyInviteCode(group.invite_code)">
              <Copy :size="15" />
              复制邀请码
            </button>
            <button type="button" :aria-pressed="group.id === shareGroupId" @click="loadGroupResources(group.id)">
              {{ group.id === shareGroupId ? "当前小组" : "查看资源" }}
            </button>
          </div>
        </article>
      </div>
    </section>

    <section class="groups-card" data-testid="study-group-share">
      <div class="section-heading">
        <div>
          <h2>共享资源</h2>
          <p>选择小组后前往题库或考试详情，一键共享，与组员一起学习。</p>
        </div>
        <span>{{ selectedGroup ? `当前：${selectedGroup.name}` : "请先选择小组" }}</span>
      </div>
      <div class="share-form">
        <label
          >共享到小组<select v-model.number="shareGroupId" @change="selectGroup">
            <option :value="null">选择小组</option>
            <option v-for="group in groups" :key="group.id" :value="group.id">{{ group.name }}</option>
          </select></label
        >
        <button type="button" :disabled="!shareGroupId || !canShare" @click="chooseResource('course')">
          选择题库后共享
        </button>
        <button type="button" :disabled="!shareGroupId || !canShare" @click="chooseResource('exam')">
          选择考试后共享
        </button>
      </div>
      <p v-if="selectedGroup && !canShare" class="empty-state">你可以学习下方资源，由组主添加共享内容。</p>
      <p v-if="resourcesLoading" class="empty-state" role="status">正在加载共享资源…</p>
      <div v-else-if="groupResources" class="resources">
        <div class="resource-section">
          <h3>
            共享题库 <span>{{ groupResources.courses.length }}</span>
          </h3>
          <p v-if="!groupResources.courses.length" class="empty-state">还没有共享题库。</p>
          <RouterLink
            v-for="course in groupResources.courses"
            :key="course.id"
            class="resource-link"
            :to="{
              name: 'course-detail',
              params: { courseId: course.id },
              query: { from: 'study-groups', share_group: String(shareGroupId) },
            }"
          >
            <BookOpen :size="18" /><span
              >{{ course.name }}<small>{{ course.question_count }} 道题 · 查看题库</small></span
            ><ChevronRight :size="16" />
          </RouterLink>
        </div>
        <div class="resource-section">
          <h3>
            共享考试 <span>{{ groupResources.exams.length }}</span>
          </h3>
          <p v-if="!groupResources.exams.length" class="empty-state">还没有已发布的考试。</p>
          <RouterLink
            v-for="exam in groupResources.exams"
            :key="exam.id"
            class="resource-link"
            :to="{ name: 'exam-detail', params: { examId: exam.id }, query: { from: 'study-groups' } }"
          >
            <BookOpen :size="18" /><span>{{ exam.title }}<small>查看考试安排</small></span
            ><ChevronRight :size="16" />
          </RouterLink>
        </div>
      </div>
    </section>
  </section>
</template>

<style scoped>
.groups-page {
  display: grid;
  gap: 16px;
}
.groups-card {
  min-width: 0;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  padding: 20px;
}
.groups-card--forms {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}
.groups-card--forms form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: end;
}
.groups-card label {
  display: grid;
  gap: 8px;
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 500;
}
.groups-card input,
.groups-card select {
  width: 100%;
  min-width: 0;
  min-height: 44px;
  border: 1px solid var(--line-soft);
  border-radius: 12px;
  padding: 0 12px;
  background: var(--surface-soft);
  color: var(--text-main);
  font: inherit;
}
.groups-card button {
  min-height: 44px;
  border: 0;
  border-radius: 12px;
  padding: 0 12px;
  background: var(--primary);
  color: white;
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
}
.groups-card button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.section-heading h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 650;
  letter-spacing: -0.02em;
}
.section-heading p,
.group-item p {
  margin: 6px 0 0;
  color: var(--text-muted);
  font-size: var(--text-xs);
  line-height: 1.6;
}
.section-heading > span {
  flex-shrink: 0;
  max-width: 30%;
  color: var(--text-muted);
  font-size: var(--text-xs);
}
.group-list {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}
.group-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--line-soft);
  border-radius: 16px;
  background: var(--surface-soft);
}
.group-item h3 {
  margin: 0;
  font-size: var(--text-md);
  font-weight: 600;
  overflow-wrap: anywhere;
}
.group-item.is-selected {
  border-color: var(--primary-border);
  background: var(--primary-soft);
}
.group-item__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.groups-card .secondary-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--surface);
  color: var(--text-main);
  border: 1px solid var(--line-soft);
}
.empty-state {
  margin: 12px 0 0;
  padding: 0;
  color: var(--text-muted);
  font-size: var(--text-xs);
}
.share-form {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 10px;
  margin-top: 16px;
  align-items: end;
}
.resources {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 20px;
}
.resource-section {
  min-width: 0;
  border-top: 1px solid var(--line-soft);
  padding-top: 16px;
}
.resource-section h3 {
  margin: 0 0 12px;
  font-size: var(--text-md);
  font-weight: 600;
}
.resource-section h3 span {
  color: var(--text-muted);
  font-weight: 400;
  margin-left: 6px;
}
.resource-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-top: 8px;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  color: var(--text-main);
  text-decoration: none;
  background: var(--surface-soft);
}
.resource-link:hover {
  border-color: var(--primary-border);
  background: var(--primary-soft);
}
.resource-link > span {
  flex: 1;
  min-width: 0;
  overflow-wrap: anywhere;
}
.resource-link > svg {
  flex-shrink: 0;
  color: var(--primary);
}
.resource-link small {
  display: block;
  color: var(--text-muted);
  margin-top: 4px;
}
@media (max-width: 620px) {
  .groups-card--forms,
  .resources {
    grid-template-columns: 1fr;
  }
  .groups-card {
    padding: 16px;
  }
  .share-form {
    grid-template-columns: 1fr 1fr;
  }
  .share-form label {
    grid-column: 1 / -1;
  }
  .group-item {
    align-items: flex-start;
    flex-direction: column;
  }
  .group-item__actions {
    width: 100%;
  }
  .group-item__actions button {
    flex: 1;
  }
}
</style>
