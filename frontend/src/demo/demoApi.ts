// Demo-mode API — only active in VITE_DEMO=1 builds.
//
// Swaps the shared axios instance's adapter for an in-app mock so a static
// build (e.g. GitHub Pages) runs end-to-end with no backend. The payloads
// mirror e2e/visual-fixture.ts (the same data the visual test suite uses).
// Production builds never import this file: main.ts only loads it when
// import.meta.env.VITE_DEMO === "1".

import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";
import request from "../api/request";

const courses = [
  {
    id: 9,
    owner_id: 42,
    name: "计算机网络期末复习",
    description: "覆盖协议、网络层与常见应用题",
    subject: "计算机网络",
    visibility: "private",
    created_at: "2026-07-01T09:30:00+08:00",
    question_count: 36,
    practice_count: 18,
    last_practiced_at: "2026-07-14T07:20:00+08:00",
  },
  {
    id: 10,
    owner_id: 42,
    name: "数据结构核心题型",
    description: "树、图、排序与复杂度分析",
    subject: "数据结构",
    visibility: "public",
    created_at: "2026-06-20T10:00:00+08:00",
    question_count: 24,
    practice_count: 7,
    last_practiced_at: "2026-07-12T18:30:00+08:00",
  },
  {
    id: 11,
    owner_id: 42,
    name: "高等数学",
    description: "极限、微分与积分基础练习",
    subject: "数学",
    visibility: "private",
    created_at: "2026-06-16T09:00:00+08:00",
    question_count: 128,
    practice_count: 65,
    last_practiced_at: "2026-07-11T10:00:00+08:00",
  },
  {
    id: 12,
    owner_id: 42,
    name: "英语四级核心",
    description: "词汇、阅读与语法专项",
    subject: "英语",
    visibility: "private",
    created_at: "2026-06-09T09:00:00+08:00",
    question_count: 256,
    practice_count: 102,
    last_practiced_at: "2026-07-09T15:00:00+08:00",
  },
  {
    id: 13,
    owner_id: 42,
    name: "计算机基础",
    description: "计算机组成与操作系统基础",
    subject: "计算机基础",
    visibility: "public",
    created_at: "2026-06-03T09:00:00+08:00",
    question_count: 89,
    practice_count: 71,
    last_practiced_at: "2026-07-06T11:00:00+08:00",
  },
];

const practiceQuestion = {
  id: 91,
  owner_id: 42,
  course_id: 9,
  visibility: "private",
  source: "manual",
  created_at: "2026-07-01T09:30:00+08:00",
  subject: "计算机网络",
  chapter: "网络层",
  type: "single_choice",
  question: "在 TCP/IP 模型中，负责将数据包从源主机转发到目标主机的是哪一层？",
  options: {
    A: "网络层",
    B: "传输层",
    C: "应用层",
    D: "数据链路层",
  },
  answer: "A",
  analysis: "网络层通过 IP 协议完成寻址和路由转发。",
  difficulty: "normal",
};

const exam = {
  id: 7,
  title: "计算机网络阶段测验",
  description: "检验网络层与传输层知识掌握情况",
  course_id: 9,
  creator_id: 3,
  time_limit: 60,
  total_score: 100,
  is_shuffle: false,
  is_blind: false,
  status: "published",
  question_count: 2,
  created_at: "2026-07-10T12:00:00+08:00",
  questions: [
    {
      id: 701,
      question_id: 91,
      question_type: "single_choice",
      question: "在 TCP/IP 模型中，负责将数据包从源主机转发到目标主机的是哪一层？",
      options: { A: "网络层", B: "传输层", C: "应用层", D: "数据链路层" },
      score: 50,
      order_index: 1,
    },
    {
      id: 702,
      question_id: 92,
      question_type: "single_choice",
      question: "TCP 建立连接时需要完成几次握手？",
      options: { A: "一次", B: "两次", C: "三次", D: "四次" },
      score: 50,
      order_index: 2,
    },
  ],
};

