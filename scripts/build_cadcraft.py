#!/usr/bin/env python3
"""Prepare the pinned CADCraft overlay and verify/build it without installing anything."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
UPSTREAM = 'https://github.com/storytold/cadcraft.git'
TAG = 'v0.7.0'
COMMIT = 'fc4e98315a8d771b5ab832f0ade0b5e7b106df7f'
PATCH = PROJECT / 'patches/cadcraft-v0.7.0-copilot.patch'


def run(args, cwd, env=None, timeout=3600):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(args, cwd=cwd, env=env, check=True, timeout=timeout)


def capture(args, cwd):
    return subprocess.check_output(args, cwd=cwd).decode().strip()


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def fingerprint(source):
    h = hashlib.sha256(capture(['git', 'rev-parse', 'HEAD'], source).encode())
    h.update(subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=source))
    for name in subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=source).split(b'\0'):
        if name:
            path = source / name.decode()
            h.update(name)
            h.update(path.read_bytes() if not path.is_symlink() else os.readlink(path).encode())
    return h.hexdigest()


def prepare(source):
    if source.exists():
        raise ValueError('Source exists; use verify to check it, or choose a NEW --source directory')
    source.parent.mkdir(parents=True, exist_ok=True)
    run(['git', 'clone', '--depth', '1', '--branch', TAG, UPSTREAM, str(source)], PROJECT, timeout=180)
    if capture(['git', 'rev-parse', 'HEAD'], source) != COMMIT:
        raise ValueError('Upstream tag does not match the reviewed commit; stopped')
    run(['git', 'apply', '--check', str(PATCH)], source)
    run(['git', 'apply', '--index', str(PATCH)], source)
    print('Prepared source:', source)


def verify(source, target):
    if capture(['git', 'rev-parse', 'HEAD'], source) != COMMIT:
        raise ValueError('This patch release supports only the pinned CADCraft commit')
    if subprocess.check_output(['git', 'ls-files', '--unmerged'], cwd=source):
        raise ValueError('Resolve Git conflicts before verifying')
    env = dict(os.environ, CARGO_TARGET_DIR=str(target))
    before = fingerprint(source)
    flags = ['--locked', '-j6', '--config', 'profile.dev.package."*".opt-level=0', '--config', 'profile.dev.debug=0', '--config', 'profile.dev.incremental=false']
    checks = [
        ['cargo', 'fmt', '--all', '--', '--check'],
        ['cargo', 'clippy', '-p', 'cadcraft-ui-egui', '-p', 'cadcraft', '--all-targets', *flags, '--', '--no-deps', '-D', 'warnings', '-A', 'clippy::collapsible_match', '-A', 'clippy::nonminimal_bool'],
        ['cargo', 'test', '--no-fail-fast', '-p', 'cadcraft-ui-egui', *flags],
        ['cargo', 'check', '-p', 'cadcraft-ui-egui', '--target', 'wasm32-unknown-unknown', *flags],
        ['cargo', 'build', '-p', 'cadcraft', '-p', 'cadcraft-cli', *flags],
    ]
    for args in checks:
        run(args, source, env)
    if fingerprint(source) != before:
        raise ValueError('Source changed during verification; verify again before installing')
    artifacts = {}
    for name in ('cadcraft', 'cadcraft-cli'):
        binary = target / 'debug' / name
        if not binary.is_file():
            raise ValueError('Missing build artifact: ' + str(binary))
        artifacts[name] = {'path': str(binary), 'sha256': sha(binary)}
    report = {'upstreamTag': TAG, 'commit': COMMIT, 'source': str(source), 'target': str(target), 'sourceFingerprint': before, 'artifacts': artifacts, 'checksPassed': True, 'toolchainBin': str(Path(capture([env.get('RUSTC', 'rustc'), '--print', 'sysroot'], source)) / 'bin')}
    (source / '.git/artcraft-verified.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Verified. Nothing installed. Run scripts/install_local.py separately.')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'verify'])
    parser.add_argument('--source', type=Path, default=PROJECT / '.work/cadcraft')
    parser.add_argument('--target-dir', type=Path, default=PROJECT / '.work/target')
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            prepare(args.source.resolve())
        else:
            verify(args.source.resolve(), args.target_dir.resolve())
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print('Stopped:', error, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
