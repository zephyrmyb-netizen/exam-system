# 配置详解

本文件承接 README 中"用到时才查"的配置细节：环境变量、密钥、AI 接口、数据库与限流。

## 后端环境变量（backend/.env）

复制 `backend/.env.example` 为 `backend/.env` 并修改：

```powershell
copy backend\.env.example backend\.env
```

| 变量                        | 默认值                               | 说明                  |
| --------------------------- | ------------------------------------ | --------------------- |
| `APP_ENV`                   | `development`                        | 运行环境：`development`（开发）或 `production`（生产） |
| `DATABASE_URL`              | `sqlite:///./xuexibao.db`            | 数据库连接            |
| `SECRET_KEY`                | `change-this-secret-key-in-production` | JWT 签名密钥（**生产环境必须修改**） |
| `INVITE_CODE`               | `dev-invite`                         | 注册邀请码            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`                             | Token 过期时间（分钟）|
| `CORS_ORIGINS`              | （空 → 允许所有）                      | CORS 允许的来源       |
| `OPENAI_API_KEY`            | （空）                               | AI API 密钥（可选）   |
| `OPENAI_BASE_URL`           | `https://api.openai.com/v1`          | AI API 地址（可选）   |
| `OPENAI_MODEL`              | `gpt-4o-mini`                        | AI 模型名（可选）     |
| `CHAT_UPSTREAM_TIMEOUT`     | `90`                                 | AI 对话单次请求超时秒数 |
| `IMPORT_UPSTREAM_TIMEOUT`   | `90`                                 | AI 文件导入每个分块的上游超时秒数 |
| `IMPORT_CHUNK_SIZE`         | `5000`                               | AI 文件导入每个分块约处理的字符数 |
| `IMPORT_MAX_CHUNKS`         | `20`                                 | AI 文件导入最多处理的分块数 |
| `IMPORT_MAX_TOKENS`         | `6000`                               | AI 文件导入单次模型输出 token 上限 |
| `PRESERVE_SYSTEM_ENV`       | `0`                                  | 是否允许系统环境变量覆盖 `backend/.env` |

### SECRET_KEY 配置说明

**开发环境（`APP_ENV=development`）：**
- 可以使用默认值，启动时会显示 warning 提醒
- 无需额外配置即可运行

**生产环境（`APP_ENV=production`）：**
- 必须设置随机 `SECRET_KEY`，否则启动时报错并拒绝运行
- 生成安全的随机密钥：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

- 将生成的字符串填入 `backend/.env`：
  ```env
  APP_ENV=production
  SECRET_KEY=<你生成的随机字符串>
  ```

### 默认邀请码

注册时需要邀请码，开发环境默认为：`dev-invite`。如需修改，在 `backend/.env` 中设置 `INVITE_CODE`。

## 前端环境变量（frontend/.env）

| 变量                | 默认值                     | 说明                               |
| ------------------- | -------------------------- | ---------------------------------- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000`    | 后端 API 地址（手机访问时改为局域网 IP）|

## AI 接口配置（Mimo 或其他 OpenAI 兼容接口）

AI 对话（`/chat/`）、文件预览导入（`/imports/file/preview`）和文件自动导入（`/imports/file/auto`）需要配置 API 密钥。

编辑 `backend/.env`：

```env
# Mimo 示例
OPENAI_API_KEY=<your-api-key>
OPENAI_BASE_URL=https://api.xiaomimimo.com/v1
OPENAI_MODEL=mimo-v2.5
CHAT_UPSTREAM_TIMEOUT=90
IMPORT_UPSTREAM_TIMEOUT=90

# OpenAI 示例
# OPENAI_API_KEY=<your-api-key>
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini

