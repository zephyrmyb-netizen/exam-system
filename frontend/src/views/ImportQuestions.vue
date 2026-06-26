<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  Sparkles,
  ArrowRight,
  CheckCircle,
  FileUp,
  BookOpen,
  ChevronDown,
  Layers,
} from "@lucide/vue";
import { getErrorMessage } from "../api/request";
import { extractFileText, confirmImport } from "../api/imports";
import { useAiImportTask } from "../stores/aiImportTask";
import ImportPreview from "../components/import/ImportPreview.vue";
import { useImportCourses } from "../composables/useImportCourses";
import { useManualQuestionImport } from "../composables/useManualQuestionImport";

const router = useRouter();
const route = useRoute();
const aiTask = useAiImportTask();

const selectedFile = ref(null);
const derivedCourseName = ref("");
const selectedCourseId = ref(0);
const advancedOpen = ref(false);
const confirmError = ref("");
const confirmLoading = ref(false);
const importResult = ref(null);
const { courses, coursesLoading, coursesError, fetchCourses } = useImportCourses();
const {
  jsonText,
  importLoading,
  importMessage,
  importError,
  jsonResultCourseId,
  importQuestions,
} = useManualQuestionImport(selectedCourseId);

const ALLOWED_EXTENSIONS = [".docx", ".pptx"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

const fileLoading = ref(false);
const fileMessage = ref("");
const fileError = ref("");
const extractedText = ref("");

const isParsing = computed(() => aiTask.status.value === "running");
const hasPreview = computed(() => aiTask.status.value === "success" && aiTask.previewData.value);
const hasImportSuccess = computed(() => !!importResult.value);
const activeFileName = computed(() => selectedFile.value?.name || aiTask.fileName.value || "");
const hasActiveFile = computed(() => !!activeFileName.value);
const activeCourseId = computed(() => selectedCourseId.value || aiTask.courseId.value || 0);
const activeCourseName = computed(() => derivedCourseName.value || aiTask.courseName.value || "");

const phase = computed(() => {
  if (hasImportSuccess.value) return "success";
  if (hasPreview.value) return "preview";
  return "select";
});

const currentTargetName = computed(() => {
  if (activeCourseId.value > 0) {
    return courses.value.find((c) => c.id === activeCourseId.value)?.name || "";
  }
  return activeCourseName.value;
});

watch(
  () => aiTask.previewData.value,
  (data) => {
    if (data?.suggested_course_name && !derivedCourseName.value) {
      derivedCourseName.value = data.suggested_course_name;
    }
  }
);

function deriveNameFromFile(file) {
  if (!file?.name) return "";
  const dot = file.name.lastIndexOf(".");
  return dot > 0 ? file.name.slice(0, dot) : file.name;
}

function goToCourse(courseId) {
  if (courseId) router.push({ name: "course-detail", params: { courseId } });
  else router.push("/courses");
}

function readTargetCourseIdFromRoute() {
  const raw = route.query.course_id || route.query.courseId;
  const value = Array.isArray(raw) ? raw[0] : raw;
  const id = Number(value);
  return Number.isFinite(id) && id > 0 ? id : 0;
}

function syncTargetCourseFromRoute() {
  const targetCourseId = readTargetCourseIdFromRoute();
  if (targetCourseId > 0) {
    selectedCourseId.value = targetCourseId;
  }
}

function onFileChange(event) {
  if (isParsing.value) {
    event.target.value = "";
    return;
  }

  const file = event.target.files?.[0] || null;
  confirmError.value = "";
  fileError.value = "";
  importResult.value = null;
  aiTask.reset();

  if (!file) {
    selectedFile.value = null;
    derivedCourseName.value = "";
    return;
  }

  const ext = file.name?.substring(file.name.lastIndexOf("."))?.toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    fileError.value = `不支持 ${ext || "未知"} 格式，仅支持 ${ALLOWED_EXTENSIONS.join("、")}`;
    selectedFile.value = null;
    event.target.value = "";
    return;
  }

  if (file.size > MAX_FILE_SIZE) {
    fileError.value = `文件过大（${(file.size / 1024 / 1024).toFixed(1)}MB），最大 10MB`;
    selectedFile.value = null;
    event.target.value = "";
    return;
  }

  selectedFile.value = file;
  derivedCourseName.value = deriveNameFromFile(file);
}

