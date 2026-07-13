# 学习宝 Codex 源码交接说明

本交接包用于在独立 Codex 环境中继续实现学习宝。请先阅读根目录的 `SOURCE_REVISION.txt`、`SOURCE_TREE.txt` 和 `MANIFEST.sha256`，再按下列顺序获取上下文：

1. `README-开始工作前必读.md`
2. `exam-platform-ui/IMPLEMENTATION_MAP.md`
3. `exam-platform-ui/CODEX_HANDOFF.md`
4. `exam-platform-ui/design-reference.md`
5. `frontend/src/router.ts`

## 设计与实现契约

- `exam-platform-ui/` 是本轮视觉实现的唯一设计真相。
- 固定技术栈是 Vue 3 + TypeScript + Vite + Pinia + Vue Router + Lucide Vue。
- 8 个参考界面映射为 7 个真实路由落点和 `PracticeSummaryModal.vue` 这 1 个现有弹窗。
- 底部导航固定为 4 个标签：首页、题库、导入、我的。
- `PracticeHub.vue` 是现有辅助页面，不是参考页或第五个底部标签。
- 保持后端 API、响应 schema、数据库和业务行为兼容。

## 明确排除

仓库根目录的 `frontend-preview.html` 是旧“墨韵书房”静态预览：它不属于当前设计输入，不得用于实现比对，也不会进入交接 ZIP。

交接包还会排除真实 `.env`、密钥、数据库、上传文件、日志、虚拟环境、依赖目录、构建产物、测试产物、缓存、验收截图，以及 `docs/ops/active/2026-07-11-pencil-mcp-install.md`。

## 验证包完整性

在仓库根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/package_codex_handoff.ps1 -Verify <zip-path>
```

验证会拒绝缺少根元数据、含禁入文件、清单不完整或 SHA-256 不匹配的归档。
