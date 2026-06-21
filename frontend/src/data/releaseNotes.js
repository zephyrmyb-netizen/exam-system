/**
 * 更新公告数据
 *
 * 每次修复 bug 或优化现有功能，都在这里新增一条公告。
 * 最新版本放在数组最前面。
 *
 * @type {Array<{id:string, version:string, date:string, type:string, title:string, items:string[]}>}
 */
export const releaseNotes = [
  {
    id: "v1.5.3-ai-import-timeout-cleanup",
    version: "v1.5.3",
    date: "2026-06-22",
    type: "修复",
    title: "修复 AI 导入超时并清理项目结构",
    items: [
      "延长 AI 文件导入等待时间，减少大文件解析时直接超时的问题",
      "后端新增独立的 AI 导入分块与超时配置，避免和普通对话互相影响",
      "补充 README 中的协作、清理和 AI 导入配置说明",
    ],
  },
  {
    id: "v1.5.2-ai-import-chat-fix",
    version: "v1.5.2",
    date: "2026-06-22",
    type: "修复",
    title: "修复 AI 导入与对话稳定性",
    items: [
      "修复 AI 导入时切换页面后看不到解析进度的问题",
      "优化 AI 对话超时处理，减少 Mimo 模型回复较慢时的失败提示",
      "修复 AI 相关页面的乱码文案与重试状态显示",
    ],
  },
  {
    id: "v1.5.1-mobile-polish",
    version: "v1.5.1",
    date: "2026-06-20",
    type: "优化",
    title: "优化移动端导航与练习细节",
    items: [
      "底部导航改为悬浮样式，减少误触底部控件",
      "练习页新增未选择答案提示和换题入口",
      "导入题目前明确显示目标题库",
    ],
  },
  {
    id: "v1.4.1-courses-and-import",
    version: "v1.4.1",
    date: "2026-06-20",
    type: "优化",
    title: "优化题库与导入体验",
    items: [
      "导入前明确显示目标题库",
      "优化我的题库和公共题库层级",
      "导入成功后引导进入题库",
    ],
  },
  {
    id: "v1.3.1-ui-polish",
    version: "v1.3.1",
    date: "2026-06-20",
    type: "优化",
    title: "优化练习页与公告展示",
    items: [
      "优化练习页顶部信息和答题操作",
      "更新公告新增版本号展示",
      "精简练习方式选择，减少不可用入口干扰",
    ],
  },
  {
    id: "v1.2.1-practice-polish",
    version: "v1.2.1",
    date: "2026-06-20",
    type: "优化",
    title: "优化练习体验",
    items: [
      "优化练习页顶部信息和答题操作",
      "精简练习方式选择，减少不可用入口干扰",
      "修复错题强化进入后不自动加载的问题",
    ],
  },
  {
    id: "v1.1.1-nav-return",
    version: "v1.1.1",
    date: "2026-06-20",
    type: "修复",
    title: "修复导航返回体验",
    items: [
      "修复从首页进入学习概览后返回位置不正确的问题",
      "优化底部导航切换，减少多余历史记录",
      "精简重复入口，让页面层级更清晰",
    ],
  },
];
