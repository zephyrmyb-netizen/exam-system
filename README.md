# 学习宝

基于 Vue 3 + FastAPI 的全栈刷题复习系统，支持课程管理、我的题库、公共题库、随机刷题、错题本、间隔复习、AI 对话、Word/PPT/图片预览导入等功能。

## 题库逻辑

```
                   ┌──────────────────┐
                   │   注册 / 登录     │
                   └────────┬─────────┘
                            │
              ┌─────────────┴──────────────┐
              ▼                             ▼
      ┌──────────────┐            ┌──────────────────┐
      │  我的题库      │            │   公共题库 (Library)│
      │  (默认私有)    │            │  (他人发布的课程)   │
      └──────┬───────┘            └────────┬─────────┘
             │                             │
             ▼                             ▼
      ┌──────────────┐            ┌──────────────────┐
      │  创建课程      │            │   浏览 / 刷题     │
      │  手动/导入题目  │            │   (只读)          │
      │  刷题 / 错题本  │            │                   │
      │  间隔复习       │            │                   │
      │  发布 → 公开   │            │                   │
      │  撤回 → 私有   │            │                   │
      └──────────────┘            └──────────────────┘
```

- **我的题库**：用户自己创建的课程和导入的题目，默认**私有**，只有自己能看
- **公共题库**（`/library/public`）：用户主动发布课程或题目后，所有人可见
- **发布与撤回**：课程或单道题目均可发布为公开，也可随时撤回为私有
- **先选课程，再看题和刷题**：所有题目归属于某个课程，刷题时必须指定课程

## 项目结构

```
xuexibao/
├── backend/             # FastAPI 后端
│   ├── main.py          # 应用入口
│   ├── config.py        # 环境配置（含生产环境安全校验）
│   ├── models.py        # SQLAlchemy 数据模型
│   ├── schemas.py       # Pydantic 校验模型
│   ├── crud.py          # 数据库操作（聚合导出）
│   ├── auth.py          # JWT 认证
│   ├── utils.py         # 答案归一化、填空/简答判分规则
│   ├── ratelimit.py     # 限流（Redis / 内存双后端）
│   ├── routers/         # API 路由
│   ├── services/        # 业务服务（导入、AI 客户端）
│   ├── migrations/      # Alembic 数据库迁移
│   └── tests/           # pytest 测试
├── docs/                # 文档
│   └── acceptance-checklist.md  # 验收清单
├── scripts/             # 工具脚本
│   ├── security_check.py        # 安全检查
│   └── smoke_test.ps1           # 冒烟测试
├── frontend/            # Vue 3 前端（TypeScript）
│   └── src/
│       ├── views/       # 页面组件
│       ├── api/         # API 请求封装（TS）
│       ├── composables/ # 可组合逻辑
│       ├── stores/      # 全局状态
│       ├── types/       # TS 类型定义
│       ├── i18n/        # 国际化（vue-i18n）
│       ├── router.ts    # 路由配置
│       └── main.ts      # 应用入口
└── .gitignore
```

## 技术栈

| 层级   | 技术                                         |
| ------ | -------------------------------------------- |
| 前端   | Vue 3 + Vite + Vue Router + Axios + TypeScript + Vue I18n |
| 测试   | pytest（后端 300+）/ Vitest（前端）           |
| 后端   | Python 3.11+ / FastAPI + SQLAlchemy + Alembic |
| 数据库 | 开发：SQLite / 生产：推荐 PostgreSQL         |
| 认证   | JWT（Bearer Token）                          |
| 限流   | 内存（开发）/ Redis（生产，可选）             |
| 部署   | Docker + docker-compose                      |

## 快速启动

### 方式一：Docker（推荐生产/一键启动）

```bash
# 1. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env：至少设置 SECRET_KEY、INVITE_CODE

# 2. 启动全部服务
docker compose up -d

# 前端 → http://localhost:8080
# 后端 → http://localhost:8000/docs
```

### 方式二：本地开发

### 1. 后端（从项目根目录启动）

```powershell
cd D:\File\exam system

# 创建虚拟环境（首次）
python -m venv backend\.venv

# 激活虚拟环境
backend\.venv\Scripts\activate

# 安装依赖
pip install -r backend\requirements.txt

# 配置环境变量
copy backend\.env.example backend\.env

# 启动服务（监听 0.0.0.0:8000 以支持手机访问）
# 日常使用不要加 --reload，避免 AI 导入时后端因文件变动自动重启
backend\.venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

> ⚠️ **必须从项目根目录启动**，因为 Python 模块路径 `backend.main` 依赖于项目根目录在 `sys.path` 中。如果从 `backend/` 目录下直接 `uvicorn main:app` 会报导入错误。

API 文档自动生成于：

- Swagger UI：http://127.0.0.1:8000/docs
- ReDoc：http://127.0.0.1:8000/redoc

### 2. 前端

```powershell
cd frontend

