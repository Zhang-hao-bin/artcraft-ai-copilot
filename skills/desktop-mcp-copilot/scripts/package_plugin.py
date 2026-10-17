#!/usr/bin/env python3
"""Package a verified MCP config and completed standalone skill into a NEW local Codex plugin directory."""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--mcp-config", type=Path, required=True)
    parser.add_argument("--skill-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    created = False
    try:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.name) or len(args.name) > 64:
            raise ValueError("Use a lowercase hyphenated plugin name, at most 64 characters")
        if args.output.exists() or args.output.is_symlink():
            raise ValueError("Output already exists; refusing to overwrite")
        config = json.loads(args.mcp_config.read_text(encoding="utf-8"))
        servers = config.get("mcpServers") if isinstance(config, dict) else None
        if not isinstance(servers, dict) or not servers:
            raise ValueError("Expected a verified .mcp.json with nonempty mcpServers")
        for server in servers.values():
            if not isinstance(server, dict) or not (isinstance(server.get("command"), str) or isinstance(server.get("url"), str)):
                raise ValueError("Each server needs a command or URL")
        skill = args.skill_file.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", skill, re.S)
        if not match or not re.search(r"^name:\s*\S", match[1], re.M) or not re.search(r"^description:\s*\S", match[1], re.M):
            raise ValueError("Completed operation skill must have name and description frontmatter")
        if "[TODO:" in skill:
            raise ValueError("Replace skill scaffold before packaging")
        # This small helper packages a standalone SKILL.md, never an arbitrary directory with secrets.
        if re.search(r"\]\((?:\./)?(?:references|scripts|assets)/", skill):
            raise ValueError("This helper packages a standalone skill only; referenced resources need a reviewed full-directory package")
        manifest = {
            "name": args.name, "version": "1.0.0", "description": args.description,
            "skills": "./skills/", "mcpServers": "./.mcp.json",
            "interface": {"displayName": args.display_name, "shortDescription": args.description},
        }
        args.output.mkdir(parents=True, exist_ok=False)
        created = True
        (args.output / ".codex-plugin").mkdir()
        folder = args.output / "skills" / args.name
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text(skill, encoding="utf-8")
        (args.output / ".mcp.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (args.output / ".codex-plugin" / "plugin.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"ok": True, "output": str(args.output.resolve()), "installed": False, "mcpVerifiedByThisScript": False}, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as error:
        if created:
            shutil.rmtree(args.output)
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
