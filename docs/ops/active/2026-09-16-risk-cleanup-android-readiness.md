# 风险处理与安卓端预留（网页端优先）

- 执行时间：2026-09-16
- 执行窗口：WorkBuddy (GLM)
- 任务目标：按项目所有者指示，先处理三个在途风险（在途工作区、双路由层、重复 venv），并确认网页端开发路径不会堵死安卓端上线；本轮不做安卓实现。
- 允许修改的文件：docs/ops/、项目记忆（.workbuddy/memory/）、backend/venv 删除（经项目自带 cleanup 脚本）。不修改 backend/、frontend/ 业务代码。
- 实际修改的文件：本文档；删除 backend/venv（未跟踪的重复虚拟环境，20M 残留）；backend/.venv/Scripts/python.exe 通过完整测试套件验证后保留。
- 验证命令与结果：
  - `backend\.venv\Scripts\python.exe -m pytest backend/tests -q` → **444 passed, 1 skipped**（含 Codex 在途改动的工作区，测试全绿）。
  - `npm.cmd run typecheck`（vue-tsc --noEmit）→ **零错误**。
  - `npm.cmd run lint` → **2 个错误**，均在 `frontend/src/components/common/ConfirmDialog.vue`（`HTMLButtonElement` no-undef）。该文件属于 Codex 窗口在途修改（git 状态 M），按多窗口规约本窗口不修复，留给该窗口或项目所有者收口。怀疑是 eslint 配置缺少 DOM lib 声明，属小问题。
  - `scripts/cleanup_local_artifacts.ps1 -IncludeDuplicateVenv` → 退出码 0，`backend/venv` 已移除，`.venv` 导入 fastapi/sqlalchemy 正常。
- Commit：暂不提交（工作区含 Codex 窗口在途改动，避免混窗提交）。
- Push：未推送。
- 遗留风险：Codex「现有功能清理与优化」任务仍在途，196 项未提交改动的收口仍需该窗口或项目所有者决策。
- 下一步：已全部完成（测试验证 → venv 清理 → 安卓清单）；后续见文末「下一步」。

## 项目决定（2026-09-16，项目所有者确认）

「刷题助手」为**学习宝仓库内的新阶段**（非独立新仓库），网页端先行，安卓端留口后上。

## 风险处理结论

| 风险 | 结论 | 状态 |
| --- | --- | --- |
| 在途工作区（196 项未提交） | 后端 444 测试全绿、类型检查零错误，工作区功能上是稳定的；仅 lint 有 2 个小错误（在 Codex 在途文件中）。**未提交**——按规约避免混窗提交，收口决策留给项目所有者/Codex 窗口。 | 已评估，挂起收口 |
| 双路由层 routers/ + api/ | 不是重复实现：main.py 混合挂载，api/ 是新模块层（配 repositories/），在途 diff 正在删除 api/ 下与 routers/ 冲突的副本（courses.py、practice.py 已标 D），方向正确。 | 已确认，随 Codex 任务自然收口 |
| 重复 venv | backend/venv（20M 残留）已按项目脚本删除；backend/.venv 验证可用。 | 已消除 |

## 安卓端预留清单（只留端口，不实现）

按项目所有者指示：网页端先行，安卓端只保证路不堵死。当前网页端已具备的安卓就绪项：

1. **认证**：后端收 HttpOnly Cookie + JWT Bearer 双模式（`backend/auth.py`）；前端 axios 已带 Bearer 拦截器（`frontend/src/api/request.ts`）。Capacitor WebView 走 Cookie，原生层可切 Bearer——无需后端改动。
2. **端点切换**：`VITE_API_BASE_URL` 环境变量即 App 端 API 地址开关；默认同源相对路径（nginx 反代）。
3. **CORS**：后端 `CORS_ORIGINS` 可配置；安卓端上线时需把 Capacitor WebView origin（如 `http://localhost` 或 `capacitor://localhost`）加入白名单，且不可用通配符（credentials 场景）。
4. **PWA 基础**：`frontend/index.html` 已含 `viewport-fit=cover`、`theme-color`、`manifest.webmanifest`、apple-mobile-web-app 元数据——移动端形态已就位。
5. **UI 形态**：Vue 3 移动端优先（底部四标签导航），套壳成本最低。

**后续上安卓时才需要做的事**（现在不做）：引入 Capacitor、持久化 token 策略（App 内登录态存储）、App 图标/启动屏、CORS 白名单更新、安卓签名打包。这些列入 `docs/` 待办即可。

## 下一步

- 网页端「刷题助手」新阶段开发（本项目仓库内），等 Codex 在途任务收口、工作区干净后从基线开始。
- `ConfirmDialog.vue` 的 2 个 lint 错误移交 Codex 窗口修复。
- 在途 196 项改动的提交/收口决策：留给项目所有者。

## 自查记录（2026-09-16 复核）

| 检查项 | 结果 |
| --- | --- |
| 留档完整性（本文件） | 通读复核，结构完整；修正两处过时的「下一步」表述，补记项目决定。 |
| INDEX.md 编辑 | diff 复核：本窗口仅新增 2026-09-16 一行；09-09 条目与 blocked 状态为 Codex 既有未提交改动，未被覆盖。 |
| backend/venv 删除 | 已确认目录不存在；`.venv` 导入 fastapi/sqlalchemy 正常（此前 444 测试亦通过）。 |
| 清理脚本副作用 | data/beta/backups 按"每前缀保留最近 5 个"规则收敛（beta 2 个、main 5 个），符合脚本设计，无过度删除。 |
| git diff --check | 干净（仅存量换行符警告，非本窗口引入）。 |
| .workbuddy/ 出现在 git status | 已加入 `.git/info/exclude`（本地排除，不动被 Codex 在途修改的 .gitignore，零冲突），`git check-ignore` 验证生效。 |
