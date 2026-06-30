# 学习宝 Backend

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

User ──1:N── WrongRecord (错题本)
User ──1:N── PracticeRecord (练习记录)
User ──1:N── UserQuestionReview (间隔复习状态)
                ├── review_level: 0~5
                ├── next_review_at
                └── consecutive_correct / consecutive_wrong
```

**可见性规则：**
- `private` → 只有题目/课程的创建者（owner）可见
- `public` → 所有人可见
- `owner_id IS NULL` → 向后兼容，等价于公开

**发布与撤回：**
1. 用户创建课程（默认私有）
2. 手动添加或批量导入题目到课程（默认私有）
3. 发布 → 课程/题目变为 `public`，所有用户可见
4. 撤回 → 课程/题目回到 `private`，仅自己可见

## 间隔复习等级

每次提交答案时自动更新复习状态：

| review_level | 间隔 | 触发条件 |
|---|---|---|
| 0 | 未开始 | 初次创建或答错降级到 0 |
| 1 | 1 天 | 答对后升级 |
| 2 | 3 天 | 连续答对升级 |
| 3 | 7 天 | 连续答对升级 |
| 4 | 14 天 | 连续答对升级 |
| 5 | 30 天 | 完全掌握 |

答错时降一级（最低 0），连续答错记录到错题本。

## 答案判分规则

**单选题（single_choice）：** `A` / `a` / `选项A` / `选A` → 归一化为 `A`

**判断题（true_false）：** `正确` / `对` / `True` / `T` → `True`；`错误` / `错` / `False` / `F` → `False`

**多选题（multiple_choice）：** `A,B` / `AB` / `["A","B"]` / `A、B` → 排序后 `A,B`

**填空题（fill_blank）：** 支持 `||` 表示多选一
- `answer = "TCP||传输控制协议"` → 用户答 "TCP" 或 "传输控制协议" 均正确
- 比较时忽略大小写、全角半角、多余空白

**简答题（short_answer）：**
- `||` 多选一（同上）
- `&&` 所有关键词必须出现，顺序无关
  - `answer = "冒泡排序&&交换&&相邻"` → 用户答案需同时包含三个关键词
- 无分隔符时严格归一化匹配

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
# 日常使用不要加 --reload，避免 AI 导入时后端自动重启
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

API 文档自动生成于 http://127.0.0.1:8000/docs

> ⚠️ **必须从项目根目录启动**，因为 Python 模块路径 `backend.main` 依赖于项目根目录在 `sys.path` 中。
> 如果从 `backend/` 目录下直接 `uvicorn main:app` 会报导入错误。

## 环境变量

在 `backend/.env` 中配置（参考 `backend/.env.example`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_ENV` | `development` | 运行环境：`development`（开发）或 `production`（生产） |
| `DATABASE_URL` | `sqlite:///./xuexibao.db` | 数据库连接（开发用 SQLite，生产用 PostgreSQL） |
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

默认使用 SQLite，数据库文件生成在 `backend/xuexibao.db`。零配置即可运行，适合单人本地开发和测试。

```bash
# 重置数据库：删除 db 文件后重启后端即可
del backend\xuexibao.db
```

### PostgreSQL（生产环境）

多人正式使用建议切换到 PostgreSQL：

```bash
# 1. 安装驱动
pip install psycopg2-binary

# 2. 修改 .env
# DATABASE_URL=postgresql://用户名:密码@localhost:5432/xuexibao
```

## AI 接口配置

支持任何 **OpenAI 兼容 API** 的 LLM 服务。推荐使用 Mimo（免费额度）：

```env
# Mimo 示例
OPENAI_API_KEY=<your-api-key>
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

> ⚠️ **安全警告**（提交公开仓库前必读）：
> - ✅ **`backend/.env` 不要提交** — 已在 `.gitignore` 中忽略
> - ✅ **`backend/xuexibao.db` 不要提交** — 包含真实数据
> - ✅ **`uploads/` 不要提交** — 用户上传的文件不应进入仓库
> - ✅ **不要截图、日志或视频中暴露 API Key / SECRET_KEY / 数据库内容**
> - ✅ **公开仓库前运行 `git status` 和 `git grep -n "sk-"` 检查**

## 公开仓库前检查清单

在将本仓库公开之前，请逐项确认：

```markdown
- [ ] `.env` 文件未被 Git 跟踪
- [ ] `backend/xuexibao.db` 未被跟踪
- [ ] `uploads/` 未被跟踪
- [ ] `.env.example` 中不含真实的 API Key（应使用 `<your-api-key>` 占位）
- [ ] 生产环境已设置随机 `SECRET_KEY`
- [ ] 生产环境已修改 `INVITE_CODE`
- [ ] 生产环境已配置 `CORS_ORIGINS`
- [ ] 生产环境已设置 `APP_ENV=production`
- [ ] 运行 `git grep -n "sk-"` 确认无 API Key 硬编码
```

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
| PATCH | `/courses/{course_id}` | 编辑课程（名称/描述/科目） |
| DELETE | `/courses/{course_id}` | 删除课程（只能删自己的） |
| GET | `/courses/{course_id}/questions` | 课程下的题目列表 |
| GET | `/courses/{course_id}/practice/random` | 在课程内随机刷题 |
| POST | `/courses/{course_id}/publish` | 发布课程（课程 + 题目变公开） |
| POST | `/courses/{course_id}/unpublish` | 撤回课程（课程 + 题目回私有） |

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
| POST | `/questions/{question_id}/unpublish` | 撤回单道题回私有 |
| GET | `/questions/meta` | 题目科目/章节筛选元数据 |

### 刷题与判分

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/practice/random` | 从全局可见题目中随机抽题（支持 course_id/type/chapter 筛选） |
| POST | `/practice/submit` | 提交答案并判分，更新错题本 + 间隔复习状态 |
| GET | `/practice/stats` | 练习统计（今日题数、正确率等） |
| GET | `/practice/history` | 练习历史（分页，最新优先） |

### 间隔复习

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/practice/review/wrong` | 错题复习（按错题数权重抽取） |
| GET | `/practice/review/today` | 今日复习建议摘要 |
| GET | `/practice/review/due` | 到期需复习的题目列表（支持 course_id 筛选） |
| GET | `/practice/insights/weak-types` | 薄弱题型分析 |

### 错题本

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/wrongbook/` | 错题本列表（支持分页/筛选） |
| DELETE | `/wrongbook/{question_id}` | 从错题本移除 |
| GET | `/wrongbook/meta` | 错题本科目/章节筛选元数据 |

### 文件导入

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/imports/file` | 上传 .docx/.pdf/.pptx/.png/.jpg/.jpeg/.webp 提取文本或图片内容（最大 10MB） |
| POST | `/imports/file/preview` | 上传文件并用 AI 解析为题目，支持 PPT 内嵌图片和直接图片，返回预览（不入库） |
| POST | `/imports/confirm` | 确认预览后的题目并写入数据库 |
| POST | `/imports/file/auto` | 上传文件并 AI 直接导入（无预览编辑环节） |

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
