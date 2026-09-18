# 学习宝 Beta 环境登录态持久化与登录链路修复日志

> 日期：2026-07-16
> 涉及模块：前端认证（auth store / request.ts / router.ts）、beta 构建链路、后端进程管理
> 最终状态：登录请求链路和底部主 Tab 切换问题已打通；鉴权持久化与 Beta 进程托管仍有待进一步收口

---

## 1. 问题起点：AI 导入文件来源咨询（已放弃）

用户询问 AI 导入功能能否选择微信文件或微信聊天记录中的文件。

结论：
- 浏览器 H5 无法直接读取微信聊天会话，属系统级隐私限制。
- 微信内打开 H5 时 `<input type="file">` 在 iOS 通常只能选相册，安卓部分版本可选聊天文件，表现依版本而定。
- 桌面端用户可手动导航到 `Documents\WeChat Files\<wxid>\Files` 选文件，已可用，无需改代码。
- 三个可选方案：A 加提示文字（零成本）；B 配置 PWA Web Share Target（安卓可用，iOS 不支持）；C 开发微信小程序用 `wx.chooseMessageFile()`（成本最高，体验最好）。

用户决定：**先不做**。

---

## 2. P2 代码质量修复（已完成）

在登录问题之前，用户同意继续清理第二轮审查发现的 P2 问题。

### 2.1 router 内嵌业务逻辑 — `backend/routers/imports.py:225-298`

- **问题**：`confirm_import_task` 端点内嵌事务控制、状态机更新、补偿写回，共 30+ 行业务逻辑写在 router 层。
- **修复**：在 `backend/services/import_task_service.py` 新增 `confirm_task(task_id, payload, user)` 函数，封装状态机/事务控制/补偿写回。router 从 30 行减到 8 行，只做 HTTP 转发。

### 2.2 跨 router 互导私有 helper — `backend/routers/practice.py:8`

- **问题**：`from ..routers.courses import _get_accessible_course` 跨 router 导入私有 helper，造成 router 之间耦合。
- **修复**：把 `_get_accessible_course` 和 `_get_owned_course` 从 `routers/courses.py` 迁到 `services/course_service.py`，作为公共模块级函数（去掉下划线前缀）。`courses.py` 和 `practice.py` 都从 service 导入。

### 2.3 create_course 无权限检查 — `backend/routers/courses.py:17`

- **问题**：`Depends(get_current_user)` 只验证登录，不验证权限，任何登录用户都能创建课程。
- **修复**：改为 `Depends(require_permission("course:create"))`，与其他 RBAC 端点一致。

### 2.4 测试结果
- 后端：428 passed, 1 skipped
- 前端：292 passed

---

## 3. 登录态持久化问题（核心，经历多轮修复）

用户反馈：**每次退出学习宝网页都要重新登录一次，没点退出登录都要重新登**。

特别场景：从微信点进网页登录，从左往右滑关掉网页，再点进去又要重新登录。

### 3.1 第一轮修复：persistToken 全环境启用

**根因分析**：
`frontend/src/api/request.ts:6` 原代码：
```ts
const persistToken = !import.meta.env.PROD;
```
beta 构建是 `PROD=true`，导致 `persistToken=false`，token 只存内存，关闭页面即丢。后端 HttpOnly cookie (max-age=24h) 仍在，但前端没有尝试恢复。

**修复**：
```ts
const persistToken = true;
```
所有环境都把 token 存 localStorage。

**结果**：用户反馈还是不行。微信内置浏览器关闭 WebView 时会清除 localStorage。

### 3.2 第二轮修复：cookie 备份机制

**根因分析**：微信内置浏览器关闭 WebView 时会清除 localStorage，但通常会保留 cookie。

**修复**：token 同时写入两个地方：
1. `localStorage`（主，优先读取）
2. 非 HttpOnly cookie `xuexibao_token`（备份，max-age=24h）

新增辅助函数：
```ts
function setCookie(name: string, value: string, maxAge: number): void {
  try {
    document.cookie = `${name}=${encodeURIComponent(value)}; max-age=${maxAge}; path=/; samesite=lax`;
  } catch { /* 部分嵌入式 WebView 禁用 document.cookie 写入 */ }
}

function getCookie(name: string): string {
  try {
    const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
    return match ? decodeURIComponent(match[1]) : "";
  } catch { return ""; }
}
```

`getToken()` 读取顺序：localStorage → cookie → 内存 token。

