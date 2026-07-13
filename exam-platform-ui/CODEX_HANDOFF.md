# 考试学习平台 · Codex 前端交接文档

> 本文档供 Codex 实现当前 Vue 前端使用。`exam-platform-ui/` 是本轮视觉实现的唯一设计真相；真实路由和组件映射以 `IMPLEMENTATION_MAP.md` 为准。

---

## 一、项目概述

- **名称**：考试学习平台
- **风格**：清新活力 · iOS 26 Liquid Glass
- **主色**：Emerald Green `#10B981`
- **字体**：Noto Sans SC（800 标题 / 400-700 正文）
- **设备**：移动端优先，420px 居中容器
- **固定技术栈**：Vue 3 + TypeScript + Vite + Pinia + Vue Router
- **图标库**：Lucide Vue（`@lucide/vue`）
- **参考界面数**：8 个（其中练习完成是现有弹窗，不是独立路由）

---

## 二、页面清单与路由

| # | 参考界面 | 文件 | 当前 Vue 落点 | 真实路由 | 底部导航 |
|---|----------|------|---------------|----------|----------|
| 1 | 首页 | home.html | `Home.vue` | `/` | 有 |
| 2 | 题库列表 | course-list.html | `CourseList.vue` | `/courses` | 有 |
| 3 | 题库练习 | course-practice.html | `CoursePractice.vue` | `/courses/:courseId/practice`（别名 `/practice/:courseId`） | 无 |
| 4 | AI 导入 | ai-import.html | `ImportQuestions.vue` | `/import` | 有 |
| 5 | 考试答题 | exam-take.html | `ExamTake.vue` | `/exams/:examId/take`（别名 `/exam/:examId`） | 无 |
| 6 | 练习完成 | practice-complete.html | `PracticeSummaryModal.vue` | 无独立路由；练习页内弹窗 | 无 |
| 7 | 考试结果 | exam-complete.html | `ExamResult.vue` | `/exams/:examId/result` | 无 |
| 8 | 我的 | mine.html | `Mine.vue` | `/mine`（别名 `/profile`） | 有 |

`/practice` 的 `PracticeHub.vue` 仍是产品中的辅助页面，但不属于这 8 个参考界面，也不是底部导航第五个标签。

### 页面跳转流程

```
首页 ─┬─→ 题库列表 ──→ [练习方式弹出层] ──→ 题库练习 ──→ 练习完成
     ├─→ AI 导入
     ├─→ 考试答题 ──→ 考试结果
     └─→ 我的

题库列表 ──→ [点击练习] ──→ 弹出选择：顺序/随机/错题/收藏 ──→ 题库练习
首页今日推荐 ──→ 题库练习
我的 ─┬─→ 题库练习（错题本）
      ├─→ 题库列表（收藏/记录）
      └─→ AI 导入（AI 对话）
```

---

## 三、底部导航

**4 个标签**（不是 5 个）：

| 标签 | 路由 | 图标 | 特殊样式 |
|------|------|------|----------|
| 首页 | `/` | home | - |
| 题库 | `/courses` | book | - |
| 导入 | `/import` | upload | 强调：实心绿色圆形图标 |
| 我的 | `/mine`（别名 `/profile`） | user | - |

**导航样式**：悬浮胶囊浮岛
- `position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);`
- `width: calc(100% - 32px); max-width: 388px; height: 64px;`
- 液态玻璃材质：`backdrop-filter: blur(24px) saturate(180%)`
- 胶囊圆角：`border-radius: 9999px`
- 选中项：绿色玻璃透镜高亮 `background: rgba(16, 185, 129, 0.12)`

---

## 四、各页面详细结构

### 1. 首页 (home.html)

