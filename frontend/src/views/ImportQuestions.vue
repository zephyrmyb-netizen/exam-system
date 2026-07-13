<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  ArrowRight,
  BookOpen,
  CheckCircle,
  ChevronDown,
  CloudUpload,
  FileUp,
  Layers,
  Sparkles,
} from "@lucide/vue";

import { confirmImport, confirmImportTask, extractFileText } from "../api/imports";
import { getErrorMessage } from "../api/request";
import ImportCapabilityStrip from "../components/import/ImportCapabilityStrip.vue";
import ImportPreview from "../components/import/ImportPreview.vue";
import ImportTaskMonitor from "../components/import/ImportTaskMonitor.vue";
import { useImportCourses } from "../composables/useImportCourses";
import { useAppNavigation } from "../composables/useAppNavigation";
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

const route = useRoute();
const { replaceTo, replaceWithSource } = useAppNavigation();
const aiTask = useAiImportTask();

const ACCEPTED_FILE_TYPES = ACCEPTED_IMPORT_FILE_TYPES;
const MAX_FILE_SIZE = 10 * 1024 * 1024;
const PARSING_RECOVERY_HINT = "AI 正在解析，请稍候，通常需要 30 秒左右";

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
const isDragging = ref(false);

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
const hasImportSuccess = computed(() => !!importResult.value || aiTask.imported.value);
const resolvedImportResult = computed(() => importResult.value || (aiTask.imported.value
  ? {
    imported_count: aiTask.importedCount.value,
    course_id: aiTask.resultCourseId.value,
    course_name: aiTask.resultCourseName.value || aiTask.courseName.value,
  }
  : null));
const activeFileName = computed(() => selectedFile.value?.name || aiTask.fileName.value || "");
const hasActiveFile = computed(() => !!activeFileName.value);
const activeFileKind = computed(() => getFileKindLabel(selectedFile.value || { name: aiTask.fileName.value }));
const activeFileSize = computed(() => formatImportFileSize(selectedFile.value?.size));
const activeFileDisplay = computed(() => [activeFileName.value, activeFileKind.value, activeFileSize.value].filter(Boolean).join(" · "));
const selectedFileIsImage = computed(() => isImageFile(selectedFile.value));
const canExtractText = computed(() => !!selectedFile.value && !selectedFileIsImage.value && !isParsing.value);
const activeCourseId = computed(() => selectedCourseId.value || aiTask.courseId.value || 0);
const activeCourseName = computed(() => derivedCourseName.value || aiTask.courseName.value || "");
const taskProgressText = computed(() => {
  const total = aiTask.progressTotal.value;
  if (!total) return "";
  return `已处理 ${Math.min(aiTask.progressCurrent.value, total)} / ${total} 个分块`;
});

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
    replaceWithSource({ name: "course-detail", params: { courseId } }, "import");
    return;
  }
  replaceTo("/courses");
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

function selectFile(file, input = null) {
  if (isParsing.value) {
    if (input) input.value = "";
    return;
  }

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
    if (input) input.value = "";
    return;
  }

  if (file.size > MAX_FILE_SIZE) {
    fileError.value = `文件过大（${(file.size / 1024 / 1024).toFixed(1)}MB），最大 10MB`;
    selectedFile.value = null;
    if (input) input.value = "";
    return;
  }

  selectedFile.value = file;
  derivedCourseName.value = deriveNameFromFile(file);
}

function onFileChange(event) {
  selectFile(event.target.files?.[0] || null, event.target);
}

function onDragEnter() {
  if (!isParsing.value) isDragging.value = true;
}

function onDragLeave(event) {
  if (!event.currentTarget.contains(event.relatedTarget)) isDragging.value = false;
}

function onFileDrop(event) {
  isDragging.value = false;
  selectFile(event.dataTransfer?.files?.[0] || null);
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
  if (confirmLoading.value) return;
  confirmError.value = "";
  confirmLoading.value = true;
  try {
    const result = aiTask.taskId.value
      ? await confirmImportTask(aiTask.taskId.value, payload)
      : await confirmImport(payload);
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
  void aiTask.resume();
});
</script>

