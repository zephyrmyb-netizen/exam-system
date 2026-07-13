import { defineStore } from "pinia";
import {
  getExamLeaderboard,
  getExamDetail,
  listExams,
  listMyExams,
  startExam,
  submitExam,
} from "@/api/exams";
import { getErrorMessage } from "@/api/request";
import type { Exam, ExamAttempt, ExamDetail, ExamLeaderboard, ExamQuestion, ExamResult } from "@/types";

const pendingSubmissions = new WeakMap<object, Promise<ExamResult>>();
const examSessionGenerations = new WeakMap<object, number>();

function advanceExamSession(storeKey: object): number {
  const nextGeneration = (examSessionGenerations.get(storeKey) || 0) + 1;
  examSessionGenerations.set(storeKey, nextGeneration);
  return nextGeneration;
}

export const useExamStore = defineStore("exam", {
  state: () => ({
    exams: [] as Exam[],
    myExams: [] as Exam[],
    currentExam: null as ExamDetail | null,
    currentAttempt: null as ExamAttempt | null,
    result: null as ExamResult | null,
    leaderboard: null as ExamLeaderboard | null,
    currentIndex: 0,
    answers: {} as Record<string, string>,
    remainingSeconds: null as number | null,
    loading: false,
    submitting: false,
    error: "",
  }),
  getters: {
    currentQuestion: (state): ExamQuestion | null => state.currentExam?.questions[state.currentIndex] || null,
    totalQuestions: (state): number => state.currentExam?.questions.length || 0,
    answeredCount: (state): number => Object.values(state.answers).filter((value) => value.trim()).length,
    progress: (state): number => {
      const total = state.currentExam?.questions.length || 0;
      return total ? Math.round((Object.values(state.answers).filter((value) => value.trim()).length / total) * 100) : 0;
    },
  },
  actions: {
    async fetchExams(): Promise<Exam[]> {
      this.loading = true;
      this.error = "";
      try {
        const data = await listExams();
        this.exams = data.items || [];
        return this.exams;
      } catch (error) {
        this.error = getErrorMessage(error, "考试列表加载失败");
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async fetchMyExams(): Promise<Exam[]> {
      this.loading = true;
      this.error = "";
      try {
        const data = await listMyExams();
        this.myExams = data.items || [];
        return this.myExams;
      } catch (error) {
        this.error = getErrorMessage(error, "我创建的考试加载失败");
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async loadExam(id: number): Promise<ExamDetail> {
      const storeKey = this as object;
      advanceExamSession(storeKey);
      pendingSubmissions.delete(storeKey);
      this.submitting = false;
      this.loading = true;
      this.error = "";
      try {
        const detail = await getExamDetail(id);
        this.currentExam = detail;
        this.currentIndex = 0;
        this.answers = {};
        this.remainingSeconds = null;
        this.result = null;
        this.leaderboard = null;
        return detail;
      } catch (error) {
        this.error = getErrorMessage(error, "考试详情加载失败");
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async startAttempt(id: number): Promise<void> {
      const storeKey = this as object;
      advanceExamSession(storeKey);
      pendingSubmissions.delete(storeKey);
      this.submitting = false;
      this.loading = true;
      this.error = "";
      try {
        const [detail, attempt] = await Promise.all([getExamDetail(id), startExam(id)]);
        this.currentExam = detail;
        this.currentAttempt = attempt;
        this.currentIndex = 0;
        this.answers = {};
        this.syncRemainingSeconds();
        this.result = null;
        this.leaderboard = null;
      } catch (error) {
        this.error = getErrorMessage(error, "考试开始失败");
        throw error;
      } finally {
        this.loading = false;
      }
    },

    setAnswer(questionId: number, answer: string): void {
      this.answers[String(questionId)] = answer;
    },

    syncRemainingSeconds(now = Date.now()): void {
      const startedAt = this.currentAttempt?.started_at;
      const timeLimit = this.currentExam?.time_limit;
      if (!startedAt || !timeLimit) {
        this.remainingSeconds = null;
        return;
      }

      const startedAtMs = Date.parse(startedAt);
      if (!Number.isFinite(startedAtMs)) {
        this.remainingSeconds = null;
        return;
      }

      const elapsedSeconds = Math.max(0, Math.floor((now - startedAtMs) / 1000));
      this.remainingSeconds = Math.max(0, timeLimit * 60 - elapsedSeconds);
    },

    next(): void {
      if (!this.currentExam) return;
      this.currentIndex = Math.min(this.currentIndex + 1, Math.max(this.currentExam.questions.length - 1, 0));
    },

    prev(): void {
      this.currentIndex = Math.max(this.currentIndex - 1, 0);
    },

    jumpTo(index: number): void {
      if (!this.currentExam) return;
      this.currentIndex = Math.min(Math.max(index, 0), Math.max(this.currentExam.questions.length - 1, 0));
    },

    submitCurrentExam(): Promise<ExamResult> {
      const storeKey = this as object;
      const pending = pendingSubmissions.get(storeKey);
      if (pending) return pending;
      if (!this.currentExam) return Promise.reject(new Error("No exam loaded"));

      const examId = this.currentExam.id;
      const sessionGeneration = examSessionGenerations.get(storeKey) || 0;
      const answers = { ...this.answers };
      this.submitting = true;
      this.error = "";
      const submission = submitExam(examId, { answers })
        .then((result) => {
          if (this.currentExam?.id === examId && examSessionGenerations.get(storeKey) === sessionGeneration) this.result = result;
          return result;
        })
        .catch((error: unknown) => {
          if (this.currentExam?.id === examId && examSessionGenerations.get(storeKey) === sessionGeneration) {
            this.error = getErrorMessage(error, "交卷失败");
          }
          throw error;
        })
        .finally(() => {
          if (pendingSubmissions.get(storeKey) === submission) {
            pendingSubmissions.delete(storeKey);
            this.submitting = false;
          }
        });

      pendingSubmissions.set(storeKey, submission);
      return submission;
    },

    async fetchLeaderboard(id: number): Promise<ExamLeaderboard> {
      this.loading = true;
      this.error = "";
      try {
        const leaderboard = await getExamLeaderboard(id);
        this.leaderboard = leaderboard;
        return leaderboard;
      } catch (error) {
        this.error = getErrorMessage(error, "排行榜加载失败");
        throw error;
      } finally {
        this.loading = false;
      }
    },

    reset(): void {
      const storeKey = this as object;
      advanceExamSession(storeKey);
      pendingSubmissions.delete(storeKey);
      this.currentExam = null;
      this.currentAttempt = null;
      this.result = null;
      this.leaderboard = null;
      this.currentIndex = 0;
      this.answers = {};
      this.remainingSeconds = null;
      this.error = "";
      this.submitting = false;
    },
  },
});
