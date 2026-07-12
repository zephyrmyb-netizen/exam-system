# Pencil MCP 安装后隔离验证

- 执行时间：2026-07-12
- 执行窗口：GPT-5.6 Luna
- 前置记录：上一次安装尝试因 NSIS 完整性检查失败，见 [2026-07-12-pencil-install-and-mcp-validation-blocked.md](./2026-07-12-pencil-install-and-mcp-validation-blocked.md)。用户随后确认已完成安装并提供 Pencil 欢迎页截图。
- 任务范围：只验证 Pencil Desktop 与 Codex 本地 MCP；不修改学习宝业务代码。

## 安装与配置

- Pencil 安装路径：`D:\Software\pencil\Pencil.exe`
- Pencil 版本：`1.1.69`，ProductVersion `1.1.69.0`
- 安装后 Pencil.exe SHA256：`CF7CE579A5F532038402364A4B72944102113DC2FD04EA809C5290E45EEE0039`
- 安装后 Pencil.exe Authenticode：`Valid`；发布者 `High Agency Inc.`，证书由 DigiCert 签发。
- 原始安装包：`D:\Devtools\Pencil\Installer\Pencil-win-x64.exe`
- 原始安装包 SHA256：`5BE5C91359E056A439AEC39CA6DC02EEF25D789862E5E70671C8989BD4CEFC89`
- 原始安装包 Authenticode：`NotSigned`；用户已明确接受该风险。
- 安装前 config.toml SHA256：`52FD61F00AE0873DC38B4B2A09D45BB8DF273CBE60AFA2784B9630FD1F0DF4CE`
- 安装后 config.toml SHA256：`AE2116B0CB0E0F30B2D714C7994CFC09DF718B515BA9F8D5878EA6BB1CD8EBA0`
- 配置变化：新增且仅新增一个 `[mcp_servers.pencil]`；command 为本地 `D:\Software\pencil\resources\app.asar.unpacked\out\mcp-server-windows-x64.exe`，args 为 `--app desktop --agent codexCLI`。未发现 Token、API Key、密码、重复 Pencil MCP、其他 MCP、模型、approval、sandbox 或 network 配置变化。另有 Codex 配置路径引号规范化及空 `[hooks.state]` 表清理，已记录为非 Pencil MCP 配置格式变化。
- 配置备份：`C:\Users\zephy\.codex\backups\config-before-pencil-install-20260712.toml`。

## MCP 验证

- MCP 工具已加载：`get_editor_state`、`batch_design`、`batch_get`、`snapshot_layout`、`get_screenshot`、`get_variables`、`get_guidelines`、`export_nodes`、`export_html`。
- `get_editor_state`：通过；最终活动文件为 `D:\Devtools\Pencil\Tests\Pencil-MCP-Safety-Test.pen`。
- `batch_design`：通过；创建 390 × 844、背景 `#F6F8FC`、圆角 8 的 `Pencil MCP Safety Test` 画板，标题为“学习宝设计测试”，创建蓝色按钮并将文字修改为“继续学习”、颜色修改为 `#1D4ED8`。
- `batch_get`：通过；重新打开后仍读取到画板、标题和按钮文字。
- `snapshot_layout`：通过；返回 `No layout problems`。
- `get_screenshot`：通过；截图非空白，并由 MCP 导出为 `D:\Devtools\Pencil\Tests\Pencil-MCP-Safety-Test.png`，文件大小 41,485 字节。
- 保存：通过；使用 Pencil 保存动作生成文件，随后移动已保存文件到指定隔离目录，未手工编辑 .pen 内容。
- 关闭与重新打开：通过；关闭 Pencil 后无残留进程，重新打开目标文件后 MCP 恢复连接，节点内容和布局仍完整。
- 首次重启后 MCP 曾因目标文件尚未在编辑器打开而报错；通过重新打开目标文件恢复，未修改配置。

## 安全检查

- 测试文件：`D:\Devtools\Pencil\Tests\Pencil-MCP-Safety-Test.pen`，大小 10,115 字节。
- 截图：`D:\Devtools\Pencil\Tests\Pencil-MCP-Safety-Test.png`，大小 41,485 字节。
- 未打开学习宝目录，未读取 backend/.env，未修改 frontend/backend、数据库、releaseNotes 或业务文件。
- 未安装 Claude Code、Pencil CLI 或全局 npm 包；`npm.cmd list -g --depth=0` 为空。
- 未发现 Pencil 开机启动项；Pencil 退出后无残留进程。
- 测试产物位于 D:\Devtools\Pencil\Tests，不提交到学习宝仓库。
- 安装包未签名及 Pencil 源码非公开仍是安全风险；安装后的 Pencil.exe 具有有效 High Agency Inc. 签名。

## 回滚与交接

1. 完全退出 Pencil。
2. 从 Codex 配置移除 `[mcp_servers.pencil]`，必要时使用配置备份恢复。
3. 备份路径：`C:\Users\zephy\.codex\backups\config-before-pencil-install-20260712.toml`。
4. 从 Windows 设置卸载 Pencil。
5. 删除 `D:\Devtools\Pencil`、测试文件或截图前须由用户确认；不自动删除测试和备份文件。

- 结论：隔离安装和 Codex 本地 MCP 读写、布局、截图、保存、关闭重开验证通过，可以交给 Ferra 开始学习宝设计；Ferra 仍只能使用独立 Pencil 测试/设计文件，不得直接打开学习宝业务目录。
- 实际修改的项目文件：docs/ops/INDEX.md，以及本归档留档。
- Commit：待提交。
- Push：待推送。
