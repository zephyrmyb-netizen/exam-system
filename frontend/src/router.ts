import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { getToken } from "./api/request";
import AppLayout from "./layouts/AppLayout.vue";
import AuthLayout from "./layouts/AuthLayout.vue";
import { useAuthStore } from "./stores/auth";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        name: "home",
        component: () => import("./views/Home.vue"),
        meta: { title: "首页", description: "快速进入题库、AI 导入和练习流程。", navKey: "home" },
      },
      { path: "questions", redirect: "/courses" },
      {
        path: "courses",
        name: "courses",
        component: () => import("./views/CourseList.vue"),
        meta: { title: "我的题库", description: "选择题库开始练习。", navKey: "list" },
      },
      {
        path: "courses/:courseId",
        name: "course-detail",
        component: () => import("./views/CourseDetail.vue"),
        meta: { title: "题库题目", navKey: "list", parent: "courses" },
      },
      {
        path: "courses/:courseId/practice",
        name: "course-practice",
        component: () => import("./views/CoursePractice.vue"),
        meta: { title: "题库练习", navKey: "list", parent: "course-detail" },
      },
      {
        path: "public-library",
        name: "public-library",
        component: () => import("./views/PublicLibrary.vue"),
        meta: { title: "公共题库", description: "公开分享的题目集。", navKey: "list", parent: "courses" },
      },
      {
        path: "import",
        name: "import",
        component: () => import("./views/ImportQuestions.vue"),
        meta: { title: "AI 导入", description: "上传资料或粘贴 JSON，把题目整理进题库。", navKey: "import" },
      },
      {
        path: "practice",
        name: "practice",
        component: () => import("./views/PracticeHub.vue"),
        meta: { title: "练习", description: "先选择题库，再进入专注练习。", navKey: "" },
      },
      {
        path: "practice/wrong",
        name: "practice-wrong",
        component: () => import("./views/WrongPractice.vue"),
        meta: { title: "错题强化", description: "集中攻克薄弱环节。", navKey: "", parent: "practice" },
      },
      {
        path: "practice/due",
        name: "practice-due",
        component: () => import("./views/DuePractice.vue"),
        meta: { title: "到期复习", description: "复习今日到期题目。", navKey: "", parent: "practice" },
      },
      {
        path: "practice/history",
        name: "practice-history",
        component: () => import("./views/PracticeHistory.vue"),
        meta: { title: "练习记录", description: "查看历史练习详情。", navKey: "", parent: "mine" },
      },
      {
        path: "exams",
        name: "exams",
        component: () => import("./views/exam/ExamList.vue"),
        meta: { title: "考试", description: "选择已发布考试并开始作答。", navKey: "home" },
      },
      {
        path: "exams/new",
        name: "exam-create",
        component: () => import("./views/exam/ExamCreate.vue"),
        meta: { title: "创建考试", description: "从题库选择题目组卷。", navKey: "home", parent: "exams", requiresPermission: "exam:create" },
      },
      {
        path: "exams/:examId",
        name: "exam-detail",
        component: () => import("./views/exam/ExamDetail.vue"),
        meta: { title: "考试详情", navKey: "home", parent: "exams" },
      },
      {
        path: "exams/:examId/take",
        name: "exam-take",
        component: () => import("./views/exam/ExamTake.vue"),
        meta: { title: "考试答题", navKey: "home", parent: "exam-detail" },
      },
      {
        path: "exams/:examId/result",
        name: "exam-result",
        component: () => import("./views/exam/ExamResult.vue"),
        meta: { title: "考试结果", navKey: "home", parent: "exams" },
      },
      {
        path: "admin",
        name: "admin-dashboard",
        component: () => import("./views/admin/AdminDashboard.vue"),
        meta: { title: "管理后台", navKey: "mine", parent: "mine", requiresPermission: "stats:view_global" },
      },
      {
        path: "admin/users",
        name: "admin-users",
        component: () => import("./views/admin/AdminUsers.vue"),
        meta: { title: "用户角色", navKey: "mine", parent: "admin-dashboard", requiresPermission: "user:manage" },
      },
      {
        path: "mine",
        name: "mine",
        component: () => import("./views/Mine.vue"),
        meta: { title: "我的", description: "查看账号信息和常用入口。", navKey: "mine" },
      },
      {
        path: "wrongbook",
        name: "wrongbook",
        component: () => import("./views/WrongBook.vue"),
        meta: { title: "错题本", description: "集中复盘错题。", navKey: "mine", parent: "mine" },
      },
      {
        path: "announcements",
        name: "announcements",
        component: () => import("./views/Announcements.vue"),
        meta: { title: "更新公告", navKey: "mine", parent: "mine" },
      },
      {
        path: "chat",
        name: "chat",
        component: () => import("./views/Chat.vue"),
        meta: { title: "AI 对话练习", description: "追问知识点，适合碎片复习。", navKey: "ai" },
      },
      {
        path: "study-overview",
        name: "study-overview",
        component: () => import("./views/StudyOverview.vue"),
        meta: { title: "学习概览", description: "学习数据和复习建议一览。", navKey: "mine", parent: "mine" },
      },
    ],
  },
  {
    path: "/login",
    component: AuthLayout,
    meta: { guest: true },
    children: [{ path: "", name: "login", component: () => import("./views/auth/LoginView.vue") }],
  },
  {
    path: "/register",
    component: AuthLayout,
    meta: { guest: true },
    children: [{ path: "", name: "register", component: () => import("./views/auth/RegisterView.vue") }],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) return savedPosition;
    return { top: 0, behavior: "smooth" };
  },
});

router.beforeEach(async (to) => {
  const token = getToken();

  if (to.matched.some((route) => route.meta.requiresAuth) && !token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  if (to.matched.some((route) => route.meta.guest) && token) {
    const redirect = to.query.redirect;
    if (
      redirect &&
      typeof redirect === "string" &&
      redirect.startsWith("/") &&
      !redirect.startsWith("/login") &&
      !redirect.startsWith("/register")
    ) {
      return { path: redirect };
    }
    return { name: "home" };
  }

  const requiredPermission = to.matched
    .map((route) => route.meta.requiresPermission)
    .find((permission): permission is string => typeof permission === "string");

  if (requiredPermission && token) {
    const auth = useAuthStore();
    if (!auth.user) await auth.fetchProfile();
    if (!auth.can(requiredPermission)) return { name: "home" };
  }
});

export default router;