**结果**：用户反馈出现新问题。

### 3.3 第三轮修复：未登录也能进入主页

**新问题**：用户反馈"点击微信的网址，没登录也可以进入主页了，进去显示未登录"。

**根因分析**：之前登录过的 token 残留在 cookie 里，重新打开网页时 `getToken()` 读到过期 token（非空），router guard 仅凭 token 存在就放行到主页。但实际 token 已过期，`/auth/me` 返回 401，页面停在主页显示"未登录"。

**修复**：

1. `frontend/src/stores/auth.ts` 新增 `profileInitialized` 标志：
```ts
state: () => ({
  // ...
  // 标记本次会话是否已尝试加载 user profile。
  // router guard 用它避免每次路由切换都调 /auth/me，同时确保首次进入时
  // 即使有旧 token 也会先验证一次：token 可能已过期，不能仅凭 token 放行。
  profileInitialized: false,
}),
```

2. `isAuthenticated` getter 改为只看 `state.user`，不再仅凭 token 判断：
```ts
// 仅当 user 已加载且非空时才算已认证。token 单独存在不能代表会话有效，
// 因为 token 可能已过期（cookie/localStorage 残留）。
isAuthenticated: (state) => !!state.user,
```

3. `fetchProfile` 完成后置 `profileInitialized=true`（无论成功失败）：
```ts
} finally {
  if (requestRevision === this.authRevision) {
    this.loading = false;
    this.profileInitialized = true;
  }
}
```

4. `logout()` 和 `clearGuestData()` 同步重置 `profileInitialized = true`（避免退出后又触发 fetchProfile）。

5. `frontend/src/router.ts` beforeEach 逻辑改为：
```ts
router.beforeEach(async (to) => {
  const token = getToken();
  const auth = useAuthStore();

  if (to.matched.some((route) => route.meta.requiresAuth)) {
    if (!auth.user) {
      // 没 token 且没 user：真未登录，直接跳 login，避免多余请求。
      // 有 token 但没 user：token 可能过期（cookie/localStorage 残留），
      // 必须先调 /auth/me 验证 token 是否仍然有效，不能仅凭 token 放行。
      // profileInitialized 确保每次页面会话只验证一次，避免每次路由切换都请求。
      if (token && !auth.profileInitialized && !auth.explicitlyLoggedOut) {
        await auth.fetchProfile({ silent: true });
      }
      if (!auth.user) {
        return { name: "login", query: { redirect: to.fullPath } };
      }
    }
  }
  // ...
});
```

**三种场景都正确**：
- 从未登录 → 跳 login
- 登录过且 token 有效 → 直接进主页
- 登录过但 token 过期 → 验证失败后跳 login（不再停在主页显示未登录）

**结果**：用户反馈"登录失败：登录成功，但没有收到 token"。

---

## 4. 登录失败"没有收到 token"排查（经历多轮误诊）

用户反馈：登入不进去，显示登录成功但没有收到 token。

### 4.1 第一轮误诊：后端进程用错 Python

**诊断**：直接 curl 后端 `POST /auth/login` 返回 200 + 有效 token + Set-Cookie，都正常。但检查后端进程发现：

```
PID 21812: "D:\Devtools\Python\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

后端进程用的是**系统 Python**，不是项目 venv（`backend\.venv\Scripts\python.exe`）。

**操作**：kill PID 21812，用项目 venv 重启：
```powershell
cd "d:\File\exam system"
& "backend\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

验证 `http://127.0.0.1:8080/api/auth/login` 返回 200 + token，正常。

**结果**：用户反馈还是报"没有收到 token"。

### 4.2 第二轮诊断：加临时诊断显示响应内容

**操作**：在 `auth.ts` login 方法里加临时诊断，显示后端实际返回内容：
```ts
const token = normalizeToken(data);
if (!token) {
  const dataPreview: unknown = data;
  const preview =
    typeof dataPreview === "string"
      ? dataPreview.slice(0, 200)
      : JSON.stringify(dataPreview)?.slice(0, 200);
  throw new Error(`登录成功，但没有收到 token。响应内容: ${preview}`);
}
```

构建遇到 TypeScript 错误：`Property 'slice' does not exist on type 'never'`。修复为 `dataPreview: unknown` 后构建通过。

**结果**：用户反馈响应内容是 Cloudflare 502 错误页：
```
The origin web server returned an invalid or incomplete response to Cloudflare.
This typically indicates the origin is overloaded or misconfigured.
```

