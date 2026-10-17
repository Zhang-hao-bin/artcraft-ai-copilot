#!/usr/bin/env python3
"""Maintain the local CADCraft Copilot overlay on upstream stable tags. No background schedule."""
import argparse
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(os.environ.get('ARTCRAFT_COPILOT_HOME', str(Path.home() / '.local/share/artcraft-ai-copilot'))).expanduser().resolve()
CONFIG = ROOT / 'updater/config.json'
ACTIVE = ROOT / 'updater/active.json'
UPDATES = ROOT / 'updates'
BINARY = ROOT / 'cadcraft'
WINDOW_LOCK = ROOT / 'window.lock'
PREFS = Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local/share'))) / 'io.github.artcraft-copilot.cadcraft/app.ron'
UPSTREAM = 'https://github.com/storytold/cadcraft.git'


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write('\n')
        os.replace(tmp, path)
    finally:
        if Path(tmp).exists():
            Path(tmp).unlink()


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def environment(config):
    env = os.environ.copy()
    toolchain = Path(config['toolchain'])
    env['PATH'] = str(toolchain) + os.pathsep + env.get('PATH', '')
    env['RUSTC'] = str(toolchain / 'rustc')
    env['RUSTDOC'] = str(toolchain / 'rustdoc')
    env['CARGO_TARGET_DIR'] = config['target']
    env.setdefault('NO_PROXY', '127.0.0.1,localhost,::1')
    return env


def command(argv, cwd, env=None, log=None, timeout=90):
    if log:
        with log.open('ab') as f:
            f.write(('\n' + ' '.join(map(str, argv)) + '\n').encode())
            f.flush()
            result = subprocess.run(argv, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
        if result.returncode:
            raise RuntimeError(f'命令失败 ({result.returncode})，详见 {log}')
        return b''
    return subprocess.check_output(argv, cwd=cwd, env=env, stderr=subprocess.PIPE, timeout=timeout)


def latest(env):
    output = command(['git', 'ls-remote', '--tags', '--refs', UPSTREAM], ROOT, env).decode()
    tags = []
    for line in output.splitlines():
        match = re.fullmatch(r'([0-9a-f]{40,64})\s+refs/tags/v(\d+)\.(\d+)\.(\d+)', line)
        if match:
            sha, *version = match.groups()
            tags.append((tuple(map(int, version)), 'v' + '.'.join(version), sha))
    if not tags:
        raise RuntimeError('上游没有可识别的稳定版本标签')
    _, tag, sha = max(tags)
    return tag, sha


def changed_paths(source):
    tracked = command(['git', 'diff', '--name-only', '-z', 'HEAD'], source).split(b'\0')
    untracked = command(['git', 'ls-files', '--others', '--exclude-standard', '-z'], source).split(b'\0')
    return sorted({p.decode() for p in tracked + untracked if p})


def snapshot(source, dest):
    if command(['git', 'ls-files', '--unmerged'], source):
        raise RuntimeError('源码中仍有未解决的 Git 合并冲突；请先解决并 git add')
    paths = changed_paths(source)
    patch = dest / 'copilot.patch'
    with tempfile.TemporaryDirectory(prefix='cadcraft-overlay-') as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / 'index'))
        command(['git', 'read-tree', 'HEAD'], source, env)
        if paths:
            command(['git', 'add', '--', *paths], source, env)
        patch.write_bytes(command(['git', 'diff', '--cached', '--binary', 'HEAD'], source, env))
    write(dest / 'overlay.json', {'source': str(source), 'base': command(['git', 'rev-parse', 'HEAD'], source).decode().strip(), 'paths': paths, 'sha256': digest(patch)})
    return patch


def fingerprint(source):
    h = hashlib.sha256(command(['git', 'rev-parse', 'HEAD'], source))
    h.update(command(['git', 'diff', '--binary', 'HEAD'], source))
    for path in changed_paths(source):
        p = source / path
        h.update(path.encode())
        if p.is_symlink():
            h.update(os.readlink(p).encode())
        elif p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def state_path(source):
    source = source.resolve()
    if not source.is_relative_to(UPDATES.resolve()) or not (source / '.git').exists():
        raise RuntimeError('构建目录必须是 updates 下独立的 Git 工作目录')
    return source / '.git/copilot-update.json'


