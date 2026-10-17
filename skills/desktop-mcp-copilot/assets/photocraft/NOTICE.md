# PhotoCraft 补丁来源与范围

本目录的补丁基于 [storytold/photocraft](https://github.com/storytold/photocraft) `v0.9.0`，精确提交 `c699e3cda69f4852b43c0b191ab0091aaeff9d6a`。上游以 MIT OR Apache-2.0 授权，许可证全文随附于 [LICENSE-MIT](LICENSE-MIT) 和 [LICENSE-APACHE](LICENSE-APACHE)。保留文件中的版权声明，分发应用时同时遵守上游及其依赖的许可证。

原生 Rust/egui 侧栏由本项目 CADCraft Copilot 的同类实现适配，复用 PhotoCraft 的文档引擎、控制通道、预览与保存能力。补丁新增 `copilot.rs`、`copilot_documents.rs`，并接入 UI 生命周期、菜单、语言目录和独立应用身份；没有附带 PhotoCraft 或 Codex 二进制。

这是一次 Linux 环境已验证实现的源材料，不是跨平台安装器，也不是官方 PhotoCraft 或 OpenAI 发行版。Codex app-server 协议、模型可用性及依赖可能变化，应在目标机器重新检查。本目录不包含账户、control token、客户端配置、聊天、截图或用户图像。

已实现的是文档命令与聊天侧栏。原生 AI 生图结果事件、生成图片预览及导入流程尚未接入；不要将本补丁当作已完成的生图集成。详细步骤和已知边界见 [PhotoCraft 接入与验证](../../references/photocraft-integration.md)。

## 2026-10-17 嵌套组预览修复

独立的 [photocraft-v0.9.0-nested-transform.patch](photocraft-v0.9.0-nested-transform.patch) 修改同一固定上游版本的 `crates/ui-egui/src/transform_tool.rs`，修复嵌套组自由变换预览夹带无关背景，并增加 2 项回归测试。沿用本目录所附 MIT OR Apache-2.0 许可证；原侧栏补丁未被替换。应用顺序及证据见 [Bug 修复说明](../../references/photocraft-bug-fixes.md)。本轮只发布源码补丁、操作说明和去除本机私有信息的验证摘要，不包含用户作品或程序二进制。