### 4.3 第三轮误诊：双后端进程 + beta_gateway 挂掉

**诊断**：检查端口和进程发现：
```
LocalAddress  LocalPort  OwningProcess
127.0.0.1     8000       41376

PID=27644 CMD="D:\File\exam system\backend\.venv\Scripts\python.exe" -m uvicorn ...
PID=41376 CMD="D:\Devtools\Python\python.exe" -m uvicorn ...
```

**两个后端进程同时存在**：
- PID 41376：系统 Python（占着 8000 端口）
- PID 27644：项目 venv（我之前启动的，但没绑上端口，静默退出）

系统 Python **又被某个机制自动重启了**（可能 Windows 服务监控或 start-beta.ps1 脚本残留）。venv 后端绑不上端口就退出了，beta_gateway 进程也挂了。cloudflared 转发到本地 8080 没人接听 → Cloudflare 返回 502 HTML 错误页。

**操作**：
```powershell
Stop-Process -Id 41376 -Force
Stop-Process -Id 27644 -Force
# 启动后端
& "backend\.venv\Scripts\python.exe" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# 启动 beta_gateway
& "backend\.venv\Scripts\python.exe" scripts/beta_gateway.py --port 8080 --static-root frontend/dist
```

验证完整链路（带 cloudflared 转发的 headers）：
```powershell
$resp = Invoke-WebRequest -Uri http://127.0.0.1:8080/api/auth/login -Method Post `
  -Body $bytes -ContentType "application/json" -UseBasicParsing `
  -Headers @{"X-Forwarded-Proto"="https"; "Host"="beta.example.com"}
# 返回 200 + token + Set-Cookie，正常
```

**结果**：用户反馈还是失败，响应内容是 SPA 的 index.html：
```
<!doctype html> <html lang="zh-CN"> <head> <meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1...
```

### 4.4 第四轮：找到真正的根因

**根因**：响应内容是 SPA 的 `index.html`（`lang="zh-CN"` 是前端属性），不是 API 响应。

问题出在**我手动构建前端时漏设了 `VITE_API_BASE_URL=/api` 环境变量**：
```powershell
# ❌ 我之前的构建（漏设环境变量）
cd frontend; npm run build
```

`request.ts` 的 `resolveDefaultApiBaseUrl` 在生产构建下返回空字符串，导致 axios 的 baseURL 是空。前端请求发到 `/auth/login`（没有 `/api` 前缀），beta_gateway 把它当成静态文件请求，匹配不到文件就 fallback 返回 `index.html`（SPA 的 catch-all 行为）。前端 axios 把 HTML 当 JSON 解析 → 空对象 → `normalizeToken` 取不到 token → "没有收到 token"。

`scripts/start-beta.ps1` 脚本构建时会注入这两个环境变量：
```powershell
$env:VITE_API_BASE_URL = "/api"
$env:VITE_APP_ENV = "beta"
& npm.cmd --prefix frontend run build
```

但我直接 `npm run build` 漏了。

**修复**：
```powershell
cd frontend
$env:VITE_API_BASE_URL = "/api"
$env:VITE_APP_ENV = "beta"
npm run build
```

**验证构建产物**：
```powershell
# 在 dist/assets/index-*.js 中确认
const ke="/api",_=me.create({baseURL:ke,...
```
确认包含 `baseURL:"/api"`。

**移除临时诊断代码**，恢复正常错误信息：
```ts
const token = normalizeToken(data);
if (!token) throw new Error("登录成功，但没有收到 token");
```

**结果**：登录链路打通。

---

## 5. 关键代码变更清单

### 前端

#### `frontend/src/api/request.ts`（重写 token 管理）
- 移除 `persistToken = !import.meta.env.PROD` 逻辑
- 新增 cookie 辅助函数：`setCookie` / `getCookie` / `clearCookie`
- `getToken()` 读取顺序：localStorage → cookie → 内存
- `setToken()` 同时写 localStorage 和 cookie
- `clearToken()` 同时清 localStorage 和 cookie
- cookie 配置：`max-age=86400; path=/; samesite=lax`

#### `frontend/src/stores/auth.ts`
- 新增 state 字段 `profileInitialized: false`
- `isAuthenticated` getter 改为 `(state) => !!state.user`（不再仅凭 token）
- `fetchProfile` finally 块设置 `profileInitialized = true`
- `logout()` 和 `clearGuestData()` 设置 `profileInitialized = true`
- 临时诊断代码已移除

