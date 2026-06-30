# 学习宝 — 大刀阔斧改造设计

- **状态**：已批准，待写实施计划
- **日期**：2026-06-27
- **作者**：ZCode brainstorming session
- **策略**：分阶段渐进式改造（4 个 Phase，总计约 8–12 周）

---

## 1. 背景与目标

### 1.1 现状

"学习宝"是一个全栈 Web 应用：

- **前端**：Vue 3 + TypeScript + Vite 6 + Vue Router + Axios + Vue I18n
- **后端**：Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **基础设施**：Docker + Nginx + GitHub Actions CI

核心功能：题库管理、AI 导入题目、随机练习、错题本、间隔复习、AI 聊天、公共题库。

### 1.2 主要痛点

经代码审查识别出以下问题（分类汇总）：

**前端**

- `frontend/src/style.css` 为 **43KB 巨石文件**，全局样式无模块化
- 17 个页面全部**静态 import**，无路由懒加载，首屏加载所有代码
- **无状态管理**：auth 和 AI 导入任务用裸 TS 模块模拟 store，数据散落组件内
- 巨石组件：`ImportQuestions.vue`（~23KB）、`CourseDetail.vue`（~12KB）、`PracticeHub.vue`（~10KB）
- CI 仅跑 `npm run build`，**前端测试未纳入 CI**

**后端**

- `backend/services/imports_service.py` 为 **22KB God Service**，混合文件解析、AI 提取、状态管理、结果处理
- CRUD 模块（`crud.py`、`crud_courses.py`、`crud_practice.py`、`crud_questions.py`、`crud_wrongbook.py`）大量重复的 `paginate` 模式
- Router 直接调用 CRUD，**无 Service 层**，业务逻辑散落 router
- `config.py` 用裸 dict 而非类型安全的配置

**架构 / 基础设施**

- 缺少统一的代码规范工具链（ESLint flat config、Ruff）
- Docker 镜像未做缓存层优化
- 缺少结构化日志和请求追踪

### 1.3 改造目标

用户确认的四大目标（全选）：

1. **全面架构升级**：从"能用的项目"升级为"工程化项目"
2. **用户体验革新**：UI 设计系统、动画、移动端、数据可视化
3. **功能大幅扩展**：考试模式、协作权限、学习路径、离线支持
4. **代码质量革命**：消灭技术债务，拆分巨石，补全测试

### 1.4 非目标

- 不切换到微服务架构（保持单体重构）
- 不更换后端语言/框架（保持 FastAPI）
- 不引入新的数据库（保持 SQLAlchemy + Alembic）

---

## 2. 实施策略

采用**分阶段渐进式改造**，每个 Phase 产出可独立交付、独立测试、独立部署的增量版本。

| Phase | 主题 | 周期 | 核心产出 |
|---|---|---|---|
| Phase 1 | 代码质量革命 | 1–2 周 | 拆巨石、通用 CRUD、Pinia 引入、测试补全 |
| Phase 2 | 架构升级 | 2–3 周 | shadcn-vue + Tailwind、Service 层、三层架构、新数据模型 |
| Phase 3 | 产品升级 | 3–4 周 | 考试模式、权限系统、UI 革新、移动端、动画 |
| Phase 4 | 差异化功能 | 2–3 周 | 智能推荐、数据分析、PWA 离线、工具增强 |

每个 Phase 的原则：

- **行为保持**：Phase 1–2 不改变面向用户的功能，只改内部结构
- **增量迁移**：避免一次性全量替换，按页面/模块逐步迁移
- **持续可测**：每个子任务完成后即可运行测试验证

---

## 3. Phase 1 — 代码质量革命

> 目标：消灭技术债务，建立可维护的代码基座。不改功能、不改架构，只改代码质量。

### 3.1 前端 — CSS 拆分（当前：43KB 单文件）

**现状**：`frontend/src/style.css` 为 43KB 巨石文件，包含所有全局样式。

**改造**：

- 废弃 `style.css`
- 引入 **Tailwind CSS v4** 作为基础样式系统
- 引入 **shadcn-vue** 组件库（基于 Radix Vue + Tailwind）
- 现有自定义样式按功能拆分：
  - `src/styles/base.css` — CSS 变量（主题色、间距、圆角等 design tokens）
  - `src/styles/transitions.css` — 动画 / 过渡
  - `src/styles/utilities.css` — 少量 Tailwind 覆盖不到的自定义工具类
