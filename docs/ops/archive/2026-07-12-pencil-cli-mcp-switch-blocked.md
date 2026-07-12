# Pencil MCP CLI/无界面文件模式切换验证（blocked）

- 执行时间：2026-07-13
- 执行窗口：Codex
- 任务目标：将 Pencil MCP 从 Desktop 通信模式切换为 CLI/无界面文件模式，并验证 CLI 写入、Desktop 只读查看的两次往返。
- 允许修改的项目文件：`docs/ops/INDEX.md` 与本归档记录。
- 实际修改的项目文件：`docs/ops/INDEX.md`、本归档记录。

## 环境与配置基线

- Pencil 版本：`1.1.69`。
- Desktop：`D:\Software\pencil\Pencil.exe`。
- MCP Server：`D:\Software\pencil\resources\app.asar.unpacked\out\mcp-server-windows-x64.exe`。
- 修改前 MCP 参数：`--app desktop --agent codexCLI`。
- `config.toml` SHA256：`EB3AB4B8362D8F16879D654ADCB76A2DCC73F897A52DC9416A6D815468E036EE`。
- 备份：`C:\Users\zephy\.codex\backups\config-before-pencil-cli-switch-20260712.toml`；备份 SHA256 与原配置一致。
- MCP 节点数：`1`；`[mcp_servers.pencil]` 节点数：`1`；未发现重复 Pencil 配置。
- 脱敏 Pencil 配置：

```toml
[mcp_servers.pencil]
command = "D:\\Software\\pencil\\resources\\app.asar.unpacked\\out\\mcp-server-windows-x64.exe"
args = [ "--app", "desktop", "--agent", "codexCLI" ]
```

## 本地帮助与停止原因

- `--help`：退出码 `0`，无输出。
- `-h`：退出码 `0`，无输出。
- `--version`：退出码 `2`，提示 `flag provided but not defined: -version`，并输出以下完整帮助（无敏感信息）：

```text
Usage of D:\Software\pencil\resources\app.asar.unpacked\out\mcp-server-windows-x64.exe:
  -agent string
        Optional name of agent connecting to Pencil
  -app string
        Pencil app to connect to
  -conversation_id string
        Optional conversation id to identify the MCP tool calls to
  -enable_spawn_agents
        Optional flag to enable spawn_agents tool
```

- 帮助没有列出 `--app` 的可用值，未明确支持 `cli`、headless、file 模式、`.pen` 文件路径或 workspace/project/file/server 参数，也没有说明 `--agent codexCLI` 在此类模式中的适用性。
- 按硬性停止条件，未将 `desktop` 猜改为 `cli`；`config.toml` 未修改，因此不需要恢复备份。Desktop、Codex 均未为本任务重启。

## 未执行项与验证结果

- 未创建 `D:\Devtools\Pencil\Tests\CLI\Pencil-CLI-Desktop-Roundtrip.pen`，未产生截图或其他测试产物。
- 未执行 CLI MCP 连接、创建、读取、修改、保存、`snapshot_layout`、`get_screenshot`、任务管理器 Desktop 进程检查或两次 CLI 与 Desktop 往返；这些步骤必须以已验证的 CLI 参数为前提。
- 未启动 Pencil Desktop；因此不存在 CLI 自动拉起 Desktop 的风险证据，也不能宣称独立 CLI 模式可用。
- `git diff -- frontend backend`：待归档前复核；本任务未修改 frontend/backend。

- Commit：待定。
- Push：待定。
- 遗留风险：Pencil MCP Server 1.1.69 的本地帮助不足以验证 CLI/无界面文件模式。正式 Ferra 设计任务不得切换到该工作流，应继续使用已验证的 Desktop MCP 流程，或取得官方明确的 CLI/headless/file 参数后再验证。
- 下一步：如需继续，先取得与当前 1.1.69 二进制对应的官方参数说明；不得从猜测的 `--app cli` 开始。
