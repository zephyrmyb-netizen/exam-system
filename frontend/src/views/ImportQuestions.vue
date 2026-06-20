<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import request, { getErrorMessage } from "../api/request";
import { previewFile, confirmImport } from "../api/imports";
import {
  Sparkles, Upload, ArrowRight, CheckCircle, AlertCircle,
  FileUp, BookOpen, ChevronDown, Layers,
} from "@lucide/vue";
import ImportPreview from "../components/import/ImportPreview.vue";

const router = useRouter();

// ── Phase: select | preview | success ──
const phase = ref("select");

// ── File ──
const selectedFile = ref(null);
const hasSelectedFile = computed(() => !!selectedFile.value);
const derivedCourseName = ref("");

const ALLOWED_EXTENSIONS = [".docx", ".pptx"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

// ── Course selector (for select phase) ──
const courses = ref([]);
const coursesLoading = ref(false);
const selectedCourseId = ref(0);

// ── Preview state ──
const previewData = ref(null);
const previewLoading = ref(false);
const previewError = ref("");

// ── Success state ──
const importResult = ref(null);

// ── Advanced options ──
const advancedOpen = ref(false);
const jsonText = ref(`[
  { "subject": "语文", "chapter": "古诗词", "type": "single_choice",
    "question": "下列诗句中，出自《静夜思》的是哪一句？",
    "options": { "A": "床前明月光", "B": "春眠不觉晓", "C": "白日依山尽", "D": "两个黄鹂鸣翠柳" },
    "answer": "A", "analysis": "《静夜思》是李白的诗，首句是床前明月光。", "difficulty": "easy" }
]`);
const importLoading = ref(false);
const importMessage = ref("");
const importError = ref("");
const jsonResultCourseId = ref(null);
const fileLoading = ref(false);
const fileMessage = ref("");
const fileError = ref("");
const extractedText = ref("");
const promptText = `请把下面的试题文本整理成标准 JSON 数组，格式如下：\n[\n  {\n    "subject": "科目",\n    "chapter": "章节",\n    "type": "single_choice",\n    "question": "题目正文",\n    "options": { "A": "选项A", ... },\n    "answer": "正确答案",\n    "analysis": "解析"\n  }\n]\n要求：只输出 JSON，不要解释。下面是试题文本：`;

// ── Helpers ──
function deriveNameFromFile(file) {
  if (!file?.name) return "";
  const dot = file.name.lastIndexOf(".");
  return dot > 0 ? file.name.slice(0, dot) : file.name;
}

function goToCourse(courseId) {
  if (courseId) router.push({ name: "course-detail", params: { courseId } });
  else router.push("/courses");
}

// ── File selection (select phase) ──
function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null;
  previewError.value = "";
  fileError.value = "";
  phase.value = "select";

  if (!selectedFile.value) { derivedCourseName.value = ""; return; }

  const ext = selectedFile.value.name?.substring(selectedFile.value.name.lastIndexOf("."))?.toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    fileError.value = `不支持 ${ext || "未知"} 格式，仅支持 ${ALLOWED_EXTENSIONS.join("、")}`;
    selectedFile.value = null; event.target.value = ""; return;
  }
  if (selectedFile.value.size > MAX_FILE_SIZE) {
    fileError.value = `文件过大（${(selectedFile.value.size / 1024 / 1024).toFixed(1)}MB），最大 10MB`;
    selectedFile.value = null; event.target.value = ""; return;
  }

  derivedCourseName.value = deriveNameFromFile(selectedFile.value);
}

// ── Step 1 → Step 2: Preview file ──
async function handlePreview() {
  if (!selectedFile.value) { previewError.value = "请先选择文件。"; return; }
  previewLoading.value = true;
  previewError.value = "";
  const params = {};
  if (derivedCourseName.value.trim()) params.course_name = derivedCourseName.value.trim();
  try {
    const data = await previewFile(selectedFile.value, params);
    previewData.value = data;
    phase.value = "preview";
  } catch (error) {
    previewError.value = getErrorMessage(error, "AI 解析失败");
  } finally {
    previewLoading.value = false;
  }
}

// ── Step 2 → Step 3: Confirm import ──
async function handleConfirm(payload) {
  try {
    const result = await confirmImport(payload);
    importResult.value = result;
    phase.value = "success";
  } catch (error) {
    previewError.value = getErrorMessage(error, "导入失败");
  }
}

// ── Back / retry from preview ──
function handleBackFromPreview() {
  phase.value = "select";
  previewData.value = null;
}

function handleRetryPreview() {
  phase.value = "select";
  previewData.value = null;
}

// ── Reset all ──
function clearAll() {
  phase.value = "select";
  selectedFile.value = null;
  derivedCourseName.value = "";
  selectedCourseId.value = 0;
  previewData.value = null;
  previewError.value = "";
  importResult.value = null;
}