- 组件级样式全部使用 Tailwind class + shadcn-vue 组件，不再写独立 CSS 文件

### 3.2 前端 — 路由懒加载

**现状**：17 个页面组件全部静态 import，首屏加载所有代码。

**改造**：

- 所有路由改为动态导入 `() => import('./views/XXX.vue')`
- 为常用页面（Home、CourseList）添加 prefetch 提示
- 添加路由级 loading 状态（`Suspense` + 骨架屏）

### 3.3 前端 — 引入 Pinia 状态管理

**现状**：零状态管理，auth 和 AI 导入任务用裸 TS 模块模拟 store，其余数据散落组件内。

**改造**：引入 Pinia，创建初始 stores：

- `useAuthStore` — 替代现有 `stores/auth.ts`
- `useImportStore` — AI 导入任务状态机（替代现有 `stores/aiImportTask.ts`）
- `useNotificationStore` — 全局 toast / 通知

后续 Phase 2 会继续扩展 store 体系。消除组件间 props drilling 和重复 API 调用。

### 3.4 前端 — 拆分巨石组件

| 当前文件 | 大小 | 拆分方案 |
|---|---|---|
| `ImportQuestions.vue` | ~23KB | 拆为：`ImportFileUpload`、`ImportAiConfig`、`ImportPreview`（已有但未充分使用）、`ImportResultList`、`ImportTaskMonitor` |
| `CourseDetail.vue` | ~12KB | 提取 `CourseQuestionList` 和 `CoursePracticeSettings` 子组件 |
| `PracticeHub.vue` | ~10KB | 提取 `DailyStatsCard` 和 `QuickPracticeEntry` 子组件 |

### 3.5 后端 — 拆分 God Service

**现状**：`backend/services/imports_service.py` 为 22KB 巨型服务，混合文件解析、AI 提取、状态管理、结果处理。

**改造**：

```
services/
├── imports/
│   ├── file_parser.py          # 文件读取 + python-docx/python-pptx 解析
│   ├── ai_extractor.py         # AI 提取逻辑（调用 ai_client）
│   ├── import_orchestrator.py  # 导入流程编排（解析→提取→验证→入库）
│   └── import_validator.py     # 题目格式验证、去重
├── ai_client.py                 # OpenAI 客户端封装（保持）
```

### 3.6 后端 — 提取通用 CRUD 基类

**现状**：CRUD 模块大量重复的 `paginate(query, page, page_size)` 模式。

**改造**：创建泛型基类：

```python
# backend/crud_base.py
class GenericCRUD(Generic[ModelType, CreateSchema, UpdateSchema]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, db, id: int) -> ModelType: ...
    async def get_list(self, db, *, skip=0, limit=100, **filters) -> list[ModelType]: ...
    async def create(self, db, obj_in: CreateSchema, **extra) -> ModelType: ...
    async def update(self, db, id: int, obj_in: UpdateSchema) -> ModelType: ...
    async def delete(self, db, id: int) -> None: ...
    async def paginate(self, db, *, page=1, page_size=20, **filters) -> PaginatedResult: ...
```

各 CRUD 模块只需继承基类并添加特有方法。

### 3.7 后端 — 结构化日志 + 配置现代化

- `config.py` 从裸 dict 改为 **Pydantic Settings**（`from pydantic_settings import BaseSettings`），类型安全、支持 `.env` 校验
- 引入 **structlog** 替代 `print/logging`，JSON 格式输出，便于日志分析
- 添加 request-id 中间件，贯穿请求全链路

### 3.8 测试补全

- **前端**：CI 中启用 `npm run test`（当前仅 build，不跑测试）
- **后端**：为新增的 Service 层补充单元测试，目标覆盖率 ≥ 80%
- 添加 E2E smoke test，覆盖核心流程：注册 → 登录 → 创建课程 → 练习 → 查错题

### 3.9 Phase 1 验收标准