# 安装依赖
npm.cmd install

# 启动开发服务器（默认 5173 端口，监听所有网卡以支持手机访问）
npm.cmd run dev -- --host 0.0.0.0
```

> **Windows PowerShell 提示**：如果 `npm` 提示执行策略错误，请使用 `npm.cmd` 代替 `npm`，避免 npm.ps1 的执行策略问题。

浏览器打开 http://127.0.0.1:5173

## 环境变量

### 后端（backend/.env）

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
| `IMPORT_MAX_CHUNKS`         | `3`                                  | AI 文件导入最多处理的分块数 |
| `PRESERVE_SYSTEM_ENV`       | `0`                                  | 是否允许系统环境变量覆盖 `backend/.env` |

#### SECRET_KEY 配置说明

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

> ⚠️ **安全警告**：
> - **不要提交 `backend/.env` 到 Git**（已写入 `.gitignore`）
> - **不要在日志或截图中暴露真实 SECRET_KEY**

### 前端（frontend/.env）

| 变量                | 默认值                     | 说明                               |
| ------------------- | -------------------------- | ---------------------------------- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000`    | 后端 API 地址（手机访问时改为局域网 IP）|

## 常用功能说明

### 课程与题目管理

- **创建课程**：进入"我的课程"，填写名称、描述、科目
- **编辑课程**：课程所有者可修改名称、描述、科目
- **删除课程**：课程所有者可删除课程及其下所有题目
- **手动添加题目**：进入课程后可以逐道添加题目（支持单选题、多选题、判断题、填空题、简答题）
- **批量导入**：通过 JSON 数组或 Word/PPT 文件批量导入

### Word/PPT/图片预览导入流程

文件上传采用**预览→修改→确认**三步流程，不是直接写入数据库：

1. **上传文件**：调用 `POST /imports/file/preview`，后端提取 Word/PPT 文本、PPT 内嵌图片或直接上传的图片后调用 AI 解析为题目数组
2. **预览与修改**：前端展示 AI 解析结果，用户可以编辑题目字段（题干、选项、答案、解析等）
3. **确认导入**：用户确认后调用 `POST /imports/confirm`，后端校验所有题目后统一写入数据库

这种方式确保用户对导入内容有完全控制权，避免 AI 解析错误直接入库。

支持的文件格式：

- 文档：`.docx`、`.pptx`
- 图片：`.png`、`.jpg`、`.jpeg`、`.webp`
- 旧版 `.ppt` 暂不支持，请在 PowerPoint/WPS 中另存为 `.pptx` 后上传

图片题目识别依赖当前 `OPENAI_MODEL` 支持 OpenAI-compatible `image_url` / base64 多模态输入，例如 `mimo-v2.5`。如果模型不支持图片输入，纯文本 Word/PPT 导入仍可使用，图片识别会返回明确错误或 warning。

#### AI 导入超时排查

AI 文件导入比普通对话更慢，因为后端会先提取 Word/PPT 文本，再把文本拆成多个分块顺序发给模型解析。
其中 Word/PPT 文字提取通常很快，主要等待时间一般在 AI 分块生成题目阶段。前端会在等待时显示“正在读取文档 / AI 正在生成题目”，切换到其他页面后也会保留全局导入进度提示。

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
- 最多处理分块数：`IMPORT_MAX_CHUNKS=3`

如果导入大文件仍然超时，优先按这个顺序处理：