// ── JSON import (unchanged) ──
function validateQuestionItem(item, index) {
  const errors = []; const n = index + 1;
  if (!item.question?.trim()) errors.push(`第 ${n} 题：缺少题干`);
  const validTypes = ["single_choice","multiple_choice","true_false","fill_blank","short_answer"];
  if (!item.type || !validTypes.includes(item.type)) errors.push(`第 ${n} 题：题型无效`);
  if (!item.answer?.trim()) errors.push(`第 ${n} 题：缺少答案`);
  return errors;
}

async function importQuestions() {
  importLoading.value = true; importMessage.value = ""; importError.value = "";
  try {
    const parsed = JSON.parse(jsonText.value);
    if (!Array.isArray(parsed)) throw new Error("请粘贴 JSON 数组");
    if (parsed.length === 0) throw new Error("JSON 数组为空");
    const allErrors = [];
    parsed.forEach((item, i) => allErrors.push(...validateQuestionItem(item, i)));
    if (allErrors.length > 0) { importError.value = `校验未通过：\n${allErrors.join("\n")}`; return; }
    const { data } = await request.post("/questions/batch", parsed, { params: { course_id: selectedCourseId.value > 0 ? selectedCourseId.value : 0 } });
    importMessage.value = `导入成功，共 ${data.imported_count || parsed.length} 道题。`;
    jsonResultCourseId.value = data.course_id || null;
  } catch (error) {
    importError.value = error instanceof SyntaxError || error.message?.includes("JSON")
      ? `JSON 格式不正确：${error.message}` : getErrorMessage(error, "导入失败");
  } finally { importLoading.value = false; }
}

async function uploadFile() {
  if (!selectedFile.value) { fileError.value = "请先选择文件。"; return; }
  fileLoading.value = true; fileMessage.value = ""; fileError.value = ""; extractedText.value = "";
  try {
    const formData = new FormData(); formData.append("file", selectedFile.value);
    const { data } = await request.post("/imports/file", formData, { params: { course_id: selectedCourseId.value > 0 ? selectedCourseId.value : 0 } });
    extractedText.value = data.text || ""; fileMessage.value = "提取成功";
  } catch (error) { fileError.value = getErrorMessage(error, "提取失败"); }
  finally { fileLoading.value = false; }
}

async function copyPromptAndText() {
  await navigator.clipboard?.writeText(`${promptText}\n\n${extractedText.value}`);
  fileMessage.value = "已复制。";
}

async function fetchCourses() {
  coursesLoading.value = true;
  try { const { data } = await request.get("/courses/mine"); courses.value = Array.isArray(data) ? data : data.items || []; }
  catch { courses.value = []; }
  finally { coursesLoading.value = false; }
}

onMounted(fetchCourses);
</script>