<template>
  <section class="stack import-page" data-reference-page="import">
    <div class="section-heading import-page__head">
      <h2>AI 导入</h2>
      <p>智能解析 · 一键导入题目</p>
    </div>

    <template v-if="phase === 'select'">
      <section v-if="isParsing" class="import-running-state" aria-live="polite">
        <div class="import-running-file">
          <span class="import-running-file__icon" aria-hidden="true"><FileUp :size="18" :stroke-width="2.3" /></span>
          <span>{{ activeFileDisplay || "正在准备导入文件" }}</span>
        </div>
        <ImportTaskMonitor
          :title="aiTask.progressTitle.value"
          :detail="[aiTask.progressDetail.value, taskProgressText].filter(Boolean).join(' · ')"
        />
        <p class="msg msg-info">{{ PARSING_RECOVERY_HINT }}</p>
      </section>

      <template v-else>
        <label
          class="hero-drop-zone"
          :class="{ 'is-dragging': isDragging }"
          for="import-file-input"
          @dragenter.prevent="onDragEnter"
          @dragover.prevent="onDragEnter"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onFileDrop"
        >
          <input
            id="import-file-input"
            class="file-input-native"
            type="file"
            :accept="ACCEPTED_FILE_TYPES"
            :aria-describedby="fileError ? 'import-file-hint import-file-limits import-file-error' : 'import-file-hint import-file-limits'"
            @change="onFileChange"
          />
          <span class="hero-drop-icon" aria-hidden="true"><CloudUpload :size="30" :stroke-width="1.8" /></span>
          <span v-if="!hasActiveFile" class="hero-drop-text">点击或拖拽上传文件</span>
          <span
            v-else
            class="hero-drop-text hero-drop-selected truncate-file-name"
            :title="activeFileName"
          >
            <CheckCircle :size="15" :stroke-width="2.5" />
            {{ activeFileDisplay }}
          </span>
          <span id="import-file-hint" class="hero-drop-hint">AI 自动解析题干、选项和答案</span>
        </label>

        <div class="import-format-tags" aria-label="支持的导入格式">
          <span class="format-tag format-tag--word">Word</span>
          <span class="format-tag format-tag--ppt">PPT</span>
          <span class="format-tag format-tag--pdf">PDF</span>
          <span class="format-tag format-tag--image">图片</span>
          <span class="format-tag format-tag--text">文本</span>
        </div>
        <p id="import-file-limits" class="import-file-limits">
          支持 DOCX / PDF / PPTX / PNG / JPG / JPEG / WEBP，单个文件最大 10MB
        </p>

        <div v-if="hasActiveFile" class="opt-panel">
          <label class="opt-row">
            <span class="opt-label">推荐题库名称</span>
            <input v-model="derivedCourseName" class="opt-input" type="text" placeholder="自动从文件名生成" />
          </label>
          <label class="opt-row">
            <span class="opt-label">或导入到已有题库</span>
            <select v-model="selectedCourseId" class="opt-input">
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

        <button class="hero-cta" type="button" :disabled="!hasActiveFile" @click="handlePreview">
          <Sparkles :size="20" :stroke-width="2.5" />
          {{ aiTask.error.value ? "重新解析" : "AI 解析文件" }}
        </button>

        <p v-if="fileError" id="import-file-error" class="msg msg-err" role="alert">{{ fileError }}</p>
        <p v-if="aiTask.error.value" class="msg msg-err" role="alert">{{ aiTask.error.value }}</p>

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
            <span>JSON / 其他导入方式</span>
            <ChevronDown :size="15" :stroke-width="2.5" class="adv-chevron" />
          </summary>

          <div class="adv-body">
            <ImportCapabilityStrip />
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

        <ol class="import-guide" aria-label="导入步骤说明">
          <li><span>1</span><p><strong>上传文件或粘贴 JSON</strong><small>选择资料并确认导入题库名称</small></p></li>
          <li><span>2</span><p><strong>AI 智能解析</strong><small>自动识别题干、选项、答案和解析</small></p></li>
          <li><span>3</span><p><strong>预览确认后导入</strong><small>检查结果后一次性写入题库</small></p></li>
        </ol>
      </template>
    </template>

    <template v-else-if="phase === 'preview'">
      <p v-if="confirmError" class="msg msg-err">{{ confirmError }}</p>
      <ImportPreview
        :preview-data="aiTask.previewData.value"
        :courses="courses"
        :courses-loading="coursesLoading"
        :confirming="confirmLoading"
        :file-name="activeFileName"
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
        <p class="ai-done-target">已导入到题库：<strong>{{ resolvedImportResult?.course_name || activeCourseName || "未命名题库" }}</strong></p>
        <div class="ai-done-stats">
          <div class="ai-done-stat">
            <span class="ai-done-num">{{ resolvedImportResult?.imported_count || 0 }}</span>
            <span class="ai-done-lbl">道题目</span>
          </div>
          <div class="ai-done-stat">
            <span class="ai-done-num ai-done-course">{{ resolvedImportResult?.course_name || "" }}</span>
            <span class="ai-done-lbl">题库</span>
          </div>
        </div>
        <div class="ai-done-actions">
          <button
            v-if="resolvedImportResult?.course_id"
            class="primary-button"
            type="button"
            @click="goToCourse(resolvedImportResult.course_id)"
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
.import-page {
  gap: 12px;
  min-width: 0;
  max-width: 100%;
  padding-top: 18px;
  overflow-x: clip;
}

.import-page__head {
  display: grid;
  gap: 4px;
  padding: 0;
}

