# 考试学习平台 · 设计参考文档

## 设计系统概览

- 风格：清新活力 · iOS 26 Liquid Glass
- 主色：Emerald #10B981
- 字体：Noto Sans SC（800 标题 / 400-700 正文）
- 圆角：12px 小 / 16px 中 / 20px 大 / 24px 特大 / 9999px 胶囊
- 交互：弹簧动画 cubic-bezier(0.34, 1.56, 0.64, 1)
- 玻璃材质：backdrop-filter blur + saturate(180%) + 内高光
- 底部导航：悬浮胶囊浮岛（不贴底，左右留边距，选中项玻璃透镜高亮）
- 参考界面：8 个（首页 / 题库列表 / 题库练习 / AI 导入 / 考试答题 / 练习完成弹窗 / 考试结果 / 我的）
- 底部导航：4 个标签（首页 / 题库 / 导入 / 我的）；题库练习、考试答题和结果界面无底部导航
- `/practice` 的练习中心是现有辅助页面，不是参考界面，也不是第五个底部标签

---

## 1. CSS 设计令牌

```css
:root {
  /* 品牌 Primary */
  --primary: #10B981;
  --primary-strong: #059669;
  --primary-soft: #ECFDF5;
  --primary-border: #A7F3D0;
  --primary-glow: rgba(16, 185, 129, 0.2);

  /* 表面 */
  --bg: #F2F4F8;
  --surface: #FFFFFF;
  --surface-muted: #F1F5F9;

  /* 玻璃材质 */
  --glass-nav: rgba(255, 255, 255, 0.72);
  --glass-nav-blur: 24px;
  --glass-card: rgba(255, 255, 255, 0.65);
  --glass-card-blur: 20px;
  --glass-header: rgba(255, 255, 255, 0.68);
  --glass-header-blur: 20px;
  --glass-overlay: rgba(255, 255, 255, 0.55);
  --glass-overlay-blur: 40px;
  --glass-highlight: rgba(255, 255, 255, 0.5);
  --glass-border: rgba(255, 255, 255, 0.6);

  /* 文字 */
  --text-primary: #0F172A;
  --text-secondary: #475569;
  --text-muted: #94A3B8;
  --text-placeholder: #CBD5E1;

  /* 边框 */
  --border: #E2E8F0;
  --border-soft: #F1F5F9;
  --border-strong: #CBD5E1;

  /* 语义状态色 */
  --state-success: #10B981;
  --state-success-soft: #ECFDF5;
  --state-warning: #F59E0B;
  --state-warning-soft: #FFFBEB;
  --state-warning-border: #FDE68A;
  --state-error: #EF4444;
  --state-error-soft: #FEF2F2;
  --state-error-border: #FECACA;
  --state-info: #3B82F6;
  --state-info-soft: #EFF6FF;

  /* 圆角 */
  --radius-sm: 12px;
  --radius-md: 16px;
  --radius-lg: 20px;
  --radius-xl: 24px;
  --radius-full: 9999px;

  /* 阴影 */
  --shadow-xs: 0 1px 3px rgba(15, 23, 42, 0.04);
  --shadow-sm: 0 2px 8px rgba(15, 23, 42, 0.05);
  --shadow-card: 0 4px 16px rgba(15, 23, 42, 0.06);
  --shadow-elevated: 0 8px 32px rgba(15, 23, 42, 0.10);
  --shadow-modal: 0 24px 64px rgba(15, 23, 42, 0.18);
  --shadow-primary: 0 8px 24px rgba(16, 185, 129, 0.22);
  --glass-inner-highlight: inset 0 1px 0 rgba(255, 255, 255, 0.5);

  /* 字体 */
  --font-sans: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-display: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;

  /* 字号 */
  --text-xs: 0.6875rem;   /* 11px */
  --text-sm: 0.8125rem;  /* 13px */
  --text-md: 0.875rem;   /* 14px */
  --text-base: 0.9375rem; /* 15px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.375rem;   /* 22px */
  --text-2xl: 1.75rem;   /* 28px */

  /* 间距 */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;

  /* 过渡 · iOS 26 弹簧动画 */
  --ease-out: 0.28s cubic-bezier(0.32, 0.72, 0, 1);
  --ease-spring: 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-spring-gentle: 0.35s cubic-bezier(0.25, 1, 0.5, 1);
}

/* 深色模式 */
.dark {
  --bg: #000000;
  --surface: #1C1C1E;
  --surface-muted: #2C2C2E;
  --glass-nav: rgba(28, 28, 30, 0.72);
  --glass-card: rgba(44, 44, 46, 0.65);
  --glass-header: rgba(28, 28, 30, 0.68);
  --glass-overlay: rgba(28, 28, 30, 0.55);
  --glass-highlight: rgba(255, 255, 255, 0.08);
  --glass-border: rgba(255, 255, 255, 0.12);
  --text-primary: #F1F5F9;
  --text-secondary: #CBD5E1;
  --text-muted: #64748B;
  --border: #3A3A3C;
  --border-soft: #2C2C2E;
  --glass-inner-highlight: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
```

---

## 2. 应用外壳 CSS（移动端容器 + 悬浮胶囊导航）