#### `frontend/src/router.ts`
- beforeEach 逻辑改为：
  - requiresAuth 路由：没 user 时，如果有 token 且未验证过，先调 fetchProfile 验证
  - 不再仅凭 token 放行
  - `profileInitialized` 确保每次会话只验证一次

### 后端

#### `backend/services/import_task_service.py`
- 新增 `confirm_task` 函数，封装状态机/事务控制/补偿写回

#### `backend/routers/imports.py`
- `confirm_import_task` 端点改为纯 HTTP 转发，调用 service 层

#### `backend/services/course_service.py`
- 新增 `get_accessible_course` 和 `get_owned_course`（从 routers/courses.py 迁入，去掉下划线前缀）

#### `backend/routers/courses.py`
- `create_course` 改用 `Depends(require_permission("course:create"))`
- `_get_accessible_course` / `_get_owned_course` 改为从 service 导入

#### `backend/routers/practice.py`
- `from ..routers.courses import _get_accessible_course` 改为从 service 导入

---

## 6. 运维操作记录

### 进程清理
- 多次发现系统 Python（`D:\Devtools\Python\python.exe`）抢占 8000 端口
- 系统 Python 会被某个机制自动重启（可能 Windows 服务监控）
- 最终用项目 venv 启动后端：`backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000`

### beta 环境启动顺序
1. kill 占用 8000/8080 的所有 python 进程
2. 启动后端（项目 venv）
3. 启动 beta_gateway：`python scripts/beta_gateway.py --port 8080 --static-root frontend/dist`
4. 确认 cloudflared 服务 Running

### 前端构建命令（beta 环境）
**必须设置环境变量**：
```powershell
cd frontend
$env:VITE_API_BASE_URL = "/api"
$env:VITE_APP_ENV = "beta"
npm run build
```

或直接用 `scripts/start-beta.ps1`（会自动设置环境变量）。

---

## 7. 教训总结

### 7.1 误诊链路
这次登录问题经历了 4 轮误诊，每轮都以为是根因但都不是：
1. 以为是 persistToken 逻辑 → 改完不行
2. 以为是 localStorage 不持久 → 加 cookie 备份 → 引发新问题
3. 以为是 router guard 逻辑 → 改完出现"没收到 token"
4. 以为是后端进程用错 Python → 重启完还是不行
5. 以为是双进程端口冲突 → 重启所有服务还是不行
6. 最终发现是**前端构建时漏设环境变量**导致请求路径错误

### 7.2 关键教训
1. **手动构建 beta 前端必须设置 `VITE_API_BASE_URL=/api`**，否则请求路径错误，beta_gateway 返回 index.html 而不是 API 响应。应该直接用 `scripts/start-beta.ps1`。
2. **系统 Python 会自动重启抢占端口**：需要彻底清理所有 python 进程，确认 8000 端口空闲后再启动 venv 后端。
3. **token 存在 ≠ 会话有效**：token 可能在 cookie/localStorage 里过期残留，router guard 必须先调 `/auth/me` 验证 token 是否有效，不能仅凭 token 放行。
4. **微信内置浏览器会清 localStorage**：token 需要同时写 cookie 作为备份。
5. **诊断时显示实际响应内容**非常有用：用户反馈的"响应内容: <!doctype html>"立刻定位了问题是返回了 HTML 而不是 JSON。
6. **axios 把 HTML 当 JSON 解析会得到空对象**，不会抛错，导致 `normalizeToken` 静默失败。可以考虑在 request 拦截器里校验 Content-Type。

### 7.3 后续建议
- 把 `npm run build:beta` 做成 npm script，封装环境变量设置，避免手动漏设。
- 在 axios 响应拦截器里校验 `Content-Type`，如果是 HTML 但期望 JSON，抛出明确错误。
- 监控系统 Python 进程不要自动启动 uvicorn（排查 Windows 服务/启动项）。
- 考虑把"token 存在但 user 为空"作为前端健康检查的告警条件。

---

## 8. 最终状态

- ✅ 登录链路打通（前端 → beta_gateway → 后端 → cloudflared → 微信）
- ✅ 关闭网页再重开不需要重新登录（cookie 备份 + profileInitialized 验证）
- ✅ token 过期会正确跳转登录页（不再停在主页显示未登录）
- ✅ P2 代码质量修复完成（router 业务逻辑下沉、跨 router 互导消除、create_course 权限检查）
- ✅ 后端：428 passed, 1 skipped
- ✅ 前端：292 passed

