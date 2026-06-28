export interface ReleaseNote {
  id: string;
  version: string;
  date: string;
  type: string;
  title: string;
  items: string[];
}

/**
 * 更新公告数据。
 *
 * 每次修复 bug 或优化现有功能，都在数组最前面新增一条。
 * 版本规则：
 * - 小修复：v1.1.1 -> v1.1.2
 * - 中等优化：v1.1.2 -> v1.2.1
 * - 大版本：v2.0.0
 */
export const releaseNotes: ReleaseNote[] = [
  {
    id: "v1.11.0-phase3-rbac-foundation",
    version: "v1.11.0",
    date: "2026-06-28",
    type: "新增",
    title: "补齐 Phase 3 权限地基",
    items: [
      "用户信息接口现在会返回默认学生角色和权限字段，为后续教师、管理员和考试模式做准备。",
      "新增后端 RBAC 权限服务，明确学生、教师、管理员的基础权限边界。",
      "Layered 课程 API 新增带权限校验的创建题库示范接口，并补充权限隔离测试。",
    ],
  },
  {
    id: "v1.10.2-backend-ruff-baseline",
    version: "v1.10.2",
    date: "2026-06-27",
    type: "优化",
    title: "补齐后端 Ruff 代码质量基线",
    items: [
      "整理后端导入、类型标注和未使用代码，让 Ruff 全量检查可以稳定通过。",
      "补充 Ruff 后端依赖，确保重新安装环境后也能执行同一套代码质量检查。",
    ],
  },
  {
    id: "v1.10.1-layered-courses-api",
    version: "v1.10.1",
    date: "2026-06-27",
    type: "优化",
    title: "补齐课程接口分层示范",
    items: [
      "新增独立的课程 API 薄路由示范，读取课程列表、我的课程和课程详情时走 service 层。",
      "补充课程 API 层独立测试，确保新旧路由共存时不影响现有接口。",
    ],
  },
  {
    id: "v1.10.0-phase2-architecture",
    version: "v1.10.0",
    date: "2026-06-27",
    type: "优化",
    title: "完成 Phase 2 架构升级与核心页面打磨",
    items: [
      "新增后端 repositories/services/api 分层骨架，并补充课程、练习统计相关测试。",
      "新增角色、考试、协作、标签、收藏、学习目标等后续阶段所需的数据模型和 Alembic 迁移。",
      "引入 Tailwind、基础 UI 组件、主题状态和课程缓存，为后续页面统一改造打地基。",
      "重做首页、题库页、练习中心和我的页，修复乱码文案、重复题库展示和底部导航体验问题。",
      "清理全局请求错误、登录注册、确认弹窗等公共文案，减少异常状态下的误解。",
    ],
  },
  {
    id: "v1.9.1-code-quality-split",
    version: "v1.9.1",
    date: "2026-06-27",
    type: "优化",
    title: "完成首轮代码质量拆分",
    items: [
      "拆分练习中心、题库详情和导入页的核心展示组件，降低后续维护成本。",
      "恢复 AI 导入、确认弹窗、题库导入相关提示文案，减少乱码和误解。",
      "补充练习中心组件测试，并保持前端测试与构建通过。",
    ],
  },
  {
    id: "v1.8.21-question-bank-wording",
    version: "v1.8.21",
    date: "2026-06-26",
    type: "优化",
    title: "统一题库文案",
    items: [
      "统一题库列表、题库详情和练习入口里的命名，减少课程与题库混用。",
      "优化空状态、弹窗和搜索提示，让导入、管理、练习路径更清晰。",
    ],
  },
  {
    id: "v1.8.8-ai-import-json-repair",
    version: "v1.8.8",
    date: "2026-06-26",
    type: "修复",
    title: "增强 AI 导入格式修复能力",
    items: [
      "AI 导入遇到普通文本响应时会尝试整理为 JSON，减少解析 0 题的情况。",
      "补充回归测试，防止 AI 返回格式异常时直接导入失败。",
    ],
  },
  {
    id: "v1.8.4-ai-import-progress-copy",
    version: "v1.8.4",
    date: "2026-06-25",
    type: "优化",
    title: "优化 AI 导入等待提示",
    items: [
      "AI 导入处理中会明确提示预计等待约 30 秒，大文件可能更久。",
      "切换页面后返回导入页时，仍会提示 AI 正在继续处理。",
    ],
  },
];
