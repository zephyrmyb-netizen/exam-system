<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowRight,
  BookOpen,
  CheckCircle,
  ChevronDown,
  FileUp,
  Layers,
  Sparkles,
} from "@lucide/vue";

import { confirmImport, extractFileText } from "../api/imports";
import { getErrorMessage } from "../api/request";
import ImportCapabilityStrip from "../components/import/ImportCapabilityStrip.vue";
import ImportPreview from "../components/import/ImportPreview.vue";
import ImportTaskMonitor from "../components/import/ImportTaskMonitor.vue";
import { useImportCourses } from "../composables/useImportCourses";
import { useManualQuestionImport } from "../composables/useManualQuestionImport";
import { useAiImportTask } from "../stores/aiImportTask";
import {
  ACCEPTED_IMPORT_FILE_TYPES,
  ALLOWED_IMPORT_EXTENSIONS,
  formatImportFileSize,
  getFileExtension,
  getFileKindLabel,
  getUnsupportedImportMessage,
  isAllowedImportFile,
  isImageFile,
  isLegacyPpt,
} from "../utils/importFiles";

const router = useRouter();
const route = useRoute();
const aiTask = useAiImportTask();

const ACCEPTED_FILE_TYPES = ACCEPTED_IMPORT_FILE_TYPES;
const MAX_FILE_SIZE = 10 * 1024 * 1024;

const selectedFile = ref(null);
const derivedCourseName = ref("");
const selectedCourseId = ref(0);
const advancedOpen = ref(false);
const confirmError = ref("");
const confirmLoading = ref(false);
const importResult = ref(null);
const fileLoading = ref(false);
const fileMessage = ref("");
const fileError = ref("");
const extractedText = ref("");

const { courses, coursesLoading, coursesError, fetchCourses } = useImportCourses();
const {
  jsonText,
  importLoading,
  importMessage,
  importError,
  jsonResultCourseId,
  importQuestions,
} = useManualQuestionImport(selectedCourseId);

const isParsing = computed(() => aiTask.status.value === "running");
const hasPreview = computed(() => aiTask.status.value === "success" && aiTask.previewData.value);
const hasImportSuccess = computed(() => !!importResult.value);
const activeFileName = computed(() => selectedFile.value?.name || aiTask.fileName.value || "");
const hasActiveFile = computed(() => !!activeFileName.value);
const activeFileKind = computed(() => getFileKindLabel(selectedFile.value || { name: aiTask.fileName.value }));
const activeFileSize = computed(() => formatImportFileSize(selectedFile.value?.size));
const activeFileDisplay = computed(() => [activeFileName.value, activeFileKind.value, activeFileSize.value].filter(Boolean).join(" · "));
const selectedFileIsImage = computed(() => isImageFile(selectedFile.value));
const canExtractText = computed(() => !!selectedFile.value && !selectedFileIsImage.value && !isParsing.value);
const activeCourseId = computed(() => selectedCourseId.value || aiTask.courseId.value || 0);
const activeCourseName = computed(() => derivedCourseName.value || aiTask.courseName.value || "");

const phase = computed(() => {
  if (hasImportSuccess.value) return "success";
  if (hasPreview.value) return "preview";
  return "select";
});