async function handlePreview() {
  const file = selectedFile.value || aiTask.fileRef.value;
  if (!file) {
    fileError.value = "请先选择文件。";
    return;
  }

  fileError.value = "";
  confirmError.value = "";
  importResult.value = null;

  const params = {};
  if (activeCourseId.value > 0) {
    params.course_id = activeCourseId.value;
  } else if (activeCourseName.value.trim()) {
    params.course_name = activeCourseName.value.trim();
  }

  await aiTask.startPreview(file, params);
}

async function handleConfirm(payload) {
  confirmError.value = "";
  confirmLoading.value = true;
  try {
    const result = await confirmImport(payload);
    importResult.value = result;
    aiTask.markImported(result);
  } catch (error) {
    confirmError.value = getErrorMessage(error, "导入失败");
  } finally {
    confirmLoading.value = false;
  }
}

function handleBackFromPreview() {
  aiTask.reset();
  importResult.value = null;
}

function handleRetryPreview() {
  if (selectedFile.value || aiTask.fileRef.value) {
    handlePreview();
  } else {
    aiTask.reset();
    fileError.value = "文件状态已失效，请重新选择文档。";
  }
}

function clearAll() {
  selectedFile.value = null;
  derivedCourseName.value = "";
  selectedCourseId.value = 0;
  confirmError.value = "";
  importResult.value = null;
  aiTask.reset();
}

async function uploadFile() {
  if (!selectedFile.value) {
    fileError.value = "请先选择文件。";
    return;
  }

  fileLoading.value = true;
  fileMessage.value = "";
  fileError.value = "";
  extractedText.value = "";
  try {
    const data = await extractFileText(selectedFile.value, {
      course_id: selectedCourseId.value > 0 ? selectedCourseId.value : 0,
    });
    extractedText.value = data.text || "";
    fileMessage.value = "提取成功";
  } catch (error) {
    fileError.value = getErrorMessage(error, "提取失败");
  } finally {
    fileLoading.value = false;
  }
}

async function copyPromptAndText() {
  if (!extractedText.value) {
    fileError.value = "暂无可复制文本。";
    return;
  }

  const promptText = `请把下面的试题文本整理成标准 JSON 数组，只输出 JSON，不要解释：\n\n${extractedText.value}`;

  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(promptText);
    } else {
      const textarea = document.createElement("textarea");
      textarea.value = promptText;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.left = "-9999px";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      const copied = document.execCommand("copy");
      document.body.removeChild(textarea);
      if (!copied) throw new Error("copy failed");
    }
    fileError.value = "";
    fileMessage.value = "已复制文本";
  } catch {
    fileMessage.value = "";
    fileError.value = "复制失败，请手动选择文本复制。";
  }
}

watch(
  () => [route.query.course_id, route.query.courseId],
  syncTargetCourseFromRoute,
);

onMounted(() => {
  syncTargetCourseFromRoute();
  fetchCourses();
});
</script>

