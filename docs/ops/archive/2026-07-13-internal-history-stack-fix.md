# 学习宝内部导航历史栈收口

- 执行时间：2026-07-13
- 执行窗口：Codex
- 任务目标：从根因减少前端内部 history entry，统一使用 replace 和来源感知返回，降低微信/iOS WebView 原生历史工具栏被激活的概率。
- 允许修改：`frontend/src` 导航相关页面、路由辅助 composable、导航测试、`releaseNotes.ts`、PWA/帮助说明与本操作留档。
- 实际修改：新增 `useAppNavigation`，将底部导航、首页/我的入口、题库/公共题库/练习/AI 导入/认证/考试页面的内部跳转统一为 replace；补充 `from` 白名单与来源返回测试；增加 v2.4.1 公告；补充 PWA standalone 使用说明。
- 导航规则：底部五项重复点击不导航；详情页按 `home`、`mine`、`courses`、`public-library`、`practice`、`import` 白名单来源返回；练习答题过程保持本地状态，不写入路由历史。
- 验证：`npm.cmd run lint` 通过；`npm.cmd run test -- --run` 通过（30 个测试文件，104 项）；`npm.cmd run build` 通过；`git diff --check` 通过；生产源码未发现 `router.push/back/go`、`history.back/go/pushState` 或 `location.href` 导航调用。
- 后端：零改动。
- 真机验收：未执行真实微信/iOS WebView 操作；已完成源码、单元测试、构建和 manifest 静态检查。原生工具栏不能由网页 CSS 隐藏。
- Commit：待完成。
- Push：待完成。
- 遗留风险：需在真实微信/iOS WebView 按人工路径确认原生工具栏实际激活频率；PWA manifest 已为 `standalone`，`start_url` 为 `/` 且图标存在。
- 下一步：归档本记录，提交并推送当前分支。
