# AI 导入题目覆盖率修复

- 执行时间：2026-07-13
- 执行窗口：Codex 主窗口
- 任务目标：修复长 Word 文档中 AI 单次返回部分题目却仍被当作导入成功的问题。
- 允许修改的文件：`backend/imports/import_orchestrator.py`、`backend/tests/test_import_reliability.py`、本留档与操作索引。
- 实际修改的文件：`backend/imports/import_orchestrator.py`、`backend/tests/test_import_reliability.py`、本留档、`docs/ops/INDEX.md`。
- 验证命令与结果：`backend\\.venv\\Scripts\\python.exe -m pytest backend\\tests\\test_import_reliability.py -q`（5 passed）；导入专项 73 passed；`backend\\.venv\\Scripts\\python.exe -m pytest backend\\tests -q`（422 passed, 1 skipped）；`backend\\.venv\\Scripts\\python.exe scripts\\security_check.py`（3/3 PASS）；`git diff --check`（通过）。
- Commit：`9f356f4 fix: prevent incomplete AI imports`；`7adc8dc docs: archive AI import coverage repair`。
- Push：已推送至 `origin/codex/phase4-differentiation`；后端已重启，`GET /health` 返回 `{"status":"ok"}`。
- 遗留风险：90 道编号题会拆成约 15 次常规 AI 请求；若某块仍少返回，会额外用 2 题小批次重试，因此耗时和模型调用次数会增加。编号格式无法识别的文档仍按原有非编号分块路径处理。
- 下一步：重启后端后，使用原始 `机器学习.docx` 重新解析；旧任务 `ab7fce45-47a5-4bd7-8368-ebac1c7a9452` 已经是不完整预览，不能自动补齐。
