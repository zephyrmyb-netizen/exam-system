# Exam System Backend

FastAPI + SQLAlchemy + SQLite/PostgreSQL + JWT 认证后端。

## 题库体系

```
User ──1:N── QuestionBank (课程/题库)
                │
                ├── name / description / subject
                ├── visibility: private(默认) / public
                └── 1:N── Question (题目)
                            ├── subject / chapter / type / difficulty
                            ├── visibility: private(默认) / public
                            ├── source: import / manual
                            └── owner_id → User
```

**可见性规则：**
- `private` → 只有题目/课程的创建者（owner）可见
- `public` → 所有人可见
- `owner_id IS NULL` → 向后兼容，等价于公开

**发布流程：**
1. 用户创建课程（默认私有）
2. 导入或手动添加题目到课程（默认私有）
3. 点击发布 → 课程 + 课程下所有题目变为 `public`
4. 发布后所有用户可在公共题库浏览和刷题

## 数据模型

| 模型           | 表名              | 说明                               |
| -------------- | ----------------- | ---------------------------------- |
| `User`         | `users`           | 用户（id, username, password_hash）|
| `QuestionBank` | `question_banks`  | 课程/题库（owner, name, visibility）|
| `Question`     | `questions`       | 题目（course_id, owner_id, visibility）|
| `WrongRecord`  | `wrong_records`   | 错题记录（user_id, question_id）    |

## 快速启动

```bash
# 1. 从项目根目录启动（重要！）
cd D:\File\exam system

# 2. 创建虚拟环境（首次）
python -m venv backend\.venv

# 3. 激活虚拟环境
backend\.venv\Scripts\activate

# 4. 安装依赖
pip install -r backend\requirements.txt

# 5. 启动服务（注意模块路径与当前目录的关系）
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档自动生成于 http://127.0.0.1:8000/docs

> ⚠️ **必须从项目根目录启动**，因为 Python 模块路径 `backend.main` 依赖于项目根目录在 `sys.path` 中。
> 如果从 `backend/` 目录下直接 `uvicorn main:app` 会报导入错误。

## 环境变量

在 `backend/.env` 中配置（参考 `backend/.env.example`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_ENV` | `development` | 运行环境：`development`（开发）或 `production`（生产） |
| `DATABASE_URL` | `sqlite:///./exam_system.db` | 数据库连接（开发用 SQLite，生产用 PostgreSQL） |
| `SECRET_KEY` | `change-this-secret-key-in-production` | JWT 签名密钥（**生产环境必须修改**） |
| `CORS_ORIGINS` | （空 → 允许所有） | 逗号分隔的允许跨域来源，如 `http://localhost:5173,http://192.168.1.8:5173` |
| `INVITE_CODE` | `dev-invite` | 注册邀请码（生产环境请修改） |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token 过期时间（分钟） |
| `OPENAI_API_KEY` | （空） | AI 接口密钥（必填，用于对话和自动导入） |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | AI 接口地址（可换 Mimo、DeepSeek 等兼容接口） |
| `OPENAI_MODEL` | `gpt-4o-mini` | AI 模型名（如 `mimo-v2.5`、`deepseek-chat`） |

#### SECRET_KEY 配置说明

**开发环境（`APP_ENV=development`，默认）：**
- 可以使用默认值，启动时会显示 warning 提醒
- 无需额外配置即可运行

**生产环境（`APP_ENV=production`）：**
- 必须设置随机 `SECRET_KEY`，否则启动时报错并拒绝运行
- 生成随机密钥（Windows / Linux / macOS 通用）：

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

- 将生成的字符串填入 `backend/.env`：

```env
APP_ENV=production
SECRET_KEY=<你生成的随机字符串>
```

> ⚠️ **安全警告**：
> - `backend/.env` 已写入 `.gitignore`，不会被提交到 Git
> - **不要在日志或截图中暴露真实 SECRET_KEY**

### 生产环境必改项

1. **`APP_ENV`** — 设置为 `production`
2. **`SECRET_KEY`** — 设置随机长字符串（用上面的 `python -c "import secrets; ..."` 生成）
3. **`CORS_ORIGINS`** — 设置为前端实际域名/IP，如 `http://192.168.1.8:5173`
4. **`INVITE_CODE`** — 修改为自定义邀请码
5. **`DATABASE_URL`** — 多人使用请切换为 PostgreSQL

## 数据库说明

