"""Installer behavior tests, with fake artifacts in a temporary prefix only."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from build_cadcraft import fingerprint, sha
from install_local import install


class InstallerTests(unittest.TestCase):
    def test_new_prefix_and_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source'
            source.mkdir()
            for args in [['init'], ['config', 'user.name', 'Fixture'], ['config', 'user.email', 'fixture@invalid']]:
                subprocess.run(['git', *args], cwd=source, check=True, capture_output=True)
            (source / 'fixture').write_text('source')
            subprocess.run(['git', 'add', '.'], cwd=source, check=True)
            subprocess.run(['git', 'commit', '-m', 'fixture'], cwd=source, check=True, capture_output=True)
            artifacts = {}
            for name in ('cadcraft', 'cadcraft-cli'):
                binary = root / name
                binary.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
                binary.chmod(0o755)
                artifacts[name] = {'path': str(binary), 'sha256': sha(binary)}
            report = {'checksPassed': True, 'toolchainBin': '/usr/bin', 'sourceFingerprint': fingerprint(source), 'source': str(source), 'target': str(root / 'target'), 'upstreamTag': 'v0.7.0', 'commit': 'fixture', 'artifacts': artifacts}
            (source / '.git/artcraft-verified.json').write_text(json.dumps(report))
            prefix = root / 'new-prefix'
            with contextlib.redirect_stdout(io.StringIO()):
                install(source, prefix)
            config = json.loads((prefix / 'plugin/.mcp.json').read_text())
            self.assertEqual(config['mcpServers']['cadcraft']['command'], str(prefix / 'launchers/artcraft-cadcraft-mcp'))
            for path in (prefix / 'launchers').iterdir():
                subprocess.run(['bash', '-n', str(path)], check=True)
            output = subprocess.check_output([str(prefix / 'launchers/artcraft-cadcraft-mcp')], text=True)
            self.assertIn('mcp\n--connect\n127.0.0.1:7981', output)
            with self.assertRaises(ValueError):
                install(source, prefix)
            (root / 'cadcraft').write_text('tampered')
            with self.assertRaises(ValueError):
                install(source, root / 'different-prefix')
            self.assertFalse((root / 'different-prefix').exists())


if __name__ == '__main__':
    unittest.main()
