import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / 'skills/desktop-mcp-copilot/scripts/probe_mcp.py'


class ProbeTests(unittest.TestCase):
    def test_paginated_directory_is_read_only_and_invalid_stdout_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            server = d / 'server.py'
            trace = d / 'trace.jsonl'
            server.write_text('''import json,sys
from pathlib import Path
for line in sys.stdin:
    v=json.loads(line)
    with Path(sys.argv[1]).open('a') as f:f.write(json.dumps(v)+'\\n')
    if 'id' not in v:continue
    if len(sys.argv)>2:print('invalid',flush=True);continue
    if v['method']=='initialize':r={'protocolVersion':'2025-06-18','capabilities':{'tools':{}},'serverInfo':{'name':'fixture','version':'1'}}
    elif v['method']=='tools/list':
        r={'tools':[{'name':'inspect' if 'cursor' not in v['params'] else 'render','inputSchema':{'type':'object'}}]}
        if 'cursor' not in v['params']:r['nextCursor']='second'
    else:raise RuntimeError('Unexpected method')
    print(json.dumps({'jsonrpc':'2.0','id':v['id'],'result':r}),flush=True)
''')
            args = ['python3', str(PROBE), '--timeout', '1', '--', 'python3', str(server), str(trace)]
            result = subprocess.run(args, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['tools'], ['inspect', 'render'])
            methods = {json.loads(line)['method'] for line in trace.read_text().splitlines()}
            self.assertEqual(methods, {'initialize', 'notifications/initialized', 'tools/list'})
            invalid = subprocess.run([*args, 'invalid'], capture_output=True, text=True, timeout=10)
            self.assertEqual(invalid.returncode, 1)


if __name__ == '__main__':
    unittest.main()
