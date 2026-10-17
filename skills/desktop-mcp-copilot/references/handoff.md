# 给其他 agent 的交接

保留并提供整个 `desktop-mcp-copilot/` 目录，包含 SKILL.md、references、scripts 和 agents。仅发入口会丢失依赖参考。Codex 可安装到 `${CODEX_HOME:-$HOME/.codex}/skills/desktop-mcp-copilot`；已有版本先比较，不盲目覆盖。其他 agent 可直接读取 SKILL.md 并按路由查阅；MCP 按该客户端实际格式注册。

## 连接已有 CADCraft

> 请使用 $desktop-mcp-copilot，连接这台电脑上已经运行的 CADCraft Copilot 窗口。读取 skill 入口和 references/cadcraft-local.md，发现实际安装前缀、端口与当前文档，再经 MCP stdio 包装连接。保留 --connect，不重复加载同一 server，不关闭已有窗口。先只读验证，写操作仅按我另行说明的任务执行。普通连接 JSON 不强制只读，有对应能力时设置已核对的工具 allowlist。

不支持技能语法时换成“请读取我提供目录里的 SKILL.md”。机器/容器中的 127.0.0.1 只指它自身；跨主机连接需要已授权、经过认证的桥接，不能把无认证原始控制端口开放到公网。

## 迁移到其他软件

> 请使用 $desktop-mcp-copilot，为我指定的软件建立集成。先发现它实际的 MCP/API/SDK 和 UI 扩展能力，按我要求完成只连接、插件封装或完整 Copilot 侧栏。完整侧栏应支持中文输入、文档与视图读取、模型/思考强度、启动/重开、各文件独立和同文件多会话，新对话保留旧记录。保留未保存工作，在新测试文件验证修改；不能内嵌时说明限制，不伪造连接或能力。

附软件名称、版本、OS、源码/SDK 地址和一个可验证动作。不要发送密码、账号导出或 API key；技能和插件不会授予账号访问权。
