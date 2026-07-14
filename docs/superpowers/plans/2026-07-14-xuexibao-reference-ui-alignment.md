# 学习宝参考 UI 逐页一致性实现计划

> **面向 AI 代理的工作者：** 必须使用 `subagent-driven-development`（推荐）或 `executing-plans` 逐任务实现本计划。步骤使用复选框跟踪进度。

**目标：** 在不改变 Vue 业务契约的前提下，使 8 个学习宝页面在 390 × 844 视口下与 `exam-platform-ui/pages/*.html` 的模块结构和视觉密度一致，并以视觉回归验证结果作为交付门槛。

**架构：** 保持 Vue 3、TypeScript、Vite、Pinia、Vue Router 和现有 XState 会话。先将公共尺寸和颜色收敛到 `src/styles` 与 `AppLayout`，然后依路由逐页调整已有 Vue 组件；不移植整段静态 HTML，不建立第二套组件库。视觉夹具继续模拟 API，生产页面继续消费真实接口和已有 stores/composables。

**技术栈：** Vue 3、TypeScript、Vite、Vitest、Playwright、Pinia、Vue Router、Lucide。

**权威规格：** `docs/superpowers/specs/2026-07-14-xuexibao-reference-ui-alignment-design.md`。

---

## 文件结构与职责

| 文件或目录 | 职责 |
| --- | --- |
| `frontend/src/styles/base.css`、`liquid-glass.css`、`utilities.css`、`transitions.css` | 唯一的颜色、间距、壳层、字体、安全区和主题令牌来源。 |
| `frontend/src/layouts/AppLayout.vue` | 普通页 420px 应用壳与固定四项底栏；沉浸路由不渲染底栏。 |
| `frontend/src/components/ui/{BottomSheet,FilterTabs,StatGrid}.vue` | 复用交互面板、筛选和统计网格，不创建平行 UI 系统。 |
| `frontend/src/views/{Home,CourseList,ImportQuestions,Mine,CoursePractice}.vue` | 四个主标签页及题库练习的页面结构和真实数据绑定。 |
| `frontend/src/components/practice/*.vue` | 练习顶部、题干、作答、结果和完成弹窗的沉浸流程。 |
| `frontend/src/views/exam/{ExamTake,ExamResult}.vue`、`frontend/src/components/exam/ExamQuestionCard.vue` | 真实考试题序、倒计时、答题卡、交卷与结果视觉。 |
| `frontend/src/views/__tests__/*`、`frontend/src/layouts/__tests__/AppLayout.test.ts`、`frontend/src/components/**/__tests__/*` | 先失败后修复的页面结构、数据状态和交互契约。 |
| `frontend/e2e/visual-fixture.ts`、`visual.spec.ts`、`reference-review.spec.ts` | 受控 API、八页截图、三种尺寸无溢出、暗色冒烟及并排审核。 |
| `exam-platform-ui/` | 只读的视觉参考和交接素材；不从该目录复制示例数据进入生产页面。 |
| `scripts/package_codex_handoff.ps1`、`artifacts/` | 所有测试通过后生成并验证同一 revision 的交接 ZIP。 |

## 任务 1：先锁定可失败的结构验收与视觉审核入口

**文件：**
- 修改：`frontend/e2e/visual.spec.ts`
- 修改：`frontend/e2e/reference-review.spec.ts`
- 修改：`frontend/e2e/visual-fixture.ts`
- 修改：`frontend/src/layouts/__tests__/AppLayout.test.ts`

- [ ] **步骤 1：为壳层与八页截图写失败断言。**

  在 `AppLayout.test.ts` 增加可观察的壳层断言，在 `visual.spec.ts` 为八个固定路由命名截图，并在 `reference-review.spec.ts` 保留对应参考 HTML 的并排产物：

  ```ts
  expect(wrapper.get('[data-testid="app-shell"]').attributes('data-layout')).toBe('tabbed')
  expect(wrapper.get('[data-testid="bottom-tab-home"]').exists()).toBe(true)
  await expect(page).toHaveScreenshot('home.png', { maxDiffPixelRatio: 0.01 })
  ```

- [ ] **步骤 2：运行针对性测试，确认它在旧 DOM 或缺少页面标记时失败。**

  ```powershell
  npm.cmd run test -- --run src/layouts/__tests__/AppLayout.test.ts
  npm.cmd run test:visual -- --grep "home"
  ```

  预期：新断言因没有稳定 `data-testid`、截图名称或对应结构而失败。

