import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { getToken } from "./api/request";
import AuthLayout from "./layouts/AuthLayout.vue";
import { useAuthStore } from "./stores/auth";
import LoginView from "./views/auth/LoginView.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: () => import("./layouts/AppLayout.vue"),
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        name: "home",
        component: () => import("./views/Home.vue"),
        meta: { title: "首页", description: "快速进入题库、AI 导入和练习流程。", navKey: "home", keepAlive: true },
      },
      { path: "questions", redirect: "/courses" },
      {
        path: "courses",
        name: "courses",
        component: () => import("./views/CourseList.vue"),
        meta: { title: "我的题库", description: "选择题库开始练习。", navKey: "list", keepAlive: true },
      },
      {
        path: "courses/:courseId",
        name: "course-detail",
        component: () => import("./views/CourseDetail.vue"),
        meta: { title: "题库题目", navKey: "list", parent: "courses" },
      },
      {
        path: "shared-courses/:token",
        name: "shared-course",
        component: () => import("./views/SharedCourse.vue"),
        meta: { title: "分享题库", navKey: "list", parent: "courses" },
      },
      {
        path: "courses/:courseId/practice",
        alias: "/practice/:courseId",
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
        meta: {
          title: "AI 导入",
          description: "上传资料或粘贴 JSON，把题目整理进题库。",
          navKey: "import",
          keepAlive: true,
        },
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
        meta: {
          title: "创建考试",
          description: "从题库选择题目组卷。",
          navKey: "home",
          parent: "exams",
        },
      },
      {
        path: "exams/:examId/leaderboard",
        name: "exam-leaderboard",
        component: () => import("./views/exam/ExamLeaderboard.vue"),
        meta: {
          title: "考试排行榜",
          navKey: "home",
          parent: "exam-detail",
        },
      },
      {
        path: "exams/:examId/analytics",
        name: "exam-analytics",
        component: () => import("./views/exam/ExamAnalytics.vue"),
        meta: { title: "考试分析", navKey: "home", parent: "exam-detail" },
      },
      {
        path: "exams/share/:shareCode",
        name: "exam-share-link",
        component: () => import("./views/exam/ExamShareLink.vue"),
        meta: { title: "打开分享考试", navKey: "home", parent: "exams" },
      },
      {
        path: "exams/:examId",
        name: "exam-detail",
        component: () => import("./views/exam/ExamDetail.vue"),
        meta: { title: "考试详情", navKey: "home", parent: "exams" },
      },
      {
        path: "exams/:examId/take",
        alias: "/exam/:examId",
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
        path: "admin/feedback",
        name: "admin-feedback",
        component: () => import("./views/admin/AdminFeedback.vue"),
        meta: { title: "反馈处理", navKey: "mine", parent: "admin-dashboard", requiresPermission: "stats:view_global" },
      },
      {
        path: "mine",
        alias: "/profile",
        name: "mine",
        component: () => import("./views/Mine.vue"),
        meta: { title: "我的", description: "查看账号信息和常用入口。", navKey: "mine", keepAlive: true },
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
        path: "help-feedback",
        name: "help-feedback",
        component: () => import("./views/HelpFeedback.vue"),
        meta: { title: "帮助与反馈", navKey: "mine", parent: "mine" },
      },
      {
        path: "bookmarks",
        name: "bookmarks",
        component: () => import("./views/bookmark/BookmarkList.vue"),
        meta: { title: "我的收藏", navKey: "mine", parent: "mine" },
      },
      {
        path: "chat",
        name: "chat",
        component: () => import("./views/Chat.vue"),
        meta: { title: "AI 对话练习", description: "追问知识点，适合碎片复习。", navKey: "home", parent: "home" },
      },
      {
        path: "study-overview",
        name: "study-overview",
        component: () => import("./views/StudyOverview.vue"),
        meta: { title: "学习概览", description: "学习数据和复习建议一览。", navKey: "mine", parent: "mine" },
      },
      {
        path: "study-groups",
        name: "study-groups",
        component: () => import("./views/StudyGroups.vue"),
        meta: { title: "学习小组", description: "创建或加入小组，共享题库与考试。", navKey: "mine", parent: "mine" },
      },
    ],
  },
  {
    path: "/login",
    component: AuthLayout,
    meta: { guest: true },
    children: [{ path: "", name: "login", component: LoginView }],
  },
  {
    path: "/register",
    component: AuthLayout,
    meta: { guest: true },
    children: [{ path: "", name: "register", component: () => import("./views/auth/RegisterView.vue") }],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("./views/NotFound.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) return savedPosition;
    // Page transitions already provide low-frequency feedback. Smooth scrolling
    // here competes with them and makes mobile navigation feel delayed.
    return { top: 0 };
  },
});

router.beforeEach(async (to) => {
  const token = getToken();
  const auth = useAuthStore();

  if (to.matched.some((route) => route.meta.requiresAuth)) {
    if (!auth.user) {
      // 前端 token 被微信 WebView 清掉时，后端 HttpOnly Cookie 仍可能有效。
      // 因此首次进入受保护路由必须尝试一次 /auth/me，而不能以 token 是否可读
      // 作为会话恢复的前置条件。
      if (!auth.profileInitialized && !auth.explicitlyLoggedOut) {
        await auth.fetchProfile({ silent: true });
      }
      if (!auth.user) {
        return { name: "login", query: { redirect: to.fullPath } };
      }
    }
  }

  if (to.matched.some((route) => route.meta.guest) && (token || auth.user)) {
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

  if (requiredPermission && (token || auth.user)) {
    if (!auth.user) await auth.fetchProfile();
    if (!auth.can(requiredPermission)) return { name: "home" };
  }
});

export default router;