const currentTargetName = computed(() => {
  if (activeCourseId.value > 0) {
    return courses.value.find((course) => course.id === activeCourseId.value)?.name || "";
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

watch(
  () => [route.query.course_id, route.query.courseId],
  syncTargetCourseFromRoute
);

function deriveNameFromFile(file) {
  if (!file?.name) return "";
  const dot = file.name.lastIndexOf(".");
  return dot > 0 ? file.name.slice(0, dot) : file.name;
}

function goToCourse(courseId) {
  if (courseId) {
    router.push({ name: "course-detail", params: { courseId } });
    return;
  }
  router.push("/courses");
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
  fileMessage.value = "";
  extractedText.value = "";
  importResult.value = null;
  aiTask.reset();

  if (!file) {
    selectedFile.value = null;
    derivedCourseName.value = "";
    return;
  }

  if (isLegacyPpt(file) || !isAllowedImportFile(file)) {
    fileError.value = getUnsupportedImportMessage(file.name);
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
  if (isLegacyPpt(file) || !ALLOWED_IMPORT_EXTENSIONS.includes(getFileExtension(file.name))) {
    fileError.value = getUnsupportedImportMessage(file.name);
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
    return;
  }
  aiTask.reset();
  fileError.value = "文件状态已失效，请重新选择文档。";
}

function clearAll() {
  selectedFile.value = null;
  derivedCourseName.value = "";
  selectedCourseId.value = 0;
  confirmError.value = "";
  fileError.value = "";
  fileMessage.value = "";
  extractedText.value = "";
  importResult.value = null;
  aiTask.reset();
}

async function uploadFile() {
  if (!selectedFile.value) {
    fileError.value = "请先选择文件。";
    return;
  }
  if (isImageFile(selectedFile.value)) {
    fileError.value = "图片文件没有可直接提取的文本，请使用 AI 解析。";
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

onMounted(() => {
  syncTargetCourseFromRoute();
  fetchCourses();
});
</script>

<template>
  <section class="stack">
    <div class="section-heading">
      <h2>导入题目</h2>
      <p>上传 Word、PPTX 或图片，AI 自动解析成题库</p>
    </div>

    <ImportCapabilityStrip />

    <template v-if="phase === 'select'">
      <label class="hero-drop-zone" :class="{ 'hero-drop-zone--disabled': isParsing }">
        <input class="file-input-native" type="file" :accept="ACCEPTED_FILE_TYPES" :disabled="isParsing" @change="onFileChange" />
        <span class="hero-drop-icon"><FileUp :size="26" :stroke-width="1.8" /></span>
        <span v-if="!hasActiveFile" class="hero-drop-text">选择 Word / PPTX / 图片</span>
        <span v-else class="hero-drop-text hero-drop-selected">
          <CheckCircle :size="15" :stroke-width="2.5" />
          {{ activeFileDisplay }}
        </span>
        <span class="hero-drop-hint">
          {{ isParsing ? "AI 正在解析，请等待，不要重复上传。" : "支持 .docx、.pptx、.png、.jpg、.webp，最大 10MB" }}
        </span>
      </label>

      <div v-if="hasActiveFile" class="opt-panel">
        <label class="opt-row">
          <span class="opt-label">推荐题库名称</span>
          <input v-model="derivedCourseName" class="opt-input" type="text" placeholder="自动从文件名生成" :disabled="isParsing" />
        </label>
        <label class="opt-row">
          <span class="opt-label">或导入到已有题库</span>
          <select v-model="selectedCourseId" class="opt-input" :disabled="isParsing">
            <option :value="0">新建题库</option>
            <option v-if="coursesLoading" disabled>加载中...</option>
            <option v-for="course in courses" :key="course.id" :value="course.id">
              {{ course.name }}（{{ course.question_count ?? 0 }} 题）
            </option>
          </select>
        </label>
        <div v-if="coursesError" class="inline-warning">
          <span>{{ coursesError }}</span>
          <button type="button" :disabled="coursesLoading" @click="fetchCourses">
            {{ coursesLoading ? "重试中..." : "重试加载" }}
          </button>
        </div>
      </div>

      <button class="hero-cta" type="button" :disabled="!hasActiveFile || isParsing" @click="handlePreview">
        <Sparkles v-if="!isParsing" :size="20" :stroke-width="2.5" />
        {{ isParsing ? "AI 正在解析..." : "AI 解析文件" }}
      </button>

      <ImportTaskMonitor
        v-if="isParsing"
        :title="aiTask.progressTitle.value"
        :detail="aiTask.progressDetail.value"
      />

      <p v-if="fileError" class="msg msg-err">{{ fileError }}</p>
      <p v-if="aiTask.error.value" class="msg msg-err">{{ aiTask.error.value }}</p>

      <p v-if="hasActiveFile && !aiTask.error.value" class="target-hint">
        <span v-if="activeCourseId > 0">
          将导入到已有题库：<strong>{{ currentTargetName }}</strong>
        </span>
        <span v-else>
          将解析文件并预览，确认后创建题库：<strong>{{ currentTargetName || "未命名" }}</strong>
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
            <div class="adv-title">JSON 导入</div>
            <textarea v-model="jsonText" class="adv-textarea" spellcheck="false" />
            <button class="primary-button small" type="button" :disabled="importLoading" @click="importQuestions">
              {{ importLoading ? "导入中..." : "导入 JSON" }}
            </button>
            <p v-if="importMessage" class="msg msg-ok">{{ importMessage }}</p>
            <pre v-if="importError" class="msg msg-err-pre">{{ importError }}</pre>
            <button v-if="importMessage" class="ghost-button" type="button" @click="goToCourse(jsonResultCourseId)">查看</button>
          </div>

          <div class="adv-card">
            <div class="adv-title">只提取文本</div>
            <p class="adv-desc">
              {{ selectedFileIsImage ? "图片文件没有可直接提取的文本，请使用 AI 解析。" : "提取文件文字，给其他 AI 工具整理。" }}
            </p>
            <button class="ghost-button" type="button" :disabled="fileLoading || !canExtractText" @click="uploadFile">
              {{ selectedFileIsImage ? "图片需使用 AI 解析" : fileLoading ? "提取中..." : "提取文本" }}
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
        :preview-data="aiTask.previewData.value"
        :courses="courses"
        :courses-loading="coursesLoading"
        :confirming="confirmLoading"
        :initial-course-id="activeCourseId"
        :initial-course-name="activeCourseName"
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
            <BookOpen :size="16" :stroke-width="2.5" />
            进入题库
            <ArrowRight :size="16" :stroke-width="2.5" />
          </button>
          <button class="ghost-button" type="button" @click="clearAll">继续导入</button>
        </div>
      </div>
    </template>
  </section>
</template>

<style scoped>
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
  border-color: var(--line-soft);
  background: var(--surface-soft);
  cursor: wait;
}

.file-input-native {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
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
  color: var(--text-secondary);
  font-size: var(--text-base);
  font-weight: 700;
}

.hero-drop-selected {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--primary-strong);
  word-break: break-all;
}

.hero-drop-hint {
  color: var(--text-placeholder);
  font-size: var(--text-xs);
}

.opt-panel,
.adv-card {
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
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 700;
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
  background: var(--surface);
  box-shadow: 0 0 0 3px var(--primary-glow);
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
  border: none;
  background: transparent;
  color: var(--primary-strong);
  cursor: pointer;
  font: inherit;
}

.hero-cta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  min-height: 50px;
  padding: var(--space-3) var(--space-4);
  border: none;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  color: #fff;
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

.target-hint {
  margin: -4px 0 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 600;
  line-height: 1.5;
  text-align: center;
}

.target-hint strong {
  color: var(--primary-strong);
  font-weight: 800;
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

.msg-err,
.msg-err-pre {
  background: var(--rose-soft);
  color: var(--rose);
}

.msg-err-pre {
  white-space: pre-wrap;
  word-break: break-word;
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

.adv-title {
  color: var(--text-main);
  font-weight: 800;
}

.adv-desc {
  margin: 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
}

.adv-textarea {
  min-height: 160px;
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface-soft);
  color: var(--text-main);
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
  font-size: 12px;
  resize: vertical;
}

.adv-extracted {
  display: grid;
  gap: var(--space-2);
}

.adv-extracted pre {
  max-height: 180px;
  overflow: auto;
  margin: 0;
  padding: var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--surface-soft);
  color: var(--text-secondary);
  font-size: 12px;
  white-space: pre-wrap;
}

.ai-done {
  display: grid;
  justify-items: center;
  gap: var(--space-3);
  padding: var(--space-6) var(--space-4);
  border: 1px solid var(--emerald-border);
  border-radius: var(--radius-lg);
  background: var(--emerald-soft);
  text-align: center;
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
  color: var(--text-main);
  font-size: var(--text-lg);
  font-weight: 800;
}

.ai-done-stats,
.ai-done-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-3);
}

.ai-done-stat {
  display: grid;
  gap: 2px;
  text-align: center;
}

.ai-done-num {
  color: var(--text-main);
  font-size: var(--text-xl);
  font-weight: 800;
}

.ai-done-course {
  color: var(--primary-strong);
  font-size: var(--text-base);
}

.ai-done-lbl {
  color: var(--text-muted);
  font-size: var(--text-xs);
  font-weight: 600;
}

.primary-button,
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.small {
  min-height: 38px;
}
</style>
