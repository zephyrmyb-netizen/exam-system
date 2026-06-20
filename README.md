# 考前刷题复习系统

基于 Vue 3 + FastAPI 的全栈刷题复习系统，支持课程管理、我的题库、公共题库、随机刷题、错题本、AI 对话、Word/PPT 导入等功能。

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
      │  导入题目      │            │   (只读)          │
      │  刷题 / 错题本 │            │                   │
      │  发布 → 公开   │            │                   │
      └──────────────┘            └──────────────────┘
```

- **我的题库**：用户自己创建的课程和导入的题目，默认**私有**，只有自己能看
- **公共题库**（`/library/public`）：用户主动发布课程或题目后，所有人可见
- **发布**：在课程详情页或题目操作中点击"发布"，课程 + 其下所有题目变为公开
- **先选课程，再看题和刷题**：所有题目归属于某个课程，刷题时必须指定课程

## 项目结构

```
exam-system/
├── backend/             # FastAPI 后端
│   ├── main.py          # 应用入口
│   ├── config.py        # 环境配置
│   ├── models.py        # SQLAlchemy 数据模型（User / QuestionBank / Question / WrongRecord）
│   ├── schemas.py       # Pydantic 校验模型
│   ├── crud.py          # 数据库操作
│   ├── auth.py          # JWT 认证
│   ├── utils.py         # 工具函数
│   ├── routers/         # API 路由
│   │   ├── auth.py      # 注册 / 登录 / 个人信息
│   │   ├── courses.py   # 课程 CRUD + 课程内刷题
│   │   ├── questions.py # 题目列表 / 批量导入 / 发布 / 删除
│   │   ├── practice.py  # 随机刷题 / 提交答案
│   │   ├── wrongbook.py # 错题本
│   │   ├── library.py   # 公共题库（浏览公开课程）
│   │   ├── imports.py   # Word/PPT 文件上传 + AI 自动导入
│   │   ├── chat.py      # AI 对话
│   │   └── health.py    # 健康检查
│   └── tests/           # pytest 测试
├── frontend/            # Vue 3 前端
│   └── src/
│       ├── views/       # 页面组件
│       ├── api/         # API 请求封装
│       └── router.js    # 路由配置
└── .gitignore
```

## 技术栈

| 层级   | 技术                                   |
| ------ | -------------------------------------- |
| 前端   | Vue 3 + Vite + Vue Router + Axios     |
| 后端   | Python 3.11+ / FastAPI + SQLAlchemy    |
| 数据库 | 开发：SQLite / 生产：推荐 PostgreSQL   |
| 认证   | JWT（Bearer Token）                    |

## 快速启动

### 1. 后端

```bash
cd backend

# 创建虚拟环境（首次）
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
copy .env.example .env

# 启动服务（监听 0.0.0.0:8000 以支持手机访问）
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档自动生成于：

- Swagger UI：http://127.0.0.1:8000/docs
- ReDoc：http://127.0.0.1:8000/redoc

### 2. 前端

```bash
cd frontend

# 安装依赖
npm.cmd install

# 启动开发服务器（默认 5173 端口，监听所有网卡以支持手机访问）
npm.cmd run dev -- --host 0.0.0.0
```

> **Windows PowerShell 提示**：如果 `npm` 提示执行策略错误，请使用 `npm.cmd` 代替 `npm`，避免 npm.ps1 的执行策略问题。例如：`npm.cmd install`、`npm.cmd run dev`。

浏览器打开 http://127.0.0.1:5173

## 环境变量

### 后端（backend/.env）

复制 `backend/.env.example` 为 `backend/.env` 并修改：

```bash
copy backend\.env.example backend\.env
```

| 变量                        | 默认值                               | 说明                  |
| --------------------------- | ------------------------------------ | --------------------- |
| `APP_ENV`                   | `development`                        | 运行环境：`development`（开发）或 `production`（生产） |
| `DATABASE_URL`              | `sqlite:///./exam_system.db`         | 数据库连接            |
| `SECRET_KEY`                | `change-this-secret-key-in-production` | JWT 签名密钥（**生产环境必须修改**） |
| `INVITE_CODE`               | `dev-invite`                         | 注册邀请码            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440`                             | Token 过期时间（分钟）|
| `CORS_ORIGINS`              | （空 → 允许所有）                      | CORS 允许的来源       |
| `OPENAI_API_KEY`            | （空）                               | AI API 密钥（可选）   |
| `OPENAI_BASE_URL`           | `https://api.openai.com/v1`          | AI API 地址（可选）   |
| `OPENAI_MODEL`              | `gpt-4o-mini`                        | AI 模型名（可选）     |

#### SECRET_KEY 配置说明

**开发环境（`APP_ENV=development`）：**
- 可以使用默认值，启动时会显示 warning 提醒
- 无需额外配置即可运行

**生产环境（`APP_ENV=production`）：**
- 必须设置随机 `SECRET_KEY`，否则启动时报错并拒绝运行
- 使用以下命令生成一个安全的随机密钥：

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

## 配置 Mimo API（或其他兼容 OpenAI 的接口）

AI 对话（`/chat/`）和文件自动导入（`/imports/file/auto`）需要配置 API 密钥。

编辑 `backend/.env`：