.import-page__head h2,
.import-page__head p {
  margin: 0;
}

.import-page__head h2 {
  font-size: 24px;
  line-height: 1.25;
}

.import-page__head p {
  color: var(--text-muted);
  font-size: var(--text-sm);
  line-height: 1.5;
}

.hero-drop-zone {
  position: relative;
  display: grid;
  place-items: center;
  gap: 6px;
  min-height: 140px;
  padding: 20px var(--space-4);
  border: 2px dashed var(--line-strong);
  border-radius: var(--radius-md);
  background: var(--surface-muted);
  text-align: center;
  cursor: pointer;
  transition: border-color var(--ease-out), background var(--ease-out), transform var(--ease-spring);
}

.import-format-tags {
  display: flex;
  gap: 6px;
  min-width: 0;
  padding: 2px 0;
  overflow-x: auto;
  scrollbar-width: none;
}
.import-format-tags::-webkit-scrollbar {
  display: none;
}
.format-tag {
  display: inline-flex;
  flex: 0 0 auto;
  min-height: 28px;
  align-items: center;
  padding: 0 10px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 800;
}
.format-tag--word { background: #eff6ff; color: #2563eb; }
.format-tag--ppt { background: #fff7ed; color: #ea580c; }
.format-tag--pdf { background: var(--rose-soft); color: var(--rose); }
.format-tag--image { background: #f5f3ff; color: #7c3aed; }
.format-tag--text { background: var(--primary-soft); color: var(--primary-strong); }

.import-file-limits {
  margin: -4px 0 0;
  color: var(--text-placeholder);
  font-size: 11px;
  line-height: 1.45;
}

.import-guide {
  display: grid;
  gap: 9px;
  margin: 4px 0 0;
  padding: 12px 14px;
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  background: var(--glass-card);
  box-shadow: var(--shadow-xs), var(--glass-inner-highlight);
  list-style: none;
}
.import-guide li { display: grid; grid-template-columns: 26px minmax(0, 1fr); gap: 9px; align-items: center; }
.import-guide li > span { display: grid; width: 26px; height: 26px; place-items: center; border-radius: 50%; background: var(--primary-soft); color: var(--primary-strong); font-size: 11px; font-weight: 850; }
.import-guide p { display: grid; gap: 2px; margin: 0; }
.import-guide strong { font-size: 12px; color: var(--text-main); }
.import-guide small { color: var(--text-muted); font-size: 11px; }

.import-running-state {
  display: grid;
  gap: var(--space-3);
  min-width: 0;
  padding: var(--space-4);
  border: 1px solid var(--primary-border);
  border-radius: var(--radius-lg);
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.import-running-file {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 750;
}

.import-running-file > span:last-child {
  overflow: hidden;
  min-width: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.import-running-file__icon {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  background: var(--primary-soft);
  color: var(--primary);
}

.hero-drop-zone:hover {
  border-color: var(--primary);
  background: var(--primary-soft);
}

.hero-drop-zone.is-dragging {
  border-color: var(--primary);
  background: var(--primary-soft);
  transform: translateY(-2px);
}

.hero-drop-zone:focus-within {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
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
  width: 44px;
  height: 44px;
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

.truncate-file-name {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
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
  background: var(--primary);
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

.msg-info {
  background: var(--primary-soft);
  color: var(--primary-strong);
}

.msg-err,
.msg-err-pre {
  background: var(--rose-soft);
  color: var(--rose);
}

.ai-done-target {
  margin: -6px 0 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 650;
  text-align: center;
}

.ai-done-target strong {
  color: var(--primary-strong);
  font-weight: 800;
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
  min-width: 0;
  max-width: 100%;
  max-height: 180px;
  overflow: auto;
  overflow-wrap: anywhere;
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
/* Reference layout overrides: compact at 390px without hiding real workflows. */
.hero-drop-selected { display: flex; }
.hero-drop-selected svg { flex-shrink: 0; }
.hero-cta { border-radius: 6px; background: var(--primary); box-shadow: var(--shadow-primary); }
.hero-cta:hover:not(:disabled) { background: var(--primary-strong); }
.opt-panel, .adv-card { border-radius: 6px; box-shadow: var(--shadow-xs); }
.ai-done { border-radius: 8px; background: var(--surface); border-color: var(--line-soft); }
@media (max-width: 420px) {
  .hero-drop-zone { min-height: 136px; padding-block: 18px; }
  .target-hint { text-align: left; }
}

@media (max-width: 340px) {
  .import-page { padding-inline: 12px; }
  .hero-drop-zone { min-height: 128px; padding-inline: 12px; }
  .import-guide { padding-inline: 10px; }
}

@media (prefers-reduced-motion: reduce) {
  .hero-drop-zone { transition: none; }
  .hero-drop-zone.is-dragging { transform: none; }
}
</style>
