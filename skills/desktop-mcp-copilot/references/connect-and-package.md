# 连接与插件封装

## 发现接口

优先顺序：软件已有 MCP → 官方 API/扩展 SDK → 已有命令行或控制通道 → 有源码时添加窄接口。仅有鼠标/键盘自动化时明确精度和可用性限制，不把它描述成原生对象级接口。

确认软件版本、操作系统、可执行文件、用户实际窗口与文档、控制通道类型、是否只支持离线文件。尚无工具连接时可先用本机进程/监听端口核对实例，再握手并用只读工具交叉核对当前文档；无可用 UI/进程元数据时如实标明尚未确认目标窗口。使用 `command -v`、本机帮助、源码中的协议定义及官方文档，勿凭相似软件猜工具名。创建和重启只限于本次授权的软件，复用已有合适窗口。

软件端最小可用能力建议包括：列出文档、读取活动文档/稳定 UID/未保存状态、读对象、获取视图、列命令、执行结构化命令、取消、保存。能力名依目标软件定义。修改操作在 UI/应用线程执行；网络读取和模型流式事件在后台，通过消息队列交接。

## MCP 运输与客户端配置

stdio server 的 stdout 只能包含协议消息，诊断写 stderr。不要在协议 stdout 混入欢迎信息、进度或编译日志。MCP 接口不应直接执行任意来自文档的 shell 字符串。

Codex CLI 当前示例（执行前核对本机 `codex mcp add --help`）：

```bash
codex mcp add cadcraft -- /usr/bin/cadcraft-cli mcp --connect 127.0.0.1:7981
codex mcp list
codex mcp get cadcraft
```

上面是 CADCraft 的实例，不要盲目用于其他软件。HTTP MCP 使用经过确认的 Streamable HTTP 地址：

```bash
codex mcp add target-app --url https://your-mcp-service.example/mcp
```

HTTP 示例域名必须替换，不可直接执行。若需要认证，使用当前客户端支持的环境变量引用或 OAuth。其他 agent 按其客户端的 MCP 配置格式注册相同 server，不默认支持 Codex 插件格式。接收方客户端名称/版本未明确时，只能交付可适配配置，不宣称已在接收方加载成功。普通连接配置会公开 server 的写工具；只读任务须遵守调用边界，并在客户端支持时设置已核对的只读工具 allowlist。不能用臆造的 readOnly 配置字段宣称已强制隔离。

修改现有配置时只改目标条目，保留其他 server、登录和模型设置。记录旧条目用于回退。同一 server 同时从全局配置和插件加载会造成重复工具；验证插件后，只停用已确认重复的目标条目，不能全量清除 MCP 配置。

## 握手诊断

随包脚本只执行 MCP `initialize`、`notifications/initialized`、分页 `tools/list`，不调用工具、不写文档。Python 3 标准库即可使用。stdio 模式不适用于 HTTP MCP 或原始控制端口。

```bash
python3 scripts/probe_mcp.py --timeout 10 -- /usr/bin/cadcraft-cli mcp --connect 127.0.0.1:7981
```

命令相对技能根目录运行。脚本会启动并结束它自己的 MCP 子进程，目标程序自身可能有启动副作用，执行前检查命令来源。成功仅证明 MCP 握手及工具目录；还需用真实客户端的 inspect 工具核对目标窗口。脚本不输出完整 schema/serverInfo，并丢弃子进程 stderr，避免把私密日志写入交接；失败时若确需 stderr，单独在本机检查并脱敏，不把空白外层 stderr 当作服务器没有错误。HTTP 模式使用客户端已有诊断或官方 MCP SDK，不用 `curl` 收到 HTTP 200 代替协议验证。

按层定位失败：软件未运行/端口不符 → 软件原始 API 不通 → MCP 包装失败/stdout 污染 → 客户端未加载 → 认证/模型网络失败。不要因为模型无法连接就重装桌面软件。

## 打包插件

插件包装 MCP 配置和软件操作 skill；它不包含软件二进制，也不自动提供软件内 UI。

CADCraft 已验证的本地 Codex 包结构：

```text
plugin-root/
├── .codex-plugin/plugin.json
├── .mcp.json
└── skills/plugin-name/SKILL.md
```

随包生成器接受既有 `.mcp.json` 和**已完成的单文件软件操作 skill**，生成一个新目录；不覆盖现有目录，不安装，不写客户端设置：

```bash
python3 scripts/package_plugin.py \
  --name target-app --display-name '目标软件助手' \
  --description '读取和操作目标软件的当前文档' \
  --mcp-config /absolute/path/to/verified-mcp.json \
  --skill-file /absolute/path/to/operation/SKILL.md \
  --output /absolute/path/to/new-plugin-directory
```

生成器仅打包不依赖其他资源的单文件操作 skill；有 references/scripts/assets 时会拒绝，需审阅后手工复制完整技能资源。配置分发前检查是否含凭证。生成器针对本次实践的本地 Codex 格式；客户端升级后对照官方插件文档验证字段。跨机器分发不能保留另一台电脑的可执行文件绝对路径，要安装依赖并生成适配目标机器的配置。仅面向本机的包可使用本机绝对路径并明确依赖。

操作 skill 应说明如何检查当前文档、参数与单位、修改范围、结果验证和保存；不要把“制作集成”的本 skill 当作该软件的操作说明。若无已完成操作 skill，先根据真实工具目录编写再打包。

通过当前客户端支持的本地插件/marketplace 安装流程导入，保留已有 marketplace 内容。CADCraft 本机案例使用 `artcraft-local`；其他环境使用自己的名称及正确路径基准。不要直接写生成的插件缓存。CLI 支持的安装子命令以 `codex --help` / 对应子命令帮助为准，不编造通用 `plugin install` 命令。

安装后重新枚举工具、核对窗口，再做一次测试文件中的真实操作。只有配置写入或插件卡片出现时报告“已配置/已打包”，不能报告“已操作成功”。客户端只在启动时读取技能/工具目录的情况下，重开会话或刷新相应客户端。

协议和安装入口参考：[Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)、[Codex 插件](https://learn.chatgpt.com/docs/plugins)。本节的包结构和操作注意事项主要来自本机工作配置。