```
渐变头部（Emerald 渐变）
  ├─ 问候语 "下午好，同学 👋" + 日期 "7月14日 周二"
  ├─ 头像（圆形，白色半透明背景）
  └─ 搜索栏（白色不透明 + 阴影 + 搜索图标 + 占位文字 + 麦克风图标）

快捷操作 2x2 网格
  ├─ AI 导入（绿色图标圆 + 标题 + 副标题）
  ├─ 开始练习（蓝色图标圆 + 标题 + 副标题）
  ├─ 正式考试（橙色图标圆 + 标题 + 副标题）
  └─ 学习概览（红色图标圆 + 标题 + 副标题）

学习统计（4列）
  ├─ 32 题 / 今日练习
  ├─ 1,248 题 / 总题数
  ├─ 85 % / 正确率
  └─ 7 天 / 连续

最近练习（3张卡片）
  ├─ 高等数学（绿色图标 sigma + 进度条 65%）
  ├─ 英语四级核心（蓝色图标 book-open + 进度条 47%）
  └─ 计算机基础（橙色图标 laptop + 进度条 34%）
  每张卡片有：图标圆、标题、元数据、进度条、右箭头

今日推荐（渐变卡片）
  └─ sparkle 图标 + "数据结构 · 链表与数组" + "去练习" 按钮
```

### 2. 题库列表 (course-list.html)

```
顶栏
  ├─ 标题 "题库" + 副标题 "我的题库 · 12个"
  └─ 添加按钮（plus 图标）

搜索栏 + 筛选标签
  ├─ 搜索输入框
  └─ 4个筛选标签：全部 / 我的 / 公共 / 最近练习

课程卡片列表（5张）
  ├─ 高等数学（绿 sigma 图标，128题，65%，进度条绿色）
  ├─ 英语四级核心（蓝 book-open 图标，256题，40%，进度条蓝色）
  ├─ 计算机基础（橙 cpu 图标，89题，80%，进度条橙色）
  ├─ 思想政治教育（红 file-text 图标，175题，15%，进度条红色）
  └─ 数据结构（绿 database 图标，203题，55%，进度条绿色）
  每张卡片有：图标圆、标题、元数据+百分比、进度条、"练习"按钮

练习方式弹出层（底部弹出）
  ├─ 标题 "选择练习方式" + 课程名 + 题数
  ├─ 顺序练习（list-ordered 图标）
  ├─ 随机练习（shuffle 图标）
  ├─ 错题强化（x-circle 图标 + 题数）
  └─ 收藏练习（bookmark 图标）
```

### 3. 题库练习 (course-practice.html)

```
沉浸式顶栏
  ├─ 返回按钮
  ├─ 进度信息 "5/20 • 25%" + 绿色进度条
  └─ 答题卡按钮（grid 图标）

题目卡片
  ├─ 标签：单选题（绿色胶囊）
  ├─ 元数据标签：2分(灰) + 中等(橙) + 数据库原理(灰)
  ├─ 题目文本
  └─ 答案解析（展开后显示）

答题选项（4个）
  ├─ A 第一范式 (1NF)
  ├─ B 第二范式 (2NF) ← 选中（绿色高亮 + 勾选）
  ├─ C 第三范式 (3NF)
  └─ D BCNF 范式

底部操作栏
  ├─ 上一题按钮
  ├─ 收藏按钮（bookmark 图标）
  └─ 完成练习按钮（绿色 + 勾选图标）

答题卡弹出层（底部弹出）
  ├─ 标题 "答题卡" + 进度信息
  ├─ 图例：已答(绿) / 未答(灰) / 标记(橙)
  └─ 题号网格（1-20，3列或4列）
```

### 4. AI 导入 (ai-import.html)

```
顶栏
  ├─ 标题 "AI 导入"
  └─ 副标题 "智能解析 · 一键导入题目"

上传区（虚线边框拖拽区）
  ├─ cloud-upload 图标
  ├─ "点击或拖拽文件上传"
  └─ "AI 自动解析并生成题目"

格式标签行
  └─ Word / PPT / PDF / 图片 / 文本（5个彩色标签）

JSON 折叠区
  ├─ "粘贴 JSON 文本"（chevron-down 折叠）
  └─ JSON 代码输入框

使用提示（3步引导卡片）
  ├─ 1. 上传文件或粘贴 JSON
  ├─ 2. AI 智能解析
  └─ 3. 预览确认后导入
```

### 5. 考试答题 (exam-take.html)

