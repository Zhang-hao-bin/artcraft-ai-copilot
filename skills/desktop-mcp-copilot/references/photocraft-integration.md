# PhotoCraft：已实测的集成范围与复用材料

适用于把 PhotoCraft 接入外部 MCP 客户端，或在有源码的原生版本内增加 Codex 聊天侧栏。先按 [agent 适配](agent-adapters.md) 区分制作 agent、接收客户端与侧栏运行时；已有通用脚本继续复用，不另造一套安装器。

## 此次新增了哪款软件

**已测试实现 PhotoCraft v0.9.0 在 Linux 上的完整文档接入与 Codex 聊天侧栏。** 本次增加的是这款图像软件的已验证案例与源码材料；仓库原有 CADCraft v0.7.0 参考不变，FreeCAD 仍是 CADCraft 的独立可选建模后端。它们不是同一款软件的别名，也不能合并描述成所有 ArtCraft 应用均已接入。

| PhotoCraft 能力 | 已观察到的结果 | 验证边界 |
|---|---|---|
| 当前窗口 MCP | 认证握手、25 个工具、活动文档/画布/图层回读；真实图层新增、撤销/重做、保存回读 | Linux v0.9.0 的可见窗口 bridge 模式 |
| Codex 插件 | 插件安装、真实 Codex 客户端加载 25 个 PhotoCraft 工具，确认没有重复 server | 源环境插件版本 1.0.2；其他客户端只提供可适配材料 |
| 原生聊天侧栏 | Rust/egui UI，启动/首次发送自动连接、文字流、停止、收起重开 | Codex app-server；不是复用桌面应用的全部工具面板 |
| 模型和思考强度 | 加载实际目录中的 7 个模型选项，选择/恢复默认；真实 `gpt-6.1-sol` 调用工具新增图层并回读 | 枚举到 7 项不等于逐个验证了 7 个模型的推理或账号权限 |
| 文档与多会话 | 稳定 UID 隔离、新文件空白会话、同文件新增/切回、消息/草稿/设置保留、关闭/重开及重启恢复 | 有界本机记录；恢复后重建模型连接，不声称原服务 thread 持续运行 |
| 取消与失效请求 | 停止、切换文件时取消旧请求；新文档内容不被旧任务修改 | 不授权把旧请求目标更新为新活动文件 |
| 中文使用 | 中文组合输入、Ctrl+Enter、聚焦输入时收起重开；切换 `zh-hans` 菜单/面板并确认设置保存 | 已有图层名、文件名和正文不随界面汉化改写 |
| 界面布局 | 14 种主题、1440×900 与 1000×760 两种尺寸共 28 组截图检查 | 仅源环境，其他显示缩放/平台重新检查 |
| 认证和保存边界 | 拒绝未认证控制请求及读写根目录外保存；原文档保留 | 不公开 token、账户、个人聊天或用户图像 |

**未测试实现的范围：** PhotoCraft 侧栏原生 AI 生图、生成图片预览/导入链路；导出 PSD 在实际 Photoshop 内打开及完整可编辑性；Windows/macOS/网页端同等侧栏；Cursor、Claude Code 内的 PhotoCraft 端到端加载与模型调用。不要把这些条目放入“已支持”清单。下文保留已有实现的复用入口与易错点，避免下一位操作者重复发现接口。

## 可直接复用的材料

| 材料 | 用途与边界 |
|---|---|
| [原生侧栏源码补丁](../assets/photocraft/photocraft-v0.9.0-copilot.patch) | 固定 PhotoCraft v0.9.0；新增原生 Rust/egui 侧栏、稳定文档 UID、模型设置、取消守卫及文件内多会话，不含生图链路 |
| [软件操作 skill](../assets/photocraft/operation/SKILL.md) | 已完成的单文件操作模板，可交给现有打包器；先按目标机器的真实工具核对 |
| [来源与许可证](../assets/photocraft/NOTICE.md) | 补丁来源、分发要求及不包含的私有材料 |
| [分阶段验证记录](../assets/photocraft/validation.json) | 区分源实现的历史验证与本次公开材料检查，不当作接收方已安装的证据 |

上游为 `https://github.com/storytold/photocraft`，标签 `v0.9.0`，提交 `c699e3cda69f4852b43c0b191ab0091aaeff9d6a`。源实现验证环境是 Linux、Rust 1.95、Codex CLI 0.159.2；其他版本与 OS 重新验收。上游 `AGENTS.md` 要求保持原生 Rust 架构，原生进程/文件模块通过 cfg 排除于 WASM；不要为聊天另加 webview。

## 先完成可见窗口连接

