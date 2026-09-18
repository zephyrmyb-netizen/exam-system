# 项目维护规范

## DeepSeek 窗口协作规则

为了避免一次改动范围过大，后续每个 DeepSeek 窗口只做一个小功能或一个小修复。推荐这样拆：

- `后端接口`：只改 `backend/routers/*`、对应 `schemas.py` 和必要测试。
- `后端数据库`：只改 `backend/models.py`、`backend/migrations/`（Alembic 迁移）和必要测试。
- `后端导入`：只改 `backend/routers/imports.py`、导入相关 schema、导入测试。
- `前端页面`：只改一个页面，例如 `frontend/src/views/Practice.vue` 或 `frontend/src/views/ImportQuestions.vue`。
- `前端接口状态`：只改 `frontend/src/api/*`、`frontend/src/stores/*`。
- `视觉打磨`：只改样式和组件展示，不改接口契约。
- `项目总控`：只做测试、构建、`git diff` 检查和 README/公告更新。

每个窗口最后都要说明：

1. 改了哪些文件。
2. 修了哪个具体问题。
3. 运行了什么验证命令。
4. `git diff --stat` 的结果。

## 目录清理规则

推荐先用脚本清理安全范围内的本地垃圾：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\cleanup_local_artifacts.ps1
```

默认只清理缓存、日志和前端构建产物。需要清理旧数据库备份或重复虚拟环境时，显式加参数：

```powershell
# 清理旧迁移备份库
powershell -ExecutionPolicy Bypass -File scripts\cleanup_local_artifacts.ps1 -IncludeBackupDbs

# 如果 backend\.venv 已可用，删除重复的 backend\venv
powershell -ExecutionPolicy Bypass -File scripts\cleanup_local_artifacts.ps1 -IncludeDuplicateVenv
```

可以删除的本地生成文件：

- `.pytest_cache/`
- `__pycache__/`
- `frontend/dist/`
- `frontend/test-results/`
- `frontend/.playwright-cli/`
- `backend/xuexibao.backup-*.db`
- `backend/server.out.log`、`backend/server.err.log`
- `frontend/server.out.log`、`frontend/server.err.log`

不要删除：

- `backend/.env`
- `backend/xuexibao.db`
- `backend/.venv/`
- `frontend/node_modules/`
- 用户自己放进项目的资料文件，除非确认已经不需要

## 验收命令

### 2.0 发布门禁

上线前从项目根目录依次执行：

```powershell
# 前端质量、测试和构建
cd "D:\File\exam system\frontend"
npm.cmd run lint
npm.cmd run test
npm.cmd run build

# 后端质量和测试
cd "D:\File\exam system"
backend\.venv\Scripts\python.exe -m ruff check backend
backend\.venv\Scripts\python.exe -m pytest backend\tests -q

# 公开仓库安全检查
python scripts\security_check.py
```

生产环境发布前必须确认：

- `APP_ENV=production`
- `SECRET_KEY` 已换成随机长密钥
- `INVITE_CODE` 已换成自己的邀请码
- `CORS_ORIGINS` 已设置为真实前端域名
- `DB_PASSWORD` 已设置为生产数据库密码
- `backend/.env`、数据库、上传文件、日志和文档资料没有进入 Git

### 补充验收

```bash
# 后端测试（详细模式）
cd "D:\File\exam system"
backend\.venv\Scripts\python.exe -m pytest backend/tests -v

# 后端健康检查（需先启动后端）
curl http://127.0.0.1:8000/health

# 安全检查
python scripts\security_check.py

# 冒烟测试（需先启动后端）
powershell -ExecutionPolicy Bypass -File scripts\smoke_test.ps1
```

## 公开仓库前检查清单

```markdown
- [ ] 已确认 `.env` 文件未被 Git 跟踪（运行 `git status` 检查）
- [ ] 已确认 `backend/xuexibao.db` 未被跟踪
- [ ] 已确认 `uploads/` 未被跟踪
- [ ] 已确认 `.env.example` 中不含真实 API Key（使用 `<your-api-key>` 占位）
- [ ] 生产环境已设置 `SECRET_KEY` 为随机字符串
- [ ] 生产环境已修改 `INVITE_CODE` 为自定义值
- [ ] 生产环境已配置 `CORS_ORIGINS` 为前端实际域名
- [ ] 生产环境已设置 `APP_ENV=production`
- [ ] 已运行 `git grep -n "sk-"` 确认无 API Key 硬编码
```

> 更多验收细节请参见 [docs/acceptance-checklist.md](../acceptance-checklist.md)。