```
沉浸式顶栏
  ├─ 返回按钮
  ├─ 考试名 + 进度 "5/20 • 25%" + 进度条
  ├─ 答题卡按钮
  └─ 倒计时圆环（45:30）

题目卡片
  ├─ 标签：单选题（绿色胶囊）
  ├─ 元数据标签：2分(灰+award) + 中等(橙+zap) + 计算机网络(灰+wifi)
  └─ 题目文本

答题选项（4个）
  ├─ A SYN=1, ACK=0 ← 用户选中（蓝色高亮 + circle 图标）
  ├─ B SYN=1, ACK=1 ← 正确答案（绿色高亮 + check 图标）
  ├─ C SYN=0, ACK=1
  └─ D SYN=0, ACK=0

底部操作栏
  ├─ 上一题按钮
  ├─ 下一题按钮
  └─ 交卷按钮

答题卡弹出层（同题库练习）
```

### 6. 练习完成弹窗 (practice-complete.html → PracticeSummaryModal.vue)

```
成功图标区
  ├─ 大型绿色勾选圆形图标
  ├─ 标题 "练习完成！"
  ├─ 副标题 "高等数学 · 顺序练习"
  ├─ 表现评级徽章 "表现优秀"（award 图标）
  └─ 鼓励语 "正确率达到 85%，继续保持！"

成绩卡片
  ├─ SVG 圆环进度图（90px，显示 85% 正确率）
  └─ 右侧数据：用时 12:30 / 总题数 20

答题详情卡片
  ├─ 标题 "答题详情"（clipboard-list 图标）
  ├─ 答对：17题（绿色）
  ├─ 答错：3题（红色）
  ├─ 正确率：85%（绿色）
  └─ 用时：12:30

操作按钮
  ├─ 查看错题详情（主按钮，绿色）
  └─ 返回题库（次按钮，白色边框）
```

### 7. 考试结果 (exam-complete.html → ExamResult.vue)

```
成功图标区
  ├─ 大型绿色勾选圆形图标
  ├─ 标题 "考试完成"
  ├─ 副标题 "计算机基础 · 期末考试"
  ├─ "通过"徽章
  └─ 鼓励语 "恭喜通过考试！继续保持学习节奏"

成绩卡片
  ├─ 大字 85 分
  └─ 满分 100 分

答题详情卡片
  ├─ 标题 "答题详情"（clipboard-list 图标）
  ├─ 单选题：16/18 正确
  ├─ 多选题：4/2 正确
  ├─ 判断题：2/0 错误
  └─ 总分：85/100

操作按钮
  ├─ 查看答题报告（主按钮）
  └─ 返回首页（次按钮）
```

### 8. 我的 (mine.html)

```
渐变头部
  ├─ 头像 + 姓名 "张同学"
  ├─ 等级信息 "学习等级 · 进阶"
  └─ 等级进度条 Lv.8 → Lv.9（6px 白色进度条）

学习统计卡片（4列，悬浮于头部下方）
  ├─ 1,248 / 总题数
  ├─ 85% / 正确率
  ├─ 7天 / 连续打卡
  └─ 12 / 徽章

快捷入口 2x2 网格
  ├─ 错题本 23题待复习（红 x-circle）
  ├─ 我的收藏 56道题目（橙 bookmark）
  ├─ 练习记录 本周12次（蓝 history）
  └─ AI 对话 智能辅导（绿 sparkles）

菜单列表
  ├─ 更新公告 v2.3.0（bell 图标 + 徽章）
  ├─ 学习设置（settings 图标）
  ├─ 深色模式（moon 图标 + 开关）
  ├─ 主题颜色（palette 图标）→ 弹出主题选择
  ├─ 帮助与反馈（help-circle 图标）
  ├─ 管理后台（shield 图标）
  └─ 关于我们 v2.3.0（info 图标）

主题颜色弹出层（底部弹出）
  ├─ 标题 "主题颜色" + "选择你喜欢的主题色"
  └─ 6个色卡：翡翠绿 / 海洋蓝 / 优雅紫 / 日落橙 / 玫瑰粉 / 青碧
```

---

## 五、CSS 设计令牌

完整 CSS 变量见 `colors_and_type.css` 文件。关键令牌：

### 颜色

