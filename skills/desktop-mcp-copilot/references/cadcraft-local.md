# CADCraft 参考实现

这份公开 skill 不附带作者机器的配置。参考源码是本仓库的 `patches/cadcraft-v0.7.0-copilot.patch`，固定上游提交及构建方法见根目录 README 和 docs/INSTALL.md。

默认新安装前缀为 `~/.local/share/artcraft-ai-copilot`：

- GUI：`launchers/artcraft-cadcraft`。
- MCP stdio：`launchers/artcraft-cadcraft-mcp`；内部调用 cadcraft-cli mcp --connect 127.0.0.1:7981。
- 本机生成的插件：`plugin/`，其中 `.mcp.json` 使用正确绝对路径。
- 版本维护：`launchers/artcraft-cadcraft-update`。
- 可选 FreeCAD 桥接：`backend/backend`，通过环境变量配置 FreeCAD 根目录和实体输出目录。

这些是默认路径，不代表另一台电脑已安装或对应客户端已加载。使用真实前缀，检查活动窗口与端口。首次启动后用 skill 的 probe_mcp.py 只读握手，再用客户端只读工具核对标题、路径、活动状态和实体数量。

原始控制通道用换行分隔 JSON，例如 `{"id":1,"method":"drawing.inspect","params":{"entities":false}}`；不是 HTTP MCP 地址。MCP 包装必须保留 `--connect`，省略它可能进入另一张独立后台图纸。

外部 inspect 摘要未必暴露稳定文档 UID；可交叉核对必要文档元数据，但不要把标签索引当稳定身份。内嵌侧栏状态池使用内部 UID。`ui.copilot.status` 含聊天，不能为了获取 UID 就公开保存完整返回。

内嵌命令包括 ui.copilot.connect/status/new/switch/send/cancel/configure/models.refresh，以及 ui.toggle.copilot。new 新增而不删除旧会话；switch 的 index 从 0 开始。发送可能修改图纸，普通诊断不应调用它。模型与思考强度以真实目录为准。

源码导航：copilot.rs 处理服务和侧栏，copilot_documents.rs 管理文档/会话，menus.rs 提供命令入口，lib.rs 同步状态与持久化，main.rs 设置独立应用身份。补丁保留上游停靠布局和配置，测试覆盖多会话、文档隔离和控件点击。

可选 create_solid 是侧栏动态工具，不代表外部 MCP 自动具备同名工具。独立 FreeCAD 后端支持 bearing/box/cylinder/sphere；模型在 FreeCAD 打开，CADCraft 画布仍是二维平面视图。验证有效实体和 STEP 回读，不能用线框冒充实体。

维护前阅读目标源码的 AGENTS.md。不要使用旧 PID 或直接退出用户窗口；先保存/备份未保存工作。更新脚本遇冲突、检查失败或运行中的窗口会停止，不自动覆盖旧版本。完整设计和边界见本仓库 docs/ARCHITECTURE.md、docs/UPDATING.md 与 docs/VALIDATION.md。
