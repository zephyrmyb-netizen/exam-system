# 前端可靠性、离线与可访问性修复

- 执行时间：2026-07-13
- 执行窗口：Codex 主窗口
- 任务目标：处理验收报告中可复现的 P0/P1 前端问题，包括考试退出路径、PWA API 缓存、离线状态可见性、搜索防抖、构建边界与可访问性。
- 实际修改：
  - 考试答题页补充“退出考试”确认入口；答题网格触达区提升至 44px。
  - Service Worker 不再缓存 API 响应，避免刷新后继续展示陈旧的学习数据。
  - 练习离线队列状态在应用内可见，恢复网络后自动尝试同步。
  - 错题本和题目列表关键词搜索改为防抖；筛选输入补充可访问名称。
  - 统一文字、警告色和暗色模式 token；收紧前端类型；拆出第三方依赖构建分包。
  - 应用清单改用“学习宝”中文名称，并提供练习、错题本快捷入口。
- 验证：`npm.cmd run lint` 通过；`npm.cmd run test -- --run` 通过（36 文件、118 用例）；`npm.cmd run build` 通过；`node --check frontend/public/sw.js` 通过；`python scripts/security_check.py` 通过（3/3）；`git diff --check` 通过。
- 依赖审计：`npm.cmd audit --json` 因仓库没有 lockfile 返回 `ENOLOCK`，本轮没有擅自生成 lockfile 或改动依赖。
- 后端影响：无。未改变 API 路径、返回结构、数据库或练习提交语义。
- 遗留风险：现有手写 Service Worker 仅保证 API 不被缓存；离线应用壳预缓存与 iOS PNG 图标需要结合正式静态托管方案单独完成。
- 功能提交：`bb9d164 fix: harden frontend reliability and accessibility`。
- Push：待本留档与公告提交后统一推送。
- 下一步：推送远端，并在真机完成离线切换、考试退出与 PWA 安装入口复验。
