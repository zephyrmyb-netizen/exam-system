<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ArrowLeft, ChevronLeft, ChevronRight, Send } from "@lucide/vue";

import ExamQuestionCard from "@/components/exam/ExamQuestionCard.vue";
import { useKeyboardShortcuts } from "@/composables/useKeyboardShortcuts";
import { useSwipe } from "@/composables/useSwipe";
import { useExamStore } from "@/stores/exam";

const route = useRoute();
const router = useRouter();
const store = useExamStore();
const pageRef = ref<HTMLElement | null>(null);
const examId = computed(() => Number(route.params.examId));
const currentAnswer = computed(() => {
  const question = store.currentQuestion;
  return question ? store.answers[String(question.question_id)] || "" : "";
});

function answer(value: string) {
  if (!store.currentQuestion) return;
  store.setAnswer(store.currentQuestion.question_id, value);
}

async function submit() {
  try {
    const result = await store.submitCurrentExam();
    router.replace({ name: "exam-result", params: { examId: result.exam_id } });
  } catch {
    // store.error 已由 store 设置，留在当前页让用户重试
  }
}

function selectOption(index: number) {
  const question = store.currentQuestion;
  if (!question?.options) return;
  const key = Object.keys(question.options)[index];
  if (key) answer(key);
}

const shortcuts = useKeyboardShortcuts({
  next: () => store.next(),
  prev: () => store.prev(),
  selectOption,
});

useSwipe(pageRef, {
  onSwipeLeft: () => store.next(),
  onSwipeRight: () => store.prev(),
});

onMounted(() => {
  shortcuts.bind();
  store.startAttempt(examId.value);
});

onUnmounted(() => {
  shortcuts.unbind();
  if (!store.result) store.reset();
});
</script>

<template>
  <section ref="pageRef" class="exam-take-page">
    <p v-if="store.loading" class="info-message">正在进入考试...</p>

    <div v-else-if="store.error" class="empty-panel">
      <p class="error-message">{{ store.error }}</p>
      <button type="button" class="back-btn" @click="router.push({ name: 'exams' })">
        <ArrowLeft :size="16" /> 返回考试列表
      </button>
    </div>

    <template v-else-if="store.currentExam && store.currentQuestion">
      <div class="exam-topbar">
        <div>
          <span>{{ store.currentExam.title }}</span>
          <strong>{{ store.answeredCount }} / {{ store.totalQuestions }}</strong>
        </div>
        <div class="progress-track"><i :style="{ width: `${store.progress}%` }"></i></div>
      </div>

      <ExamQuestionCard
        :question="store.currentQuestion"
        :answer="currentAnswer"
        :index="store.currentIndex"
        :total="store.totalQuestions"
        @answer="answer"
      />

      <div class="question-nav">
        <button type="button" :disabled="store.currentIndex === 0" @click="store.prev">
          <ChevronLeft :size="17" />
          上一题
        </button>
        <button type="button" :disabled="store.currentIndex >= store.totalQuestions - 1" @click="store.next">
          下一题
          <ChevronRight :size="17" />
        </button>
      </div>

      <div class="answer-map">
        <button
          v-for="(question, index) in store.currentExam.questions"
          :key="question.question_id"
          type="button"
          :class="{ active: index === store.currentIndex, answered: store.answers[String(question.question_id)] }"
          @click="store.jumpTo(index)"
        >
          {{ index + 1 }}
        </button>
      </div>

      <button class="submit-button" type="button" :disabled="store.submitting" @click="submit">
        <Send :size="18" />
        {{ store.submitting ? "提交中..." : "交卷并查看成绩" }}
      </button>
    </template>
  </section>
</template>

<style scoped>
.exam-take-page { display: grid; gap: var(--space-4); }
.empty-panel {
  display: grid;
  gap: var(--space-4);
  place-items: center;
  padding: var(--space-8) var(--space-4);
  text-align: center;
}
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 44px;
  padding: 0 20px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-md);
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.exam-topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 1px solid var(--line-soft);
  border-radius: 22px;
  background: color-mix(in srgb, var(--surface) 92%, transparent);
  backdrop-filter: blur(16px);
}
.exam-topbar div:first-child { display: flex; justify-content: space-between; gap: var(--space-2); color: var(--text-muted); font-size: var(--text-sm); font-weight: 850; }
.exam-topbar strong { color: var(--primary); }
.progress-track { height: 8px; overflow: hidden; border-radius: var(--radius-full); background: var(--surface-soft); }
.progress-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--primary), var(--teal)); transition: width .2s ease; }
.question-nav {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-2);
}
.question-nav button, .submit-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 48px;
  border-radius: 18px;
  border: 1px solid var(--line-soft);
  background: var(--surface);
  color: var(--text-main);
  font: inherit;
  font-weight: 900;
}
.question-nav button:disabled, .submit-button:disabled { opacity: .55; }
.answer-map {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(42px, 1fr));
  gap: 8px;
}
.answer-map button {
  min-height: 42px;
  border: 1px solid var(--line-soft);
  border-radius: 14px;
  background: var(--surface);
  color: var(--text-muted);
  font: inherit;
  font-weight: 900;
}
.answer-map button.answered { color: var(--primary); background: var(--primary-soft); }
.answer-map button.active { border-color: var(--primary); color: #fff; background: var(--primary); }
.submit-button {
  border: 0;
  min-height: 56px;
  color: #fff;
  background: linear-gradient(135deg, var(--primary), var(--primary-strong));
  box-shadow: var(--shadow-primary);
}
</style>