### SQLite（开发环境）

默认使用 SQLite，数据库文件生成在 `backend/exam_system.db`。零配置即可运行，适合单人本地开发和测试。

```bash
# 重置数据库：删除 db 文件后重启后端即可
del backend\exam_system.db
```

### PostgreSQL（生产环境）

多人正式使用建议切换到 PostgreSQL：

```bash
# 1. 安装驱动
pip install psycopg2-binary

# 2. 修改 .env
# DATABASE_URL=postgresql://用户名:密码@localhost:5432/exam_system
```

## AI 接口配置

支持任何 **OpenAI 兼容 API** 的 LLM 服务。推荐使用 Mimo（免费额度）：

```env
# Mimo（推荐）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.xiaomimimo.com/v1
OPENAI_MODEL=mimo-v2.5
```

其他常见配置：

| 服务 | `OPENAI_BASE_URL` | 推荐 `OPENAI_MODEL` |
|------|-------------------|---------------------|
| Mimo | `https://api.xiaomimimo.com/v1` | `mimo-v2.5` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 自定义兼容接口 | 你的接口地址 | 对应模型名 |

> ⚠️ **安全警告**：
> - `backend/.env` 已写入 `.gitignore`，不会被提交到 Git
> - **不要截图或分享你的 API Key**
> - **不要提交 `.env` 文件到公开仓库**

这些配置同时影响以下接口：
- `POST /chat` — AI 学习对话助手
- `POST /imports/file/auto` — 上传文件后 AI 自动结构化并导入题目

## 接口列表

### 认证（无需认证）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/auth/register` | 注册（需要 invite_code） |
| POST | `/auth/login` | 登录，返回 JWT token |

### 认证（需 Bearer Token）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/auth/me` | 获取当前用户信息 |

### 课程 / 题库

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/courses/` | 创建课程（默认私有） |
| GET | `/courses/` | 获取用户可见的所有课程 |
| GET | `/courses/mine` | 只获取我创建的课程 |
| GET | `/courses/{course_id}` | 课程详情 |
| DELETE | `/courses/{course_id}` | 删除课程（只能删自己的） |
| GET | `/courses/{course_id}/questions` | 课程下的题目列表 |
| GET | `/courses/{course_id}/practice/random` | 在课程内随机刷题 |
| POST | `/courses/{course_id}/publish` | 发布课程（课程 + 题目变公开） |

### 公共题库

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/library/public` | 浏览所有公开课程 |
| GET | `/library/public/{course_id}/questions` | 查看公开课程下的题目 |

### 题目

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/questions/` | 题目列表（可见范围，支持分页/筛选） |
| GET | `/questions/my` | 只看我自己的题目 |
| GET | `/questions/public` | 只看公开题目 |
| POST | `/questions/batch` | 批量导入题目 |
| DELETE | `/questions/{question_id}` | 删除自己的题目 |
| POST | `/questions/{question_id}/publish` | 发布单道题到公共题库 |
| GET | `/questions/meta` | 题目科目/章节筛选元数据 |

### 刷题

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/practice/random` | 从全局可见题目中随机刷题 |
| POST | `/practice/submit` | 提交答案并判分 |

### 错题本

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/wrongbook/` | 错题本列表（支持分页/筛选） |
| DELETE | `/wrongbook/{question_id}` | 从错题本移除 |
| GET | `/wrongbook/meta` | 错题本科目/章节筛选元数据 |

### 文件导入

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/imports/file` | 上传 .docx/.pptx 提取文本（最大 10MB） |
| POST | `/imports/file/auto` | 上传文件并 AI 自动导入题目（需配置 OPENAI_API_KEY） |

### AI 对话

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat/` | AI 对话助手（需配置 OPENAI_API_KEY） |

## 前端 API 地址配置

默认情况下前端自动推断后端地址：
- 本地开发：`http://127.0.0.1:8000`
- 同 WiFi 访问：`http://<电脑局域网IP>:8000`

如需手动指定，在 `frontend/` 目录下创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

然后重启前端：

```bash
cd frontend
npm.cmd run dev -- --host 0.0.0.0
```

## 测试

```bash
# 从项目根目录运行
cd D:\File\exam system
backend\.venv\Scripts\pytest backend\tests\ -v

# 健康检查
curl http://127.0.0.1:8000/health

# 注册
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456","invite_code":"dev-invite"}'

# 登录
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"123456"}'
```