- [ ] **步骤 3：仅补充可测试的结构标记和受控夹具。**

  - 在壳和每个页面根节点增加语义化 `data-testid`，不改业务事件；
  - 固定夹具中的时间、用户名、题库、试题、考试和导入任务状态；
  - 每张截图显式设定 `390 × 844` 浅色视口。

- [ ] **步骤 4：重新运行针对性测试。**

  ```powershell
  npm.cmd run test -- --run src/layouts/__tests__/AppLayout.test.ts
  npm.cmd run test:visual -- --grep "home"
  ```

  预期：测试通过，并可生成可与参考页比较的同名截图。

- [ ] **步骤 5：提交测试基线准备。**

  ```powershell
  git add frontend/e2e frontend/src/layouts/__tests__/AppLayout.test.ts frontend/src/layouts/AppLayout.vue
  git commit -m "test: define reference UI structure gates"
  ```

## 任务 2：对齐公共令牌、普通壳和固定四项导航

**文件：**
- 修改：`frontend/src/styles/base.css`
- 修改：`frontend/src/styles/liquid-glass.css`
- 修改：`frontend/src/styles/utilities.css`
- 修改：`frontend/src/style.css`
- 修改：`frontend/src/layouts/AppLayout.vue`
- 测试：`frontend/src/layouts/__tests__/AppLayout.test.ts`

- [ ] **步骤 1：写出普通壳与沉浸壳的失败测试。**

  ```ts
  it('keeps four tabs on ordinary routes and removes them on immersive routes', async () => {
    await router.push('/courses')
    expect(wrapper.get('[data-testid="app-shell"]').attributes('data-layout')).toBe('tabbed')
    expect(wrapper.find('[data-testid="bottom-tabs"]').exists()).toBe(true)
    await router.push('/courses/course-1/practice')
    expect(wrapper.find('[data-testid="bottom-tabs"]').exists()).toBe(false)
  })
  ```

- [ ] **步骤 2：运行并确认旧逻辑或样式约束不满足。**

  ```powershell
  npm.cmd run test -- --run src/layouts/__tests__/AppLayout.test.ts
  ```

  预期：若路由分类或底栏渲染不精确，测试失败。

- [ ] **步骤 3：实现最小令牌和壳层收敛。**

  - `base.css` 定义 `--app-max-width: 420px`、安全区、390 参考间距、浅/深色令牌和字体回退；
  - `liquid-glass.css` 只保留卡片、面板和阴影变体；
  - `AppLayout.vue` 用路由元信息或现有路由名判断普通/沉浸页，普通页固定四个 `router.replace` 标签；
  - `style.css` 不再以宽泛 `body` 和 `!important` 覆盖八个核心页面。

- [ ] **步骤 4：重新运行壳层测试并在三种宽度人工查看。**

  ```powershell
  npm.cmd run test -- --run src/layouts/__tests__/AppLayout.test.ts
  npm.cmd run test:visual -- --grep "no horizontal overflow"
  ```

  预期：普通页存在底栏，沉浸页没有底栏；320、390、420 宽度无横向滚动。

- [ ] **步骤 5：提交公共壳。**

  ```powershell
  git add frontend/src/styles frontend/src/style.css frontend/src/layouts/AppLayout.vue frontend/src/layouts/__tests__/AppLayout.test.ts
  git commit -m "feat: align mobile app shell"
  ```

## 任务 3：首页与题库列表先完成结构轮和视觉轮

**文件：**
- 修改：`frontend/src/views/Home.vue`
- 修改：`frontend/src/views/CourseList.vue`
- 可修改：`frontend/src/components/ui/{FilterTabs,BottomSheet}.vue`
- 测试：`frontend/src/views/__tests__/Home.ux.test.ts`
- 测试：`frontend/src/views/__tests__/CourseList.ux.test.ts`
- 测试：`frontend/src/components/ui/__tests__/{FilterTabs,BottomSheet}.test.ts`

- [ ] **步骤 1：写失败的页面结构与真实数据测试。**

  ```ts
  expect(wrapper.get('[data-testid="home-greeting"]').text()).toContain('测试用户')
  expect(wrapper.findAll('[data-testid="home-overview-card"]')).toHaveLength(1)
  expect(wrapper.findAll('[data-testid="home-recent-course"]')).toHaveLength(2)
  expect(wrapper.findAll('[data-testid="course-filter-tab"]')).toHaveLength(4)
  await wrapper.get('[data-testid="course-filter-published"]').trigger('click')
  expect(fetchCourses).toHaveBeenLastCalledWith(expect.objectContaining({ status: 'published' }))
  ```

