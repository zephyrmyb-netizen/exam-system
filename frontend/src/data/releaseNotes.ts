export interface ReleaseNote {
  id: string;
  version: string;
  date: string;
  type: string;
  title: string;
  items: string[];
}

/**
 * Release notes shown in the app.
 *
 * Version rules:
 * - Small fix: v1.1.1 -> v1.1.2
 * - Medium update: v1.1.2 -> v1.2.1
 * - Major release: v2.0.0
 */
export const releaseNotes: ReleaseNote[] = [
  {
    id: "v2.1.0-ai-import-ppt-image",
    version: "v2.1.0",
    date: "2026-06-30",
    type: "新增",
    title: "AI 导入支持 PPT 与图片识别",
    items: [
      "AI 导入新增图片题目识别，支持 PNG、JPG、WEBP。",
      "增强 PPTX 导入，支持读取页内文字并识别内嵌图片题目。",
      "优化导入页文件类型提示、解析进度和失败提示。",
      "旧版 PPT 会提示另存为 PPTX，避免用户反复上传失败。",
    ],
  },
  {
    id: "v2.0.1-mobile-practice-immersive",
    version: "v2.0.1",
    date: "2026-06-29",
    type: "修复",
    title: "移动端练习体验修复",
    items: [
      "修复刷题页底部导航遮挡问题",
      "修复练习页返回/结束入口重复问题",
      "优化手机端安全区域和页面比例",
      "减少底部导航触发浏览器历史控件的问题",
    ],
  },
  {
    id: "v2.0.0-major-release",
    version: "v2.0.0",
    date: "2026-06-29",
    type: "大版本",
    title: "学习宝 2.0 发布准备完成",
    items: [
      "完成题库、刷题、错题本、AI 导入、学习概览、考试模式、管理后台和个人中心的主流程整合。",
      "补齐收藏、导出、搜索、推荐、学习分析、PWA 基础和离线提交队列，为后续移动端体验继续打底。",
      "修复发布前工程化问题：前端 lint、后端 Ruff、前后端测试、安全检查和构建流程全部纳入上线验收。",
      "强化生产配置：生产环境必须显式设置 SECRET_KEY、INVITE_CODE、CORS_ORIGINS 和数据库密码，降低公开部署风险。",
      "修复 Nginx 生产代理范围，新增的考试、管理、标签、推荐、分析、导出和收藏接口都会正确转发到后端。",
    ],
  },
  {
    id: "v1.15.2-release-hardening",
    version: "v1.15.2",
    date: "2026-06-29",
    type: "修复",
    title: "大版本发布前稳定性收口",
    items: [
      "修复前端 lint 与后端 Ruff 检查未通过的问题，让发布前工程化检查回到干净状态。",
      "刷题提交在离线或网络中断时会先进入待同步队列，恢复网络后自动补交，减少练习记录丢失。",
      "补齐 AI 导入服务拆包的维护入口，保留旧接口兼容的同时方便后续按职责维护。",
    ],
  },
  {
    id: "v1.15.1-study-overview-charts",
    version: "v1.15.1",
    date: "2026-06-29",
    type: "优化",
    title: "学习概览补齐热力图与课程分析",
    items: [
      "学习概览新增刷题热力图和课程使用统计，让学习数据更接近完整仪表盘。",
      "清理学习概览与图表组件中的乱码文案，移动端查看更自然。",
      "教师课程统计接口改为可选展示，普通用户权限不足时不影响学习概览加载。",
    ],
  },
  {
    id: "v1.15.0-phase4-frontend-tools",
    version: "v1.15.0",
    date: "2026-06-29",
    type: "新增",
    title: "补齐搜索、收藏、导出和离线基础",
    items: [
      "新增全局搜索入口，支持快速查找题库与题目。",
      "新增我的收藏页面，并在课程详情补齐题库导出入口。",
      "新增 PWA 基础配置和离线队列骨架，为离线刷题与自动同步打基础。",
      "统一网页标题和应用清单为学习宝，避免安装到桌面后显示旧名称或乱码。",
    ],
  },
  {
    id: "v1.13.0-phase4-recommend-analytics",
    version: "v1.13.0",
    date: "2026-06-28",
    type: "新增",
    title: "接入智能推荐与学习分析接口",
    items: [
      "新增今日推荐接口，综合薄弱知识点、薄弱题型和到期复习生成练习建议。",
      "新增薄弱题目接口，按个人错题记录排序，方便后续做针对性练习入口。",
      "新增学习分析接口，支持每日刷题趋势、题型正确率、连续学习天数、课程统计和考试分数分布。",
    ],
  },
  {
    id: "v1.11.3-phase3-exam-frontend",
    version: "v1.11.3",
    date: "2026-06-28",
    type: "新增",
    title: "接入前端考试模式",
    items: [
      "新增考试列表、考试详情、创建考试、考试答题和考试结果页面。",
      "首页快捷入口接入正式考试，教师和管理员可以从题库组卷并发布考试。",
      "考试答题页支持题号跳转、进度展示、左右键和滑动切题、数字键选择选项。",
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
      "引入 Tailwind、基础 UI 组件、主题状态和课程缓存，为后续页面统一改造打基础。",
      "重做首页、题库页、练习中心和我的页，修复乱码文案、重复题库展示和底部导航体验问题。",
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
];