# DeepSeek 示例
# OPENAI_API_KEY=<your-api-key>
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# OPENAI_MODEL=deepseek-chat
```

重启电脑后如果 AI 不能用，先打开：

```text
http://127.0.0.1:8000/health/ai
```

重点看：

- `api_key_configured` 是否为 `true`
- `dotenv_loaded` 是否为 `true`
- `base_url_host` 是否是你配置的接口域名
- `model` 是否是你正在使用的模型

本项目默认让 `backend/.env` 优先于 Windows 用户/系统环境变量，避免重启后读到旧的 `OPENAI_*`。只有部署平台确实需要系统环境变量覆盖 `.env` 时，才设置 `PRESERVE_SYSTEM_ENV=1`。

## AI 导入超时排查

AI 文件导入比普通对话更慢，因为后端会先提取 Word/PDF/PPT 文本，再把文本拆成多个分块顺序发给模型解析。其中文字提取通常很快，主要等待时间在 AI 分块生成题目阶段。前端会在等待时显示"正在读取文档 / AI 正在生成题目"，切换到其他页面后也会保留全局导入进度提示。

`POST /imports/file`、`POST /imports/file/preview` 和 `POST /imports/file/auto` 会返回安全的 `timing` 统计，单位为毫秒：

```json
{
  "timing": {
    "extract_ms": 320,
    "chunk_ms": 12,
    "ai_ms": 54000,
    "total_ms": 54500,
    "chunks": 2,
    "ai_chunks": [28000, 26000]
  }
}
```

当前默认配置：

- 前端等待导入接口：`420` 秒
- 后端单个分块上游超时：`IMPORT_UPSTREAM_TIMEOUT=90`
- 每个分块字符数：`IMPORT_CHUNK_SIZE=5000`
- 最多处理分块数：`IMPORT_MAX_CHUNKS=20`
- 单次模型输出上限：`IMPORT_MAX_TOKENS=6000`

如果导入大文件仍然超时，优先按这个顺序处理：

1. 确认 `backend/.env` 中 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL` 正确。
2. 先用小文件测试 AI 导入，确认模型接口可用。
3. 大文件可以适当调高 `IMPORT_UPSTREAM_TIMEOUT`，但要注意总耗时约等于 `IMPORT_UPSTREAM_TIMEOUT × IMPORT_MAX_CHUNKS`。
4. 不建议无限调高 `IMPORT_MAX_CHUNKS`，否则用户会等待太久，模型费用也会变高。

## 数据库说明

### 开发环境 — SQLite

默认使用 SQLite，数据库文件生成在 `backend/xuexibao.db`，零配置即可运行，适合单人本地开发和测试。

### 生产环境 — 推荐 PostgreSQL

多人正式使用时，SQLite 并发能力不足，建议切换到 PostgreSQL：

1. 安装 PostgreSQL，创建数据库（如 `xuexibao`）
2. 修改 `backend/.env`：

```env
DATABASE_URL=postgresql://用户名:密码@localhost:5432/xuexibao
```

3. 安装驱动：

```bash
pip install psycopg2-binary
```

### 数据库迁移（Alembic）

项目已配置 Alembic 用于版本化数据库迁移，PostgreSQL / SQLite 通用：

```bash
cd "D:\File\exam system"

# 生成新迁移（改完 models.py 后）
backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini revision --autogenerate -m "描述修改"

# 应用迁移到数据库
backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head
```

### 限流配置

AI 对话（`/chat`）和 AI 导入（`/imports/file/*`）均受每用户每小时频次限制。

| 变量                            | 默认值  | 说明                              |
| ------------------------------- | ------- | --------------------------------- |
| `CHAT_RATE_LIMIT_PER_HOUR`      | 20      | 每用户每小时最多对话次数          |
| `IMPORT_RATE_LIMIT_PER_HOUR`    | 10      | 每用户每小时最多导入次数          |
| `REDIS_URL`                     | （空）  | 设置后限流由 Redis 管理（多 worker/实例下精确计数） |

`REDIS_URL` 留空时使用进程内内存计数（单 worker 准确）。

### 重置开发数据库

```bash
del backend\xuexibao.db
```

重启后端后会自动创建全新的空数据库。

## 安全警告

> ⚠️ **提交公开仓库前必读**：
> - **`backend/.env` 不要提交** — 已在 `.gitignore` 中忽略，提交前请确认 `git status` 中没有 `.env`
> - **`backend/xuexibao.db` 不要提交** — 包含真实数据，已在 `.gitignore` 中忽略
> - **`uploads/` 不要提交** — 用户上传的文件不应进入仓库
> - **不要在日志、截图或视频中暴露 API Key / SECRET_KEY**
> - **不要在任何公开渠道分享 `.env` 内容**