def prepare(config, env, tag, sha):
    source = Path(config['source'])
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dest = UPDATES / f'{tag}-{stamp}-{uuid.uuid4().hex[:6]}'
    dest.mkdir(parents=True)
    patch = snapshot(source, dest)
    stage = dest / 'source'
    log = dest / 'prepare.log'
    command(['git', 'clone', '--no-local', '--no-checkout', str(source), str(stage)], ROOT, env, log)
    command(['git', 'remote', 'set-url', 'origin', UPSTREAM], stage, env, log)
    command(['git', 'fetch', '--depth', '1', 'origin', 'tag', tag], stage, env, log)
    actual = command(['git', 'rev-parse', 'refs/tags/' + tag], stage, env).decode().strip()
    if actual != sha:
        raise RuntimeError('标签在检查和下载之间发生变化，保留旧版并停止更新')
    command(['git', 'checkout', '--detach', tag], stage, env, log)
    state = {'tag': tag, 'tagObject': sha, 'commit': command(['git', 'rev-parse', 'HEAD'], stage).decode().strip(), 'stage': 'prepared', 'logs': str(dest), 'source': str(stage), 'originalSource': str(source)}
    write(state_path(stage), state)
    write(ROOT / 'updater/pending.json', {'source': str(stage)})
    try:
        command(['git', 'apply', '--3way', str(patch)], stage, env, log)
    except RuntimeError:
        state['stage'] = 'conflict'
        write(state_path(stage), state)
        raise RuntimeError(f'定制补丁与上游有冲突，旧版未改变。请在 {stage} 解决冲突，随后运行 artcraft-cadcraft-update build --source "{stage}"')
    print(f'已合并 {tag}：{stage}', flush=True)
    return stage


def build(config, env, source):
    path = state_path(source)
    state = read(path)
    if command(['git', 'ls-files', '--unmerged'], source):
        raise RuntimeError('仍有未解决的冲突，拒绝构建或安装')
    before = fingerprint(source)
    state['stage'] = 'building'
    write(path, state)
    logs = Path(state['logs'])
    profile = ['--config', 'profile.dev.package."*".opt-level=0', '--config', 'profile.dev.debug=0', '--config', 'profile.dev.incremental=false']
    common = ['--locked', '-j6', *profile]
    gates = [
        ('fmt', ['cargo', 'fmt', '--all', '--', '--check']),
        ('clippy', ['cargo', 'clippy', '-p', 'cadcraft-ui-egui', '-p', 'cadcraft', '--all-targets', *common, '--', '--no-deps', '-D', 'warnings', '-A', 'clippy::collapsible_match', '-A', 'clippy::nonminimal_bool']),
        ('tests', ['cargo', 'test', '--no-fail-fast', '-p', 'cadcraft-ui-egui', *common]),
        ('wasm', ['cargo', 'check', '-p', 'cadcraft-ui-egui', '--target', 'wasm32-unknown-unknown', *common]),
        ('build', ['cargo', 'build', '-p', 'cadcraft', *common]),
    ]
    try:
        for name, argv in gates:
            print(f'正在执行 {name}，日志：{logs / (name + ".log")}', flush=True)
            command(argv, source, env, logs / (name + '.log'), timeout=3600)
        if fingerprint(source) != before:
            raise RuntimeError('检查期间源码发生变化，拒绝安装，请重新检查')
        artifact = logs / 'cadcraft-verified'
        shutil.copy2(Path(config['target']) / 'debug/cadcraft', artifact)
        command(['strip', str(artifact)], source, env)
        state.update(stage='verified', fingerprint=before, artifact=str(artifact), sha256=digest(artifact))
        write(path, state)
        print(f'全部检查通过：{artifact}', flush=True)
    except Exception:
        state['stage'] = 'failed'
        write(path, state)
        raise
    return state


@contextlib.contextmanager
def idle_window():
    WINDOW_LOCK.parent.mkdir(parents=True, exist_ok=True)
    with WINDOW_LOCK.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('CADCraft 正在运行。请自行保存并退出后再安装；不会关闭任何窗口') from error
        for entry in Path('/proc').iterdir():
            if entry.name.isdigit():
                try:
                    exe = os.readlink(entry / 'exe')
                except OSError:
                    continue
                if exe.removesuffix(' (deleted)') == str(BINARY):
                    raise RuntimeError('检测到运行中的 Copilot 进程，请保存并退出后再安装')
        yield


