import { expect, test as base, type Page, type Route } from "@playwright/test";

export const FIXED_NOW = Date.parse("2026-07-14T08:00:00.000Z");

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

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json; charset=utf-8",
    body: JSON.stringify(body),
  });
}

async function handleApi(route: Route): Promise<void> {
  const request = route.request();
  if (!(["xhr", "fetch"] as string[]).includes(request.resourceType())) {
    await route.continue();
    return;
  }

  const url = new URL(request.url());
  const path = url.pathname;
  const method = request.method();

  if (path === "/auth/me") {
    await json(route, {
      id: 42,
      username: "林同学",
      role: "student",
      permissions: ["course:read", "course:create", "exam:take", "exam:view_result", "exam:view_leaderboard", "import:use"],
    });
    return;
  }
  if (path === "/courses/mine") {
    await json(route, courses);
    return;
  }
  if (path === "/courses/9") {
    await json(route, courses[0]);
    return;
  }
  if (path === "/practice/stats") {
    await json(route, {
      today_count: 12,
      total_count: 168,
      correct_count: 132,
      wrong_count: 36,
      accuracy_rate: 0.786,
      recent_count_7d: 48,
    });
    return;
  }
  if (path === "/practice/review/today") {
    await json(route, { due_count: 8, wrong_count: 5, weak_types: [], recommended_modes: ["spaced_repeat"] });
    return;
  }
  if (path === "/practice/insights/weak-types") {
    await json(route, [{ question_type: "multiple_choice", total_attempts: 20, wrong_attempts: 8, error_rate: 0.4 }]);
    return;
  }
  if (path === "/practice/random" && method === "GET") {
    if (url.searchParams.has("exclude_ids")) {
      await json(route, { detail: "没有更多题目" }, 404);
    } else {
      await json(route, practiceQuestion);
    }
    return;
  }
  if (path === "/practice/submit" && method === "POST") {
    await json(route, {
      is_correct: true,
      correct_answer: "A",
      analysis: practiceQuestion.analysis,
      wrongbook_recorded: false,
    });
    return;
  }
  if (path === "/analytics/daily-activity") {
    await json(route, [
      { date: "2026-07-12", count: 10 },
      { date: "2026-07-13", count: 14 },
      { date: "2026-07-14", count: 12 },
    ]);
    return;
  }
  if (path === "/analytics/type-distribution") {
    await json(route, [{ question_type: "single_choice", total_count: 70, correct_count: 58, wrong_count: 12, accuracy_rate: 0.829 }]);
    return;
  }
  if (path === "/tags/accuracy") {
    await json(route, [{ tag_id: 1, tag_name: "网络层", total_count: 18, correct_count: 11, accuracy_rate: 0.611 }]);
    return;
  }
  if (path === "/analytics/streak") {
    await json(route, { current_streak: 7, longest_streak: 16, last_practiced_date: "2026-07-14" });
    return;
  }
  if (path === "/recommendations/today") {
    await json(route, {
      weak_tags: [{ tag_id: 1, tag_name: "网络层", total_count: 18, correct_count: 11, accuracy_rate: 0.611 }],
      weak_types: [],
      due_count: 8,
      due_question_ids: [91],
      recommended_modes: ["spaced_repeat"],
    });
    return;
  }
  if (path === "/analytics/teacher/courses") {
    await json(route, []);
    return;
  }
  if (path === "/exams/7" && method === "GET") {
    await json(route, exam);
    return;
  }
  if (path === "/exams/7/start" && method === "POST") {
    await json(route, {
      id: 7001,
      exam_id: 7,
      user_id: 42,
      started_at: "2026-07-14T07:50:00.000Z",
      submitted_at: null,
      score: null,
    });
    return;
  }
  if (path === "/exams/7/submit" && method === "POST") {
    await json(route, {
      exam_id: 7,
      submission_id: 7001,
      score: 50,
      total_score: 100,
      correct_count: 1,
      wrong_count: 1,
      accuracy_rate: 50,
      submitted_at: "2026-07-14T08:00:00.000Z",
    });
    return;
  }

  await json(route, { detail: `Unhandled visual fixture endpoint: ${method} ${path}` }, 404);
}

export type SurfaceName =
  | "home"
  | "course-list"
  | "course-practice"
  | "ai-import"
  | "exam-take"
  | "practice-complete"
  | "exam-complete"
  | "mine";

export const surfaces: Array<{ name: SurfaceName; referencePage: string }> = [
  { name: "home", referencePage: "home" },
  { name: "course-list", referencePage: "courses" },
  { name: "course-practice", referencePage: "course-practice" },
  { name: "ai-import", referencePage: "import" },
  { name: "exam-take", referencePage: "exam-take" },
  { name: "practice-complete", referencePage: "practice-complete" },
  { name: "exam-complete", referencePage: "exam-complete" },
  { name: "mine", referencePage: "mine" },
];

export async function prepareSurface(page: Page, surface: SurfaceName): Promise<void> {
  // Completion surfaces must start from a newly mounted session. The review
  // command intentionally reuses one Page, and navigating to an identical URL
  // does not remount Vue Router components.
  if (surface === "practice-complete" || surface === "exam-complete") {
    await page.goto("/");
  }

  if (surface === "home") await page.goto("/");
  if (surface === "course-list") await page.goto("/courses");
  if (surface === "course-practice" || surface === "practice-complete") {
    await page.goto("/courses/9/practice?autostart=1");
  }
  if (surface === "ai-import") await page.goto("/import");
  if (surface === "exam-take" || surface === "exam-complete") await page.goto("/exams/7/take");
  if (surface === "mine") await page.goto("/mine");

  if (surface === "practice-complete") {
    await expect(page.locator("[data-reference-page='course-practice'] .practice-option-card").first()).toBeVisible();
    await page.locator("[data-reference-page='course-practice'] .practice-option-card").first().click();
  }

  if (surface === "exam-complete") {
    await expect(page.locator("[data-reference-page='exam-take'] .option-button").first()).toBeVisible();
    await page.locator("[data-reference-page='exam-take'] .option-button").first().click();
    await page.locator("[data-reference-page='exam-take'] .submit-button").click();
  }

  const pageId = surfaces.find((item) => item.name === surface)?.referencePage;
  if (!pageId) throw new Error(`Unknown visual surface: ${surface}`);
  await expect(page.locator(`[data-reference-page='${pageId}']`)).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
        caret-color: transparent !important;
      }
    `,
  });
  await page.waitForTimeout(50);
}

type VisualFixtures = {
  mockedPage: Page;
};

export const test = base.extend<VisualFixtures>({
  mockedPage: async ({ page }, use) => {
    await page.addInitScript((fixedNow) => {
      const NativeDate = Date;
      class FixedDate extends NativeDate {
        constructor(...args: ConstructorParameters<typeof Date>) {
          super(...(args.length ? args : [fixedNow]));
        }
        static now() {
          return fixedNow;
        }
      }
      Object.setPrototypeOf(FixedDate, NativeDate);
      window.Date = FixedDate as DateConstructor;
      window.localStorage.setItem("xuexibao_token", "visual-test-token");
      window.localStorage.setItem("xuexibao-theme", "light");
      window.localStorage.removeItem("xuexibao:active-import-task");
    }, FIXED_NOW);
    await page.route("**/*", handleApi);
    await use(page);
  },
});

export { expect };