1. 发现本机 `photocraft`、`photocraft-cli` 的路径和版本，读取 `--help`，确认用户实际窗口和未保存工作。不要先关闭原版窗口。若需集成版，使用独立应用身份、设置目录和监听端口。
2. 确认控制通道为**回环 TCP、认证、换行 JSON**。下面的 7982 仅是本次实例端口；目标机器先检查占用。它不是 HTTP MCP URL。
3. 在用户私有配置目录以独占创建方式生成 control token：用 `secrets.token_hex(32)`，文件权限 0600、目录 0700；不覆盖已有 token，不把值放进参数、日志或公共包。原版 v0.9.0 支持 `--control-token-file`，不需要为此重写服务端。

在原生桌面会话中，下面是**完成本机路径发现后**的启动形状。`pc_gui`、`pc_cli`、`pc_config`、`pc_workdir` 必须先解析为目标机器的真实绝对路径，`pc_port` 为已确认的空闲回环端口；只做 MCP 时可先使用原版 GUI。

```bash
PHOTOCRAFT_CONFIG_DIR="$pc_config" \
PHOTOCRAFT_AUTOMATION_READ_ROOT="$pc_workdir" \
PHOTOCRAFT_AUTOMATION_WRITE_ROOT="$pc_workdir" \
"$pc_gui" --control "$pc_port" --control-token-file "$pc_config/control.token"
```

软件控制监听就绪后，另一终端运行 stdio 包装或使用现有探针。以下命令从本 skill 根目录执行；探针只握手和列工具，不读写图像。

```bash
python3 scripts/probe_mcp.py --timeout 10 -- \
  "$pc_cli" mcp --bridge "127.0.0.1:$pc_port" \
  --control-token-file "$pc_config/control.token"
```

本次 v0.9.0 枚举到 25 个工具，协商协议为 `2025-06-18`。这是版本记录，不是以后版本的固定数量要求。探针通过后仍须由真实客户端读 `ui_inspect` / `session_list` / `doc_inspect`，对上窗口、活动文件、尺寸和图层。

### 已验证的 bridge 差异

| 接口 | v0.9.0 行为 |
|---|---|
| MCP stdio | `photocraft-cli mcp --bridge ...`；省略 bridge 会进入独立 headless 文档 |
| `session_list` | bridge 返回完整 UI 对象，实际文档列表在 `session.documents`；不要假定所有模式同形 |
| `doc_close` / `doc_select` | 仅 headless；可见窗口改用 `ui.menu.invoke` 的 `file.close`、`window.document.<index>`，然后重读身份 |
| bridge `render_preview` / `doc_render_preview` | 应用窗口截图；侧栏动态 `preview` 才是当前文档合成缩略图 |
| `ui_inspect.documentUID` | 本补丁新增稳定 UID；普通上游接口缺失时如实记录，不能拿 index 替代 |
| `app.open` / `app.save` | 补丁在配置了自动化根目录时先把相对路径归一为根内绝对路径，再交给原有权限校验；保存后回读实际路径 |
| 完整文档保存 | PSD/PSB/pcraft 可能改变当前路径及 dirty 状态；平面格式通常导出副本，按实际返回确认 |
| `app.quit` | 跳过保存提示；不能用来清理用户窗口或未保存工作 |

用新测试图像验证一轮可量化操作：新建 640×480、8 位图像 → 查询 `layer.new.layer` 参数 → 新增中文命名图层 → 回读数量 → 撤销/重做 → 保存新路径 → 回读。不能在用户正在编辑的图像上运行这组测试。

## 复用侧栏源码

只有用户要求软件内助手时才应用补丁；仅连接或打包不需要重建 GUI。在**新的独立源码目录**固定上述提交，保留上游许可证并先读其 AGENTS.md。`patch_file` 是本 skill 内补丁的绝对路径；命令在新源码目录执行：

```bash
git rev-parse HEAD
# 确认输出恰为 c699e3cda69f4852b43c0b191ab0091aaeff9d6a 后再继续
git apply --check "$patch_file"
git apply "$patch_file"
cargo fmt --all -- --check
cargo build -p photocraft -p photocraft-cli --locked
```

不在用户原有检出上 reset；新版本补丁冲突时停止直接应用，按 [迁移与验收](adapt-and-verify.md) 适配。应用补丁只提供程序能力，仍需创建独立启动器、配置和桌面入口，检查依赖、真实运行与回退。不要把 debug/release 构建缓存或二进制塞进 skill。

补丁的本机配置入口如下，值由启动器在子进程内设置；无需把账户认证复制进来：