1. 确认 `backend/.env` 中 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL` 正确。
2. 先用小文件测试 AI 导入，确认模型接口可用。
3. 大文件可以适当调高 `IMPORT_UPSTREAM_TIMEOUT`，但要注意总耗时约等于 `IMPORT_UPSTREAM_TIMEOUT × IMPORT_MAX_CHUNKS`。
4. 不建议无限调高 `IMPORT_MAX_CHUNKS`，否则用户会等待太久，模型费用也会变高。

### 发布与撤回公开

**发布范围：**
- **整门课程发布**：`POST /courses/{course_id}/publish` → 课程 + 其下所有题目变为公开
- **单道题目发布**：`POST /questions/{question_id}/publish` → 仅该题目公开

**撤回范围：**
- **整门课程撤回**：`POST /courses/{course_id}/unpublish` → 课程 + 其下所有题目回到私有
- **单道题目撤回**：`POST /questions/{question_id}/unpublish` → 仅该题目回到私有

> 只有题目/课程的所有者可以执行发布和撤回操作。

### 间隔复习机制

每次提交答案后，系统自动更新该题的间隔复习状态：

| review_level | 下次复习间隔 | 说明 |
|---|---|---|
| 0 | 未开始 | 初次创建，或重置后 |
| 1 | 1 天 | 第一次答对 |
| 2 | 3 天 | 连续第二次答对 |
| 3 | 7 天 | 连续第三次答对 |
| 4 | 14 天 | 持续稳定的掌握 |
| 5 | 30 天 | 完全掌握，低频复习 |

答错时降级（review_level 减 1，最低 0），连续答错积累到错题本。

**复习入口：**
- `GET /practice/review/due` — 到期需复习的题目列表
- `GET /practice/review/wrong` — 错题复习（按错题数权重抽取）
- `GET /practice/review/today` — 今日复习建议摘要

### 填空 `||` 与简答 `&&` 答案规则

**填空题（fill_blank）：**

使用 `||` 分隔多个可接受答案。用户答对其一即判对：

```
# 标准答案中任意一个匹配即可
answer = "TCP||传输控制协议"
→ "TCP" ✓
→ "传输控制协议" ✓
→ "UDP" ✗
```

**简答题（short_answer）：**

- `||` 表示**多选一**：匹配任一即正确（同填空题）
- `&&` 表示**所有关键词必须出现**：用户答案中需包含所有关键词，顺序无关

```
# && 要求全部关键词都出现在用户答案中
answer = "冒泡排序&&交换&&相邻"
→ "冒泡排序通过交换相邻元素实现排序" ✓
→ "通过相邻元素交换完成排序" ✓（顺序不限）
→ "冒泡排序是一种排序算法" ✗（缺少"交换"和"相邻"）
```

> 比较时会忽略：首尾空格、全角/半角标点、大小写（英文）、多余空白。

## 配置 Mimo API（或其他兼容 OpenAI 的接口）

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

> ⚠️ **安全警告**（提交公开仓库前必读）：
> - ✅ **`backend/.env` 不要提交** — 已在 `.gitignore` 中忽略，提交前请确认 `git status` 中没有 `.env`
> - ✅ **`backend/xuexibao.db` 不要提交** — 包含真实数据，已在 `.gitignore` 中忽略
> - ✅ **`uploads/` 不要提交** — 用户上传的文件不应进入仓库
> - ✅ **不要在日志、截图或视频中暴露 API Key / SECRET_KEY**
> - ✅ **不要在任何公开渠道分享 `.env` 内容**

## 数据库说明

### 开发环境 — SQLite

默认使用 SQLite，数据库文件生成在 `backend/xuexibao.db`，零配置即可运行。

适合单人本地开发和测试。

### 生产环境 — 推荐 PostgreSQL

多人正式使用时，SQLite 并发能力不足，建议切换到 PostgreSQL。

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

> 旧的 `backend/migrate_sqlite.py` 脚本保留作为 SQLite 专用兼容入口。

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

## 默认邀请码

注册时需要邀请码，开发环境默认为：`dev-invite`

如需修改，在 `backend/.env` 中设置 `INVITE_CODE`。

## API 地址

### 认证

| 端点               | 方法   | 说明                          |
| ------------------ | ------ | ----------------------------- |
| `/health`          | GET    | 健康检查                      |
| `/auth/register`   | POST   | 用户注册（需邀请码）          |
| `/auth/login`      | POST   | 用户登录，返回 JWT Token      |
| `/auth/me`         | GET    | 获取当前用户信息（需认证）    |

### 课程

| 端点                                     | 方法     | 说明                                |
| ---------------------------------------- | -------- | ----------------------------------- |
| `/courses/`                              | POST     | 创建课程（默认私有）                |
| `/courses/`                              | GET      | 获取用户可见的所有课程              |
| `/courses/mine`                          | GET      | 只获取我创建的课程                  |
| `/courses/{course_id}`                   | GET      | 课程详情                            |
| `/courses/{course_id}`                   | PATCH    | 编辑课程名称/描述/科目              |
| `/courses/{course_id}`                   | DELETE   | 删除课程（只能删自己的）            |
| `/courses/{course_id}/questions`         | GET      | 课程下的题目列表                    |
| `/courses/{course_id}/practice/random`   | GET      | 在指定课程内随机刷题                |
| `/courses/{course_id}/publish`           | POST     | 发布课程（课程 + 所有题目变公开）   |
| `/courses/{course_id}/unpublish`         | POST     | 撤回课程（课程 + 所有题目回私有）   |

### 公共题库

| 端点                                     | 方法   | 说明                            |
| ---------------------------------------- | ------ | ------------------------------- |
| `/library/public`                        | GET    | 浏览所有公开课程                |
| `/library/public/{course_id}/questions`  | GET    | 查看公开课程下的题目            |

### 题目

| 端点                                 | 方法     | 说明                            |
| ------------------------------------ | -------- | ------------------------------- |
| `/questions/`                        | GET      | 题目列表（可见范围，支持筛选）  |
| `/questions/my`                      | GET      | 只看我自己的题目                |
| `/questions/public`                  | GET      | 只看公开的题目                  |
| `/questions/batch`                   | POST     | 批量导入题目                    |
| `/questions/{question_id}`           | DELETE   | 删除自己的题目                  |
| `/questions/{question_id}/publish`   | POST     | 发布单道题目到公共题库          |
| `/questions/{question_id}/unpublish` | POST     | 撤回单道题目回私有              |
| `/questions/meta`                    | GET      | 题目科目/章节元数据             |

### 刷题与判分

| 端点                  | 方法   | 说明                    |
| --------------------- | ------ | ----------------------- |
| `/practice/random`    | GET    | 从可见题目中随机抽题（支持 course_id 指定课程） |
| `/practice/submit`    | POST   | 提交答案并判分          |
| `/practice/stats`     | GET    | 练习统计（今日题数、正确率等）|
| `/practice/history`   | GET    | 练习历史（分页）        |

### 间隔复习

| 端点                              | 方法   | 说明                            |
| --------------------------------- | ------ | ------------------------------- |
| `/practice/review/wrong`          | GET    | 错题复习（按错题数权重抽取）    |
| `/practice/review/today`          | GET    | 今日复习建议摘要                |
| `/practice/review/due`            | GET    | 到期需复习的题目列表            |
| `/practice/insights/weak-types`   | GET    | 薄弱题型分析                    |

### 错题本

| 端点                          | 方法   | 说明            |
| ----------------------------- | ------ | --------------- |
| `/wrongbook/`                 | GET    | 错题本列表      |
| `/wrongbook/{question_id}`    | DELETE | 从错题本移除    |
| `/wrongbook/meta`             | GET    | 错题本科目/章节 |

### 文件导入

| 端点                  | 方法   | 说明                                        |
| --------------------- | ------ | ------------------------------------------- |
| `/imports/file`       | POST   | 上传 .docx/.pptx/.png/.jpg/.jpeg/.webp 文件，提取文本或图片识别文本（最大 10MB）|
| `/imports/file/preview`| POST   | 上传文件并用 AI 解析为题目，支持 PPT 内嵌图片和直接图片，返回预览（不入库）|
| `/imports/confirm`    | POST   | 确认预览后的题目并写入数据库                |
| `/imports/file/auto`  | POST   | 上传文件并用 AI 直接解析并导入              |

### AI 对话

| 端点     | 方法   | 说明                              |
| -------- | ------ | --------------------------------- |
| `/chat/` | POST   | AI 对话（需配置 OPENAI_API_KEY）  |

完整 API 文档请访问 http://127.0.0.1:8000/docs

## 移动端访问

在同一个局域网内用手机访问：

1. 查看电脑局域网 IP，例如 `192.168.1.8`
2. 后端已在 `--host 0.0.0.0` 下运行
3. 在前端 `frontend/.env` 中设置：
   ```env
   VITE_API_BASE_URL=http://192.168.1.8:8000
   ```
4. 重启前端：`npm.cmd run dev -- --host 0.0.0.0`
5. 手机浏览器打开：`http://192.168.1.8:5173`

