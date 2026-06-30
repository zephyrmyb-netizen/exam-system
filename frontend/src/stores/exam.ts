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
      this.loading = true;
      this.error = "";
      try {
        const detail = await getExamDetail(id);
        this.currentExam = detail;
        this.currentIndex = 0;
        this.answers = {};
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
      this.loading = true;
      this.error = "";
      try {
        const [detail, attempt] = await Promise.all([getExamDetail(id), startExam(id)]);
        this.currentExam = detail;
        this.currentAttempt = attempt;
        this.currentIndex = 0;
        this.answers = {};
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

    async submitCurrentExam(): Promise<ExamResult> {
      if (!this.currentExam) throw new Error("No exam loaded");
      this.submitting = true;
      this.error = "";
      try {
        const result = await submitExam(this.currentExam.id, { answers: this.answers });
        this.result = result;
        return result;
      } catch (error) {
        this.error = getErrorMessage(error, "交卷失败");
        throw error;
      } finally {
        this.submitting = false;
      }
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
      this.currentExam = null;
      this.currentAttempt = null;
      this.result = null;
      this.leaderboard = null;
      this.currentIndex = 0;
      this.answers = {};
      this.error = "";
      this.submitting = false;
    },
  },
});