| 环境变量 | 含义 |
|---|---|
| `PHOTOCRAFT_CONFIG_DIR` | 独立原生偏好/恢复目录，避免与用户原版混用 |
| `PHOTOCRAFT_COPILOT_STATE` | 私有聊天状态 JSON 路径；父目录先创建并保护 |
| `PHOTOCRAFT_CODEX_BIN` | 实际可用且已登录的 Codex 可执行文件 |
| `PHOTOCRAFT_COPILOT_WORKDIR` | 聊天运行时工作目录 |
| `PHOTOCRAFT_AUTOMATION_READ_ROOT` | 允许自动化读取的根目录 |
| `PHOTOCRAFT_AUTOMATION_WRITE_ROOT` | 允许自动化保存的根目录 |

原生侧栏的 stdio JSON-RPC、模型目录、动态工具和 thread 生命周期沿用 [侧栏与多会话](copilot-and-conversations.md)。当前补丁注册 7 个 `photocraft` 动态文档工具：inspect、list_commands、execute、preview、save、jobs_list、jobs_cancel。它们与外部 25 个 MCP 工具不同，不能因为数量不同就判断连接失败。

补丁在 app-server 子进程局部停用 `photocraft@photocraft-local`，避免自家外部 MCP 重复入口。该名称是本参考的约定；接收方使用其他 marketplace 时同步适配，不能改全局设置或误停别的软件插件。

按稳定 `DocId` 而非标签索引建立会话池；每次请求绑定文档 UID 与会话身份，切换/停止会失效旧 runtime 并取消其后台任务。已保存文件按规范化路径恢复近期记录；同路径多副本持久化以活动副本为准。启动时软件恢复功能可能额外打开标签，核对全部文档及 dirty 状态，不以“标签数与参数数量不同”就丢弃恢复副本。

### 中文输入与界面

- 简体中文是现成偏好：先查 `prefs.get {path:"interface.language"}`，再执行 `prefs.set {path:"interface.language",value:"zh-hans"}`，读设置、保存的偏好与截图确认；无需重新编译。文件名、图层名和图像正文属于用户内容，不随界面汉化改写。
- 区分中文字体回退、输入法 composition、输入框焦点。Linux 原生启动环境与 agent 的终端环境可能不同；只从当前用户可信桌面进程取必要 DISPLAY/WAYLAND/XAUTHORITY 等白名单变量。GNOME Shell 的环境未必有 DISPLAY，本次 Xwayland 进程有可用值；不要写死 PID、显示编号或认证路径。
- 本机曾采用 Xwayland 解决 IME 路径问题，应先检查目标机器桌面和输入法，不全局改用户的显示设置或输入法。
- Ctrl+Enter 在 TextEdit 处理前、且输入框有焦点时消费按键事件；读取事件自己的 modifiers，不能只看全局修饰键状态。合成控制事件可能没有 ModifiersChanged。验证普通 Enter 换行、中文组合提交、焦点外不误发送。
- Linux 的重开组合为 Ctrl+Alt+Shift+F12；保留 PhotoCraft 原有 Ctrl+Shift+L 自动色调快捷键。窗口菜单 Copilot 和 AI 按钮也能重开。其他平台按原生修饰键语义核对。

## 复用现有打包器

根据本机验证过的可执行路径和 token **文件路径**生成目标 `mcpServers.photocraft` 的 stdio 配置。示意如下，尖括号必须替换，不作为可直接安装的配置；不把 token 值写入 JSON：

```json
{
  "mcpServers": {
    "photocraft": {
      "command": "<本机 photocraft-cli 绝对路径>",
      "args": ["mcp", "--bridge", "127.0.0.1:<已确认端口>",
               "--control-token-file", "<本机私有 token 文件路径>"]
    }
  }
}
```

从 skill 根目录，用新输出目录生成接收客户端的材料：

```bash
python3 scripts/package_agent.py --client cursor --name photocraft \
  --mcp-config "$verified_mcp_json" \
  --skill-file assets/photocraft/operation/SKILL.md --output "$new_bundle"
```

Claude Code 用 `--client claude-code`，未知客户端用 `--client generic` 再适配其规范；Codex 原生插件用 `scripts/package_plugin.py`，同样使用本操作 skill，并提供显示名与描述。不要直接分发另一台机器生成的绝对路径或凭证。打包脚本不启动服务器、不注册客户端、不证明连接成功；安装后重新加载工具并确认无重复 server。不要手改生成的插件缓存。

## 生图与 PSD 的单独边界

