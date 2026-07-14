# 首页 AI 入口与四项导航

- 执行时间：2026-07-13
- 执行窗口：Codex 主窗口
- 任务目标：将 AI 对话从底部导航移至首页紧凑入口，底部导航收为首页、题库、导入、我的四项。
- 允许修改的文件：首页、应用布局、路由元信息、对应前端测试、版本公告与本留档。
- 实际修改的文件：`frontend/src/layouts/AppLayout.vue`、`frontend/src/router.ts`、`frontend/src/views/Home.vue`、`frontend/src/layouts/__tests__/AppLayout.test.ts`、`frontend/src/views/__tests__/Home.ux.test.ts`、版本公告与本留档。
- 验证命令与结果：定向测试通过；`npm.cmd run test -- --run` 通过（36 文件、119 用例）；`npm.cmd run lint` 通过；`npm.cmd run build` 通过；`git diff --check` 待提交前执行。
- Commit：`235df3b feat: move AI chat entry to home`。
- Push：已推送至 `origin/codex/phase4-differentiation`。
- 遗留风险：仅迁移入口，不改变聊天、导入或练习接口与业务逻辑。
- 下一步：在手机端复验四项导航和首页 AI 入口。
