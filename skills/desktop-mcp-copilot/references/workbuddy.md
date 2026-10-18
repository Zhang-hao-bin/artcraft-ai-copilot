# WorkBuddy 接入流程

本节针对腾讯 **WorkBuddy**（不是 CodeBuddy IDE，也不是软件内聊天运行时）。适用于让 WorkBuddy 自己按本 skill 建立集成，或让其他 agent 为 WorkBuddy 制作连接材料。官方文档核对日期：2026-10-18；本仓库没有执行 WorkBuddy 客户端端到端验收。

## 1. 确认本机与目标

记录 WorkBuddy 的实际版本、OS、运行位置、目标软件版本/窗口、现有连接器与技能。使用 WorkBuddy 已授权的本机文件/命令能力读取完整 skill 目录；如果当前任务在云端/容器执行，localhost 不指用户电脑，不能用本机示例端口冒充已连通。

将制作流程 skill 和软件操作 skill 分开：前者是本目录 `desktop-mcp-copilot`，用于创建集成；后者按发现的真实 MCP 工具编写，用于日常操作目标软件。安装制作 skill 不会自动注册 MCP，也不会让目标软件出现内嵌侧栏。

## 2. 把制作 skill 交给 WorkBuddy

优先让 WorkBuddy 直接读取已下载仓库中的 `skills/desktop-mcp-copilot/SKILL.md`，继续读取必要相对参考。无需先猜 WorkBuddy 的全局配置路径。需要在技能列表里使用时，按官方 [技能说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)，进入技能页面的添加技能、上传技能，导入完整目录或该版本接受的本地技能包，并检查已安装/启用状态。

打包完整制作 skill 时保留 `SKILL.md`、`references/`、`scripts/`、`agents/` 及存在的 `assets/`；不要只上传入口，也不要把整个仓库 ZIP 当技能包。ZIP 可以以 skill 目录内容作为根，导入格式以当前客户端实际解析结果为准。若解析拒绝，记录错误并按当前官方要求修正，或回到显式读文件流程，不把“文件存在”标成“客户端已加载”。

官方开放平台的 [Skill 格式](https://open.workbuddy.cn/en/docs/skill) 另有发布用的语言描述、版本等字段要求。需要发布时再按规范补齐，不把上传本地技能与完成市场发布混为一谈。未验证 WorkBuddy 通用 `/skill` 或 `$skill` 语法，使用下面的自然语言提示即可。

## 3. 准备真实 MCP 与操作说明

按 [连接与封装](connect-and-package.md) 发现软件已有 MCP，或用正式 API/SDK/CLI 建立桥接。区分原始软件控制协议与 MCP。stdio 启动命令和每个参数必须来自接收者电脑，先做握手/工具目录检查，再核对软件当前窗口及文档。

工作目录、解释器及认证环境需单独确认：GUI 启动的 WorkBuddy 未必继承交互终端 PATH。优先使用已核对的本机可执行文件路径，避免把命令和全部参数拼成一个 shell 字符串。跨电脑重新发现路径与端口，不复制另一台电脑的账号配置。

按真实工具 schema 编写单文件软件操作 skill，写清文档身份、参数/单位、只读检查、修改后回读、撤销/保存及实际限制。只读任务不能靠普通连接 JSON 强制隔离；如有工具筛选能力按当前版本配置并验证，要求 server 级只读时实现真正的只读工具表/代理。

## 4. 生成本地接入材料

在 skill 根目录运行，替换下面文件路径、名称；输入配置只包含本次一个 stdio server，且 server key、操作 skill 的 name 与 `--name` 一致。

```bash
python3 scripts/package_agent.py --client workbuddy --name target-app \
  --mcp-config /absolute/path/to/verified-mcp.json \
  --skill-file /absolute/path/to/operation/SKILL.md \
  --output /absolute/path/to/new-workbuddy-bundle
```

生成内容：

```text
new-workbuddy-bundle/
├── mcp.json                      # 一个 stdio server 的接入参数
├── skills/target-app/SKILL.md     # 软件操作说明
├── operation-skill.zip           # 仅含上述操作 SKILL.md，供上传
├── bundle.json                   # 生成结果及未验收状态
└── INSTALL.md                    # 加载、验收和回退说明
```

生成器不执行 MCP 命令、不安装软件、不改 WorkBuddy 设置、不联网，也不把输出目录写到猜测的 `.workbuddy/` 路径。ZIP 只适用于已经审阅的单文件操作 skill；多文件技能须完整审阅并打包。含 `env`、URL、`cwd` 或其他字段的输入会拒绝，避免丢失认证或运输设置；这些场景按当前客户端格式单独适配。

## 5. 在 WorkBuddy 注册并验收

按官方 [连接器说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Connector)，在连接器管理中选择自定义连接器，按当前界面填入 `mcp.json` 的命令/参数，或使用该版本支持的 JSON 配置入口。已有同名条目先比较并留回退材料，保留其他连接器。随后在技能上传入口导入 `operation-skill.zip` 并确认操作 skill 启用；在本次任务里启用目标连接器，再做验证。菜单名称随版本变动时用当前官方说明，不编造 CLI 注册命令。

| 阶段 | 必须看到的证据 |
|---|---|
| 材料生成 | MCP JSON、操作 skill/ZIP 与依赖说明可读取；尚未连接 |
| WorkBuddy 加载 | 当前版本中连接器和技能已出现，任务启用正确目标 |
| 协议正常 | MCP 初始化与 tools/list 成功，真实工具可见 |
| 目标正确 | 只读返回符合当前窗口的文档路径/标题、可用稳定身份及状态 |
| 写入可用 | 仅在新测试文档完成可量化动作，回读属性并验证撤销/保存 |

CADCraft 示例可在新测试图纸创建 100×60 的矩形并标注，回读几何和尺寸；其他软件换成对应最小动作。这是验收任务建议，不是假定所有软件已有同名工具。缺少稳定身份时先补核对能力或限制写入，不能用标签索引冒充。

无法操作 WorkBuddy UI 时可交付材料并标记“待客户端加载验收”，保留已经完成的桥接/协议证据。卸载只移除本次连接器和操作 skill，替换的条目按备份恢复；不要删除其他技能、登录、聊天或用户文档。

## 6. 开放平台发布与内嵌助手边界

本地材料包**不是完整市场连接器**。按官方 [开放平台连接器规范](https://open.workbuddy.cn/docs/connector)，发布 MCP 连接器还需 `connector-meta.json`、图标等元信息；本地可用 stdio，远程配置需按其运输/鉴权规范，扩展字段有最低客户端版本要求。发布要另行验证，不能由本脚本自动宣称审核通过。

WorkBuddy 作为外部 MCP 客户端可调用软件工具；把它嵌进软件侧栏需要另外确认官方可调用运行时。当前仓库没有实现 WorkBuddy 聊天运行时适配器，不把 Codex app-server JSON-RPC 发给 WorkBuddy，也不使用账号文件拼凑非官方服务。完整侧栏仍参考 [运行时适配](agent-adapters.md) 和 [多会话设计](copilot-and-conversations.md)，如无可靠接口则交付已验证的外部 MCP 接入并说明缺口。