**原生生图尚未接通。** 本补丁的提示词限定使用 PhotoCraft 文档工具，事件处理只接文字流和动态工具，未处理 `imageGeneration` 产物、图片展示及导入。源环境的 Codex CLI 生图 feature 为 true 仍不代表该侧栏已实现完整链路。不要仅查 PhotoCraft 命令后就断言“Codex 没有生图能力”，也不能把手工图层绘制当作 AI 生图。

接入生图属于明确的后续工作：核对实际运行时/账号可用的原生工具 → 允许该能力但保留文档修改守卫 → 处理生成开始/完成/失败和落地文件 → 在当前会话显示真实产物 → 用户请求导入时调用真实置入命令 → 再读文档验证。停止/切换后迟到的图片不得自动导入新文件。特性开关、模型文字承诺及生成占位图都不能代替一次真实验证；其他客户端是否支持同一机制分别核对。参见 [OpenAI 生图说明](https://learn.chatgpt.com/docs/image-generation)。

**PSD 导出不等于 Photoshop 已验收。** `.pcraft` 是 PhotoCraft 原生文件，不能改后缀冒充 PSD。真正导出 `.psd` 后检查格式、警告、图层树及独立回读；PSD 文件头的 `8BPS` 只证明格式特征，不能证明全部兼容。文字、字体、混合、蒙版、效果和智能对象需在实际 Photoshop 中打开检查；没有该环境就标记未验证。本次没有 Photoshop 打开实测。保留原生源文件，方便继续调整。格式依据可查 [Adobe 文件格式说明](https://helpx.adobe.com/photoshop/desktop/save-and-export/export-files-to-different-formats/photoshop-file-formats-overview.html) 和目标版本的上游 `docs/file-format-parity.md`。

## 验证与交接

源实现历史验证包括：真实窗口 MCP 读取，测试图像新增图层与撤销/重做、原生保存回读；真实模型调用工具；模型/思考强度与默认恢复；首次发送自动连接；中文输入与 Ctrl+Enter；收起重开；按文件和会话隔离；停止/切换拒绝旧请求；已保存文件重开及进程重启恢复。记录摘要放在随附 validation.json，没有发布聊天或用户图像。

完整 UI 库回归为 2697 通过、12 忽略，26 组集成测试共 109 通过；最后键盘修复后另跑 11 项 Copilot 定向测试全过，计数不相加冒充不重复总数。Clippy、分层、WASM、原生构建与菜单注册检查通过。Clippy 以 `--no-deps -D warnings -A clippy::collapsible_match` 运行，明确保留上游既有样式警告豁免。GPU 离屏集成测试在默认硬件驱动曾崩溃，改用仅对测试进程生效的 lavapipe 软件 Vulkan 后通过；不以此关闭用户桌面 GPU。

接收方按本次变更和上游要求运行适当检查，不照抄历史数量：

```bash
cargo test -p photocraft-ui-egui --lib copilot --locked
cargo xtask layers
cargo xtask wasm
# 上游要求的完整库/集成测试、Clippy 和构建按变更范围执行
```

测试阶段若需要 lavapipe，先确认 ICD 实际路径，再只给测试命令设置 `VK_DRIVER_FILES` / `VK_ICD_FILENAMES` 与 `WGPU_BACKEND=vulkan`。在多个窗口尺寸及实际支持的主题下检查侧栏；源实现检查过 14 种主题、两种尺寸共 28 组。菜单注册数只证明命令接线，不证明全部 Photoshop 功能等价。

最终分别交付：外部 MCP 已验证层级、接收客户端加载状态、内嵌侧栏与多会话验收、可复现源码基线、依赖/启动与回退，以及未完成能力。只收集必要计数和布尔结果；不发布 `ui.copilot.status` 全量、control token、账户文件、偏好、原始聊天或用户作品。自动化根目录、代理和独立配置只在目标实例内设置。

## 后续修复特别说明：嵌套组变换预览

2026-10-17 在上述集成版本上补充修复了自由变换预览夹带父组背景的问题。复用上文侧栏源码时，在原补丁应用后、编译前增加 [嵌套组预览修复补丁](../assets/photocraft/photocraft-v0.9.0-nested-transform.patch)；原侧栏补丁保持不变。[Bug 修复说明](photocraft-bug-fixes.md) 给出症状、根因、修改位置、应用顺序和生效方式，[独立验证记录](../assets/photocraft/nested-transform-validation.json) 记录本轮证据。

本轮完整 UI 库与集成测试共 2,809 项通过、12 项忽略；其中包含 2 项新增回归测试。上文保留的是集成阶段的历史计数，不与本轮数量相加。此次未重新调用真实模型，也未改变已记录的生图和 Photoshop 实测边界。