- [ ] `style.css` 不再存在，所有样式通过 Tailwind + 少量模块化 CSS
- [ ] 所有路由使用动态 import，首屏 JS 体积下降可量化
- [ ] Pinia stores 替代裸模块，无新增裸 TS store
- [ ] 三个巨石组件拆分完成，单文件不超过 400 行
- [ ] `imports_service.py` 拆分为 4 个职责单一的模块
- [ ] `GenericCRUD` 基类被至少 3 个 repo 复用
- [ ] CI 同时跑前后端测试并通过
- [ ] 现有 300+ 后端测试全部通过，前端测试通过

---

## 4. Phase 2 — 架构升级

> 目标：将架构从"学生项目"升级为"生产级工程"。引入现代框架、规范分层、完善基础设施。

### 4.1 前端 UI 体系重建 — shadcn-vue + Tailwind CSS

**Design System 基础设施**：

- 配置 Tailwind v4，定义主题色板（基于现有 CSS 变量迁移）
- 安装 shadcn-vue CLI，按需生成基础组件（Button、Card、Dialog、Table、Form、Tabs 等 20+ 组件）
- 建立设计 token 系统（`src/styles/tokens.css`）：
  - 颜色：`--color-primary`、`--color-success`、`--color-warning`、`--color-danger`
  - 圆角：`--radius-sm`、`--radius-md`、`--radius-lg`

**全局布局重做**：

- `AppLayout.vue` 使用 shadcn-vue 的 `Sidebar` + `Sheet`（移动端抽屉）
- 顶部导航栏：用户头像、通知铃铛、全局搜索入口
- 支持暗色模式切换（Tailwind `dark:` 前缀 + CSS 变量）

**页面逐步迁移策略**：

- 每个页面迁移时：手写 HTML → shadcn-vue 组件 + Tailwind class
- 按页面重要性排序迁移：Login/Register → Home → CourseList → CourseDetail → Practice（核心路径优先）
- 不做一次性全量替换

### 4.2 前端 — 完整 Pinia Store 体系

Phase 1 引入 Pinia 后，Phase 2 进一步完善：

```
stores/
├── auth.ts              # 认证状态 + token 管理
├── course.ts            # 课程 CRUD + 缓存
├── practice.ts          # 练习会话状态机
├── notification.ts      # 全局通知 / toast
├── import.ts            # AI 导入任务
├── theme.ts             # 主题 / 暗色模式
└── ui.ts                # UI 状态（侧边栏展开、全局 loading）
```

**数据缓存策略**：

- `course.ts` 内置 stale-while-revalidate 缓存：首次加载后缓存，后台静默刷新
- 避免页面切换时重复请求相同数据

### 4.3 后端 — Service 层 + 依赖注入

**现状**：Router → 直接调用 CRUD 函数，没有 Service 层，业务逻辑散落在 router 中。

**改造为三层架构**：

```
backend/
├── api/                  # FastAPI 路由层（薄层，只做参数校验和响应格式化）
│   ├── deps.py           # 依赖注入（get_db, get_current_user, get_service）
│   ├── auth.py
│   ├── courses.py
│   ├── practice.py
│   └── ...
├── services/             # 业务逻辑层（所有业务规则集中在此）
│   ├── auth_service.py
│   ├── course_service.py
│   ├── practice_service.py
│   ├── import_service/   # Phase 1 已拆分的导入服务
│   ├── exam_service.py   # Phase 3 新增
│   └── analytics_service.py  # Phase 4 新增
├── repositories/         # 数据访问层（CRUD，Phase 1 已有通用基类）
│   ├── base.py
│   ├── user_repo.py
│   ├── course_repo.py
│   ├── question_repo.py
│   ├── practice_repo.py
│   └── review_repo.py
├── models.py             # SQLAlchemy 模型（保持，可能微调）
├── schemas.py            # Pydantic 模型（保持）
└── config.py             # Pydantic Settings（Phase 1 已改）
```

**三层分离原则**：

- **Router (api/)**：只做 HTTP 关心事（参数解析、状态码、响应格式）
- **Service (services/)**：业务逻辑、跨 Repository 编排、AI 调用
- **Repository (repositories/)**：纯粹的数据 CRUD，不关心业务

**依赖注入模式**：

```python
# api/deps.py
def get_course_service(db = Depends(get_db)) -> CourseService:
    return CourseService(CourseRepository(db), QuestionRepository(db))
```

### 4.4 后端 — 数据库模型扩展（为 Phase 3/4 预铺路）

