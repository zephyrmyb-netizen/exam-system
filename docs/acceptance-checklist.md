# 验收清单

在部署或提交测试前逐项执行，确认系统功能正常。

> 运行前确保：后端已启动（`uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`），
> 运行中如有失败项，检查后端日志定位原因。

---

## 1. 注册与登录

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 1.1 | 健康检查 | `curl http://127.0.0.1:8000/health` | 返回 `{"status":"ok"}` | |
| 1.2 | 注册成功 | `curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" -d '{"username":"testuser","password":"123456","invite_code":"dev-invite"}'` | 返回 201，`{"message":"注册成功"}` | |
| 1.3 | 空邀请码拒绝 | `curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" -d '{"username":"user2","password":"123456","invite_code":""}'` | 返回 400，包含"邀请码" | |
| 1.4 | 错误邀请码拒绝 | `curl -X POST http://127.0.0.1:8000/auth/register -H "Content-Type: application/json" -d '{"username":"user3","password":"123456","invite_code":"wrong"}'` | 返回 400，包含"邀请码" | |
| 1.5 | 重复用户名拒绝 | 再次执行 1.2 | 返回 400，包含"已存在" | |
| 1.6 | 登录成功 | `curl -X POST http://127.0.0.1:8000/auth/login -H "Content-Type: application/json" -d '{"username":"testuser","password":"123456"}'` | 返回 200，包含 `access_token` | |
| 1.7 | 登录密码错误 | `curl -X POST http://127.0.0.1:8000/auth/login -H "Content-Type: application/json" -d '{"username":"testuser","password":"wrong"}'` | 返回 401 | |
| 1.8 | 获取个人信息 | 用 1.6 返回的 token 调用 `curl http://127.0.0.1:8000/auth/me -H "Authorization: Bearer <token>"` | 返回 200，包含 `username: testuser` | |
| 1.9 | 未认证拒绝 | `curl http://127.0.0.1:8000/auth/me` | 返回 401 | |

## 2. 课程管理

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 2.1 | 创建课程 | 用 token 调用 `curl -X POST http://127.0.0.1:8000/courses/ -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"name":"高等数学","subject":"数学"}'` | 返回 201，含课程 ID | |
| 2.2 | 查看我的课程 | `curl http://127.0.0.1:8000/courses/mine -H "Authorization: Bearer <token>"` | 返回数组，包含刚创建的课程 | |
| 2.3 | 编辑课程 | `curl -X PATCH http://127.0.0.1:8000/courses/{course_id} -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"name":"高数上册"}'` | 返回 200，name 已修改 | |
| 2.4 | 删除课程 | `curl -X DELETE http://127.0.0.1:8000/courses/{course_id} -H "Authorization: Bearer <token>"` | 返回 200，`{"message":"课程已删除"}` | |
| 2.5 | 权限拒绝 | 用另一用户 token 删除他人课程 | 返回 403 | |

## 3. 题目管理

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 3.1 | 手动加题（单选题） | `curl -X POST http://127.0.0.1:8000/questions/batch -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '[{"type":"single_choice","question":"1+1=?","options":{"A":"1","B":"2","C":"3","D":"4"},"answer":"B","course_id":1}]'` | 返回 200，`imported_count: 1` | |
| 3.2 | 手动加题（判断题） | 同上，`type` 改为 `true_false`，`answer` 为 `正确` | 返回 200 | |
| 3.3 | 手动加题（填空题） | 同上，`type` 改为 `fill_blank`，`answer` 为 `TCP||传输控制协议` | 返回 200 | |
| 3.4 | 手动加题（简答题） | 同上，`type` 改为 `short_answer`，`answer` 为 `冒泡排序&&交换&&相邻` | 返回 200 | |
| 3.5 | 查看题目列表 | `curl "http://127.0.0.1:8000/questions/my?course_id=1" -H "Authorization: Bearer <token>"` | 返回题目数组 | |
| 3.6 | 删除题目 | `curl -X DELETE http://127.0.0.1:8000/questions/{question_id} -H "Authorization: Bearer <token>"` | 返回 200 | |
| 3.7 | 非法删除 | 用另一用户 token 删除他人的题 | 返回 403 | |

## 4. Word/PPT 预览导入

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 4.1 | 上传预览 | `curl -X POST http://127.0.0.1:8000/imports/file/preview -H "Authorization: Bearer <token>" -F "file=@test.docx"` | 返回预览题目数组（需配置 OPENAI_API_KEY） | |
| 4.2 | 确认导入 | 将 4.1 返回的题目数组放入 `curl -X POST http://127.0.0.1:8000/imports/confirm -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"questions":[...],"course_id":1}'` | 返回 200，含 `imported_count` | |
| 4.3 | 文件格式拒绝 | 上传非 docx/pptx 文件 | 返回 400，提示格式不支持 | |
| 4.4 | 空文件拒绝 | 上传空文件 | 返回 400 | |