```css
/* 品牌色 */
--primary: #10B981;
--primary-strong: #059669;
--primary-soft: #ECFDF5;
--primary-border: #A7F3D0;

/* 语义状态色 */
--state-success: #10B981;  --state-success-soft: #ECFDF5;
--state-warning: #F59E0B;  --state-warning-soft: #FFFBEB;
--state-error: #EF4444;    --state-error-soft: #FEF2F2;
--state-info: #3B82F6;     --state-info-soft: #EFF6FF;

/* 表面 */
--bg: #F2F4F8;
--surface: #FFFFFF;
--surface-muted: #F1F5F9;

/* 文字 */
--text-primary: #0F172A;
--text-secondary: #475569;
--text-muted: #94A3B8;
```

### 圆角

```css
--radius-sm: 12px;    /* 小卡片、标签 */
--radius-md: 16px;    /* 卡片 */
--radius-lg: 20px;    /* 大卡片 */
--radius-xl: 24px;    /* 弹出层 */
--radius-full: 9999px; /* 胶囊、圆形 */
```

### 玻璃材质

```css
--glass-nav: rgba(255, 255, 255, 0.72);
--glass-card: rgba(255, 255, 255, 0.65);
--glass-border: rgba(255, 255, 255, 0.6);

/* 使用方式 */
.glass-card {
  background: var(--glass-card);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid var(--glass-border);
  box-shadow: 0 4px 16px rgba(15,23,42,0.06), inset 0 1px 0 rgba(255,255,255,0.5);
}
```

### 动画

```css
--ease-out: 0.28s cubic-bezier(0.32, 0.72, 0, 1);        /* 常规过渡 */
--ease-spring: 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);    /* 弹簧效果 */
--ease-spring-gentle: 0.35s cubic-bezier(0.25, 1, 0.5, 1);
```

---

## 六、关键组件规范

### 玻璃卡片

```css
.glass-card {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06),
              inset 0 1px 0 rgba(255, 255, 255, 0.5);
}
```

### 按钮规范

| 类型 | 高度 | 圆角 | 背景 | 字号 |
|------|------|------|------|------|
| 主按钮 | 48px | full | var(--primary) | 15px / 700 |
| 次按钮 | 48px | full | var(--surface) + border | 15px / 600 |
| 小按钮 | 36px | 8px | var(--primary-soft) | 13px / 600 |
| 图标按钮 | 44px | full | transparent | - |

### 底部弹出层（Sheet）

```css
.bottom-sheet {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) translateY(100%);
  width: 100%;
  max-width: 420px;
  background: var(--surface);
  border-radius: 24px 24px 0 0;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 100;
}
.bottom-sheet--open {
  transform: translateX(-50%) translateY(0);
}
```

### 答题选项

```css
/* 未选中 */
.option-btn {
  border: 2px solid var(--border);
  background: var(--surface);
  border-radius: 12px;
  padding: 12px;
}

/* 选中（用户选择） */
.option-btn--selected {
  border-color: var(--state-info);
  background: var(--state-info-soft);
}

/* 正确答案 */
.option-btn--correct {
  border-color: var(--primary);
  background: var(--primary-soft);
}
```

### SVG 圆环进度图

```html
<svg width="90" height="90" viewBox="0 0 90 90">
  <g transform="rotate(-90 45 45)">
    <circle cx="45" cy="45" r="38" fill="none" stroke="var(--border)" stroke-width="6"/>
    <circle cx="45" cy="45" r="38" fill="none" stroke="var(--primary)" stroke-width="6"
            stroke-linecap="round"
            stroke-dasharray="238.76"
            stroke-dashoffset="35.81"/>
  </g>
</svg>
<!-- 公式：dashoffset = 238.76 * (1 - percentage) -->
```

---

## 七、深色模式

通过 `.dark` 类切换。关键变化：

```css
.dark {
  --bg: #000000;
  --surface: #1C1C1E;
  --surface-muted: #2C2C2E;
  --glass-nav: rgba(28, 28, 30, 0.72);
  --glass-card: rgba(44, 44, 46, 0.65);
  --text-primary: #F1F5F9;
  --text-secondary: #CBD5E1;
  --text-muted: #64748B;
  --border: #3A3A3C;
}
```

---

## 八、交互逻辑说明

### 筛选标签切换

