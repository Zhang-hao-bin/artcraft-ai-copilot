# 复制给你的 agent

将下面的提示词发给**运行在你自己电脑上、能读取文件并执行命令**的 Cursor、Claude Code、Codex、WorkBuddy 或其他开发 agent。先替换 `【软件名】`；如果安装了多个版本，可补版本或安装路径。无需先配置 MCP，也不必先安装本 skill：首次提示词会让 agent 取得仓库并读取入口。

这是一份让 agent 按本机条件实施的流程。软件需要可用的 MCP、API、SDK、CLI 或可修改源码；没有接口时 agent 应说明缺口并选择可实现方式。有 MCP 不等于能嵌入聊天侧栏；不支持原生 skill 的 agent 也可以显式读文件执行。网页聊天或云端 agent 如果无法访问你的电脑，需要改用本机 agent，或在你授权的远程环境中工作。

## 一句话：连接并自行封装

```text
请读取 https://github.com/Zhang-hao-bin/artcraft-ai-copilot 中 skills/desktop-mcp-copilot/SKILL.md 及必要参考，为我这台电脑上的【软件名】建立 MCP 连接，并封装成当前 agent 可用的连接包和操作 skill；自行发现环境，保留已有配置及未保存工作，在新测试文档中回读验证后交付安装与回退说明。
```

## 首次使用：完整执行提示词

适合尚未下载仓库、未安装 skill 的使用者；把软件名替换后整段发送。

```text
请在我自己的电脑上，为【软件名】建立能被你调用的真实软件连接，并自行封装交付。

请使用 https://github.com/Zhang-hao-bin/artcraft-ai-copilot 的 desktop-mcp-copilot skill：如果本地已有仓库先检查版本与未提交修改，否则克隆到新的工作目录；读取 skills/desktop-mcp-copilot/SKILL.md，按其中路由读取必要参考和工具，不只阅读 README。若不能直接读 GitHub，用你已有的下载/Git 能力取得完整目录。不支持原生 skills 时直接读取上述文件执行即可。

先发现本机 OS、目标软件版本和路径、当前窗口/未保存文档、你实际运行的位置、客户端名称/版本及已有配置。优先使用已有 MCP；否则用软件正式 API/SDK/CLI 建立 MCP 桥接；有源码时按项目规范增加必要的窄接口。不要照搬仓库示例里的路径、端口或 Linux 命令到我的电脑。

本次目标是连接加封装，不默认改造软件 UI。按当前客户端真实支持的格式生成 MCP 配置增量、软件操作 skill，支持原生插件时可打包插件。保留其他 server、登录和模型设置，不关闭审批。先做 MCP 初始化/工具枚举，再只读核对当前目标窗口和文档；在一个新测试文档中完成最小可量化修改、回读、撤销及保存验证，不覆盖个人工作。不能确认目标身份时先补确认能力，不盲目写入。

交付可在这台电脑上使用的产物、依赖/启动说明、配置位置、加载或重开步骤、回退/卸载说明，以及逐项验证结果。模板生成、握手、客户端加载、当前文档确认、测试写入回读分别报告；未验证的不要标成成功。必要信息先自行发现，只有无法发现且阻碍工作时才问我。不要只给计划，持续完成当前已授权的可实施工作。
```

## 已安装 skill：一句话调用

| Agent | 使用方式 |
|---|---|
| Cursor | 将完整目录放入项目 `.cursor/skills/desktop-mcp-copilot/`，再用下方自然语言；是否自动发现按你的版本确认 |
| Claude Code | 完整目录放入项目 `.claude/skills/desktop-mcp-copilot/`；可用 `/desktop-mcp-copilot` 加需求，或下方自然语言 |
| Codex | 使用当前安装支持的技能入口，例如 `$desktop-mcp-copilot` 加需求 |
| WorkBuddy | 在技能页面上传完整本地技能包并确认启用，或直接读取入口；见 [WorkBuddy 流程](docs/WORKBUDDY.md)，不假设 `$skill` / `/skill` 语法 |
| 其他 agent | 按当前客户端的技能机制安装；没有则显式提供本地 `SKILL.md` 路径，不要求它理解 `$skill` 或 `/skill` |

```text
使用 desktop-mcp-copilot skill，为本机【软件名】发现并建立真实 MCP 接口，按当前客户端格式自行封装和加载；保留现有配置，在新测试文档验证后交付产物、使用方法和验证结果。
```