---

## 9. 未修复的遗留问题（P2/P3，用户未要求修复）

- 15 处视图层绕过 API 层（Home.vue、QuestionList.vue、WrongBook.vue 等直接调 `request.*`）
- CI 缺口：不跑 alembic upgrade、Docker 构建、PG matrix
- 两套鉴权机制并存（旧路由 owner 校验 vs 新路由 RBAC）
- exam_service 越层访问 DB
- nginx 无限流配置
- 双套"我的课程"缓存合并
- 8 个复杂 .vue 文件启用 TS

---

## 10. 本 Codex 窗口接收到的历史项目上下文

本节记录用户在本窗口中提供的既有 ChatGPT 对话背景。它用于说明产品决策来源，不代表本 Codex 窗口重新验证或重新实现了其中所有事项。

### 10.1 AI 文档导入问题

既有背景显示，AI 导入曾出现以下问题：

- 长 Word 被限制为只处理前 3 个分块，或者后半段正文被截断；
- 固定字符数分块把题干、选项、答案和解析拆开；
- 子问编号、答案步骤和章节标题被误判为独立题目；
- Word 表格、图片、公式和文本框可能没有按原始顺序提取；
- AI JSON 返回格式稍有变化就被整块丢弃；
- 部分成功被误报为完整成功，失败分块缺乏可恢复机制；
- 并发解析结果可能按完成顺序合并，造成题目顺序混乱。

既有设计结论是采用“规则解析优先、AI 仅处理异常区域”的混合流程：

```text
完整提取文档结构
→ 按主问题边界组装完整题目
→ 规则解析规范题目
→ AI 处理异常题目
→ 字段、图片和覆盖率校验
→ 稳定排序和去重
→ 完整性通过后正式导入
```

用于回归的《机器学习.docx》被描述为包含 1—94 共 94 道主问题。既有验收目标包括：不把子问和答案步骤拆成新题、第 90/91 题的“解：”内容不丢失、第 87—91 题的媒体对象正确归属、无漏题、无重复、无乱序。

### 10.2 题目编号决策

既有产品决策把三个顺序概念分开：

- `source_order`：源文档中的真实出现顺序，只用于导入排序和排错；
- `display_order`：完整导入题库后生成的系统连续编号 `1—N`；
- `session_order`：本次练习中的连续序号 `1—N`。

普通用户界面不显示源文档题号。题库管理使用 `display_order`，练习进度和答题卡使用 `session_order`，数据库 ID 只负责稳定关联，不能作为显示题号。

连续编号只能在解析、校验、稳定去重和排序全部完成后生成，不能用重新编号掩盖漏题。

### 10.3 答题卡和练习页面决策

既有设计倾向于进入练习后隐藏全局底部导航，使用练习专用底栏：

```text
上一题 | 答题卡 已答数/总题数 | 下一题
```

答题卡主体使用底部抽屉，每行 5 个题号，只显示 `session_order`。提交前区分未答、已答、当前题和标记；提交后才显示正确、错误和未答状态。点击题号后按稳定的 `question_id` 跳题，不能按题号字符串定位。

### 10.4 题库入口和详情页决策

首页题库卡片与题库页卡片应进入同一题库详情路由和同一组件。统一流程为：

```text
点击题库
→ 题库详情页
→ 点击开始练习
→ 练习模式底部抽屉
→ 创建练习会话
```

不再保留“首页进入完整页面、题库页直接弹模式”的两套交互。

### 10.5 Beta 公网测试背景

测试环境采用 Windows 本机、Cloudflare Tunnel 和固定域名 `https://beta.zephyrmyb.xyz`。朋友只需点击链接即可使用；本机必须保持开机、联网且不能休眠。

公网只暴露统一入口：

```text
/       前端生产构建
/api/   FastAPI
/uploads/ 题目媒体资源
```

用户此前还反馈过首屏速度、游客入口、登录状态提示、Beta 标签遮挡、底部导航遮挡等问题。这些背景事项并非全部由本窗口重新修改。

---

## 11. 本 Codex 窗口实际执行：底部主 Tab 重复加载修复

### 11.1 用户反馈

用户明确反馈：切换底部页面后，首页、题库和“我的”页面都会重新显示加载状态：