```js
// 点击筛选标签时，切换 active 状态
filterTab.addEventListener('click', () => {
  document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
  filterTab.classList.add('active');
  // 根据筛选条件过滤课程列表
});
```

### 底部弹出层

```js
// 打开
document.getElementById('sheetId').classList.add('sheet--open');
// 关闭
document.getElementById('sheetId').classList.remove('sheet--open');
// 点击遮罩关闭
overlay.addEventListener('click', () => {
  document.getElementById('sheetId').classList.remove('sheet--open');
});
```

### 主题色切换

```js
const themes = {
  emerald: { '--primary': '#10B981', '--primary-strong': '#059669', '--primary-soft': '#ECFDF5', '--primary-border': '#A7F3D0' },
  ocean:   { '--primary': '#3B82F6', '--primary-strong': '#2563EB', '--primary-soft': '#EFF6FF', '--primary-border': '#93C5FD' },
  purple:  { '--primary': '#8B5CF6', '--primary-strong': '#7C3AED', '--primary-soft': '#F5F3FF', '--primary-border': '#C4B5FD' },
  sunset:  { '--primary': '#F97316', '--primary-strong': '#EA580C', '--primary-soft': '#FFF7ED', '--primary-border': '#FDBA74' },
  rose:    { '--primary': '#F43F5E', '--primary-strong': '#E11D48', '--primary-soft': '#FFF1F2', '--primary-border': '#FDA4AF' },
  teal:    { '--primary': '#14B8A6', '--primary-strong': '#0D9488', '--primary-soft': '#F0FDFA', '--primary-border': '#5EEAD4' },
};
// 应用主题
function applyTheme(name) {
  const theme = themes[name];
  Object.entries(theme).forEach(([key, value]) => {
    document.documentElement.style.setProperty(key, value);
  });
}
```

### 答题交互

```js
// 选项点击
optionBtn.addEventListener('click', () => {
  // 移除其他选项的选中状态
  document.querySelectorAll('.option-btn').forEach(b => {
    b.classList.remove('option-btn--selected');
  });
  // 标记当前选项
  optionBtn.classList.add('option-btn--selected');
});

// 答题卡题号点击
questionNumber.addEventListener('click', () => {
  // 跳转到对应题目
});
```

---

## 九、文件结构

```
exam-platform-ui/
├── pages/                      # 8 个页面 HTML（自包含，CSS 内联）
│   ├── home.html               # 首页
│   ├── course-list.html        # 题库列表
│   ├── course-practice.html    # 题库练习
│   ├── ai-import.html          # AI 导入
│   ├── exam-take.html          # 考试答题
│   ├── practice-complete.html  # 练习完成
│   ├── exam-complete.html      # 考试完成
│   └── mine.html               # 我的
├── partials/
│   └── project-shell.html      # 应用外壳（容器 + 导航 CSS/HTML）
├── colors_and_type.css         # 设计令牌 + 排版类
├── design-reference.md         # 设计参考文档
└── CODEX_HANDOFF.md            # 本文档
```

每个 HTML 页面都是完全自包含的（CSS 内联在 `<style>` 标签中），可以直接在浏览器中打开预览。实现时需要将这些页面转换为组件化的前端项目。

---

## 十、实现建议

1. **路由结构**：只使用现有 Vue Router；8 个参考界面对应 7 个路由落点和 1 个练习总结弹窗，禁止新增 `/practice/complete` 或 `/exam/complete`
2. **状态管理**：使用现有 Pinia stores，保持当前用户、题库列表、当前练习/考试进度和主题设置的业务契约
3. **组件拆分**：
   - `BottomNav` — 底部导航（4 标签）
   - `GlassCard` — 玻璃卡片容器
   - `CourseCard` — 课程卡片
   - `BottomSheet` — 底部弹出层
   - `QuestionCard` — 题目卡片
   - `OptionButton` — 答题选项
   - `ProgressRing` — SVG 圆环进度图
   - `StatGrid` — 统计网格
   - `FilterTabs` — 筛选标签
4. **主题系统**：通过 CSS 变量实现，切换时修改 `:root` 上的变量
5. **响应式**：420px 容器居中，桌面端附带柔和投影
6. **图标**：使用 `@lucide/vue`
7. **字体**：加载 Google Fonts `Noto Sans SC`
