# 安装并验证本地 Figma MCP

- 执行时间：2026-07-10
- 执行窗口：GPT-5.6 Luna
- 任务目标：安装 figma-mcp-go 本地插件桥接，绕开官方 Starter MCP 读取次数限制，并在空白 Figma 文件验证读写。
- 允许修改的项目文件：本操作留档与 docs/ops/INDEX.md。
- 实际修改的项目文件：docs/ops/INDEX.md、docs/ops/archive/2026-07-10-figma-local-mcp-install.md。
- 工具安装目录：D:\Devtools\figma-mcp-go
- 验证命令与结果：Node v24.16.0、npm 11.13.0、Git 2.54.0.windows.1；Figma Desktop 已安装并运行，已创建 C:\Users\zephy\Desktop\Figma.lnk。固定 tag 克隆失败：GitHub 返回“Repository unavailable due to DMCA takedown”，HTTP 403。
- Commit：待提交阻断留档。
- Push：待提交阻断留档。
- 遗留风险：第三方仓库当前不可访问，无法验证源码、许可证、manifest、npm 元数据或进行本地安装；未执行 npm 安装、Codex MCP 配置及 Figma 插件读写测试。
- 下一步：等待用户提供经核实且合法可用的官方仓库恢复路径；不得改用 main、镜像或 latest。