- [ ] **步骤 2：运行并确认旧页面与参考骨架的差异被捕获。**

  ```powershell
  npm.cmd run test -- --run src/views/__tests__/Home.ux.test.ts src/views/__tests__/CourseList.ux.test.ts src/components/ui/__tests__/FilterTabs.test.ts src/components/ui/__tests__/BottomSheet.test.ts
  ```

- [ ] **步骤 3：按参考 HTML 重排模板，不改变数据和操作。**

  - 首页固定为绿色欢迎区、今日统计卡、推荐/快捷区和最近题库；直接渲染 `useStudyOverview` 的真实字段；
  - 题库固定为标题搜索、四筛选、紧凑卡片、创建入口；卡片密度匹配参考，但保留编辑、发布、删除和练习底部面板；
  - 题库为空时用原位置空状态替换卡片，不移走创建入口。

- [ ] **步骤 4：运行单测与两张 390 截图。**

  ```powershell
  npm.cmd run test -- --run src/views/__tests__/Home.ux.test.ts src/views/__tests__/CourseList.ux.test.ts src/components/ui/__tests__/FilterTabs.test.ts src/components/ui/__tests__/BottomSheet.test.ts
  npm.cmd run test:visual -- --grep "home|course-list"
  npm.cmd run test:visual:review
  ```

  预期：首页和题库的参考/实现并排图模块顺序、密度和固定底栏一致。

- [ ] **步骤 5：提交首页和题库。**

  ```powershell
  git add frontend/src/views/Home.vue frontend/src/views/CourseList.vue frontend/src/components/ui frontend/src/views/__tests__/Home.ux.test.ts frontend/src/views/__tests__/CourseList.ux.test.ts frontend/e2e
  git commit -m "feat: align home and course reference layouts"
  ```

## 任务 4：对齐“我的”和 AI 导入，并覆盖恢复与空状态

**文件：**
- 修改：`frontend/src/views/Mine.vue`
- 修改：`frontend/src/views/ImportQuestions.vue`
- 可修改：`frontend/src/components/import/{ImportCapabilityStrip,ImportTaskMonitor,ImportPreview}.vue`
- 测试：`frontend/src/views/__tests__/Mine.ux.test.ts`
- 测试：`frontend/src/views/__tests__/ImportQuestions.import.test.ts`
- 测试：`frontend/src/stores/__tests__/aiImportTask.test.ts`

- [ ] **步骤 1：写失败的账号、空字段、导入恢复和结构测试。**

  ```ts
  expect(wrapper.get('[data-testid="mine-profile-header"]').text()).toContain('测试用户')
  expect(wrapper.findAll('[data-testid="mine-stat"]')).toHaveLength(3)
  expect(wrapper.get('[data-testid="mine-level-value"]').text()).toBe('--')
  expect(wrapper.get('[data-testid="import-upload-panel"]').exists()).toBe(true)
  expect(wrapper.get('[data-testid="import-task-monitor"]').text()).toContain('处理中')
  ```

- [ ] **步骤 2：运行并确认旧 DOM、错误数据回退或恢复位置不符合。**

  ```powershell
  npm.cmd run test -- --run src/views/__tests__/Mine.ux.test.ts src/views/__tests__/ImportQuestions.import.test.ts src/stores/__tests__/aiImportTask.test.ts
  ```

- [ ] **步骤 3：实现参考骨架，保持真实状态机。**

  - 我的页固定为绿色账户头图、三项统计、入口网格和主题/退出区；后端缺失等级仅显示 `--`；
  - 导入页固定为独立标题、大上传面板、方式/格式说明与任务/预览区域；
  - 恢复中的异步导入任务在上传面板之后的固定区域呈现，预览确认仍调用当前确认逻辑。

- [ ] **步骤 4：运行单测、两张截图、深色冒烟和 320/420 无溢出检查。**

  ```powershell
  npm.cmd run test -- --run src/views/__tests__/Mine.ux.test.ts src/views/__tests__/ImportQuestions.import.test.ts src/stores/__tests__/aiImportTask.test.ts
  npm.cmd run test:visual -- --grep "mine|ai-import|dark|no horizontal overflow"
  npm.cmd run test:visual:review
  ```

  预期：真实账号和导入恢复功能可用，参考/实现并排图的主区块一致。