<template>
  <section class="stack">
    <div class="section-heading">
      <h2>导入题目</h2>
      <p>上传 Word / PPT，AI 自动生成题库</p>
    </div>

    <!-- ══════════════════════════════════════════════════════════
         PHASE 1: SELECT FILE
         ══════════════════════════════════════════════════════════ -->
    <template v-if="phase === 'select'">
      <div class="hero-drop-zone">
        <input class="file-input-native" type="file" accept=".docx,.pptx" @change="onFileChange" />
        <div class="hero-drop-icon"><FileUp :size="26" :stroke-width="1.8" /></div>
        <p v-if="!hasSelectedFile" class="hero-drop-text">选择 .docx 或 .pptx 文件</p>
        <p v-else class="hero-drop-text hero-drop-selected">
          <CheckCircle :size="15" :stroke-width="2.5" style="margin-right:6px;flex-shrink:0" />
          {{ selectedFile?.name }}
        </p>
        <p class="hero-drop-hint">最大 10MB</p>
      </div>

      <div v-if="hasSelectedFile" class="opt-panel">
        <div class="opt-row">
          <label class="opt-label">推荐题库名称</label>
          <input v-model="derivedCourseName" class="opt-input" type="text" placeholder="自动从文件名生成" />
        </div>
        <div class="opt-row">
          <label class="opt-label">或导入到已有题库</label>
          <select v-model="selectedCourseId" class="opt-input">
            <option :value="0">— 新建题库 —</option>
            <option v-if="coursesLoading" disabled>加载中...</option>
            <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}（{{ c.question_count ?? 0 }}题）</option>
          </select>
        </div>
      </div>

      <!-- Preview button -->
      <button class="hero-cta" type="button" :disabled="!hasSelectedFile || previewLoading" @click="handlePreview">
        <Sparkles v-if="!previewLoading" :size="20" :stroke-width="2.5" style="margin-right:8px" />
        {{ previewLoading ? "AI 正在解析..." : "AI 解析文档" }}
      </button>

      <!-- Error -->
      <p v-if="previewLoading" class="preview-loading-hint">正在解析文档，请等待约 30 秒...</p>
      <p v-if="fileError" class="msg msg-err">{{ fileError }}</p>
      <p v-if="previewError" class="msg msg-err">{{ previewError }}</p>

      <!-- Target hint -->
      <p v-if="hasSelectedFile && !previewError" class="target-hint">
        <span v-if="selectedCourseId > 0">
          将导入到已有题库：<strong>{{ courses.find(c => c.id === selectedCourseId)?.name || '' }}</strong>
        </span>
        <span v-else>
          将解析文档并预览，确认后创建题库：<strong>{{ derivedCourseName || '未命名' }}</strong>
        </span>
      </p>

      <!-- ═══ Advanced options ═══ -->
      <details class="adv-section" :open="advancedOpen" @toggle="advancedOpen = $event.target.open">
        <summary class="adv-summary">
          <Layers :size="15" :stroke-width="2.2" />
          <span>其他导入方式</span>
          <ChevronDown :size="15" :stroke-width="2.5" class="adv-chevron" />
        </summary>
        <div class="adv-body">
          <!-- JSON -->
          <div class="adv-card">
            <div>JSON</div>
            <textarea v-model="jsonText" class="adv-textarea" spellcheck="false" />
            <button class="primary-button small" type="button" :disabled="importLoading" @click="importQuestions">
              {{ importLoading ? "导入中..." : "导入 JSON" }}
            </button>
            <p v-if="importMessage" class="msg msg-ok">{{ importMessage }}</p>
            <pre v-if="importError" class="msg msg-err-pre">{{ importError }}</pre>
            <button v-if="importMessage" class="ghost-button" type="button" @click="goToCourse(jsonResultCourseId)">查看</button>
          </div>
          <!-- Text extraction -->
          <div class="adv-card">
            <div>只提取文本</div>
            <p class="adv-desc">提取文件文字给其他 AI 工具整理</p>
            <button class="ghost-button" type="button" :disabled="fileLoading || !selectedFile" @click="uploadFile">
              {{ fileLoading ? "提取中..." : "提取文本" }}
            </button>
            <p v-if="fileError" class="msg msg-err">{{ fileError }}</p>
            <div v-if="extractedText" class="adv-extracted">
              <pre>{{ extractedText }}</pre>
              <button class="ghost-button" type="button" @click="copyPromptAndText">复制文本</button>
            </div>
          </div>
        </div>
      </details>
    </template>

    <!-- ══════════════════════════════════════════════════════════
         PHASE 2: PREVIEW & CONFIRM
         ══════════════════════════════════════════════════════════ -->
    <template v-else-if="phase === 'preview' && previewData">
      <ImportPreview
        :previewData="previewData"
        :courses="courses"
        :coursesLoading="coursesLoading"
        @confirm="handleConfirm"
        @back="handleBackFromPreview"
        @retry="handleRetryPreview"
      />
    </template>

    <!-- ══════════════════════════════════════════════════════════
         PHASE 3: SUCCESS
         ══════════════════════════════════════════════════════════ -->
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
            <span class="ai-done-num ai-done-course">{{ importResult?.course_name || '' }}</span>
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
/* ── File drop ── */
.hero-drop-zone {
  position: relative; display: grid; place-items: center; gap: var(--space-2);
  padding: var(--space-10) var(--space-4);
  border: 2px dashed var(--line-strong); border-radius: var(--radius-xl);
  background: var(--surface); text-align: center; cursor: pointer;
  transition: border-color var(--ease-out), background var(--ease-out);
}
.hero-drop-zone:hover { border-color: var(--primary); background: var(--primary-soft); }
.hero-drop-icon {
  display: grid; place-items: center;
  width: 48px; height: 48px; border-radius: 50%;
  background: var(--surface-strong); color: var(--primary);
}
.hero-drop-zone:hover .hero-drop-icon { background: var(--surface); }
.hero-drop-text { margin: 0; font-size: var(--text-base); font-weight: 700; color: var(--text-secondary); }
.hero-drop-selected { color: var(--primary-strong); display: inline-flex; align-items: center; word-break: break-all; }
.hero-drop-hint { margin: 0; font-size: var(--text-xs); color: var(--text-placeholder); }