<template>
  <section class="stack">
    <div class="section-heading">
      <h2>导入题目</h2>
      <p>上传 Word / PPT，AI 自动解析成题库</p>
    </div>

    <div class="import-capability-strip">
      <div class="import-capability">
        <span class="capability-label">当前支持</span>
        <strong>Word .docx / PPT .pptx</strong>
      </div>
      <div class="import-capability">
        <span class="capability-label">处理提示</span>
        <strong>约 30 秒，大文件会更久</strong>
      </div>
      <div class="import-capability import-capability--wide">
        <span class="capability-label">切换页面</span>
        <strong>解析不中断，回来可继续查看</strong>
      </div>
    </div>

    <template v-if="phase === 'select'">
      <div class="hero-drop-zone" :class="{ 'hero-drop-zone--disabled': isParsing }">
        <input class="file-input-native" type="file" accept=".docx,.pptx" :disabled="isParsing" @change="onFileChange" />
        <div class="hero-drop-icon"><FileUp :size="26" :stroke-width="1.8" /></div>
        <p v-if="!hasActiveFile" class="hero-drop-text">选择 .docx 或 .pptx 文件</p>
        <p v-else class="hero-drop-text hero-drop-selected">
          <CheckCircle :size="15" :stroke-width="2.5" style="margin-right:6px;flex-shrink:0" />
          {{ activeFileName }}
        </p>
        <p class="hero-drop-hint">{{ isParsing ? "AI 正在解析，暂不能更换文件" : "最大 10MB" }}</p>
      </div>

      <div v-if="hasActiveFile" class="opt-panel">
        <div class="opt-row">
          <label class="opt-label">推荐题库名称</label>
          <input v-model="derivedCourseName" class="opt-input" type="text" placeholder="自动从文件名生成" :disabled="isParsing" />
        </div>
        <div class="opt-row">
          <label class="opt-label">或导入到已有题库</label>
          <select v-model="selectedCourseId" class="opt-input" :disabled="isParsing">
            <option :value="0">新建题库</option>
            <option v-if="coursesLoading" disabled>加载中...</option>
            <option v-for="c in courses" :key="c.id" :value="c.id">
              {{ c.name }}（{{ c.question_count ?? 0 }}题）
            </option>
          </select>
        </div>
        <div v-if="coursesError" class="inline-warning">
          <span>{{ coursesError }}</span>
          <button type="button" :disabled="coursesLoading" @click="fetchCourses">
            {{ coursesLoading ? "重试中..." : "重试加载" }}
          </button>
        </div>
      </div>

      <button class="hero-cta" type="button" :disabled="!hasActiveFile || isParsing" @click="handlePreview">
        <Sparkles v-if="!isParsing" :size="20" :stroke-width="2.5" style="margin-right:8px" />
        {{ isParsing ? "AI 正在解析..." : "AI 解析文档" }}
      </button>

      <div v-if="isParsing" class="running-panel">
        <span class="running-dot"></span>
        <div>
          <strong>{{ aiTask.progressTitle.value }}</strong>
          <p>{{ aiTask.progressDetail.value }}</p>
        </div>
      </div>

      <p v-if="fileError" class="msg msg-err">{{ fileError }}</p>
      <p v-if="aiTask.error.value" class="msg msg-err">{{ aiTask.error.value }}</p>

      <p v-if="hasActiveFile && !aiTask.error.value" class="target-hint">
        <span v-if="activeCourseId > 0">
          将导入到已有题库：<strong>{{ currentTargetName }}</strong>
        </span>
        <span v-else>
          将解析文档并预览，确认后创建题库：<strong>{{ currentTargetName || "未命名" }}</strong>
        </span>
      </p>

      <details class="adv-section" :open="advancedOpen" @toggle="advancedOpen = $event.target.open">
        <summary class="adv-summary">
          <Layers :size="15" :stroke-width="2.2" />
          <span>其他导入方式</span>
          <ChevronDown :size="15" :stroke-width="2.5" class="adv-chevron" />
        </summary>
        <div class="adv-body">
          <div class="adv-card">
            <div>JSON 导入</div>
            <textarea v-model="jsonText" class="adv-textarea" spellcheck="false" />
            <button class="primary-button small" type="button" :disabled="importLoading" @click="importQuestions">
              {{ importLoading ? "导入中..." : "导入 JSON" }}
            </button>
            <p v-if="importMessage" class="msg msg-ok">{{ importMessage }}</p>
            <pre v-if="importError" class="msg msg-err-pre">{{ importError }}</pre>
            <button v-if="importMessage" class="ghost-button" type="button" @click="goToCourse(jsonResultCourseId)">查看</button>
          </div>

          <div class="adv-card">
            <div>只提取文本</div>
            <p class="adv-desc">提取文件文字，给其他 AI 工具整理。</p>
            <button class="ghost-button" type="button" :disabled="fileLoading || isParsing || !selectedFile" @click="uploadFile">
              {{ fileLoading ? "提取中..." : "提取文本" }}
            </button>
            <p v-if="fileMessage" class="msg msg-ok">{{ fileMessage }}</p>
            <p v-if="fileError" class="msg msg-err">{{ fileError }}</p>
            <div v-if="extractedText" class="adv-extracted">
              <pre>{{ extractedText }}</pre>
              <button class="ghost-button" type="button" @click="copyPromptAndText">复制文本</button>
            </div>
          </div>
        </div>
      </details>
    </template>

    <template v-else-if="phase === 'preview'">
      <p v-if="confirmError" class="msg msg-err">{{ confirmError }}</p>
      <ImportPreview
        :previewData="aiTask.previewData.value"
        :courses="courses"
        :coursesLoading="coursesLoading"
        :confirming="confirmLoading"
        :initialCourseId="activeCourseId"
        :initialCourseName="activeCourseName"
        @confirm="handleConfirm"
        @back="handleBackFromPreview"
        @retry="handleRetryPreview"
      />
    </template>

    <template v-else-if="phase === 'success'">
      <div class="ai-done">
        <div class="ai-done-icon"><CheckCircle :size="36" :stroke-width="2.5" color="var(--emerald)" /></div>
        <p class="ai-done-title">导入成功</p>
        <div class="ai-done-stats">
          <div class="ai-done-stat">
            <span class="ai-done-num">{{ importResult?.imported_count || 0 }}</span>
            <span class="ai-done-lbl">道题目</span>
          </div>
          <div class="ai-done-stat">
            <span class="ai-done-num ai-done-course">{{ importResult?.course_name || "" }}</span>
            <span class="ai-done-lbl">题库</span>
          </div>
        </div>
        <div class="ai-done-actions">
          <button
            v-if="importResult?.course_id"
            class="primary-button"
            type="button"
            @click="goToCourse(importResult.course_id)"
          >
            <BookOpen :size="16" :stroke-width="2.5" style="margin-right:6px" />
            进入题库
            <ArrowRight :size="16" :stroke-width="2.5" style="margin-left:4px" />
          </button>
          <button class="ghost-button" type="button" @click="clearAll">继续导入</button>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