在现有 6 个模型基础上，通过 Alembic migration 增量新增（不影响现有数据）：

```python
class Role(Base):                    # 角色表
    id, name (admin/teacher/student)

class Exam(Base):                    # 考试表（Phase 3）
    id, title, course_id, creator_id, time_limit, total_score
    is_shuffle, is_blind, status (draft/published/closed)

class ExamQuestion(Base):            # 考试-题目关联
    id, exam_id, question_id, score, order_index

class ExamSubmission(Base):          # 考试提交
    id, exam_id, user_id, started_at, submitted_at, score, is_passed

class Collaboration(Base):           # 协作关系表
    id, course_id, user_id, role (owner/editor/viewer), invited_by

class StudyGoal(Base):               # 学习目标
    id, user_id, title, target_count, deadline, progress

class Bookmark(Base):                # 收藏
    id, user_id, question_id, folder_name, created_at
```

### 4.5 基础设施升级

- **CI 完整化**：GitHub Actions 同时跑 backend pytest + frontend vitest + lint
- **代码规范**：前端 ESLint (flat config) + Prettier；后端 Ruff（替代 flake8）
- **Pre-commit hooks**：husky（前端）+ pre-commit（后端），提交前自动 lint + format + type-check
- **Docker 优化**：multi-stage build 缓存层优化，镜像体积减半
- **Nginx**：增加缓存策略（API 长缓存 + 静态资源 hash 缓存）

### 4.6 Phase 2 验收标准

- [ ] Tailwind v4 配置完成，shadcn-vue 基础组件库就位
- [ ] 至少 5 个核心页面完成 shadcn-vue 迁移
- [ ] 暗色模式可用并持久化
- [ ] 后端三层架构（api/services/repositories）建立，所有路由迁移完成
- [ ] 依赖注入工作正常，无直接 import service 实例
- [ ] 新增数据模型通过 Alembic migration 创建并回填
- [ ] ESLint + Ruff + Prettier 全量通过，pre-commit hooks 生效
- [ ] Docker 镜像体积较改造前减少 ≥ 30%

---

## 5. Phase 3 — 产品升级

> 目标：产品级体验。让系统从"刷题工具"变成"完整的考试学习平台"。

### 5.1 考试模式（核心新功能）

**考试 vs 练习的区别**：

| | 练习（现有） | 考试（新增） |
|---|---|---|
| 题目来源 | 随机 / 手动选题 | 考试创建者指定 |
| 计时 | 无 | 倒计时，到时自动提交 |
| 回看 | 可以 | 不可回看已答题目 |
| 题序 | 固定 | 可选择乱序 |
| 评分 | 即时 | 交卷后统一评分 |
| 结果 | 简单对 / 错 | 成绩报告 + 排行榜 |

**考试创建流程**：

```
创建考试 → 选择题库 → 勾选题目（自动/手动）→ 设置分值/时限/规则 → 发布
```

**考试界面**：

- 顶部固定栏：考试名称、倒计时、进度条、交卷按钮
- 左侧题目导航面板：已答 / 未答 / 标记状态
- 中间答题区域
- 交卷确认弹窗 + 防误触

**考试结果**：

- 个人成绩报告：总分、各题型得分率、用时、排名
- 管理员视角：所有提交列表、平均分、得分分布图

**新增 API**（基于 Phase 2 的 Exam / ExamQuestion / ExamSubmission 模型）：

- `POST /exams` 创建考试（Teacher+）
- `GET /exams` 列表（按角色过滤）
- `POST /exams/{id}/submit` 提交答卷
- `GET /exams/{id}/result` 成绩报告
- `GET /exams/{id}/leaderboard` 排行榜

### 5.2 多人协作 & 权限系统

**角色定义**：

| 角色 | 权限 |
|---|---|
| **Admin** | 全系统管理（用户管理、系统配置、公告管理） |
| **Teacher** | 创建题库 / 考试、邀请协作者、审核题目 |
| **Student** | 练习、考试、查错题、查看公共题库 |

**权限实现**：

```python
# services/auth_service.py
class Permission:
    COURSE_CREATE = "course:create"
    COURSE_EDIT = "course:edit"       # 需要 owner 或 editor 角色
    COURSE_DELETE = "course:delete"   # 仅 owner
    EXAM_CREATE = "exam:create"       # Teacher+
    EXAM_PUBLISH = "exam:publish"     # Teacher+
    USER_MANAGE = "user:manage"       # Admin
```

