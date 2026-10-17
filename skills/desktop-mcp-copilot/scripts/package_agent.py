#!/usr/bin/env python3
"""Generate a NEW stdio MCP project bundle for Cursor, Claude Code, or manual adaptation.

Does not execute servers, install files, merge client settings, or verify a live connection.
Only credential-free command/args configurations and standalone operation skills are accepted.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

LAYOUTS = {
    'cursor': ('.cursor/mcp.json', '.cursor/skills'),
    'claude-code': ('.mcp.json', '.claude/skills'),
    'generic': ('mcp-stdio.json', 'skills'),
}


def package(client, name, config_path, skill_path, output):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name) > 64:
        raise ValueError('Use a lowercase hyphenated name, at most 64 characters')
    if output.exists() or output.is_symlink():
        raise ValueError('Output already exists; refusing to overwrite')
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if not isinstance(config, dict) or set(config) != {'mcpServers'}:
        raise ValueError('Expected only a mcpServers object')
    servers = config['mcpServers']
    if not isinstance(servers, dict) or set(servers) != {name}:
        raise ValueError('Include exactly the target server; its key must match --name')
    server = servers[name]
    if not isinstance(server, dict) or set(server) - {'type', 'command', 'args'}:
        raise ValueError('Only stdio type, command and args are supported; adapt other fields manually')
    if server.get('type', 'stdio') != 'stdio':
        raise ValueError('Only stdio is supported; HTTP/auth require a client-specific adapter')
    command = server.get('command')
    args = server.get('args', [])
    if not isinstance(command, str) or not command.strip() or '\0' in command:
        raise ValueError('command must be a nonempty executable path or PATH name')
    if not isinstance(args, list) or any(not isinstance(a, str) or '\0' in a for a in args):
        raise ValueError('args must be an array of strings without NUL')
    if any('${' in v for v in [command, *args]):
        raise ValueError('Client interpolation differs; resolve paths locally or adapt manually')
    skill = skill_path.read_text(encoding='utf-8')
    match = re.match(r'\A---\n(.*?)\n---(?:\n|$)', skill, re.S)
    if not match or not re.search(r'^name:\s*[\'\"]?' + re.escape(name) + r'[\'\"]?\s*$', match[1], re.M):
        raise ValueError('Standalone operation skill name must match --name')
    if not re.search(r'^description:\s*\S', match[1], re.M) or '[TODO:' in skill:
        raise ValueError('Provide a completed operation skill with a description')
    # A one-file helper must not silently omit referenced local resources.
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', skill):
        if not target.startswith(('https://', 'http://', '#', 'mailto:')):
            raise ValueError('Local skill resources need a reviewed full-directory package')
    config_file, skill_root = LAYOUTS[client]
    normalized = {'mcpServers': {name: {'type': 'stdio', 'command': command, 'args': args}}}
    created = False
    try:
        output.mkdir(parents=True, exist_ok=False)
        created = True
        cp = output / config_file
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        sp = output / skill_root / name / 'SKILL.md'
        sp.parent.mkdir(parents=True)
        sp.write_text(skill, encoding='utf-8')
        result = {
            'client': client, 'server': name, 'config': config_file,
            'operationSkill': sp.relative_to(output).as_posix(),
            'installed': False, 'mcpVerified': False, 'clientLoadVerified': False,
            'genericRequiresTranslation': client == 'generic',
        }
        (output / 'bundle.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        (output / 'INSTALL.md').write_text(
            '# 本机连接包\n\n'
            f'目标客户端：{client}；目标 server：`{name}`。\n\n'
            '此目录仅是待安装的材料，不含软件或依赖，也未执行 MCP server。'
            'command/args 必须来自接收者本机发现；不要在参数中放密钥。\n\n'
            f'1. 检查 `{config_file}` 的可执行文件、参数、当前软件窗口及依赖。\n'
            '2. 备份目标工作区已有配置，仅合并本次 server 条目；同名条目先比较。'
            '其他 server、账号和模型设置保持不变。generic 配置需按实际客户端规范转译。\n'
            f'3. 安装 `{skill_root}/{name}/` 到相应技能位置，已有技能先比较。'
            '这是软件操作 skill，制作流程另见 desktop-mcp-copilot。\n'
            '4. 用当前客户端支持的刷新/重开方式加载，遵守其工作区信任和工具授权。\n'
            '5. MCP 初始化、工具枚举后，用只读工具确认目标窗口及文档；'
            '仅在授权的新测试文档中写入并回读。记录客户端版本、实际结果和未验证项。\n'
            '6. 卸载只删除此次新增的 server/skill；替换过的条目按备份还原，'
            '保留其他配置、聊天和文档。\n\n'
            '原生插件、HTTP/OAuth、额外环境设置需独立适配。普通配置不强制只读；'
            '生成本目录不表示客户端已加载、软件已连接或侧栏已实现。\n', encoding='utf-8')
        return result
    except (OSError, ValueError):
        if created:
            shutil.rmtree(output)
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client', choices=LAYOUTS, required=True)
    p.add_argument('--name', required=True)
    p.add_argument('--mcp-config', type=Path, required=True)
    p.add_argument('--skill-file', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        result = package(a.client, a.name, a.mcp_config, a.skill_file, a.output)
        print(json.dumps({'ok': True, 'output': str(a.output.resolve()), **result}, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as e:
        print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
