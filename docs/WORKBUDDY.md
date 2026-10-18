# 在 WorkBuddy 中使用本项目

本项目现提供 WorkBuddy 的接入流程与本地 stdio 材料包生成方式。核对的是 2026-10-18 的官方文档，尚未在 WorkBuddy 客户端执行端到端验收。不会自动安装 WorkBuddy，也不要求先装 Codex。

把下面提示词中的 `【软件名】` 换成你要连接的软件，发给能操作这台电脑的 WorkBuddy：

```text
请读取 https://github.com/Zhang-hao-bin/artcraft-ai-copilot 中 skills/desktop-mcp-copilot/SKILL.md 和 references/workbuddy.md（相对该 skill 目录），为我这台电脑上的【软件名】建立真实 MCP 连接并封装成 WorkBuddy 可用的接入材料。自行发现 OS、软件窗口、接口、依赖及 WorkBuddy 版本；保留已有连接器、技能和未保存工作。按当前自定义连接器和上传技能流程加载，在新测试文档做最小修改并回读、验证撤销及保存。生成材料、协议握手、WorkBuddy 加载和真实操作分别报告；没有完成的不要标成成功。若当前无法操作客户端界面，先交付材料与准确加载步骤，并明确待验收项。本次不默认开发软件内聊天侧栏。
```

如果不能直接读取 GitHub，先下载完整仓库到本机，再让 WorkBuddy 读取对应本地文件。也可以先在技能页面上传完整 `desktop-mcp-copilot` 目录/包，确认已启用后用自然语言调用；导入形式按你安装版本支持的格式操作。

完整流程和故障定位集中在 [WorkBuddy skill 参考](../skills/desktop-mcp-copilot/references/workbuddy.md)，包括：

- 让 WorkBuddy 读取或导入制作 skill。
- 发现/开发目标软件 MCP，编写软件操作 skill。
- 使用 `package_agent.py --client workbuddy` 生成 MCP 配置、操作 skill ZIP 与使用说明。
- 在 WorkBuddy 自定义连接器中注册、在任务中启用并验证目标文档。
- 备份/回退、跨机器差异、开放平台发布及内嵌运行时边界。

本地接入包不会自动成为 WorkBuddy 市场连接器，也不代表已给软件安装内嵌助手。格式依据：[WorkBuddy 官方连接器文档](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Connector)、[官方技能文档](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)、[开放平台连接器规范](https://open.workbuddy.cn/docs/connector)。
