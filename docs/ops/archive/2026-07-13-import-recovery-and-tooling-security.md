# 导入恢复与开发工具安全修复

- 执行时间：2026-07-13
- 执行窗口：Codex 主窗口
- 任务目标：补齐 AI 导入服务重启恢复、确认导入原子写入，并清除前端测试工具链已知依赖漏洞。

## 实际修改

- `backend/services/import_task_service.py`：服务启动时恢复排队或解析中的任务；中断的确认导入回到可确认状态，不会自动重放写入。
- `backend/main.py`、`backend/config.py`：在应用启动期有界恢复任务，支持用环境变量关闭或调整恢复数量。
- `backend/routers/imports.py`、`backend/crud_courses.py`、`backend/imports/import_orchestrator.py`：确认导入改为单次事务提交，失败后回滚并保留可重试状态。
- `backend/tests/conftest.py`、`backend/tests/test_import_tasks.py`：新增重启恢复、缺失文件和事务回滚覆盖。
- `frontend/package.json`、`frontend/package-lock.json`：升级 Vitest 与 happy-dom，清除已知测试工具链漏洞。
- `frontend/src/data/releaseNotes.ts`：新增 v2.7.2 公告。

## 验证

- 后端：`backend\.venv\Scripts\python.exe -m pytest backend\tests -q`，417 passed、1 skipped。
- 前端：`npm.cmd run lint`、`npm.cmd run test -- --run`、`npm.cmd run build` 均通过；34 个测试文件、115 项测试通过。
- 依赖：`npm.cmd audit --json`，0 vulnerabilities。
- 安全：`python scripts\security_check.py`，3/3 PASS。
- Diff：`git diff --check` 通过。

## 提交与推送

- `ee55e9a fix(import): recover interrupted import tasks`
- `1c25618 chore(frontend): upgrade test tooling security`
- 版本公告和本留档随后的文档提交。

## 遗留风险

- 当前恢复机制适用于单进程部署，并且每次启动默认最多恢复 2 个任务。多实例生产环境应改用独立队列/worker，避免多个应用实例并发领取同一任务。
