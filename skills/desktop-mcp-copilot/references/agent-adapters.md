# Agent、客户端与聊天运行时适配

## 先分清三个角色

- 制作 agent：本次读取 skill、执行命令、编写桥接/插件的人机助手，可以是 Cursor、Claude Code、Codex、WorkBuddy 或其他具备这些能力的工具。
- MCP 客户端：实际发现工具并调用软件的客户端。与制作 agent 不必相同。
- 软件内聊天运行时：侧栏发送请求、接收流式回复和工具调用的后端。MCP 标准不定义模型聊天、模型列表或会话恢复接口。

制作时先读取客户端本机版本/帮助，查询对应官方文档。以下为已核对的客户端入口（Cursor/Claude Code 于 2026-10-17，WorkBuddy 于 2026-10-18），不代表所有版本均通过实际加载测试：

| 客户端 | 制作 skill 的发现位置 | 软件 MCP 项目配置 | 接入方式与验证 |
|---|---|---|---|
| Cursor | `.cursor/skills/desktop-mcp-copilot/`（完整目录） | `.cursor/mcp.json` 的 `mcpServers` | 用客户端当前 MCP 页面确认工具，然后读目标文档；技能可通过自然语言或当前版本技能入口使用 |
| Claude Code | `.claude/skills/desktop-mcp-copilot/`（完整目录） | 项目根 `.mcp.json` 的 `mcpServers` | 核对 `claude mcp --help`，通过 `/mcp` 查看连接；原生技能入口通常为 `/desktop-mcp-copilot` |
| Codex | 当前安装支持的 skill 目录；可使用已安装的 `$desktop-mcp-copilot` | 当前版本的 MCP 注册命令/配置，或 Codex 原生插件 | 依照本机帮助与已验证 Codex 参考；不能把 `.mcp.json` 项目文件当其通用全局配置 |
| WorkBuddy | 上传完整本地技能包或显式读取 SKILL.md | 自定义连接器中的 MCP 配置；不假设项目自动发现 | 按 [WorkBuddy 流程](workbuddy.md) 注册并在任务中启用，实际文档操作仍需客户端验收 |
| 其他 agent | 查客户端技能机制；没有就显式读 SKILL.md | 按其 MCP 配置规范转译 | 若无 MCP，可开发官方工具 SDK 适配；不能只改文件名就宣称兼容 |

Cursor 的 `${env:NAME}` 和 Claude Code 的 `${NAME}` 语法不同，认证信息与路径不要跨客户端原样复制。HTTP/SSE 的 type、URL、header、OAuth 必须按客户端版本核对；生成器只处理无额外字段的 stdio 配置。工作区信任、工具授权由原客户端处理，不关闭审批机制。

来源：[Cursor MCP](https://cursor.com/docs/mcp)、[Cursor Skills](https://cursor.com/docs/skills)、[Claude Code MCP](https://code.claude.com/docs/en/mcp)、[Claude Code Skills](https://code.claude.com/docs/en/skills)。这些来源用于格式核对；真实加载需要在目标版本另验。

## 生成客户端项目包

相对 skill 根目录运行；准备好的 `verified-mcp.json` 是 `{"mcpServers":{"软件名":{"command":"实际可执行文件","args":["实际参数"]}}}`。实际 command/args 必须先发现和验证，不能运行这里的占位文字。`--skill-file` 是依据真实工具编写的单文件软件操作说明，不是制作 skill。

```bash
python3 scripts/package_agent.py --client cursor --name target-app \
  --mcp-config /absolute/path/to/verified-mcp.json \
  --skill-file /absolute/path/to/operation/SKILL.md \
  --output /absolute/path/to/new-bundle
```

`--client claude-code` 生成 Claude Code 项目包，`--client workbuddy` 生成自定义连接器接入参数、操作 skill ZIP 与加载说明（不是自动注册的项目配置或市场包）；`--client generic` 生成中性转译材料。后者的 `mcp-stdio.json` 不是未知客户端自动识别的配置。Codex 原生插件使用 `package_plugin.py`。多文件操作 skill 应审阅资源后完整复制，不用该单文件打包器。

只将生成目录内本次目标 server 的条目合并到实际工作区；已有配置有同名 server 时比较/备份后决定复用或替换，不整文件覆盖，不安装到本仓库当作用户软件工作区。软件操作 skill 同样保持其他技能。包内 INSTALL.md 记录加载、目标验证与卸载步骤。输出目录是草稿交付，不自动注册、不执行 server。含额外配置字段时生成器会拒绝，而非悄悄丢弃认证、权限或工作目录设置。

## 软件内运行时适配

用户没指定运行时就复用已安装、已授权且提供可调用接口的选项；只有不同选择影响费用或能力时询问。开发统一边界，按实际实现返回能力：

```text
capabilities() -> stream, images, tools, cancellation, resume, modelOptions
startSession(documentUID, conversationID) -> runtimeSessionID
send(userText, documentSnapshot, view?, settings) -> event stream
handleTool(callID, validatedArgs, ownership) -> structured result
cancel(turnID), closeSession()
```

这是本项目设计契约，不是可直接调用的某家 API。实现时映射该运行时的正式协议/SDK，不发明通用 `thread/start`。无模型列表或思考强度就隐藏控件或显示“不支持”；无图片输入则只提供结构化文档；无恢复则重建会话并附有界历史。如无可靠取消机制，至少拒绝迟到工具写入，不谎报已停止服务端计算。

- **Codex**：参考已实现的 app-server 分支及相应 schema。
- **Claude Code**：可评估官方 Agent SDK 或程序化 CLI；先核对本机帮助、SDK 事件、权限交互、工具调用及会话行为，再实现适配器。本仓库尚未实现 Claude 侧栏后端。[程序化接口](https://code.claude.com/docs/en/headless) 支持结构化/流式输出；不能把其事件当作 Codex app-server 响应。
- **Cursor**：可先作为外部 MCP 客户端。内嵌聊天需再确认目标版本是否提供合适的 CLI/SDK、非交互模式和工具接口，不能尝试操控编辑器聊天窗口冒充服务端。不可用时保留外部 MCP 接入，报告内嵌运行时尚缺，不偷偷换用户指定的运行时。
- **WorkBuddy**：按 [独立接入流程](workbuddy.md) 作为制作 agent 或外部 MCP 客户端；本仓库未实现其软件内聊天后端，需先确认正式运行时接口。
- **其他运行时**：按已确认 SDK 实现工具循环。模型 API key 只用于已授权服务，不从账号配置导出；有 MCP 支持不代表可嵌入该 agent。

所有后端都在工具真正执行前检查 `(documentUID, conversationID, generation, turnID)`、取消和参数，沿用用户权限。外部 MCP 若缺稳定 UID 则先补可验证身份能力或限制写入范围，不以标题/标签索引冒充稳定身份。