```css
/* 应用容器 */
.shell-container {
  position: relative;
  display: flex;
  flex-direction: column;
  max-width: 420px;
  min-height: 100vh;
  margin: 0 auto;
  background: var(--bg);
  box-shadow: 0 0 40px rgba(15, 23, 42, 0.10);
}

/* 内容区 */
.shell-content {
  flex: 1;
  padding-bottom: 96px; /* 悬浮导航空间 */
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
}

/* 底部悬浮胶囊导航 · iOS 26 Liquid Glass */
.bottom-nav {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 32px);
  max-width: 388px;
  height: 64px;
  background: var(--glass-nav);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid var(--glass-border);
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px;
  gap: 2px;
  z-index: 50;
  box-shadow:
    0 8px 32px rgba(15, 23, 42, 0.12),
    0 2px 8px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

/* 单个标签 */
.nav-item {
  flex: 1;
  height: 52px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  background: transparent;
  border: none;
  border-radius: 9999px;
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.28s cubic-bezier(0.32, 0.72, 0, 1),
              background 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.nav-item:active { transform: scale(0.92); }
.nav-item svg { width: 22px; height: 22px; stroke-width: 2; }

/* 选中态 · 玻璃透镜高亮 */
.nav-item[data-active="true"] {
  color: var(--primary);
  background: rgba(16, 185, 129, 0.12);
  box-shadow: inset 0 0 0 1px rgba(16, 185, 129, 0.15),
              inset 0 1px 0 rgba(255, 255, 255, 0.5);
}
.nav-item[data-active="true"] svg { transform: scale(1.1); }

/* 强调标签（导入） · 胶囊内实心圆形图标 */
.nav-item--emphasis { flex: 0 0 auto; width: 52px; }
.nav-emphasis-badge {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: var(--primary);
  color: #FFFFFF;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.30),
              inset 0 1px 0 rgba(255, 255, 255, 0.5);
}
.nav-emphasis-badge svg { width: 20px; height: 20px; stroke-width: 2.5; }

/* 玻璃卡片材质（复用于页面内容卡片） */
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

---

## 3. 底部导航 HTML 结构

```html
<nav class="bottom-nav" aria-label="主导航">
  <!-- 首页 -->
  <button class="nav-item" data-nav-key="home" data-active="true">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
    <span class="nav-label">首页</span>
  </button>

  <!-- 题库 -->
  <button class="nav-item" data-nav-key="courses">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
    <span class="nav-label">题库</span>
  </button>

  <!-- 导入（强调） -->
  <button class="nav-item nav-item--emphasis" data-nav-key="import">
    <div class="nav-emphasis-badge">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
    </div>
    <span class="nav-label">导入</span>
  </button>

  <!-- 我的 -->
  <button class="nav-item" data-nav-key="mine">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
    <span class="nav-label">我的</span>
  </button>
</nav>
```

---

## 4. 页面结构约定

### 带导航页面（首页/题库列表/AI 导入/我的）

```html
<div class="shell-container">
  <main class="shell-content">
    <!-- 页面内容 -->
  </main>
  <nav class="bottom-nav"><!-- 4 个标签：首页 / 题库 / 导入 / 我的 --></nav>
</div>
```

### 沉浸式页面（题库练习/考试答题/考试结果）

```html
<div class="shell-container">
  <main class="shell-content">
    <!-- 沉浸式顶栏 + 内容 + 底部操作栏（无 bottom-nav） -->
  </main>
</div>
```

### 8 个参考界面清单

| 页面 | 文件 | 类型 | 底部导航 |
|------|------|------|----------|
| 首页 | home.html | 信息密集 | 有 |
| 题库列表 | course-list.html | 信息密集 | 有 |
| 题库练习 | course-practice.html | 沉浸式 | 无 |
| AI 导入 | ai-import.html | 任务驱动 | 有 |
| 考试答题 | exam-take.html | 沉浸式 | 无 |
| 练习完成弹窗 | practice-complete.html | 结果弹窗 | 无 |
| 考试结果 | exam-complete.html | 结果页 | 无 |
| 我的 | mine.html | 信息密集 | 有 |

---

## 5. 完整首页示例（可直接复制运行）

首页 `home.html` 是一个完全自包含的 HTML 文件（CSS 全部内联），位于：
`d:\File\exam system\exam-platform-ui\pages\home.html`

结构：渐变头部（问候+头像）→ 2x2 快捷操作网格 → 4列统计行 → 最近练习课程列表 → 悬浮胶囊导航

其他 7 个参考界面也在同目录下；实现时按 `IMPLEMENTATION_MAP.md` 映射到现有 Vue 页面或组件。

---

## 6. 关键设计规范

- **移动端优先**：420px 容器居中，桌面端附带柔和投影
- **触控目标**：最小 44px，按钮 48px
- **内边距**：页面 16px，卡片 16-20px
- **卡片间距**：12px
- **图标系统**：Lucide 线性图标，彩色圆形背景
- **玻璃卡片**：半透明 + 模糊 + 饱和度增强 + 内高光边框
- **交互反馈**：hover translateY(-2px)，active scale(0.95-0.98)
- **深色模式**：纯黑背景 #000000，玻璃材质更深
- **无障碍**：支持 prefers-reduced-motion，focus-visible 轮廓