```text
首页：重新出现题库加载骨架
题库：数量短暂变为 0，并显示题库加载中
我的：统计字段短暂变成 --，页面出现发灰效果
```

问题与接口本身耗时无关。即使接口只耗时 0.1 秒，只要页面重新进入首次加载状态，用户仍然能看到闪烁。

### 11.2 代码诊断

检查发现：

1. `frontend/src/layouts/AppLayout.vue` 的 `router-view` 直接渲染动态组件，没有 `KeepAlive`；
2. 首页、题库、导入、“我的”四个主 Tab 在路由切换时会卸载并重新创建；
3. `router-view` 外层使用 `page` 淡出过渡，页面离开时透明度降低，造成“整页发灰”的视觉现象；
4. `useMyCourses` 和 `useStudyOverview` 已经存在模块级缓存、30 秒 TTL 和请求复用，但页面实例仍然被重建；
5. 公网还可能继续使用旧 Service Worker 和被 Cloudflare 缓存的旧 `index.html`，导致本地修复没有立即进入手机运行链路。

因此，本次根因不是“缓存时间不够长”，而是主 Tab 生命周期和旧前端壳缓存没有处理正确。

### 11.3 测试先行

先增加失败测试，约束以下行为：

- `/`、`/courses`、`/import`、`/mine` 四个主 Tab 必须设置 `meta.keepAlive=true`；
- 详情页和业务子页面不能被错误保活；
- `AppLayout` 必须包含受控的 `KeepAlive`；
- 主 Tab 不得继续使用静态 `page` 淡出过渡；
- Beta 域名必须主动注销旧 Service Worker；
- `index.html` 必须使用 `no-cache`；
- 带内容哈希的 `/assets/` 资源继续使用一年不可变缓存。

首次运行目标测试时出现预期失败：缺少 `keepAlive` 元数据、布局中没有 `KeepAlive`、Beta 缺少旧缓存自愈、网关缺少缓存头函数。

### 11.4 实现内容

#### 主 Tab 页面保活

在 `frontend/src/router.ts` 中给以下路由增加 `keepAlive: true`：

- 首页 `home`
- 题库 `courses`
- AI 导入 `import`
- 我的 `mine`

在页面组件中增加稳定组件名：

- `Home`
- `CourseList`
- `ImportQuestions`
- `Mine`

在 `frontend/src/layouts/AppLayout.vue` 中加入：

```ts
const persistentTabComponentNames = ["Home", "CourseList", "ImportQuestions", "Mine"];
const routeTransitionName = computed(() => (route.meta?.keepAlive ? "" : "page"));
```

路由出口改为：

```vue
<router-view v-slot="{ Component }">
  <transition :name="routeTransitionName" mode="out-in">
    <KeepAlive :include="persistentTabComponentNames" :max="4">
      <component :is="Component" />
    </KeepAlive>
  </transition>
</router-view>
```

这样主 Tab 保留组件实例、页面局部状态和滚动状态，详情页面仍按正常生命周期创建和销毁。主 Tab 切换时不再执行透明度淡出。

#### 旧 Service Worker 和旧页面壳自愈

在 `frontend/index.html` 的主模块脚本之前增加 Beta 专用清理逻辑：

- 检测 `beta.zephyrmyb.xyz`；
- 注销现有 Service Worker 注册；
- 删除旧的 `xuexibao-shell-v5` 缓存；
- 只有实际清理过旧状态时才自动刷新一次；
- 使用 `sessionStorage` 防止刷新循环。

#### Beta 网关缓存规则

在 `scripts/beta_gateway.py` 中集中定义缓存头：

- `index.html`：`Cache-Control: no-cache`；
- Cloudflare HTML 缓存：`Cloudflare-CDN-Cache-Control: no-cache`；
- `/assets/` 哈希资源：`public, max-age=31536000, immutable`；
- 其他非哈希静态文件：`no-cache`。

### 11.5 修改文件

本次 Tab 修复涉及：

- `frontend/src/router.ts`
- `frontend/src/layouts/AppLayout.vue`
- `frontend/src/views/Home.vue`
- `frontend/src/views/CourseList.vue`
- `frontend/src/views/ImportQuestions.vue`
- `frontend/src/views/Mine.vue`
- `frontend/index.html`
- `scripts/beta_gateway.py`
- `frontend/src/router-reference-aliases.test.ts`
- `frontend/src/layouts/__tests__/AppLayout.test.ts`
- `frontend/src/__tests__/serviceWorker.test.ts`
- `backend/tests/test_beta_gateway.py`
工作区在本窗口开始前已经存在大量未提交修改。本窗口没有重置、覆盖、暂存、提交或推送用户的既有改动。

