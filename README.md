# 学习宝

> [!IMPORTANT]
> **项目所有者、Codex、DeepSeek、GLM 及其他执行窗口，在开始任何操作前，必须先阅读 [README-开始工作前必读.md](./README-开始工作前必读.md)。**

基于 Vue 3 + FastAPI 的全栈刷题复习系统，支持课程管理、我的题库、公共题库、随机刷题、错题本、间隔复习、学习小组、课程分享、考试与成绩分析、帮助反馈、AI 对话、Word/PDF/PPT/图片预览导入等功能。

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

## 技术栈

| 层级   | 技术                                         |
| ------ | -------------------------------------------- |
| 前端   | Vue 3 + Vite + Vue Router + Pinia + Tailwind CSS 4 + Axios + TypeScript + Vue I18n |
| 测试   | pytest（后端 300+）/ Vitest（前端）/ Playwright（E2E 与视觉回归） |
| 后端   | Python 3.11+ / FastAPI + SQLAlchemy + Alembic |
| 数据库 | 开发：SQLite / 生产：推荐 PostgreSQL         |
| 认证   | HttpOnly Cookie（浏览器）+ JWT Bearer（兼容客户端） |
| 限流   | 内存（开发）/ Redis（生产，可选）             |
| 部署   | Docker + docker-compose                      |

## 项目结构

```
xuexibao/
├── backend/             # FastAPI 后端
│   ├── main.py          # 应用入口
│   ├── config.py        # 环境配置（含生产环境安全校验）
│   ├── models.py        # SQLAlchemy 数据模型
│   ├── schemas.py       # Pydantic 校验模型
│   ├── crud_common.py   # 通用数据库操作
│   ├── routers/         # API 路由（auth、courses、practice、exams、imports、feedback、study_groups…）
│   ├── services/        # 业务服务（导入、AI 客户端、课程、考试…）
│   ├── repositories/    # 数据访问层
│   ├── migrations/      # Alembic 数据库迁移
│   └── tests/           # pytest 测试
├── docs/                # 文档（验收清单、毕业论文材料、运维日志、beta 指南）
├── scripts/             # 工具脚本
│   ├── start-beta.ps1   # Beta 一键启动（构建前端 + 后端 + 网关 + 隧道）
│   ├── stop-beta.ps1    # 停止 Beta 全部服务
│   ├── beta_gateway.py  # 8080 网关（伺服 dist、代理 /api）
│   ├── security_check.py        # 安全检查
│   └── smoke_test.ps1           # 冒烟测试
├── frontend/            # Vue 3 前端（TypeScript）
│   └── src/
│       ├── views/       # 页面组件
│       ├── components/  # 可复用组件（按业务域分组）
│       ├── layouts/     # 页面布局（AppLayout / AuthLayout）
│       ├── api/         # API 请求封装（TS）
│       ├── composables/ # 可组合逻辑
│       ├── stores/      # 全局状态
│       ├── types/       # TS 类型定义
│       ├── i18n/        # 国际化（vue-i18n）
│       ├── router.ts    # 路由配置
│       └── main.ts      # 应用入口
└── .gitignore
```

## 快速启动

### 方式一：Docker（推荐生产/一键启动）

```bash
# 1. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env：至少设置 SECRET_KEY、INVITE_CODE

# 2. 启动全部服务
docker compose up -d

# 应用与 API → http://localhost:8080
# 后端 8000 仅在 Compose 内网，由 Nginx 反向代理，不直接暴露到主机
```

### 方式二：本地开发

后端（**必须从项目根目录启动**，模块路径 `backend.main` 依赖根目录在 `sys.path` 中）：

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\activate
pip install -r backend\requirements.txt
copy backend\.env.example backend\.env
backend\.venv\Scripts\uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

> 日常使用不要加 `--reload`，避免 AI 导入时后端因文件变动自动重启。开发环境默认邀请码 `dev-invite`。