项目技能路径依据 [Cursor Skills](https://cursor.com/docs/skills) 与 [Claude Code Skills](https://code.claude.com/docs/en/skills)（2026-10-17 核对）；加载行为仍需在实际版本验证。

## 只连接，不改软件

```text
请按 https://github.com/Zhang-hao-bin/artcraft-ai-copilot 的 skills/desktop-mcp-copilot/SKILL.md，连接我电脑上已经运行的【软件名】，只完成现有接口发现、MCP 桥接与当前客户端注册。保留当前窗口和文档，先只读核对目标文档。本次不开发侧栏、不修改软件源码、不做文档写入；交付准确的连接状态和后续使用方式。
```

## 完整软件内 Copilot：连接 + 封装 + 侧栏

```text
请按 https://github.com/Zhang-hao-bin/artcraft-ai-copilot 的 skills/desktop-mcp-copilot/SKILL.md，在本机【软件名】中实现完整 Copilot 助手：发现/实现 MCP、生成当前客户端可用的连接包与操作 skill，并用软件官方扩展面板或可修改源码开发聊天侧栏。

制作 agent、MCP 客户端与侧栏运行时分开适配；优先复用本机已授权且有可靠程序接口的运行时，别把 Codex 协议直接发给 Claude Code/Cursor。支持读取当前文档和可选视图、真实工具修改、流式回复、停止、启动/重试、中文输入、收起后重开；模型/思考强度只展示后端实际支持项。

新文件新会话，同文件新对话保留旧记录；消息、草稿、设置和产物按稳定文档与会话身份隔离。切换或取消后拒绝迟到工具写入；持久化有界历史，重开可恢复记录。保留我的未保存工作、原安装和已有设置，在隔离的新测试文件验收。无源码或面板能力时完成可用的外部连接，说明内嵌缺口与可行的伴随面板方案，不伪造“原生侧栏已完成”。目标信息充分就实施，最后给出实际产物、运行方式、回退和已验证范围。
```

## 让一个 agent 给另一个客户端打包

```text
请按 https://github.com/Zhang-hao-bin/artcraft-ai-copilot 的 desktop-mcp-copilot skill，为本机【软件名】建立 MCP；本次由你完成实现，但接收客户端是【Cursor / Claude Code / Codex / WorkBuddy / 其他名称，选择一个】。核对该客户端的版本、项目/用户配置范围及重载方式，生成它支持的配置和操作 skill/插件，不沿用你的客户端格式。用接收客户端实际加载并验证目标文档；如果当前无法操作该客户端，交付可执行材料并明确“等待客户端验收”，不要把配置生成称作连接成功。
```

## WorkBuddy：在自己的电脑上连接软件

```text
请读取 https://github.com/Zhang-hao-bin/artcraft-ai-copilot 的 skills/desktop-mcp-copilot/SKILL.md，并读取该 skill 下 references/workbuddy.md，为本机【软件名】建立 MCP 连接并自行封装 WorkBuddy 接入材料。先发现软件、版本、窗口、依赖及 WorkBuddy 运行位置；按当前自定义连接器和技能上传方式注册，保留已有配置和未保存工作，在新测试文档回读验证。只生成配置或无法操作 WorkBuddy UI 时，明确待客户端验收，不声称已连接；本次不默认增加软件内侧栏。
```

安装、打包、验证及回退见 [WorkBuddy 指南](docs/WORKBUDDY.md)。WorkBuddy 也可以为其他客户端制作连接包，接收客户端需另外指定；制作 agent 与侧栏运行时仍分开适配。

## 在另一台电脑复现

```text
请读取 https://github.com/Zhang-hao-bin/artcraft-ai-copilot 的 desktop-mcp-copilot skill，在这台电脑为【软件名】重新发现环境并完成接入。我提供的旧连接包仅作参考；请重新确认 OS、依赖、可执行文件、端口、当前窗口、客户端及运行位置，不照搬旧机器绝对路径或凭据。保留原配置，生成本机可用产物并做新的握手、目标文档和测试文档验证。
```

连接配置、操作 skill 和软件侧栏是不同交付。已有 CADCraft v0.7.0 参考实现见 [安装文档](docs/INSTALL.md)；其他软件按 skill 适配，并非下载本仓库就已全部接入。具体客户端格式与目前验收边界见 [agent 适配](skills/desktop-mcp-copilot/references/agent-adapters.md) 和 [验证记录](docs/VALIDATION.md)。
