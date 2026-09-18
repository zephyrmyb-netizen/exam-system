# 测试方法与当前证据

## 1. 测试策略

项目采用“静态检查 + 单元/接口测试 + 构建验证 + 安全扫描”的分层门禁。

| 层级 | 工具 | 覆盖目标 |
| --- | --- | --- |
| 前端静态检查 | ESLint、Prettier、vue-tsc | 语法、类型、DOM 全局和格式一致性 |
| 前端测试 | Vitest、Vue Test Utils | API 封装、store、composable、组件和路由交互 |
| 前端构建 | Vite | 生产资源打包和按路由拆包 |
| 后端静态检查 | Ruff | Python 语法、导入和常见质量问题 |
| 后端测试 | pytest、FastAPI TestClient | 认证、权限、题库、导入、练习、考试和事务 |
| 仓库安全 | `scripts/security_check.py` | 密钥、数据库、上传、构建产物和高风险文件 |
| CI | GitHub Actions | 在干净 Linux 环境重复执行上述门禁及视觉测试 |

## 2. 本地验证基线

验证日期：2026-09-17。验证对象是当时的本地工作区，不代表后续提交自动保持相同结果。

| 命令 | 结果 |
| --- | --- |
| `npm.cmd run lint` | 通过 |
| `npm.cmd run test -- --run` | 60 个测试文件、309 项测试通过 |
| `npm.cmd run build` | 通过，Vite 完成生产构建 |
| `backend\\.venv\\Scripts\\python.exe -m ruff check backend` | 通过 |
| `backend\\.venv\\Scripts\\python.exe -m pytest backend\\tests -q` | 444 通过、1 跳过 |
| `backend\\.venv\\Scripts\\python.exe scripts\\security_check.py` | 3/3 通过 |

## 3. 可重复执行命令

```powershell
cd "D:\File\exam system\frontend"
npm.cmd ci
npm.cmd run format:check
npm.cmd run lint
npm.cmd run test -- --run
npm.cmd run build

cd "D:\File\exam system"
backend\.venv\Scripts\python.exe -m ruff check backend
backend\.venv\Scripts\python.exe -m pytest backend\tests -q
backend\.venv\Scripts\python.exe scripts\security_check.py
```

正式发布前还应执行 GitHub Actions 中的 Playwright 视觉回归测试，并用真实手机复验登录、题库、练习、AI 导入、AI 对话、我的页和深浅主题。

## 4. 评价指标建议

毕业论文不能只写“测试通过”，建议补充可测指标：

- 功能正确性：各模块用例通过率与主要异常分支覆盖。
- AI 导入完整性：原始题目数、成功解析数、无效数、重复数和人工修订数。
- 导入性能：文字提取耗时、AI 总耗时、平均每块耗时和失败重试次数。
- 练习可靠性：重复提交是否只产生一条记录、题库结束是否停止、错题状态是否正确更新。
- 移动端可用性：375、390、430 像素宽度下是否横向溢出，底部操作是否被安全区域遮挡。
- 安全性：未授权访问、越权访问、默认密钥、CORS 和敏感文件检查。

## 5. 当前限制与风险

- pytest 仍提示 `starlette.testclient` 与 `httpx` 的弃用警告，未来依赖升级时需要单独处理。
- 测试环境固定使用开发邀请码并允许宽松 CORS，因此生产配置必须另行验证。
- 自动化测试通过不能替代真实 AI 上游、真实文档和真机 WebView 验收。
- 当前工作区包含大量未提交并行改动；在形成正式版本标签前，需要按模块拆分提交并在干净检出中重跑全部门禁。