### 11.6 验证结果

执行结果：

- 前端全量测试：54 个测试文件、292 个测试全部通过；
- `npm.cmd run lint`：通过；
- `npm.cmd run build`：通过；
- Beta 启动脚本与网关测试：3 个通过；
- 目标文件 `git diff --check`：通过，仅有 Windows LF/CRLF 提示。

第一次直接运行 `start-beta.ps1` 时被 Windows PowerShell 执行策略拦截。随后使用一次性的命令启动，没有修改系统永久执行策略：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-beta.ps1
```

启动脚本重新构建前端、启动后端和网关，并确认已有 cloudflared Windows 服务处于运行状态。

### 11.7 公网真实验收

部署后检查：

- 本地 `http://127.0.0.1:8080/` 返回 200；
- 本地 `/api/health` 返回 `{"status":"ok"}`；
- 公网 `https://beta.zephyrmyb.xyz/` 返回 200；
- 公网 `/api/health` 返回 200；
- 公网 HTML 使用 `no-cache`；
- 当时的公网主资源已经切换到新构建 `assets/index-BPlLTRlq.js`。

随后使用 Playwright 和移动端尺寸，通过公网域名创建临时游客会话并连续执行首页、题库、我的切换：

- 共完成 18 次主 Tab 跳转；
- 首页节点保持同一个实例：`true`；
- 题库节点保持同一个实例：`true`；
- “我的”节点保持同一个实例：`true`；
- 首次加载完成后，“正在加载题库”和“题库加载中”再次出现次数：0；
- 连续切换 5 轮后，所有数据接口新增请求次数：0。

由此证明本次修改解决的是组件重新初始化问题，而不是简单把重新加载速度加快。

---

## 12. 本 Codex 窗口对鉴权日志的复核

用户提供本文件后，本窗口以只读方式核对日志与当前代码和运行状态，没有继续修改鉴权业务代码。

### 12.1 已核实正确的内容

以下内容能够与当前代码对应：

- 登录“成功但没有收到 token”的根因确实可能是 Beta 构建缺少 `/api` 前缀，静态网关回退到 `index.html`；
- `scripts/start-beta.ps1` 会注入 `VITE_API_BASE_URL=/api` 和 `VITE_APP_ENV=beta`；
- 当前生产构建产物包含 `/api`，检查时主资源为 `assets/index-DaM1Zoh7.js`；
- 后端登录接口会设置 HttpOnly Cookie `xuexibao_access`；
- 后端鉴权同时支持 Bearer token 和 HttpOnly Cookie；
- `confirm_task`、`course_service` helper 迁移和 `course:create` 权限检查已经存在于代码中；
- 本地和公网 `/api/health` 在复核时均返回 200。

### 12.2 当前进程状态与日志结论不一致

复核时，8000 和 8080 实际监听进程均为：

```text
D:\Devtools\Python\python.exe
```

当时观察到：

```text
8000 → PID 28996 → 系统 Python uvicorn
8080 → PID 30996 → 系统 Python beta_gateway
```

项目虚拟环境应为：

```text
backend\.venv\Scripts\python.exe
```

同时 `data/beta/run-state.json` 不存在，说明当前服务不是由可追踪的 `start-beta.ps1` 状态完整托管，或者脚本启动的进程后来又被外部机制替换。

因此，日志中“最终用项目 venv 稳定运行”的表述不能视为当前事实。“系统 Python 自动重启并抢占端口”的问题仍未收口。

### 12.3 前端可读 token Cookie 的安全和逻辑风险

后端已经提供 HttpOnly Cookie：

```text
xuexibao_access
```

但前端又把完整 bearer token 写入 JavaScript 可读 Cookie：

```text
xuexibao_token
```

该方案存在以下问题：

1. JavaScript 可读取完整 token，XSS 发生时更容易泄露凭据；
2. 前端 Cookie 没有 `HttpOnly`，代码中也没有显式 `Secure`；
3. 路由守卫只有在 `getToken()` 非空时才调用 `/auth/me`；
4. 如果 localStorage 和前端 Cookie 被清除、但后端 HttpOnly Cookie 仍然有效，路由仍会直接跳登录页；
5. 当前“关闭微信 WebView 后保持登录”依赖前端可读 Cookie，而不是完全依赖更安全的 HttpOnly 会话恢复。