- 路由装饰器 `@require_permission("course:create")`
- 题库协作：Owner 邀请 Editor/Viewer，通过邀请链接或用户名搜索

**管理后台页面（新增）**：

- `/admin/users` — 用户列表（禁用 / 启用 / 角色修改）
- `/admin/announcements` — 公告管理
- `/admin/stats` — 全局统计数据

### 5.3 UI 体验全面革新

**设计理念**：从"后台管理系统风格"升级为"现代学习平台风格"。

**关键改进**：

1. **全新首页**：
   - 欢迎区域：用户名 + 今日学习目标进度
   - 每日数据卡片：练习数、正确率、连续天数（streak）
   - 快速操作：继续上次练习、待复习题目、即将到来的考试
   - 学习热力图（类似 GitHub contribution graph）

2. **练习体验升级**：
   - 题目间滑动切换（支持左右滑动手势 + 键盘快捷键 ←→）
   - 答题后即时动画反馈（正确绿色脉冲 ✗ 错误红色抖动）
   - 做题进度条 + 预估剩余时间
   - 底部操作栏：上一题、下一题、收藏、标记不确定

3. **移动端适配**：
   - Sidebar → 底部 Tab Bar（首页、课程、练习、我的）
   - 卡片布局替代表格布局
   - 触摸优化：按钮最小 44px，间距加大

4. **动画体系**：
   - 页面切换过渡（`<Transition>` + 路由 meta）
   - 列表项入场动画（stagger）
   - 数字变化动画（分数、统计数字）
   - 加载骨架屏（shadcn-vue Skeleton 组件）

5. **键盘快捷键**：
   - `←/→` 或 `A/D`：切换题目
   - `1-5`：选择题选项
   - `Enter`：确认 / 下一题
   - `Esc`：退出 / 取消

### 5.4 响应式 & 暗色模式

- 使用 Tailwind 的 `sm:` / `md:` / `lg:` 断点系统
- 暗色模式：`<html class="dark">` + Tailwind `dark:` 前缀
- 主题切换持久化到 localStorage + 用户偏好同步

### 5.5 Phase 3 验收标准

- [ ] 考试模式端到端可用：创建 → 发布 → 答题 → 交卷 → 成绩报告
- [ ] 三种角色权限正确隔离，越权访问被拒绝（有测试覆盖）
- [ ] 管理后台三页面可用
- [ ] 首页数据卡片 + 学习热力图渲染正确
- [ ] 练习页面支持键盘快捷键和滑动手势
- [ ] 移动端布局在 375px 宽度下无溢出
- [ ] 暗色模式全页面无样式破损

---

## 6. Phase 4 — 差异化功能

> 目标：差异化竞争力。让系统不只是"刷题工具"，而是"智能学习伙伴"。

### 6.1 智能学习路径

**数据基础**：

- 追踪每道题的练习次数、正确率、最后一次正确时间
- 基于知识点维度聚合（通过题目标签 / 分类实现）

**知识点标签系统（新增）**：

```python
class Tag(Base):
    id, name, color, parent_id  # 支持层级（如：高数 → 微积分 → 极限）

class QuestionTag(Base):
    question_id, tag_id
```

- AI 导入时自动建议标签
- 手动为题目添加 / 修改标签

**艾宾浩斯复习曲线**：

```
复习等级 0 → 1 → 2 → 3 → 4 → 5
间隔     立即  1天  3天  7天  15天  30天
```

- 可视化：日历视图标记"今日待复习"
- 现有 `UserQuestionReview` 已有基础，Phase 4 优化算法

**智能推荐引擎**：

- 分析用户在各知识点的正确率
- 每日生成"今日推荐"：优先推送正确率 < 70% 的知识点 + 到期待复习题目
- "薄弱项练习"模式：自动筛选错误率最高的 20 道题

**学习路径可视化**：

```
src/views/StudyOverview.vue  (重构为数据仪表盘)
├── 学习热力图（过去 30/90 天）
├── 知识点雷达图（正确率 × 练习量）
├── 艾宾浩斯复习日历
├── 每周/每月趋势折线图
└── 薄弱知识点 Top 10 列表
```