## 5. 刷题与判分

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 5.1 | 随机抽题 | `curl "http://127.0.0.1:8000/practice/random?course_id=1" -H "Authorization: Bearer <token>"` | 返回一道题目 | |
| 5.2 | 提交正确答案 | 将 5.1 返回的 `id` 和答案提交：`curl -X POST http://127.0.0.1:8000/practice/submit -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"question_id":1,"user_answer":"B"}'` | 返回 `is_correct: true` | |
| 5.3 | 提交错误答案 | `curl -X POST http://127.0.0.1:8000/practice/submit -H "Content-Type: application/json" -H "Authorization: Bearer <token>" -d '{"question_id":1,"user_answer":"A"}'` | 返回 `is_correct: false` | |
| 5.4 | 不存在的题目 | 提交一个不存在的 question_id | 返回 404 | |

## 6. 错题本

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 6.1 | 错题列表 | `curl http://127.0.0.1:8000/wrongbook/ -H "Authorization: Bearer <token>"` | 返回错题记录（含答错的题） | |
| 6.2 | 移除错题 | `curl -X DELETE http://127.0.0.1:8000/wrongbook/{question_id} -H "Authorization: Bearer <token>"` | 返回 200，`{"message":"已从错题本移除"}` | |
| 6.3 | 移除不存在的记录 | `curl -X DELETE http://127.0.0.1:8000/wrongbook/999999 -H "Authorization: Bearer <token>"` | 返回 404 | |

## 7. 间隔复习

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 7.1 | 到期复习列表 | `curl "http://127.0.0.1:8000/practice/review/due?course_id=1" -H "Authorization: Bearer <token>"` | 返回到期复习题目列表（可能为空） | |
| 7.2 | 错题复习 | `curl "http://127.0.0.1:8000/practice/review/wrong?course_id=1" -H "Authorization: Bearer <token>"` | 返回错题或 404（无错题时） | |
| 7.3 | 今日复习摘要 | `curl http://127.0.0.1:8000/practice/review/today -H "Authorization: Bearer <token>"` | 返回今日复习统计 | |
| 7.4 | 薄弱题型 | `curl http://127.0.0.1:8000/practice/insights/weak-types -H "Authorization: Bearer <token>"` | 返回错误率分析 | |

## 8. 公共题库

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 8.1 | 发布课程 | `curl -X POST http://127.0.0.1:8000/courses/{course_id}/publish -H "Authorization: Bearer <token>"` | 返回课程，visibility 为 `public` | |
| 8.2 | 查看公共题库 | 用另一个用户 token：`curl http://127.0.0.1:8000/library/public -H "Authorization: Bearer <token2>"` | 返回包含已发布课程的列表 | |
| 8.3 | 查看公开课程题目 | `curl http://127.0.0.1:8000/library/public/{course_id}/questions -H "Authorization: Bearer <token2>"` | 返回题目列表 | |
| 8.4 | 撤回课程 | `curl -X POST http://127.0.0.1:8000/courses/{course_id}/unpublish -H "Authorization: Bearer <token>"` | 返回课程，visibility 为 `private` | |
| 8.5 | 撤回后不可见 | 用 token2 再次查看 8.2 | 该课程不再出现在公共列表 | |
| 8.6 | 发布单题 | `curl -X POST http://127.0.0.1:8000/questions/{question_id}/publish -H "Authorization: Bearer <token>"` | 返回题目，visibility 为 `public` | |
| 8.7 | 撤回单题 | `curl -X POST http://127.0.0.1:8000/questions/{question_id}/unpublish -H "Authorization: Bearer <token>"` | 返回题目，visibility 为 `private` | |

## 9. 手机访问

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 9.1 | 局域网访问 | 手机连同一 WiFi，浏览器打开 `http://电脑IP:5173` | 页面正常加载，登录后显示数据 | |
| 9.2 | API 自动推导 | 手机访问时前端自动使用 `http://电脑IP:8000` 作为 API 地址 | 请求正常，无跨域错误 | |

## 10. 权限与错误场景

| # | 步骤 | 操作 | 预期结果 | 状态 |
|---|------|------|----------|------|
| 10.1 | 未认证访问 | 调用任意需认证接口（不带 token） | 返回 401 | |
| 10.2 | Token 过期 | 使用过期 token | 返回 401 | |
| 10.3 | 访问他人私有课程 | 用 token A 访问 token B 的私有课程 `GET /courses/{course_id}` | 返回 404（视为不存在） | |
| 10.4 | 删除他人课程 | 用 token A 执行 `DELETE /courses/{course_id}` 对 token B 的课程 | 返回 403 | |
| 10.5 | 重复注册 | 用已存在的用户名再次注册 | 返回 400 | |

---

## 环境信息记录

| 项目 | 值 |
|---|---|
| 后端地址 | http://127.0.0.1:8000 |
| 前端地址 | http://127.0.0.1:5173 |
| 测试用户 | testuser / 123456 |
| 测试时间 | |
| 测试环境 | |
| 测试人 | |
