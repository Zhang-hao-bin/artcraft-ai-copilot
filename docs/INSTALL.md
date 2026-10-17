# 安装与连接

## 1. 准备构建环境

参考实现针对 Linux。使用 Rust 1.95，安装 rustfmt、clippy 和 wasm32-unknown-unknown：

```bash
rustup toolchain install 1.95.0 --component rustfmt --component clippy
rustup override set 1.95.0
rustup target add wasm32-unknown-unknown
```

CADCraft 的 Linux 原生依赖以固定版本上游 README/构建说明为准，包括系统编译工具、图形窗口、输入及 udev 相关开发库。先满足这些依赖，再运行仓库构建脚本。Python 辅助脚本只使用标准库，要求 Python 3.11+。

## 2. 构建并安装到新目录

```bash
python3 scripts/build_cadcraft.py prepare
python3 scripts/build_cadcraft.py verify
python3 scripts/install_local.py
```

可以用 `--source` 和 `--target-dir` 选择独立源码和 Cargo 缓存目录；不要把新的 clone 指向已有工作目录。安装器用检查报告校验源码指纹和两个二进制 SHA256，拒绝覆盖已存在的安装前缀。

默认前缀是 `~/.local/share/artcraft-ai-copilot`。如需另外的位置：

```bash
python3 scripts/install_local.py --prefix /absolute/path/to/new/install-prefix
```

安装器不写系统目录、不修改原版 CADCraft、不给 Codex 注册账号，也不改系统代理。代理由进程环境提供；需要访问模型服务时按本机网络配置 HTTPS_PROXY，并让本机控制通道走 NO_PROXY。

## 3. 启动 GUI 和中文输入

```bash
~/.local/share/artcraft-ai-copilot/launchers/artcraft-cadcraft
```

需要已安装可用的 Codex CLI；默认从 PATH 查找 `codex`，也可设置 `CADCRAFT_CODEX_BIN` 为本机真实路径。登录沿用自己的 Codex 配置，不要把认证文件复制到项目中。

默认控制端口是回环地址 7981。若该端口已有应用运行，先确认目标窗口；不要启动第二个实例去覆盖其工作。可以设置 `CADCRAFT_CONTROL_PORT`，但 GUI 和 MCP 包装必须一致。

操作系统需先配置好中文输入法。Fcitx5 示例是仅在该进程设置 `XMODIFIERS=@im=fcitx`、`GTK_IM_MODULE=fcitx`、`QT_IM_MODULE=fcitx`；IBus 或其他桌面按其环境使用，不要盲目覆盖。字体回退由新版 CADCraft 处理。

收起后点击右侧「Codex 对话」或 Ctrl+Shift+L 重开。每张文件有自己的会话列表；「新对话」新增会话，旧消息保留。发送时会读取图纸快照，可选附图。

## 4. 连接外部 agent

原始控制端口不是 HTTP MCP。包装命令为：

```bash
~/.local/share/artcraft-ai-copilot/launchers/artcraft-cadcraft-mcp
```

安装器生成 `plugin/.mcp.json`，其中 command 已替换为本机绝对路径。仓库里的同名文件是使用 PATH 命令的模板，不能据它证明任意客户端已连接。将实际生成配置按目标客户端格式注册，重载后检查 initialize、tools/list 和当前文档。

只读握手检查：

```bash
python3 skills/desktop-mcp-copilot/scripts/probe_mcp.py -- \
  ~/.local/share/artcraft-ai-copilot/launchers/artcraft-cadcraft-mcp
```

这只枚举工具，不调用工具、不核对文档。再用客户端实际的只读工具确认目标窗口。只读任务可在支持的客户端只允许 inspect/render 等工具；不要给普通连接 JSON 编造 readOnly 字段。

## 5. Codex 插件

生成目录 `~/.local/share/artcraft-ai-copilot/plugin` 包含 `.codex-plugin/plugin.json`、`.mcp.json` 和操作 skill。按当前 Codex 的本地插件/marketplace 入口安装；示例 marketplace 名为 `artcraft-local`，其他名称需同步侧栏停用重复插件的配置。

不要重复加载同一 server 的全局和插件配置。插件格式不能直接当作其他 agent 的配置格式；CLI 具体安装子命令以本机帮助与官方文档为准。

## 6. 可选独立 FreeCAD 后端

本仓库只附桥接代码，不下载或链接 FreeCAD 内核。验证过的环境是官方 FreeCAD 1.1.4 Linux AppImage 解压目录，包含 AppRun 和 usr/bin/freecadcmd。设置 `CADCRAFT_FREECAD_ROOT` 指向解压后的根目录。

默认实体输出位置是 `~/Documents/CADCraft/solids`，可用 `CADCRAFT_SOLID_OUTPUT_DIR` 改变。桥接参数为 kind（bearing/box/cylinder/sphere）、units（mm/inch）和 dimensions。输出原生 FCStd、STEP、输入及验证报告。打开实体也限制在该输出目录内。

不安装 FreeCAD 不影响二维 MCP 和聊天侧栏。未配置后端时不要承诺三维操作可用；实际错误由后端返回。复杂发动机、任意曲面等没有自动实现。
