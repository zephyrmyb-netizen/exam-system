# 学习宝核心前端体验收口

- 执行时间：2026-07-13
- 执行窗口：Codex
- 任务目标：直接优化现有前端核心用户体验，收口移动端布局、练习、AI 导入、AI 对话、我的页面、导航返回和主题状态。
- 允许修改的文件：`frontend/src` 指定核心页面、组件、composables、stores、样式、测试与 `releaseNotes.ts`；本操作留档与索引。
- 实际修改的文件：`frontend/src/layouts/AppLayout.vue`、`frontend/src/style.css`、`frontend/src/views/CourseList.vue`、`frontend/src/views/CoursePractice.vue`、`frontend/src/views/Chat.vue`、`frontend/src/views/Mine.vue`、`frontend/src/components/practice/PracticeTopBar.vue`、`frontend/src/stores/theme.ts`、`frontend/src/data/releaseNotes.ts`、相关前端测试。
- 验证命令与结果：`cd frontend && npm.cmd run lint` 通过；`npm.cmd run test -- --run` 通过（28 个测试文件、92 项测试）；`npm.cmd run build` 通过；`git diff --check` 通过。静态检查确认 100vh/100dvh、安全区、16px 输入框、横向溢出约束和练习底部留白存在。浏览器/Playwright 视觉检查未执行，原因是本机未安装项目现有 Playwright/Puppeteer。
- Commit：待完成。
- Push：待完成。
- 遗留风险：未进行真实登录后端联调和 375/390/430 浏览器截图验收；后端零改动。
- 下一步：归档本记录，提交本轮前端改动并推送 `codex/phase4-differentiation`。