def replace_binary(artifact):
    tmp = BINARY.with_name('cadcraft.update-' + uuid.uuid4().hex[:8])
    try:
        shutil.copy2(artifact, tmp)
        os.replace(tmp, BINARY)
    finally:
        if tmp.exists():
            tmp.unlink()


def install(config, source):
    state = read(state_path(source))
    if state['stage'] != 'verified' or state.get('fingerprint') != fingerprint(source):
        raise RuntimeError('没有与当前源码匹配的通过检查的构建，请先 build')
    artifact = Path(state['artifact'])
    if digest(artifact) != state.get('sha256'):
        raise RuntimeError('构建文件校验失败，保留旧版')
    with idle_window():
        backup = UPDATES / ('installed-backup-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6])
        backup.mkdir(mode=0o700)
        shutil.copy2(BINARY, backup / 'cadcraft')
        old_active = read(ACTIVE) if ACTIVE.exists() else {}
        write(backup / 'metadata.json', {'config': config, 'active': old_active, 'binarySha256': digest(BINARY)})
        if PREFS.exists():
            shutil.copy2(PREFS, backup / 'app.ron')
        try:
            replace_binary(artifact)
            write(ACTIVE, {**state, 'installedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'previousBackup': str(backup)})
            write(CONFIG, {**config, 'source': str(source.resolve())})
        except Exception:
            replace_binary(backup / 'cadcraft')
            write(ACTIVE, old_active)
            write(CONFIG, config)
            raise
    print(f'已安装 {state["tag"]} + Copilot，下次启动生效。回退备份：{backup}')


def rollback(config):
    active = read(ACTIVE)
    backup = Path(active.get('previousBackup', '')).resolve()
    if not backup.is_relative_to(UPDATES.resolve()) or not (backup / 'metadata.json').is_file():
        raise RuntimeError('没有可用的回退版本')
    metadata = read(backup / 'metadata.json')
    if digest(backup / 'cadcraft') != metadata['binarySha256']:
        raise RuntimeError('回退文件校验失败')
    with idle_window():
        # Keep current chat/preferences; a binary rollback must not silently overwrite newer work.
        replace_binary(backup / 'cadcraft')
        write(ACTIVE, metadata['active'])
        write(CONFIG, metadata['config'])
    print('已回退程序和版本记录，现有图纸及聊天设置保持原样')


def main():
    parser = argparse.ArgumentParser(description='为 CADCraft Copilot 跟进上游稳定版；不关闭窗口、不创建定时任务。')
    parser.add_argument('action', nargs='?', default='check', choices=['check', 'prepare', 'build', 'install', 'update', 'rollback', 'status'])
    parser.add_argument('--source', type=Path, help='build/install 使用的独立源码目录；默认使用待更新目录')
    args = parser.parse_args()
    try:
        config = read(CONFIG)
        env = environment(config)
        if args.action == 'status':
            print(json.dumps({'active': read(ACTIVE) if ACTIVE.exists() else None, 'source': config['source']}, ensure_ascii=False, indent=2))
            return 0
        with (ROOT / 'updater/operation.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError('已有更新操作在运行') from error
            if args.action in ('check', 'prepare', 'update'):
                tag, sha = latest(env)
                active = read(ACTIVE) if ACTIVE.exists() else {}
                same = active.get('tag') == tag and active.get('tagObject') == sha and BINARY.is_file() and active.get('sha256') == digest(BINARY)
                if args.action == 'check':
                    print(json.dumps({'installed': active.get('tag'), 'latestStable': tag, 'updateAvailable': not same}, ensure_ascii=False, indent=2))
                    return 0
                if args.action == 'update' and same:
                    print(f'已跟进当前最新稳定版 {tag}')
                    return 0
                source = prepare(config, env, tag, sha)
                if args.action == 'prepare':
                    return 0
                build(config, env, source)
                install(config, source)
            elif args.action == 'rollback':
                rollback(config)
            else:
                source = (args.source or Path(read(ROOT / 'updater/pending.json')['source'])).resolve()
                if args.action == 'build':
                    build(config, env, source)
                else:
                    install(config, source)
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'更新未完成：{error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
