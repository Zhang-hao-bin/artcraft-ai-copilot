# CADCraft AI Copilot 插件模板

这个目录包含 Codex 插件元数据、MCP 配置和 CAD 操作 skill。它不包含应用二进制、账号或自动安装脚本。

仓库模板使用 PATH 中的 `artcraft-cadcraft-mcp`。`scripts/install_local.py` 会生成本机绝对路径配置和完整插件目录，再按当前 Codex 的本地插件流程导入。默认示例 marketplace 为 `artcraft-local`。

注册后先初始化并列工具，再以只读接口确认当前窗口。不要重复注册同一个 server。单独安装此模板不会给其他软件增加侧栏，也不会提供强制只读模式。
