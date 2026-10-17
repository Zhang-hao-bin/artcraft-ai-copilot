# PhotoCraft 特别说明：已修复的 Bug

本轮记录 2026-10-17 在 Linux、PhotoCraft v0.9.0 上实际修复并验证的 1 项缺陷。`PC-TRANSFORM-001` 是本仓库的说明编号，不是上游 GitHub Issue 编号。

## PC-TRANSFORM-001：嵌套组自由变换预览夹带背景

| 项目 | 本轮结果 |
|---|---|
| 症状 | 对嵌套组中的透明形状或整组执行自由变换、拖到不同颜色的区域时，目标后方出现一块随动的实心矩形。例如野草移到红色杯身前方，草的空隙仍显示原来的蓝色背景 |
| 适用基线 | `storytold/photocraft` v0.9.0，提交 `c699e3cda69f4852b43c0b191ab0091aaeff9d6a`；本仓库原侧栏补丁单独应用时仍有该问题 |
| 根因 | `preview_image` 扁平化目标时只隐藏顶层无关图层；为保留嵌套目标而保留祖先组后，该组内的其他背景与兄弟图层也进入预览裁剪区域 |
| 修改文件 | `crates/ui-egui/src/transform_tool.rs` |
| 实际代码变更 | 用已存在的递归 `show_only(&mut solo.layers, &[id])` 替换只遍历 `solo.layers` 的可见性循环；沿祖先路径保留目标，逐层隐藏无关兄弟图层，保留目标组内子图层各自的显示状态 |
| 修复后行为 | 选中形状和整组都能在透明区域透出当前位置的画面；预览不修改文档，确认平移后透明度仍正确，隐藏子图层保持隐藏 |
| 源内容 | 检查到的草由透明矢量形状组成；这次修复只改预览隔离逻辑，没有重建用户图层或改写用户文件 |

[独立源码补丁](../assets/photocraft/photocraft-v0.9.0-nested-transform.patch) 包含上述修改和 2 项回归测试。补丁 SHA-256：`d692763b9bd31a33caab238d0e384b9d2ae0675f04eab2740745d2904d8c8ae6`。来源与许可证见 [NOTICE](../assets/photocraft/NOTICE.md)。

## 接入时怎样包含修复

在独立源码目录固定上述上游提交，先按 [PhotoCraft 集成说明](photocraft-integration.md) 应用原侧栏补丁，再在格式检查和构建之前应用本补丁。以下变量是接收方解析出的两个补丁的真实绝对路径，命令在固定基线的源码根目录执行：

```bash
git rev-parse HEAD
# 先核对为 c699e3cda69f4852b43c0b191ab0091aaeff9d6a
git apply --check "$copilot_patch"
git apply "$copilot_patch"
git apply --check "$transform_patch"
git apply "$transform_patch"
cargo fmt --all -- --check
cargo test -p photocraft-ui-egui --lib nested_transform --locked
cargo test -p photocraft-ui-egui --lib --tests --locked
cargo build -p photocraft -p photocraft-cli --locked
```

侧栏补丁已经应用时，只应用新增的变换补丁。遇到已经包含此修复的源码，可用 `git apply --reverse --check "$transform_patch"` 检查匹配情况；这是只读检查，不执行反向应用。检查失败或版本不符时先读实际源码，不能强行套用、反向删除修复或 reset 用户检出。其他版本需要重新适配与验收。

还需按上游要求执行 Clippy、依赖层级与 WASM 检查。GPU 离屏测试如需软件 Vulkan，先发现接收机器上的 ICD 路径，只给测试进程设置环境；不要照搬源机器路径或全局禁用桌面 GPU。

已有安装需要重建并更新 GUI 程序；只安装 skill、更新插件配置或重新连接 MCP 不会更新可执行文件。保留用户未保存文档、聊天与草稿，让用户完成当前变换并保存，再退出并重新打开更新后的应用。本次源环境以原子替换程序文件的方式安装，保留旧程序备份，没有关闭或保存正在编辑的窗口；当时运行中的窗口需下次启动才生效。

## 已完成的验证及其范围

- 2 项新增回归测试在旧逻辑上均失败：本应透明的位置 alpha 为 255；应用修复后均通过。
- 覆盖单个形状和整组、8/16/32 位文档、两种预览输入模式、多个祖先层级、隐藏子图层、预览不改源文档，以及确认平移后的透明度。
- 完整 UI 库与集成测试：27 组，共 2,809 项通过、0 失败、12 忽略；已包含上述 2 项回归测试，不重复相加。
- 原生桌面构建、Clippy、依赖层级、WASM、格式和 diff 检查通过。Clippy 沿用上游既有 `-A clippy::collapsible_match` 豁免；不是取消全部警告检查。
- 离屏中文界面截图中，将草组移到红色杯身前方，已目视确认杯身与线条从透明区域正常显示。检查使用软件 Vulkan、CPU 画布；用户作品与截图不随仓库发布。
- 已在干净固定基线上依次应用两个公开补丁，并逐文件对照实际通过上述构建与测试的源码。公开材料验证不代表接收方机器已安装、已重启或已验收。

去除本机路径、程序指纹、文档标识和用户内容后的摘要见 [nested-transform-validation.json](../assets/photocraft/nested-transform-validation.json)。集成阶段的历史记录继续保存在原 [validation.json](../assets/photocraft/validation.json) 中；本轮没有重新执行真实模型调用、Photoshop 打开验证或其他平台侧栏测试，原生生图链路也未因此接通。
