# 参考界面到当前 Vue 项目的实现映射

`exam-platform-ui/` 是本轮前端视觉迁移的唯一设计真相。参考 HTML 只定义视觉、布局和交互意图；现有 Vue 代码、API、Pinia 状态和路由契约继续定义真实业务行为。

固定实现栈：Vue 3、TypeScript、Vite、Pinia、Vue Router、Lucide Vue（`@lucide/vue`）。

| 参考文件 | 当前实现 | 真实路由 | 说明 |
| --- | --- | --- | --- |
| `pages/home.html` | `frontend/src/views/Home.vue` | `/` | 四标签底部导航中的“首页” |
| `pages/course-list.html` | `frontend/src/views/CourseList.vue` | `/courses` | 四标签底部导航中的“题库” |
| `pages/course-practice.html` | `frontend/src/views/CoursePractice.vue` | `/courses/:courseId/practice`；别名 `/practice/:courseId` | 沉浸式页面，无底部导航 |
| `pages/ai-import.html` | `frontend/src/views/ImportQuestions.vue` | `/import` | 四标签底部导航中的“导入” |
| `pages/exam-take.html` | `frontend/src/views/exam/ExamTake.vue` | `/exams/:examId/take`；别名 `/exam/:examId` | 沉浸式页面，无底部导航 |
| `pages/practice-complete.html` | `frontend/src/components/practice/PracticeSummaryModal.vue` | 无独立路由 | 练习结束后在练习页内展示，禁止新增 `/practice/complete` |
| `pages/exam-complete.html` | `frontend/src/views/exam/ExamResult.vue` | `/exams/:examId/result` | 考试结果页，禁止改写为 `/exam/complete` |
| `pages/mine.html` | `frontend/src/views/Mine.vue` | `/mine`；别名 `/profile` | 四标签底部导航中的“我的” |

## 不参与本轮参考映射的现有页面

- `frontend/src/views/PracticeHub.vue` 和 `/practice` 是现有辅助入口，不是第九个参考界面，也不是底部导航第五个标签。
- 题库详情、错题强化、到期复习、考试列表/详情等现有页面继续保留，但不得用来替换上表中的参考落点。

## 实现边界

- 不从 `frontend-preview.html` 复制颜色、排版、组件或布局；它是旧“墨韵书房”预览，仅供历史对照。
- 不改变后端 API、响应 schema、数据库表、鉴权与业务规则。
- 不新增平行路由来迁就静态参考文件；静态页面名必须映射到现有路由。
- 参考界面中的示例数据必须接入现有真实数据流，不得把演示数据硬编码为生产行为。