图表库：**Chart.js**（轻量）或 **ECharts**（功能丰富），实施计划阶段定。

### 6.2 数据分析仪表盘

**学生视角**：

- 总练习量、累计时长、总正确率
- 各题型正确率对比（饼图）
- 知识点掌握度（热力矩阵）
- 学习趋势（折线图：每日练习量、正确率变化）
- 学习连续天数（streak）及最长记录
- 与"平均用户"对比

**教师 / 管理员视角**（需 Teacher+ 权限）：

- 题库使用统计：各课程练习人数、平均分
- 考试成绩分布（正态分布图）
- 学生活跃度排名
- 知识点级错误率热力图（一眼看出哪些知识点是共性问题）

### 6.3 离线支持（PWA）

**Service Worker 策略**：

```
静态资源：Cache-First（版本化 hash，长期缓存）
API 数据：Network-First（在线时走网络，离线时走缓存）
离线页面：用户可练习已缓存的题目
```

**离线功能范围**：

- ✅ 已缓存的题库练习
- ✅ 错题本浏览
- ✅ 复习提醒（本地 Notification）
- ❌ AI 聊天（需在线）
- ❌ 提交成绩（离线队列，上线后自动同步）

**实现方式**：

- 使用 **Workbox** 管理 Service Worker
- IndexedDB 存储离线题目数据
- 离线队列模式：离线期间的练习记录暂存 IndexedDB，上线后批量同步

### 6.4 工具增强

**数据导出**：

- 题库导出：JSON / Excel 格式
- 练习记录导出：CSV 格式
- 错题本导出：PDF（带答案解析）

**题目收藏 & 标记**：

- 收夹功能：按文件夹组织收藏的题目（基于 Phase 2 的 Bookmark 模型）
- 标记系统：⭐ 重点、🔴 易错、💡 有趣
- 标记筛选练习

**快捷操作增强**：

- 全局搜索（Ctrl+K）：搜索题目、课程、考试
- 批量操作：批量删除题目、批量移动到其他课程
- 拖拽排序：题目在课程内的手动排序

### 6.5 Phase 4 验收标准

- [ ] 知识点标签系统可用，AI 导入可自动建议标签
- [ ] 智能推荐"今日推荐"基于真实练习数据生成
- [ ] 数据分析仪表盘 5+ 图表正确渲染
- [ ] 教师视角统计数据正确（聚合逻辑有测试）
- [ ] PWA 安装可用，离线状态下可练习已缓存题库
- [ ] 离线练习记录上线后成功同步
- [ ] 数据导出 3 种格式（JSON/Excel/CSV）可用
- [ ] 全局搜索（Ctrl+K）可搜索题目、课程、考试

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| Phase 1–2 迁移过程中引入回归 bug | 功能异常 | 每个子任务后跑全量测试；保持 Phase 1–2 行为不变 |
| Tailwind 迁移导致样式大面积破损 | UI 不可用 | 按页面逐个迁移，每页面迁移后视觉对比验证 |
| 后端三层架构迁移工作量超预期 | 延期 | Router 一个一个迁移，保持旧 CRUD 函数可调用直到迁移完成 |
| 新增功能（考试/权限）模型设计返工 | 架构不稳 | Phase 2 预先定义模型，Phase 3 实现时如需调整走 Alembic migration |
| 离线同步冲突（PWA） | 数据不一致 | 离线队列只追加不修改，同步时以服务端为准，冲突提示用户 |

---

## 8. 测试策略

贯穿所有 Phase 的测试要求：

- **单元测试**：每个新 Service / Repository / composable 都有对应测试
- **集成测试**：每个新 API 端点都有 happy path + error path 测试
- **回归测试**：Phase 1–2 迁移过程中，原有 300+ 后端测试必须全程通过
- **E2E 测试**：核心流程（注册、登录、创建课程、练习、考试、查错题）有 Playwright/Cypress 覆盖
- **视觉回归**：Phase 3 UI 改造可考虑引入 Storybook + 视觉快照测试

---

## 9. 下一步

本设计文档批准后，进入 **writing-plans** 阶段，为 Phase 1 撰写详细的实施计划（任务分解、依赖关系、验证步骤）。后续 Phase 在前一 Phase 完成后再各自撰写实施计划。