```env
# Mimo（推荐，免费额度）
OPENAI_API_KEY=sk-your-mimo-key-here
OPENAI_BASE_URL=https://api.xiaomimimo.com/v1
OPENAI_MODEL=mimo-v2.5

# 或者 OpenAI
# OPENAI_API_KEY=sk-your-key-here
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-4o-mini

# 或者 DeepSeek
# OPENAI_API_KEY=sk-your-key-here
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# OPENAI_MODEL=deepseek-chat
```

> ⚠️ **安全警告**：
> - **不要提交 `backend/.env` 到 Git**（已写入 `.gitignore`）
> - **不要截图或分享你的 API Key**
> - 后端启动时会检查 `SECRET_KEY` 是否仍为默认值，若是则打印警告

## 数据库说明

### 开发环境 — SQLite

默认使用 SQLite，数据库文件生成在 `backend/exam_system.db`，零配置即可运行。

适合单人本地开发和测试。

### 生产环境 — 推荐 PostgreSQL

多人正式使用时，SQLite 并发能力不足，建议切换到 PostgreSQL。

1. 安装 PostgreSQL，创建数据库（如 `exam_system`）
2. 修改 `backend/.env`：

```env
DATABASE_URL=postgresql://用户名:密码@localhost:5432/exam_system
```

3. 安装驱动：

```bash
pip install psycopg2-binary
```

### 重置开发数据库

如需清空所有数据重新开始，只需删除 SQLite 文件：

```bash
del backend\exam_system.db
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

### 课程（我的题库 + 公共浏览）

| 端点                                     | 方法   | 说明                                |
| ---------------------------------------- | ------ | ----------------------------------- |
| `/courses/`                              | POST   | 创建课程（默认私有）                |
| `/courses/`                              | GET    | 获取当前用户可见的所有课程          |
| `/courses/mine`                          | GET    | 只获取我创建的课程                  |
| `/courses/{course_id}`                   | GET    | 课程详情                            |
| `/courses/{course_id}`                   | DELETE | 删除课程（只能删自己的）            |
| `/courses/{course_id}/questions`         | GET    | 课程下的题目列表                    |
| `/courses/{course_id}/practice/random`   | GET    | 在指定课程内随机刷题                |
| `/courses/{course_id}/publish`           | POST   | 发布课程（课程 + 所有题目变为公开） |
| `/library/public`                        | GET    | 公共题库：浏览所有公开课程          |
| `/library/public/{course_id}/questions`  | GET    | 查看公开课程下的题目                |

### 题目

| 端点                             | 方法   | 说明                            |
| -------------------------------- | ------ | ------------------------------- |
| `/questions/`                    | GET    | 题目列表（可见范围，支持筛选）  |
| `/questions/my`                  | GET    | 只看我自己的题目                |
| `/questions/public`              | GET    | 只看公开的题目                  |
| `/questions/batch`               | POST   | 批量导入题目                    |
| `/questions/{question_id}`       | DELETE | 删除自己的题目                  |
| `/questions/{question_id}/publish` | POST | 发布单道题目到公共题库          |
| `/questions/meta`                | GET    | 题目科目/章节元数据             |

### 刷题

| 端点                  | 方法   | 说明                    |
| --------------------- | ------ | ----------------------- |
| `/practice/random`    | GET    | 从全局可见题目中随机刷题 |
| `/practice/submit`    | POST   | 提交答案并判分          |

### 错题本

| 端点                          | 方法   | 说明            |
| ----------------------------- | ------ | --------------- |
| `/wrongbook/`                 | GET    | 错题本列表      |
| `/wrongbook/{question_id}`    | DELETE | 从错题本移除    |
| `/wrongbook/meta`             | GET    | 错题本科目/章节 |

### 文件导入

| 端点                  | 方法   | 说明                                    |
| --------------------- | ------ | --------------------------------------- |
| `/imports/file`       | POST   | 上传 .docx/.pptx 文件，提取文本（最大 10MB）|
| `/imports/file/auto`  | POST   | 上传文件并用 AI 自动解析为题目并导入     |

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

在项目根目录打开 PowerShell，粘贴以下命令即可同时启动前后端：

```powershell
# 启动后端（新窗口）
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$pwd\backend'; .venv\Scripts\activate; uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"

# 启动前端（新窗口）
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$pwd\frontend'; npm.cmd run dev -- --host 0.0.0.0"
```

> 前端命令使用 `npm.cmd` 而非 `npm`，以避免 PowerShell 执行策略阻止 npm.ps1。

## 验收命令

快速验证项目各模块正常：

```bash
# 1. 后端测试
cd "D:\File\exam system"
backend\.venv\Scripts\python.exe -m pytest backend/tests -v

# 2. 前端构建
cd frontend
npm.cmd run build

# 3. 后端健康检查（需先启动后端）
curl http://127.0.0.1:8000/health
# 预期返回：{"status":"ok"}
```

后端测试覆盖：注册/登录、题目 CRUD、批量导入、刷题提交、错题本，共 58+ 个测试用例，使用 SQLite 内存数据库隔离测试数据。

## Git 初始化

本项目尚未初始化 Git 仓库。如需版本管理，请在根目录执行：

```bash
git init
git add .
git commit -m "初始提交"
```

> 请确保 `.env` 文件未被提交——`.gitignore` 已配置忽略 `.env`，提交前务必确认。
