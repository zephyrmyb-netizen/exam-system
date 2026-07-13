# AI 导入可靠性修复

## 目标

修复长 Word 文档或带图片 Word 文档的 AI 导入只解析少量题目、却被误标记为成功的问题。

## 根因

1. 文档含图片时，全文与全部图片被发送到单次多模态请求，绕过文本分块。
2. 单个超长 Word 段落不会被原有按段落分块逻辑切开。
3. 手机端创建后台导入任务的上传等待只有 30 秒，大文件在弱网络下容易在任务创建前超时。
4. 文件选择器展示了旧版 DOC/PPT/TXT，实际 AI 导入并不支持，造成无效尝试。

## 修改范围

- `backend/imports/import_orchestrator.py`
- `backend/config.py`
- `backend/.env.example`
- `backend/tests/test_import_reliability.py`
- `frontend/src/api/imports.ts`
- `frontend/src/stores/aiImportTask.ts`
- `frontend/src/utils/importFiles.ts`
- `frontend/src/views/ImportQuestions.vue`
- 导入相关前端测试与 `releaseNotes.ts`

## 处理

1. 默认文本分块从 5000 字符降至 2000 字符；示例配置与运行时默认的最大分块数统一为 20。
2. 超长单段文本优先按编号题目边界切分；没有编号边界时才按自然标点或空白切分。
3. 文本题先走分块解析；嵌入图片改为每 3 张一组补充解析，合并后去重。单个图片批次失败只生成警告，不会覆盖已成功的文本题。
4. 创建后台导入任务的客户端超时延长至 120 秒，并明确失败提示。
5. 手机文件选择器只展示可直接解析的 DOCX、PDF、PPTX、PNG、JPG、JPEG、WEBP 格式；旧格式仍保留清晰的转换提示。

## 回归测试

- 新增长单段编号题分块测试：旧实现失败，新实现通过。
- 新增“文本题 + 嵌入图片题”合并测试：旧实现只返回图片题，新实现合并返回。
- 导入后端相关测试：68 passed。
- 后端全量测试（拆分执行以避开终端 120 秒输出窗口）：379 passed, 1 skipped。
- `python scripts\\security_check.py`：3/3 passed。
- 前端 lint：通过。
- 前端测试：36 个文件、121 项通过。
- 前端构建：通过。
- `git diff --check`：通过。

## 风险与后续

- 第三方模型仍可能对格式极差或扫描质量很低的文件返回不完整内容；用户应在预览页核对题目数后确认导入。
- 本轮未变更数据库、API 路径、题库写入逻辑或用户权限。

## Git

- Commit: `45907c0 fix: harden long document AI imports`
- Push: completed to `origin/codex/phase4-differentiation`
