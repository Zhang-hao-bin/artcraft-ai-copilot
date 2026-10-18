# 让使用者在自己电脑上调用

交付整个 `desktop-mcp-copilot/` 目录，保留 references/scripts/agents 及存在的 assets。仅发 SKILL.md 会丢失依赖。先核对目标 agent 当前技能机制，支持项目技能时复制到其对应目录（见 [agent 适配](agent-adapters.md)）；已有技能先比较，不覆盖用户修改。只有明确要全局使用才安装全局技能。

无需先安装也能启动：让本机 agent 克隆/读取仓库并显式读取 `skills/desktop-mcp-copilot/SKILL.md`，再按路由读取相对参考。仓库根 `PROMPTS.md` 提供完整提示词，包括首次启动、已安装技能、仅连接、完整侧栏与换机复现。

一句话（替换软件名）：

> 请读取 https://github.com/Zhang-hao-bin/artcraft-ai-copilot 中 skills/desktop-mcp-copilot/SKILL.md 及必要参考，为我这台电脑上的【软件名】建立 MCP 连接并封装成当前 agent 可用的交付包；自行发现环境，在新测试文档回读验证，保留已有配置和未保存工作。

如果 agent 不能直接读 GitHub，让它用自己可用的 Git/下载能力取得完整仓库。不能联网时使用已下载的完整目录；路径由用户或本机搜索确认。不要声称仓库 URL 会自动注册技能。

制作 agent、接收客户端、侧栏后端分别记录；例如“Claude Code 制作 → Cursor 调用软件”完全可行，但生成配置不代表已在 Cursor 加载。缺少目标软件名称时必须问清；缺少本机执行权限时只能交付用户可执行材料，不能虚构安装。

记录检查到的版本、依赖、接口/实际端口、可执行路径、客户端配置增量、还原步骤和验收结果。分发材料排除账号、个人文档和聊天；实际机器路径留在本机适配记录，对外提供可重新发现的说明。容器/SSH/云端的 localhost 不指用户电脑，跨主机须使用已授权且经认证的连接，不开放无认证控制端口。