前端：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev -- --host 0.0.0.0
```

> **Windows PowerShell 提示**：如果 `npm` 提示执行策略错误，请使用 `npm.cmd` 代替 `npm`。浏览器打开 http://127.0.0.1:5173

### 方式三：Beta 模式（日常自用 / 微信访问）

```powershell
.\scripts\start-beta.ps1
```

脚本会自动构建前端、启动后端（8000）和 Beta 网关（8080，伺服 `frontend/dist` 并把 `/api` 反向代理到后端），并启动 cloudflared 隧道：

- 本地访问：http://127.0.0.1:8080
- 外网访问：cloudflared 隧道域名（微信内置浏览器可直接打开）
- 停止全部服务：`.\scripts\stop-beta.ps1`

> Beta 构建固定使用 `VITE_API_BASE_URL=/api` 和 `VITE_APP_ENV=beta`，与网关的 `/api` 代理配套。手动执行 `npm run build` 时漏设这两个变量，会导致登录请求打到错误路径而收不到 token。详见 [docs/beta-testing.md](docs/beta-testing.md)。

## 常用功能

### 课程与题目管理

- **创建课程**：进入"我的课程"，填写名称、描述、科目
- **手动添加题目**：单选题、多选题、判断题、填空题、简答题
- **批量导入**：通过 JSON 数组或 Word/PPT 文件批量导入
- **发布与撤回**：整门课程或单道题目均可发布为公开/撤回为私有（`/courses/{id}/publish|unpublish`、`/questions/{id}/publish|unpublish`），仅所有者可操作

### 学习小组、课程分享与考试

- **学习小组**：创建小组、邀请成员、共享课程，小组内可发起小组考试
- **课程分享链接**：生成只读分享链接（share token），无需登录即可浏览课程内容
- **考试**：从课程抽题组卷、定时开考、自动判分，支持考试分享链接
- **成绩分析**：按题型/知识点统计正确率，定位薄弱项
- **帮助反馈**：用户提交问题反馈，管理员在后台跟进处理

### Word/PDF/PPT/图片预览导入

文件上传采用**预览 → 修改 → 确认**三步流程，不是直接写入数据库：

1. **上传文件**（`POST /imports/file/preview`）：后端提取文本或图片后调用 AI 解析为题目数组
2. **预览与修改**：前端展示解析结果，用户可编辑题目字段
3. **确认导入**（`POST /imports/confirm`）：后端校验后统一写入数据库

AI 解析错误不会直接入库，用户对导入内容有完全控制权。支持：`.docx` / `.pdf` / `.pptx` / 图片（`.png .jpg .jpeg .webp`）。旧版 `.ppt` 需另存为 `.pptx` 后上传；图片识别依赖多模态模型，扫描版 PDF 建议导出为图片。大文件超时排查见 [配置详解](docs/configuration.md#ai-导入超时排查)。

### 间隔复习

每次提交答案后自动更新该题的复习状态：

| review_level | 下次复习间隔 | 说明 |
|---|---|---|
| 0 | 未开始 | 初次创建，或重置后 |
| 1 | 1 天 | 第一次答对 |
| 2 | 3 天 | 连续第二次答对 |
| 3 | 7 天 | 连续第三次答对 |
| 4 | 14 天 | 持续稳定的掌握 |
| 5 | 30 天 | 完全掌握，低频复习 |

答错时降级（review_level 减 1，最低 0），连续答错积累到错题本。复习入口：`/practice/review/due`（到期复习）、`/practice/review/wrong`（错题复习）、`/practice/review/today`（今日建议）。

### 填空 `||` 与简答 `&&` 答案规则

**填空题**：用 `||` 分隔多个可接受答案，答对其一即判对（`"TCP||传输控制协议"`）。

**简答题**：`||` 同填空（多选一）；`&&` 要求所有关键词都出现在用户答案中，顺序无关（`"冒泡排序&&交换&&相邻"`）。

> 比较时会忽略：首尾空格、全角/半角标点、大小写（英文）、多余空白。

## 移动端访问

同一个局域网内用手机访问：

1. 查看电脑局域网 IP（如 `192.168.1.8`）
2. 手机浏览器打开 `http://192.168.1.8:5173`（前端已 `--host 0.0.0.0`）
3. 如需绕过 Vite 代理直连后端，设置 `VITE_API_BASE_URL=http://192.168.1.8:8000` 并把该来源加入后端 `CORS_ORIGINS`

## 安全提醒

- `backend/.env`、`backend/xuexibao.db`、`uploads/`、日志一律不进 Git（`.gitignore` 已拦截）
- **生产环境必须修改**：`SECRET_KEY`（随机长密钥）、`INVITE_CODE`、`CORS_ORIGINS`，并设置 `APP_ENV=production`
- 不要在日志、截图或文档中暴露 API Key / SECRET_KEY
- 完整发布前检查清单见 [docs/ops/maintenance.md](docs/ops/maintenance.md)

## 文档导航

| 主题 | 位置 |
| --- | --- |
| 配置详解（环境变量 / SECRET_KEY / AI 接口 / 数据库 / 限流） | [docs/configuration.md](docs/configuration.md) |
| API 文档（Swagger 自动生成，与代码实时同步） | 启动后端后访问 http://127.0.0.1:8000/docs |
| 运维规范（维护规则 / 验收命令 / 公开前检查） | [docs/ops/maintenance.md](docs/ops/maintenance.md) |
| Beta 测试环境说明 | [docs/beta-testing.md](docs/beta-testing.md) |
| 课程作业与毕业论文材料 | [docs/thesis/](docs/thesis/README.md) |
| 验收清单 | [docs/acceptance-checklist.md](docs/acceptance-checklist.md) |
