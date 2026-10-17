#!/usr/bin/env python3
"""Install a verified build into a NEW user prefix; never overwrite an existing install."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import sys

from build_cadcraft import PROJECT, fingerprint, sha


def install(source, prefix):
    if prefix.exists():
        raise ValueError('Prefix already exists; refusing to overwrite it. Choose a NEW --prefix')
    report = json.loads((source / '.git/artcraft-verified.json').read_text())
    if report.get('checksPassed') is not True or report['sourceFingerprint'] != fingerprint(source):
        raise ValueError('Verify the current source before installing')
    for name in ('cadcraft', 'cadcraft-cli'):
        if sha(Path(report['artifacts'][name]['path'])) != report['artifacts'][name]['sha256']:
            raise ValueError('Artifact changed since verification: ' + name)
    prefix.mkdir(parents=True)
    try:
        for name in ('cadcraft', 'cadcraft-cli'):
            shutil.copy2(report['artifacts'][name]['path'], prefix / name)
        shutil.copytree(PROJECT / 'backends/freecad', prefix / 'backend')
        (prefix / 'backend/backend').chmod(0o755)
        (prefix / 'launchers').mkdir()
        q = shlex.quote
        gui = '#!/usr/bin/env bash\nset -euo pipefail\n'
        gui += 'export ARTCRAFT_COPILOT_HOME=' + q(str(prefix)) + '\n'
        gui += 'export CADCRAFT_CONFIG_DIR=' + q(str(prefix / 'config')) + '\n'
        gui += 'export CADCRAFT_SOLID_BACKEND=' + q(str(prefix / 'backend/backend')) + '\n'
        gui += 'mkdir -p "$CADCRAFT_CONFIG_DIR"\n'
        gui += 'exec flock --nonblock --close --conflict-exit-code 0 ' + q(str(prefix / 'window.lock')) + ' ' + q(str(prefix / 'cadcraft')) + ' --control "${CADCRAFT_CONTROL_PORT:-7981}" "$@"\n'
        bridge = '#!/usr/bin/env bash\nset -euo pipefail\nexec ' + q(str(prefix / 'cadcraft-cli')) + ' mcp --connect "127.0.0.1:${CADCRAFT_CONTROL_PORT:-7981}" "$@"\n'
        for name, text in [('artcraft-cadcraft', gui), ('artcraft-cadcraft-mcp', bridge)]:
            path = prefix / 'launchers' / name
            path.write_text(text)
            path.chmod(0o755)
        shutil.copytree(PROJECT / 'plugins/cadcraft', prefix / 'plugin')
        (prefix / 'plugin/.mcp.json').write_text(json.dumps({'mcpServers': {'cadcraft': {'command': str(prefix / 'launchers/artcraft-cadcraft-mcp'), 'args': []}}}, indent=2) + '\n')
        (prefix / 'updater').mkdir()
        shutil.copy2(PROJECT / 'scripts/update.py', prefix / 'updater/update.py')
        toolchain = Path(report['toolchainBin'])
        (prefix / 'updater/config.json').write_text(json.dumps({'source': str(source), 'target': report['target'], 'toolchain': str(toolchain)}, indent=2))
        (prefix / 'updater/active.json').write_text(json.dumps({'tag': report['upstreamTag'], 'tagObject': report['commit'], 'source': str(source), 'sha256': sha(prefix / 'cadcraft')}, indent=2))
        update = '#!/usr/bin/env bash\nset -euo pipefail\nexport ARTCRAFT_COPILOT_HOME=' + q(str(prefix)) + '\nexec python3 ' + q(str(prefix / 'updater/update.py')) + ' "$@"\n'
        path = prefix / 'launchers/artcraft-cadcraft-update'
        path.write_text(update)
        path.chmod(0o755)
        (prefix / 'updates').mkdir()
        print(json.dumps({'installed': str(prefix), 'launch': str(prefix / 'launchers/artcraft-cadcraft'), 'mcpConfig': str(prefix / 'plugin/.mcp.json'), 'updater': str(path)}, indent=2))
    except Exception:
        shutil.rmtree(prefix)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=PROJECT / '.work/cadcraft')
    parser.add_argument('--prefix', type=Path, default=Path.home() / '.local/share/artcraft-ai-copilot')
    args = parser.parse_args()
    try:
        install(args.source.resolve(), args.prefix.resolve())
        return 0
    except (OSError, ValueError, KeyError) as error:
        print('Not installed:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
