"""Exercise generated layouts, literal arguments, and refusal of lossy/unsafe packaging."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/desktop-mcp-copilot/scripts/package_agent.py'
spec = importlib.util.spec_from_file_location('package_agent', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackageAgentTests(unittest.TestCase):
    def inputs(self, d, server=None):
        config = d / 'input.json'
        config.write_text(json.dumps({'mcpServers': {'test-app': server or {
            'command': 'C:\\Program Files\\工具\\mcp.exe',
            'args': ['--connect', '127.0.0.1:12345', 'a b', '$(never-execute)', '中文'],
        }}}), encoding='utf-8')
        skill = d / 'operation.md'
        skill.write_text('---\nname: test-app\ndescription: 操作测试软件\n---\n先读取文档，再回读验证。\n', encoding='utf-8')
        return config, skill

    def test_all_profiles_preserve_arguments_and_skills_without_installing(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            config, skill = self.inputs(d)
            original = config.read_bytes()
            for client, (cp, sp) in module.LAYOUTS.items():
                with self.subTest(client=client):
                    out = d / client
                    result = module.package(client, 'test-app', config, skill, out)
                    generated = json.loads((out / cp).read_text())['mcpServers']['test-app']
                    expected = json.loads(original)['mcpServers']['test-app']
                    self.assertEqual(generated, {'type': 'stdio', **expected})
                    self.assertEqual((out / sp / 'test-app/SKILL.md').read_bytes(), skill.read_bytes())
                    self.assertFalse(result['installed'])
                    self.assertFalse(result['clientLoadVerified'])
                    self.assertEqual(result, json.loads((out / 'bundle.json').read_text()))
                    self.assertTrue((out / 'INSTALL.md').is_file())
            self.assertEqual(config.read_bytes(), original)

    def test_existing_directory_and_symlink_are_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            config, skill = self.inputs(d)
            out = d / 'existing'
            out.mkdir()
            marker = out / 'keep'
            marker.write_text('original')
            link = d / 'link'
            link.symlink_to(out, target_is_directory=True)
            for target in (out, link):
                with self.assertRaisesRegex(ValueError, 'already exists'):
                    module.package('cursor', 'test-app', config, skill, target)
            self.assertEqual(marker.read_text(), 'original')
            self.assertTrue(link.is_symlink())

    def test_lossy_transport_auth_and_interpolation_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            for server in ({'url': 'https://example.com/mcp'},
                           {'type': 'http', 'command': 'server'},
                           {'command': 'server', 'env': {'TOKEN': 'must-not-be-copied'}},
                           {'command': 'server', 'cwd': '/app'},
                           {'command': '${env:EXEC}'},
                           {'command': 'server', 'args': 'not an array'},
                           {'command': 'server', 'args': [1]}):
                config, skill = self.inputs(d, server)
                with self.assertRaises(ValueError):
                    module.package('claude-code', 'test-app', config, skill, d / 'rejected')
                self.assertFalse((d / 'rejected').exists())

    def test_wrong_identity_or_incomplete_skill_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            config, skill = self.inputs(d)
            for bad in ('---\nname: other\ndescription: test\n---\n',
                        '---\nname: test-app\n---\n',
                        '---\nname: test-app\ndescription: test\n---\n[read](references/tool.md)',
                        '---\nname: test-app\ndescription: test\n---\n[TODO: replace]'):
                skill.write_text(bad)
                with self.assertRaises(ValueError):
                    module.package('generic', 'test-app', config, skill, d / 'rejected')
                self.assertFalse((d / 'rejected').exists())
            config.write_text('{"mcpServers":{"other":{"command":"server"}}}')
            with self.assertRaises(ValueError):
                module.package('cursor', 'test-app', config, skill, d / 'rejected')

    def test_cli_does_not_launch_server_and_errors_are_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            marker = d / 'launched'
            config, skill = self.inputs(d, {'command': sys.executable,
                'args': ['-c', f'from pathlib import Path; Path({str(marker)!r}).touch()']})
            args = [sys.executable, str(SCRIPT), '--client', 'cursor', '--name', 'test-app',
                    '--mcp-config', str(config), '--skill-file', str(skill), '--output', str(d / 'out')]
            result = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)['mcpVerified'])
            self.assertFalse(marker.exists())
            again = subprocess.run(args, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)
            self.assertFalse(json.loads(again.stderr)['ok'])


if __name__ == '__main__':
    unittest.main()