/* ── Options panel ── */
.opt-panel { display: grid; gap: var(--space-3); padding: var(--space-3); border: 1px solid var(--line-soft); border-radius: var(--radius-md); background: var(--surface); }
.opt-row { display: grid; gap: 4px; }
.opt-label { font-size: var(--text-xs); font-weight: 700; color: var(--text-muted); }
.opt-input {
  min-height: 44px; padding: 10px 14px;
  border: 1.5px solid var(--line-strong); border-radius: var(--radius-md);
  background: var(--surface-soft); font-size: var(--text-base); outline: none;
  transition: border-color var(--ease-out), box-shadow var(--ease-out);
}
.opt-input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); background: var(--surface); }
.opt-input:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── CTA ── */
.hero-cta {
  display: flex; align-items: center; justify-content: center; width: 100%;
  min-height: 50px; padding: var(--space-3) var(--space-4);
  border: none; border-radius: var(--radius-lg);
  color: #fff; background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  box-shadow: var(--shadow-primary);
  font-size: var(--text-base); font-weight: 800; cursor: pointer;
  transition: transform var(--ease-out), box-shadow var(--ease-out);
}
.hero-cta:active { transform: scale(0.98); }
.hero-cta:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
.preview-loading-hint { margin: 0; font-size: var(--text-sm); color: var(--text-muted); font-weight: 600; text-align: center; }

/* ── Target hint ── */
.target-hint { margin: -4px 0 0; text-align: center; font-size: var(--text-sm); color: var(--text-muted); font-weight: 600; line-height: 1.5; }
.target-hint strong { color: var(--primary-strong); font-weight: 800; }

/* ── AI Done ── */
.ai-done {
  display: grid; gap: var(--space-3); padding: var(--space-6) var(--space-4);
  border-radius: var(--radius-lg); text-align: center; justify-items: center;
  background: var(--emerald-soft); border: 1px solid var(--emerald-border);
}
.ai-done-icon { display: grid; place-items: center; width: 56px; height: 56px; border-radius: 50%; background: rgba(255,255,255,0.7); }
.ai-done-title { margin: 0; font-size: var(--text-lg); font-weight: 800; color: var(--text-main); }
.ai-done-stats { display: flex; gap: var(--space-5); justify-content: center; }
.ai-done-stat { display: grid; gap: 2px; text-align: center; }
.ai-done-num { font-size: var(--text-xl); font-weight: 800; color: var(--text-main); }
.ai-done-course { font-size: var(--text-base); color: var(--primary-strong); }
.ai-done-lbl { font-size: var(--text-xs); color: var(--text-muted); font-weight: 600; }
.ai-done-actions { display: flex; flex-wrap: wrap; gap: var(--space-2); justify-content: center; margin-top: var(--space-1); }

/* ── Messages ── */
.msg { margin: 0; padding: 8px 12px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 600; text-align: center; }
.msg-ok { background: var(--emerald-soft); color: var(--emerald); }
.msg-err { background: var(--rose-soft); color: var(--rose); }
.msg-err-pre { white-space: pre-wrap; word-break: break-word; background: var(--rose-soft); color: var(--rose); text-align: left; }

/* ── Advanced Section ── */
.adv-section { display: grid; border: none; }
.adv-summary {
  display: flex; align-items: center; justify-content: center; gap: var(--space-2);
  padding: var(--space-3); border: 1px solid var(--line-soft); border-radius: var(--radius-lg);
  background: var(--surface); color: var(--text-muted); font-size: var(--text-sm); font-weight: 700;
  cursor: pointer; list-style: none; transition: border-color var(--ease-out), color var(--ease-out);
}
.adv-summary::-webkit-details-marker { display: none; }
.adv-summary:hover { border-color: var(--line-accent); color: var(--text-secondary); }
.adv-chevron { transition: transform 0.2s ease; }
.adv-section[open] .adv-chevron { transform: rotate(180deg); }
.adv-body { display: grid; gap: var(--space-2); padding-top: var(--space-2); }
.adv-card { display: grid; gap: var(--space-2); padding: var(--space-3); border: 1px solid var(--line-soft); border-radius: var(--radius-md); background: var(--surface); }
.adv-desc { margin: 0; font-size: var(--text-xs); color: var(--text-muted); }
.adv-textarea {
  width: 100%; min-height: 120px; padding: var(--space-3);
  border: 1px solid var(--line-strong); border-radius: var(--radius-sm);
  background: var(--surface-soft); font-size: var(--text-sm); font-family: "SF Mono", monospace;
  resize: vertical; outline: none;
}
.adv-textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 2px var(--primary-glow); }
.adv-extracted { display: grid; gap: 6px; }
.adv-extracted pre { max-height: 180px; overflow: auto; margin: 0; padding: var(--space-2); border: 1px solid var(--line-soft); border-radius: var(--radius-sm); background: var(--surface-soft); font-size: var(--text-xs); white-space: pre-wrap; word-break: break-word; }

.file-input-native { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }

.primary-button, .ghost-button { display: inline-flex; align-items: center; justify-content: center; }
.primary-button { width: 100%; min-height: 44px; }

@media (max-width: 420px) {
  .hero-drop-zone { padding: var(--space-8) var(--space-3); }
  .hero-drop-icon { width: 40px; height: 40px; }
  .hero-drop-icon svg { width: 22px; height: 22px; }
  .ai-done-stats { gap: var(--space-3); }
}
</style>
