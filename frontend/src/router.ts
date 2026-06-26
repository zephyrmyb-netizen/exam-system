import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { getToken } from "./api/request";
import AppLayout from "./layouts/AppLayout.vue";
import AuthLayout from "./layouts/AuthLayout.vue";
import Home from "./views/Home.vue";
import QuestionList from "./views/QuestionList.vue";
import ImportQuestions from "./views/ImportQuestions.vue";
import Mine from "./views/Mine.vue";
import WrongBook from "./views/WrongBook.vue";
import Announcements from "./views/Announcements.vue";
import Chat from "./views/Chat.vue";
import LoginView from "./views/auth/LoginView.vue";
import RegisterView from "./views/auth/RegisterView.vue";
import PracticeHub from "./views/PracticeHub.vue";
import PracticeHistory from "./views/PracticeHistory.vue";
import WrongPractice from "./views/WrongPractice.vue";
import DuePractice from "./views/DuePractice.vue";
import CourseList from "./views/CourseList.vue";
import CourseDetail from "./views/CourseDetail.vue";
import CoursePractice from "./views/CoursePractice.vue";
import PublicLibrary from "./views/PublicLibrary.vue";
import StudyOverview from "./views/StudyOverview.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    component: AppLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "",
        name: "home",
        component: Home,
        meta: {
          title: "首页",
          description: "快速进入题库、AI 导入和练习流程。",
          navKey: "home",
        },
      },
      {
        path: "questions",
        redirect: "/courses",
      },
      {
        path: "courses",
        name: "courses",
        component: CourseList,
        meta: {
          title: "我的题库",
          description: "选择题库开始练习。",
          navKey: "list",
        },
      },
      {
        path: "courses/:courseId",
        name: "course-detail",
        component: CourseDetail,
        meta: {
          title: "题库题目",
          navKey: "list",
          parent: "courses",
        },
      },
      {
        path: "courses/:courseId/practice",
        name: "course-practice",
        component: CoursePractice,
        meta: {
          title: "题库练习",
          navKey: "list",
          parent: "course-detail",
        },
      },
      {
        path: "public-library",
        name: "public-library",
        component: PublicLibrary,
        meta: {
          title: "公共题库",
          description: "公开分享的题目集。",
          navKey: "list",
          parent: "courses",
        },
      },
      {
        path: "import",
        name: "import",
        component: ImportQuestions,
        meta: {
          title: "AI 导入",
          description: "上传资料或粘贴 JSON，把题目整理进题库。",
          navKey: "import",
        },
      },
      {
        path: "practice",
        name: "practice",
        component: PracticeHub,
        meta: {
          title: "练习",
          description: "查看今日数据，选择练习方式，开始专注练习。",
          navKey: "",
        },
      },
      {
        path: "practice/wrong",
        name: "practice-wrong",
        component: WrongPractice,
        meta: {
          title: "错题强化",
          description: "集中攻克薄弱环节，逐题复盘。",
          navKey: "",
          parent: "practice",
        },
      },
      {
        path: "practice/due",
        name: "practice-due",
        component: DuePractice,
        meta: {
          title: "到期复习",
          description: "今日到期题目，逐题巩固。",
          navKey: "",
          parent: "practice",
        },
      },
      {
        path: "practice/history",
        name: "practice-history",
        component: PracticeHistory,
        meta: {
          title: "练习记录",
          description: "查看历史练习详情、正确率和时间。",
          navKey: "",
          parent: "mine",
        },
      },
      {
        path: "mine",
        name: "mine",
        component: Mine,
        meta: {
          title: "我的",
          description: "查看账号信息，并进入常用复盘入口。",
          navKey: "mine",
        },
      },
      {
        path: "wrongbook",
        name: "wrongbook",
        component: WrongBook,
        meta: {
          title: "错题本",
          description: "集中复盘错题，及时清理已掌握内容。",
          navKey: "mine",
          parent: "mine",
        },
      },
      {
        path: "announcements",
        name: "announcements",
        component: Announcements,
        meta: {
          title: "更新公告",
          navKey: "mine",
          parent: "mine",
        },
      },
      {
        path: "chat",
        name: "chat",
        component: Chat,
        meta: {
          title: "AI 对话练习",
          description: "像聊天一样追问知识点，适合碎片复习。",
          navKey: "ai",
        },
      },
      {
        path: "study-overview",
        name: "study-overview",
        component: StudyOverview,
        meta: {
          title: "学习概览",
          description: "学习数据和复习建议一览。",
          navKey: "mine",
          parent: "mine",
        },
      },
    ],
  },
  {
    path: "/login",
    component: AuthLayout,
    meta: { guest: true },
    children: [
      {
        path: "",
        name: "login",
        component: LoginView,
      },
    ],
  },
  {
    path: "/register",
    component: AuthLayout,
    meta: { guest: true },
    children: [
      {
        path: "",
        name: "register",
        component: RegisterView,
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    return { top: 0, behavior: "smooth" };
  },
});

router.beforeEach((to) => {
  const token = getToken();

  if (to.matched.some((route) => route.meta.requiresAuth) && !token) {
    return {
      name: "login",
      query: { redirect: to.fullPath },
    };
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
});

export default router;
