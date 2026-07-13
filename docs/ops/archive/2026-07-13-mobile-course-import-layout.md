# 手机端题库与导入布局修复

- 执行时间：2026-07-13
- 执行窗口：Codex 主窗口
- 任务目标：修复题库页在 401-700px 宽度的横向溢出，并收紧 AI 解析中的导入页面布局。
- 允许修改的文件：`CourseList.vue`、`ImportQuestions.vue`、`ImportTaskMonitor.vue`、对应前端测试、版本公告与本留档。
- 实际修改的文件：`frontend/src/views/CourseList.vue`、`frontend/src/views/ImportQuestions.vue`、`frontend/src/components/import/ImportTaskMonitor.vue`、`frontend/src/views/__tests__/ImportQuestions.import.test.ts`、`frontend/src/data/releaseNotes.ts` 与本留档。
- 验证命令与结果：解析中紧凑状态和单一文件输入框的失败测试已复现；定向测试通过（2 文件、15 用例）；`npm.cmd run lint` 通过；`npm.cmd run test -- --run` 通过（36 文件、119 用例）；`npm.cmd run build` 通过；`git diff --check` 通过。
- Commit：`2de639f fix: stabilize mobile course and import layouts`。
- Push：已推送至 `origin/codex/phase4-differentiation`。
- 遗留风险：当前环境未安装 Playwright，仍需在真实手机 WebView 复验长题库名与长文件名。
- 下一步：在手机端复验题库与导入解析流程。