.import-capability-strip {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
}

.import-capability {
  display: grid;
  gap: 2px;
  min-height: 58px;
  padding: 10px 12px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background:
    linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(255, 255, 255, 0.88)),
    var(--surface);
}

.import-capability--wide {
  grid-column: 1 / -1;
}

.capability-label {
  color: var(--text-placeholder);
  font-size: 10px;
  font-weight: 800;
}

.import-capability strong {
  color: var(--text-main);
  font-size: var(--text-xs);
  line-height: 1.35;
}

.hero-drop-zone {
  position: relative;
  display: grid;
  place-items: center;
  gap: var(--space-2);
  padding: var(--space-10) var(--space-4);
  border: 2px dashed var(--line-strong);
  border-radius: var(--radius-xl);
  background: var(--surface);
  text-align: center;
  cursor: pointer;
}

.hero-drop-zone:hover {
  border-color: var(--primary);
  background: var(--primary-soft);
}

.hero-drop-zone--disabled,
.hero-drop-zone--disabled:hover {
  cursor: wait;
  border-color: var(--line-soft);
  background: var(--surface-soft);
}

.hero-drop-zone--disabled .file-input-native {
  cursor: not-allowed;
}

.hero-drop-icon {
  display: grid;
  place-items: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--surface-strong);
  color: var(--primary);
}

.hero-drop-text {
  margin: 0;
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-secondary);
}

.hero-drop-selected {
  color: var(--primary-strong);
  display: inline-flex;
  align-items: center;
  word-break: break-all;
}

.hero-drop-hint {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--text-placeholder);
}

.opt-panel {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface);
}

.opt-row {
  display: grid;
  gap: 4px;
}

.opt-label {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--text-muted);
}

.opt-input {
  min-height: 44px;
  padding: 10px 14px;
  border: 1.5px solid var(--line-strong);
  border-radius: var(--radius-md);
  background: var(--surface-soft);
  font-size: var(--text-base);
  outline: none;
}

.opt-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-glow);
  background: var(--surface);
}

