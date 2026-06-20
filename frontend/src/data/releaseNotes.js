/**
 * 更新公告数据
 *
 * 每次修 bug 或增加功能必须在此新增一条公告。
 * 详见 docs/RELEASE_NOTE_GUIDE.md。
 *
 * @type {Array<{id:string, date:string, type:string, title:string, items:string[]}>}
 */
export const releaseNotes = [
  {
    id: "2026-06-20-nav-return",
    date: "2026-06-20",
    type: "修复",
    title: "修复导航返回体验",
    items: [
      "修复从首页进入学习概览后返回位置不正确的问题",
      "优化底部导航切换，减少多余历史记录",
      "精简重复入口，让页面层级更清晰",
    ],
  },
  {
    id: "2026-06-20-nav-study-overview",
    date: "2026-06-20",
    type: "优化",
    title: "优化导航与学习概览",
    items: [
      "底部导航新增 AI 对话入口",
      "练习入口移至首页",
      "我的页新增学习概览入口",
    ],
  },
];