> 前端代码已内置自动推导逻辑：如果访问的 hostname 不是 localhost 或 127.0.0.1，会自动将 API 地址拼为 `http://<hostname>:8000`。

## 一键启动（Windows PowerShell）

推荐直接双击：

```text
scripts/start_xuexibao.bat
```

脚本会启动后端、前端，并自动打开 `http://localhost:8000/health/ai` 检查 AI 配置是否读取成功。日常使用的后端启动不带 `--reload`，这样 AI 导入大文件时不会因为文件变化自动重启。

在项目根目录打开 PowerShell，粘贴以下命令即可同时启动前后端：

```powershell
# 启动后端（新窗口）
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$pwd'; backend\.venv\Scripts\activate; uvicorn backend.main:app --host 0.0.0.0 --port 8000"

# 启动前端（新窗口）
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$pwd\frontend'; npm.cmd run dev -- --host 0.0.0.0"
```

需要调后端代码时，才临时加 `--reload`：

```powershell
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 项目维护规范

### DeepSeek 窗口协作规则

为了避免一次改动范围过大，后续每个 DeepSeek 窗口只做一个小功能或一个小修复。推荐这样拆：

- `后端接口`：只改 `backend/routers/*`、对应 `schemas.py` 和必要测试。
- `后端数据库`：只改 `backend/models.py`、`backend/migrate_sqlite.py`、迁移文档和测试。
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

### 目录清理规则

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

```bash
# 后端测试
cd "D:\File\exam system"
backend\.venv\Scripts\python.exe -m pytest backend/tests -v

# 前端构建
cd frontend
npm.cmd run build

# 后端健康检查（需先启动后端）
curl http://127.0.0.1:8000/health

# 安全检查
python scripts/security_check.py

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

> 更多验收细节请参见 [docs/acceptance-checklist.md](docs/acceptance-checklist.md)。