.inline-warning {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--amber-soft);
  color: var(--amber);
  font-size: var(--text-xs);
  font-weight: 700;
}

.inline-warning button {
  flex-shrink: 0;
  border: none;
  background: transparent;
  color: var(--primary-strong);
  font: inherit;
  cursor: pointer;
}

.inline-warning button:disabled {
  opacity: 0.6;
  cursor: wait;
}

.hero-cta {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 50px;
  padding: var(--space-3) var(--space-4);
  border: none;
  border-radius: var(--radius-lg);
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  box-shadow: var(--shadow-primary);
  font-size: var(--text-base);
  font-weight: 800;
  cursor: pointer;
}

.hero-cta:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}

.running-panel {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  border: 1px solid var(--line-accent);
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.running-panel p {
  margin: 2px 0 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.running-dot {
  flex-shrink: 0;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--primary);
  animation: running-pulse 1.2s ease-in-out infinite;
}

@keyframes running-pulse {
  0%, 100% { opacity: 0.4; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.25); }
}

.target-hint {
  margin: -4px 0 0;
  text-align: center;
  font-size: var(--text-sm);
  color: var(--text-muted);
  font-weight: 600;
  line-height: 1.5;
}

.target-hint strong {
  color: var(--primary-strong);
  font-weight: 800;
}

.ai-done {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-6) var(--space-4);
  border-radius: var(--radius-lg);
  text-align: center;
  justify-items: center;
  background: var(--emerald-soft);
  border: 1px solid var(--emerald-border);
}

.ai-done-icon {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
}

.ai-done-title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 800;
  color: var(--text-main);
}

.ai-done-stats {
  display: flex;
  gap: var(--space-5);
  justify-content: center;
}

.ai-done-stat {
  display: grid;
  gap: 2px;
  text-align: center;
}

.ai-done-num {
  font-size: var(--text-xl);
  font-weight: 800;
  color: var(--text-main);
}

.ai-done-course {
  font-size: var(--text-base);
  color: var(--primary-strong);
}

.ai-done-lbl {
  font-size: var(--text-xs);
  color: var(--text-muted);
  font-weight: 600;
}

.ai-done-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: center;
  margin-top: var(--space-1);
}

.msg {
  margin: 0;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}

.msg-ok {
  background: var(--emerald-soft);
  color: var(--emerald);
}

.msg-err {
  background: var(--rose-soft);
  color: var(--rose);
}

.msg-err-pre {
  white-space: pre-wrap;
  word-break: break-word;
  background: var(--rose-soft);
  color: var(--rose);
  text-align: left;
}

.adv-section {
  display: grid;
  border: none;
}

.adv-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: var(--surface);
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 700;
  cursor: pointer;
  list-style: none;
}

.adv-summary::-webkit-details-marker {
  display: none;
}

.adv-chevron {
  transition: transform 0.2s ease;
}

.adv-section[open] .adv-chevron {
  transform: rotate(180deg);
}

.adv-body {
  display: grid;
  gap: var(--space-2);
  padding-top: var(--space-2);
}

.adv-card {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface);
}

.adv-desc {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--text-muted);
}

.adv-textarea {
  width: 100%;
  min-height: 120px;
  padding: var(--space-3);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
  font-size: var(--text-sm);
  font-family: "SF Mono", monospace;
  resize: vertical;
  outline: none;
}

.adv-extracted {
  display: grid;
  gap: 6px;
}

.adv-extracted pre {
  max-height: 180px;
  overflow: auto;
  margin: 0;
  padding: var(--space-2);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
  font-size: var(--text-xs);
  white-space: pre-wrap;
  word-break: break-word;
}

.file-input-native {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.primary-button,
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.primary-button {
  width: 100%;
  min-height: 44px;
}

@media (max-width: 420px) {
  .import-capability-strip { gap: 7px; }
  .import-capability { min-height: 54px; padding: 9px 10px; }

  .hero-drop-zone {
    padding: var(--space-8) var(--space-3);
  }

  .hero-drop-icon {
    width: 40px;
    height: 40px;
  }

  .ai-done-stats {
    gap: var(--space-3);
  }
}
</style>