const demoUser = {
  id: 42,
  username: "林同学",
  role: "student",
  permissions: ["course:read", "course:create", "exam:take", "exam:view_result", "exam:view_leaderboard", "import:use"],
};

const demoToken = { access_token: "demo-token", token: "demo-token", token_type: "bearer" };

function ok(config: InternalAxiosRequestConfig, data: unknown, status = 200): AxiosResponse {
  return { data, status, statusText: "OK", headers: {}, config } as AxiosResponse;
}

function fail(config: InternalAxiosRequestConfig, status: number, detail: string): Promise<never> {
  const error = new Error(detail) as Error & {
    response?: unknown;
    config?: unknown;
    isAxiosError?: boolean;
  };
  error.response = { status, data: { detail }, headers: {}, config };
  error.config = config;
  error.isAxiosError = true;
  return Promise.reject(error);
}

function route(config: InternalAxiosRequestConfig): Promise<AxiosResponse> {
  const method = (config.method || "get").toLowerCase();
  let raw = config.url || "";
  let query = new URLSearchParams();
  if (raw.startsWith("http")) {
    const parsed = new URL(raw);
    raw = parsed.pathname;
    query = parsed.searchParams;
  } else if (raw.includes("?")) {
    const [pathname, search] = raw.split("?");
    raw = pathname;
    query = new URLSearchParams(search || "");
  }
  const path = raw.length > 1 ? raw.replace(/\/+$/, "") : raw;
  const params = (config.params || {}) as Record<string, unknown>;
  const hasParam = (key: string) => params[key] !== undefined || query.has(key);

  let body: unknown = config.data;
  if (typeof body === "string") {
    try {
      body = JSON.parse(body);
    } catch {
      body = {};
    }
  }
  const bodyRecord = (body || {}) as Record<string, unknown>;

  // Auth: any credentials work in the demo; the guest entry returns a token too.
  if (path === "/auth/me") return Promise.resolve(ok(config, demoUser));
  if (path === "/auth/login" && method === "post") return Promise.resolve(ok(config, demoToken));
  if (path === "/auth/guest" && method === "post") return Promise.resolve(ok(config, demoToken, 201));
  if (path === "/auth/register" && method === "post") return Promise.resolve(ok(config, demoToken, 201));
  if (path === "/auth/logout") return Promise.resolve(ok(config, null));

  if (path === "/courses/mine" || path === "/courses") return Promise.resolve(ok(config, courses));
  const courseMatch = path.match(/^\/courses\/(\d+)$/);
  if (courseMatch) {
    const course = courses.find((item) => item.id === Number(courseMatch[1])) || courses[0];
    return Promise.resolve(ok(config, course));
  }
  if (/^\/courses\/\d+\/questions$/.test(path) || path === "/questions") {
    return Promise.resolve(ok(config, [practiceQuestion]));
  }
  if (path === "/library/public") return Promise.resolve(ok(config, courses));

  if (path === "/imports/tasks" && method === "post") {
    return Promise.resolve(
      ok(config, {
        id: "visual-import-preview-task",
        status: "ready",
        source_filename: "very-long-source-file-name-for-mobile-import-layout-check.docx",
        course_id: null,
        course_name: "",
        progress_current: 1,
        progress_total: 1,
        questions: [{ id: 901, type: "short_answer", question: "Explain the result.", answer: "Answer" }],
        suggested_course_name: "A very long course name that must never expand the preview layout on a phone",
        warnings: [],
        total_valid: 1,
        total_invalid: 0,
        timing: null,
        error_message: "",
        created_at: null,
        started_at: null,
        finished_at: null,
      }),
    );
  }

  if (path === "/practice/stats") {
    return Promise.resolve(
      ok(config, {
        today_count: 12,
        total_count: 168,
        correct_count: 132,
        wrong_count: 36,
        accuracy_rate: 0.786,
        recent_count_7d: 48,
      }),
    );
  }
  if (path === "/practice/review/today") {
    return Promise.resolve(ok(config, { due_count: 8, wrong_count: 5, weak_types: [], recommended_modes: ["spaced_repeat"] }));
  }
  if (path === "/practice/review/questions") return Promise.resolve(ok(config, [practiceQuestion]));
  if (path === "/practice/insights/weak-types") {
    return Promise.resolve(ok(config, [{ question_type: "multiple_choice", total_attempts: 20, wrong_attempts: 8, error_rate: 0.4 }]));
  }
  if (path === "/practice/random" && method === "get") {
    if (hasParam("exclude_ids")) return fail(config, 404, "没有更多题目");
    return Promise.resolve(ok(config, practiceQuestion));
  }
  if ((path === "/practice/submit" || path === "/practice/review/submit") && method === "post") {
    const isCorrect = String(bodyRecord.user_answer ?? "") === practiceQuestion.answer;
    return Promise.resolve(
      ok(config, {
        is_correct: isCorrect,
        correct_answer: practiceQuestion.answer,
        analysis: practiceQuestion.analysis,
        wrongbook_recorded: !isCorrect,
      }),
    );
  }

  if (path === "/analytics/daily-activity") {
    return Promise.resolve(
      ok(config, [
        { date: "2026-07-12", count: 10 },
        { date: "2026-07-13", count: 14 },
        { date: "2026-07-14", count: 12 },
      ]),
    );
  }
  if (path === "/analytics/type-distribution") {
    return Promise.resolve(ok(config, [{ question_type: "single_choice", total_count: 70, correct_count: 58, wrong_count: 12, accuracy_rate: 0.829 }]));
  }
  if (path === "/tags/accuracy") {
    return Promise.resolve(ok(config, [{ tag_id: 1, tag_name: "网络层", total_count: 18, correct_count: 11, accuracy_rate: 0.611 }]));
  }
  if (path === "/analytics/streak") {
    return Promise.resolve(ok(config, { current_streak: 7, longest_streak: 16, last_practiced_date: "2026-07-14" }));
  }
  if (path === "/analytics/teacher/courses" || path === "/analytics/owner/courses") {
    return Promise.resolve(ok(config, []));
  }
  if (path === "/recommendations/today") {
    return Promise.resolve(
      ok(config, {
        weak_tags: [{ tag_id: 1, tag_name: "网络层", total_count: 18, correct_count: 11, accuracy_rate: 0.611 }],
        weak_types: [],
        due_count: 8,
        due_question_ids: [91],
        recommended_modes: ["spaced_repeat"],
      }),
    );
  }

  if (path === "/exams" || path === "/exams/mine") return Promise.resolve(ok(config, [exam]));
  if (/^\/exams\/\d+$/.test(path) && method === "get") return Promise.resolve(ok(config, exam));
  if (/^\/exams\/\d+\/start$/.test(path) && method === "post") {
    return Promise.resolve(
      ok(config, { id: 7001, exam_id: 7, user_id: 42, started_at: "2026-07-14T07:50:00.000Z", submitted_at: null, score: null }),
    );
  }
  if (/^\/exams\/\d+\/submit$/.test(path) && method === "post") {
    return Promise.resolve(
      ok(config, {
        exam_id: 7,
        submission_id: 7001,
        score: 50,
        total_score: 100,
        correct_count: 1,
        wrong_count: 1,
        accuracy_rate: 50,
        submitted_at: "2026-07-14T08:00:00.000Z",
      }),
    );
  }

  if (path === "/study-groups" || path === "/study-groups/mine") return Promise.resolve(ok(config, []));
  if (path === "/bookmarks") return Promise.resolve(ok(config, []));
  if (path === "/wrongbook") return Promise.resolve(ok(config, []));

  return fail(config, 404, "演示版未覆盖该接口");
}

export function installDemoApi(): void {
  request.defaults.adapter = (config) => route(config);
}
