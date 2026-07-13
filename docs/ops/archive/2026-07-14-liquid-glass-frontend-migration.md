# 学习宝 Liquid Glass 前端视觉迁移

## Objective
Apply the user-provided `exam-platform-ui` handoff to the existing Learning Bao Vue frontend without changing backend APIs, import behavior, practice state, or route contracts.

## Scope
- Shared visual tokens, shell, and four-item navigation.
- Full page-level migration for home, course library, AI import, practice, chat, and profile surfaces.
- Targeted frontend tests for navigation and high-value page entry points.

## Constraints
- Treat `exam-platform-ui/` as an untracked reference package; do not edit or stage it.
- Preserve existing API paths, stores, route names, and practice/import workflows.
- Keep immersive practice and exam routes free of the bottom navigation.

## Verification
- `npm.cmd run lint`
- `npm.cmd run test -- --run`
- `npm.cmd run build`

## Delivered
- Replaced the shared surface tokens, floating four-item navigation, mobile shell, and dark semantic surfaces with the supplied Emerald Liquid Glass system.
- Rebuilt the information hierarchy of Home, Course Library, AI Import, Mine, Practice, and Exam Take around the supplied page references.
- Added the course practice mode sheet and real course coverage indicators without changing backend API paths.
- Kept AI chat as a Home entry rather than a fifth navigation tab.
- Passed real course question counts into the immersive practice header so the progress display does not use reference-data placeholders.

## Verification
- `npm.cmd run lint` - passed.
- `npm.cmd run test -- --run` - passed: 36 test files, 121 tests.
- `npm.cmd run build` - passed.
- `git diff --check` - passed; only Git line-ending notices were emitted for existing Windows working-copy normalization.

## Status
Completed. No backend API, database, or import/practice business contract was changed.