- [ ] **步骤 5：提交“我的”和导入。**

  ```powershell
  git add frontend/src/views/Mine.vue frontend/src/views/ImportQuestions.vue frontend/src/components/import frontend/src/views/__tests__/Mine.ux.test.ts frontend/src/views/__tests__/ImportQuestions.import.test.ts frontend/src/stores/__tests__/aiImportTask.test.ts frontend/e2e
  git commit -m "feat: align profile and import reference layouts"
  ```

## 任务 5：对齐题库练习和会话内完成态，不伪造随机题序

**文件：**
- 修改：`frontend/src/views/CoursePractice.vue`
- 修改：`frontend/src/components/practice/{PracticeTopBar,PracticeQuestionStem,PracticeChoiceOptions,PracticeTextAnswer,PracticeResultPanel,PracticeActionBar,PracticeSummaryModal}.vue`
- 测试：`frontend/src/views/__tests__/CoursePractice.test.ts`
- 测试：`frontend/src/components/practice/__tests__/PracticeInteraction.test.ts`

- [ ] **步骤 1：写失败的沉浸结构、随机题序和完成弹窗测试。**

  ```ts
  expect(wrapper.find('[data-testid="bottom-tabs"]').exists()).toBe(false)
  expect(wrapper.get('[data-testid="practice-question-stem"]').exists()).toBe(true)
  expect(wrapper.get('[data-testid="practice-progress-total"]').text()).toBe('--')
  await wrapper.get('[data-testid="practice-submit"]').trigger('click')
  expect(wrapper.get('[data-testid="practice-result-panel"]').exists()).toBe(true)
  expect(wrapper.get('[data-testid="practice-summary-modal"]').attributes('role')).toBe('dialog')
  ```

- [ ] **步骤 2：运行并确认当前页面没有达到参考结构或随机数据约束。**

  ```powershell
  npm.cmd run test -- --run src/views/__tests__/CoursePractice.test.ts src/components/practice/__tests__/PracticeInteraction.test.ts
  ```

- [ ] **步骤 3：最小化重排练习组件。**

  - 顶部只承载返回、真实进度与退出；题干、题型、选项、解析和操作按参考顺序排列；
  - 若会话不能提供完整题数，显示未知状态而非参考示例总数；
  - 完成态继续由 `PracticeSummaryModal` 在当前路由内显示，视觉采用参考完成页的成就、统计、操作层级；
  - 保持原 submit、自动下一题和离线同步事件与 store/composable 调用不变。

- [ ] **步骤 4：运行交互测试和练习/完成态截图。**

  ```powershell
  npm.cmd run test -- --run src/views/__tests__/CoursePractice.test.ts src/components/practice/__tests__/PracticeInteraction.test.ts
  npm.cmd run test:visual -- --grep "course-practice|practice-complete"
  npm.cmd run test:visual:review
  ```

  预期：完成态无新 URL，提交和继续按钮仍驱动既有会话；两张并排图结构一致。

- [ ] **步骤 5：提交题库练习。**

  ```powershell
  git add frontend/src/views/CoursePractice.vue frontend/src/components/practice frontend/src/views/__tests__/CoursePractice.test.ts frontend/e2e
  git commit -m "feat: align course practice reference layout"
  ```

## 任务 6：对齐考试答题和结果态，保持真实倒计时与提交保护

**文件：**
- 修改：`frontend/src/views/exam/ExamTake.vue`
- 修改：`frontend/src/views/exam/ExamResult.vue`
- 可修改：`frontend/src/components/exam/ExamQuestionCard.vue`
- 测试：`frontend/src/views/exam/__tests__/ExamTake.test.ts`
- 测试：`frontend/src/views/exam/__tests__/ExamResult.test.ts`
- 测试：`frontend/src/components/exam/__tests__/ExamQuestionCard.test.ts`

- [ ] **步骤 1：写失败的倒计时、真实题序、模态隔离和结果数据测试。**

  ```ts
  expect(wrapper.get('[data-testid="exam-countdown"]').text()).toMatch(/^\d{2}:\d{2}$/)
  expect(wrapper.findAll('[data-testid="exam-answer-sheet-item"]')).toHaveLength(exam.questions.length)
  await wrapper.get('[data-testid="exam-submit"]').trigger('click')
  expect(wrapper.get('[data-testid="exam-submit-dialog"]').attributes('aria-modal')).toBe('true')
  expect(submitExam).toHaveBeenCalledTimes(1)
  expect(result.get('[data-testid="exam-score"]').text()).toContain('50')
  ```