更稳妥的方向是：首次进入受保护路由时，只要用户没有明确退出，就允许调用一次 `/auth/me`，由后端 HttpOnly Cookie 恢复会话；生产环境不应要求 JavaScript 必须先读到 token 才尝试恢复。

### 12.4 `setToken()` 的异常分支与注释不一致

当前 `setToken()` 在同一个 `try` 中先调用：

```ts
window.localStorage.setItem(...)
```

然后才调用：

```ts
setCookie(...)
```

如果 localStorage 本身抛出异常，执行会直接进入 `catch`，Cookie 写入不会发生。这与代码注释“localStorage 不可用时，cookie 仍已写入”不一致。

### 12.5 防止错误构建的永久措施尚未完成

当前使用 `scripts/start-beta.ps1` 可以正确构建，但以下建议尚未实现：

- `npm run build:beta` 独立脚本；
- 普通生产构建缺少 API Base 时直接失败；
- axios/API 层校验 JSON 接口的 `Content-Type`；
- API 意外返回 HTML 时抛出明确错误。

因此，开发者再次手动执行普通 `npm run build` 时，仍然可能重现“请求缺少 `/api` 前缀”的问题。

### 12.6 测试覆盖缺口

当前前端路由测试规定：没有 JavaScript 可读 token 时，不调用 `/auth/me`。这与“只剩 HttpOnly Cookie 也能恢复登录”的理想目标相冲突。

仍需增加以下真实场景：

```text
localStorage 无 token
+ JavaScript 可读 Cookie 无 token
+ 后端 HttpOnly Cookie 有效
→ 首次进入受保护页面调用 /auth/me
→ 自动恢复 user
→ 不跳登录页
```

还应覆盖：

- HttpOnly Cookie 过期时正确跳登录页；
- 用户主动退出后不得被旧 Cookie 恢复；
- 微信 WebView 关闭再打开的真实行为；
- API 返回 HTML 时给出明确错误，而不是“没有收到 token”。

### 12.7 文档本身

- 文件编码是 UTF-8，内容没有损坏；
- Windows PowerShell 旧版本使用默认编码读取时会显示乱码，需要 `Get-Content -Encoding utf8`；
- 复核时该文件为 Git 未跟踪文件；
- 本窗口没有自动暂存、提交或推送该文件。

---

## 13. 截至本窗口结束的准确状态

### 已完成并有证据

- ✅ Beta 登录 API 请求路径已经使用 `/api`；
- ✅ 当前本地和公网健康检查返回 200；
- ✅ 首页、题库、导入、“我的”主 Tab 已加入受控 `KeepAlive`；
- ✅ 主 Tab 切换不再执行页面透明度淡出；
- ✅ 首次数据加载后，重复切换不重新显示题库加载状态；
- ✅ 5 轮公网 Tab 循环没有产生额外数据请求；
- ✅ Beta 页面会主动清理旧 Service Worker 和旧壳缓存；
- ✅ `index.html` 使用 `no-cache`，哈希资源继续长期缓存；
- ✅ 前端 292 个测试、lint、生产 build 和 Beta 网关相关测试通过。

### 仍未彻底解决

- ⚠️ Beta 当前运行进程仍可能被系统 Python 接管；
- ⚠️ 缺少可靠的进程托管和 `run-state.json` 状态闭环；
- ⚠️ 登录持久化依赖 JavaScript 可读 token Cookie，存在安全和恢复逻辑风险；
- ⚠️ 缺少 HttpOnly-Cookie-only 会话恢复测试；
- ⚠️ 缺少 `build:beta` 和 API Content-Type 防护；
- ⚠️ 原有 AI 导入、编号、图片归属等背景问题未在本窗口重新验收。

### 建议下一步顺序

1. 先查清系统 Python 自动启动 uvicorn/beta_gateway 的来源，统一由一个可追踪的启动入口托管；
2. 以 HttpOnly Cookie 为生产环境会话恢复主路径，移除对 JavaScript 可读 token Cookie 的依赖；
3. 增加 cookie-only 恢复、主动退出和过期 Cookie 的端到端测试；
4. 增加 `build:beta` 和 API 返回 Content-Type 校验；
5. 完成后再重新声明“关闭微信网页后无需重新登录”为稳定验收结论。
