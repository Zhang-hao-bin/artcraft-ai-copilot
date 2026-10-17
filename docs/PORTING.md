# 迁移到其他软件

先确定交付层级：只连接 MCP、封装插件，还是改造软件 UI。已有 MCP 就先握手并读取当前文档；只有原始 API/命令行时增加包装层；需要内嵌侧栏时还必须有源码或可用的 UI 扩展 SDK。

记录目标软件版本、OS、窗口/文档身份、未保存状态、接口运输、单位、命令 schema、撤销/保存及线程模型。图像软件验证图层和像素，办公软件验证段落/单元格，CAD 验证对象几何。截图不能替代对象级的精确结果。

以新测试文件验证一个简单动作，再增加侧栏：启动/重试、中文输入、模型与强度、当前视图采样、流式消息、停止、收起后重开。最后做文档 UID 隔离、同文件多会话、草稿/输出保留、路径持久化和过期请求守卫。

后续项目可进一步使用 `(documentUID, conversationId, generation, turnId)` 完整守卫，并为外部 agent 增加不含聊天的文档身份只读工具。普通连接配置不提供强制只读隔离；若需要 server 级只读，必须实现独立的只读工具表或代理并测试。

将完整 `skills/desktop-mcp-copilot` 目录交给执行 agent，或让它按仓库根 [PROMPTS.md](../PROMPTS.md) 的提示词自行取得和读取 skill。Cursor、Claude Code、Codex 等使用相同实施流程，但分别生成自己的配置/插件格式，见 [客户端适配](../skills/desktop-mcp-copilot/references/agent-adapters.md)。

制作 agent 不必等于接收客户端或侧栏后端。外部 agent 走 MCP；内嵌侧栏需单独映射运行时的会话、流式消息、工具调用和取消协议，不能要求 Cursor/Claude Code 接收 Codex app-server 消息。配置生成、客户端加载及真实文档操作分别验收。

无源码和面板接口时可交付外部连接或独立伴随面板，不能把覆盖窗口称作原生内嵌。ArtCraft 主程序、PhotoCraft、VectorCraft 等需要分别实现和验证；本仓库没有宣称已完成这些适配。