- [ ] **步骤 2：运行并确认当前 DOM 或状态隔离不足时失败。**

  ```powershell
  npm.cmd run test -- --run src/views/exam/__tests__/ExamTake.test.ts src/views/exam/__tests__/ExamResult.test.ts src/components/exam/__tests__/ExamQuestionCard.test.ts
  ```

- [ ] **步骤 3：按参考层级重排，禁止替换业务时序。**

  - 答题页重排为标题/倒计时、题号/题干、选项、答题卡导航和交卷确认；
  - 答题卡长度仅使用后端真实题序；模态显示时阻断键盘和滑动；
  - 结果页重排为成绩主视觉、真实用时/正确率、逐题结果和排行榜入口；
  - 保持超时一次交卷、弱映射/会话代际重复提交保护与提交成功后的结果交接。

- [ ] **步骤 4：运行测试与两张考试截图。**

  ```powershell
  npm.cmd run test -- --run src/views/exam/__tests__/ExamTake.test.ts src/views/exam/__tests__/ExamResult.test.ts src/components/exam/__tests__/ExamQuestionCard.test.ts
  npm.cmd run test:visual -- --grep "exam-take|exam-complete"
  npm.cmd run test:visual:review
  ```

  预期：固定夹具的结果页显示真实模拟得分，不出现空白结果；答题页不能双重提交。

- [ ] **步骤 5：提交考试流程。**

  ```powershell
  git add frontend/src/views/exam frontend/src/components/exam frontend/e2e
  git commit -m "feat: align exam reference layouts"
  ```

## 任务 7：最终视觉门槛、全量验证和同 revision 交接包

**文件：**
- 修改：`frontend/e2e/__screenshots__/visual-edge/*.png`（只在全部并排审核通过后更新）
- 可修改：`frontend/e2e/visual.spec.ts`
- 可修改：`scripts/package_codex_handoff.ps1`
- 修改：`docs/ops/active/<new-alignment-record>.md` 与 `docs/ops/INDEX.md`（仅新增本次记录，不动用户已有 Pencil 留档）

- [ ] **步骤 1：先使截图基线更新测试失败。**

  ```powershell
  npm.cmd run test:visual
  ```

  预期：结构变化后的旧基线出现截图差异；不要以 `--update-snapshots` 直接掩盖差异。

- [ ] **步骤 2：对每张参考/实现并排图进行人工结构审核。**

  逐张查看首页、题库、题库练习、导入、练习完成、考试答题、考试完成、我的；确认顺序、密度、关键位置和底栏/沉浸壳一致。发现任一不一致，返回对应任务修复。

- [ ] **步骤 3：仅在八页审核通过后更新基线并验证差异阈值。**

  ```powershell
  npm.cmd run test:visual -- --update-snapshots
  npm.cmd run test:visual
  ```

  预期：八张 390 × 844 浅色基线、320 × 720 与 420 × 900 无溢出、四张深色冒烟共 28 个测试均通过，截图差异阈值为 `1%`。

- [ ] **步骤 4：运行完整验收，写入操作记录并生成 ZIP。**

  ```powershell
  npm.cmd run lint
  npm.cmd run test -- --run
  npm.cmd run test:visual
  npm.cmd run build
  git diff --check
  python scripts/security_check.py
  powershell -ExecutionPolicy Bypass -File scripts/package_codex_handoff.ps1
  ```

  预期：所有命令成功；脚本解压验证必需入口、禁止文件和 `MANIFEST.sha256`，ZIP revision 与通过验收的 commit 相同。

- [ ] **步骤 5：提交基线、记录和交接包脚本变化。**

  ```powershell
  git add frontend/e2e docs/ops scripts/package_codex_handoff.ps1
  git commit -m "test: approve reference UI visual baseline"
  ```

  不提交 `artifacts/`、真实 `.env`、`.git`、数据库、上传文件、日志、`.venv`、`node_modules`、`dist`、测试产物、验收截图缓存或 `frontend-preview.html`。

## 计划自检

- 覆盖规格的 8 页、普通/沉浸壳、真实数据、空状态、深色模式、三种视口、视觉并排审核和交接包。
- 每个实施阶段都先写可失败测试，再实现最小修改、重跑测试并独立提交。
- 计划不要求后端、数据库或权限变更，不会移动现有兼容路由或业务状态机。
- 计划内未使用“待定”“后续补充”等占位项；所有提及的路径、命令和验收输出均可执行或可观察。
