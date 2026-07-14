# Pencil 1.1.69 安装与 Codex MCP 隔离验证（Blocked）

- 执行时间：2026-07-12
- 执行窗口：GPT-5.6 Luna
- 任务目标：在用户明确接受未签名风险的前提下，安装 Pencil 1.1.69，并仅在 D:\Devtools\Pencil\Tests 中隔离验证 Codex MCP；不修改学习宝业务代码。
- 用户授权：用户明确知晓安装包 Authenticode 为 NotSigned，并授权运行指定安装包；仍未关闭 Defender、未绕过 SmartScreen、未添加白名单、未使用管理员权限强行安装。
- 安装包：D:\Devtools\Pencil\Installer\Pencil-win-x64.exe
- 安装包版本：1.1.69
- 安装包 SHA256：5BE5C91359E056A439AEC39CA6DC02EEF25D789862E5E70671C8989BD4CEFC89，与用户指定值一致。
- 安装包签名：Authenticode `NotSigned`，无签名发布者。
- 安装前 config.toml SHA256：52FD61F00AE0873DC38B4B2A09D45BB8DF273CBE60AFA2784B9630FD1F0DF4CE。
- 安装前配置备份：C:\Users\zephy\.codex\backups\config-before-pencil-install-20260712.toml，SHA256 与安装前 config.toml 一致。
- 安装前 MCP：未发现 `[mcp_servers...]` 配置节；未写入 Token、API Key 或密码。
- 安装前全局 npm：`npm.cmd list -g --depth=0` 显示为空。
- 安装前 Pencil 进程：未发现。
- 安装前已知安装路径：四个用户指定系统路径均不存在；D:\Devtools\Pencil 仅包含 Installer 工作目录。

## 执行结果

- 以当前普通用户启动指定安装包，未使用管理员权限。启动进程为 `Pencil-win-x64.exe`。
- 安装器弹出 NSIS Error：`Installer integrity check has failed`，提示安装器完整性检查失败。
- 安装未完成；未发现 Pencil 安装目录或 Pencil.exe，未完成邮箱激活。
- 未启动 Pencil Desktop，未创建测试文件 `D:\Devtools\Pencil\Tests\Pencil-MCP-Safety-Test.pen`。
- 未修改 Codex `config.toml`；未出现 Pencil MCP，也没有重复 MCP。
- 未能运行 MCP 读写、布局、截图、保存或关闭重开测试。
- 同一官方 URL `https://www.pencil.dev/download/Pencil-win-x64.exe` 的独立重下载在当前连接中未能在超时前完成，未用于安装；原安装包未被覆盖或修改。
- Codex CLI 基线仍因 Windows `Access is denied` 无法直接执行 `codex --version` 与 `codex mcp list`；该问题独立于本次 NSIS 安装器失败。

## 业务代码与安全边界

- 未修改 frontend/** 或 backend/**，未读取 backend/.env，未修改数据库、releaseNotes 或学习宝业务文件。
- 未安装 Claude Code，未安装 Pencil CLI，未安装全局 npm 包。
- 未关闭 Defender，未绕过 SmartScreen，未增加未知网络代理或启动项。
- 测试 .pen 文件和截图未创建，项目仓库未产生工具测试产物。

## 结论与风险

- 本次验证状态：blocked。
- 根因证据：安装器自身 NSIS 完整性校验失败；虽然 SHA256 与用户指定值一致，但这不能证明安装器可运行。
- 根因尚未能区分为官方安装包自身问题或下载/传输链路问题；第二次官方重下载未在本轮完成，不能据此宣称已修复。
- Pencil MCP、Codex 读写能力和重新打开持久化均未验证；不得交给 Ferra 开始正式设计。

## 回滚方法

1. 不运行当前失败安装包；保留安装失败证据。
2. 如未来发生配置异常，退出 Pencil 后恢复 `C:\Users\zephy\.codex\backups\config-before-pencil-install-20260712.toml`。
3. 如已安装 Pencil，使用 Windows 设置卸载或官方卸载流程，并移除 Pencil MCP 配置。
4. 删除 `D:\Devtools\Pencil`、安装包或测试证据前必须由用户确认。

- 实际修改的项目文件：docs/ops/INDEX.md，以及本归档留档。
- Commit：0fb193c，`docs: record blocked Pencil MCP validation`。
- Push：已成功推送至 `origin/codex/phase4-differentiation`。
