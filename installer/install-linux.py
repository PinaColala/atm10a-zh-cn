#!/usr/bin/env python3
"""SPDX-License-Identifier: GPL-3.0-or-later. Linux server installer; Python 3.8+."""
import sys
sys.dont_write_bytecode = True
import argparse
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import tempfile
import uuid
import zipfile
from snbt import parse, structural_hash, language_bytes

PACKAGE = Path(__file__).absolute().parent
BACKUPS = '.atm10a-zh-linux-backups'
LANG = 'config/ftbquests/quests/lang/'


def safe(base, relative):
    if not relative or '\\' in relative or ':' in relative:
        raise ValueError('Invalid relative path: ' + relative)
    parts = relative.split('/')
    if any(p in ('', '.', '..') for p in parts):
        raise ValueError('Invalid relative path: ' + relative)
    path = base.joinpath(*parts)
    for item in [path] + list(path.parents):
        if item.is_symlink():
            raise ValueError('Symlink paths are not supported: ' + str(item))
    return path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hash_file(path):
    if path.exists() and not path.is_file():
        raise ValueError('Expected a regular file: ' + str(path))
    return digest(path.read_bytes()) if path.exists() else None


def load(path):
    return json.loads(path.read_text('utf-8-sig'))


def atomic_write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'wb') as out:
            os.fchmod(out.fileno(), mode)
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save_state(directory, state):
    atomic_write(safe(directory, 'backup.json'),
                 json.dumps(state, ensure_ascii=False, indent=2).encode('utf8'), 0o600)


def writable(path):
    if path.exists() and (not path.is_file() or not path.stat().st_mode & 0o222):
        raise ValueError('File is not writable: ' + str(path))
    parent = path.parent
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir() or not parent.stat().st_mode & 0o222 or not os.access(parent, os.W_OK | os.X_OK):
        raise ValueError('Directory is not writable by this user: ' + str(parent))
    if path.exists() and not os.access(path, os.W_OK):
        raise ValueError('File is not writable by this user: ' + str(path))


@contextlib.contextmanager
def stopped(root):
    import fcntl
    props = safe(root, 'server.properties')
    text = props.read_text('utf8')
    match = re.search(r'^level-name=(.*)$', text, re.M)
    world = match[1].strip() if match else 'world'
    if not world or '\\' in world:
        raise ValueError('Unsupported level-name; use a relative unescaped world directory')
    # Directory flock serializes installer invocations without writing a lock file.
    directory_fd = os.open(str(root), os.O_RDONLY)
    world_lock = None
    try:
        fcntl.flock(directory_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock = safe(root, world + '/session.lock')
        if lock.exists():
            world_lock = lock.open('r+b')
            # Java FileChannel.lock uses POSIX record locks, not BSD flock.
            fcntl.lockf(world_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for process in Path('/proc').glob('[0-9]*'):
            try:
                if (process / 'comm').read_text().strip().startswith('java') and (process / 'cwd').resolve() == root:
                    raise ValueError('Java is running in the server directory; shut down the server first')
            except (PermissionError, FileNotFoundError, ProcessLookupError):
                pass
        yield
    except BlockingIOError:
        raise ValueError('Server/world or another installer is running; shut it down first') from None
    finally:
        if world_lock:
            world_lock.close()
        os.close(directory_fd)


def restore(root, directory, state, rollback=False, applied=None):
    if state['target'] != str(root) or state['side'] != 'server':
        raise ValueError('Backup belongs to a different server path')
    records = state['files'] if applied is None else [f for f in state['files'] if f['path'] in applied]
    for entry in records:
        path = safe(root, entry['path'])
        current = hash_file(path)
        if current not in (entry['before'], entry['after']):
            raise ValueError('File changed after installation; restore stopped: ' + entry['path'])
        if entry['before'] is not None and hash_file(safe(directory, 'originals/' + entry['path'])) != entry['before']:
            raise ValueError('Backup checksum failed: ' + entry['path'])
        writable(path)
    for entry in records:
        path = safe(root, entry['path'])
        if hash_file(path) not in (entry['before'], entry['after']):
            raise ValueError('File changed during restore: ' + entry['path'])
        if entry['before'] is not None:
            atomic_write(path, safe(directory, 'originals/' + entry['path']).read_bytes(), entry['mode'])
        elif path.exists():
            path.unlink()
        if hash_file(path) != entry['before']:
            raise ValueError('Restore checksum failed: ' + entry['path'])
    state['status'] = 'restored'
    save_state(directory, state)


def plan_install(root, manifest):
    text = safe(root, 'config/bcc-common.toml').read_text('utf8')
    if not re.search(r'^\s*modpackName\s*=\s*"ATM10: Aeronautics"\s*$', text, re.M) or not re.search(r'^\s*modpackVersion\s*=\s*"0\.7\.1"\s*$', text, re.M):
        raise ValueError('Only ATM10: Aeronautics 0.7.1 is supported')
    for guard in manifest['requiredMods']:
        if hash_file(safe(root, guard['path'])) != guard['sha256']:
            raise ValueError('Mod version mismatch: ' + guard['path'])
    for path in safe(root, 'mods').iterdir():
        if 'vaultpatcher' in path.name.lower() and path.suffix == '.jar' and path.name != 'vaultpatcher.jar':
            raise ValueError('Remove the duplicate VaultPatcher jar first: ' + path.name)
    known = set()
    for guard in manifest['questStructure']:
        known.add(guard['path'])
        text = safe(root, guard['path']).read_text('utf-8-sig')
        if structural_hash(text) not in guard['accepted']:
            raise ValueError('Quest structure mismatch: ' + guard['path'])
    for path in safe(root, 'config/ftbquests/quests').rglob('*.snbt'):
        relative = path.relative_to(root).as_posix()
        safe(root, relative)
        if '/lang/' not in relative and relative not in known:
            raise ValueError('Unknown quest definition: ' + relative)
    plan = {}
    translated = {}
    for entry in manifest['files']:
        relative = entry['path']
        data = safe(PACKAGE / 'payload', relative).read_bytes()
        if digest(data) != entry['sha256']:
            raise ValueError('Package checksum failed: ' + relative)
        if relative.startswith(LANG + 'zh_cn/'):
            values = parse(data.decode('utf-8-sig'))
            for key, value in values.items():
                if key in translated and translated[key] != value:
                    raise ValueError('Conflicting quest translation: ' + key)
                translated[key] = value
        else:
            safe(root, relative)
            plan[relative] = data
    # FTB Quests may already have merged its split language files on first launch.
    merged_path = safe(root, LANG + 'zh_cn.snbt')
    merged = parse(merged_path.read_text('utf-8-sig')) if merged_path.exists() else {}
    loose = safe(root, LANG + 'zh_cn')
    for path in sorted(loose.rglob('*.snbt')) if loose.exists() else []:
        relative = path.relative_to(root).as_posix()
        merged.update(parse(safe(root, relative).read_text('utf-8-sig')))
        plan[relative] = None  # Backed up individually; never recursively delete.
    merged.update(translated)
    plan[LANG + 'zh_cn.snbt'] = language_bytes(merged)
    for script in manifest['scripts']:
        text = safe(root, script['path']).read_text('utf-8-sig').replace('\r\n', '\n')
        if digest(text.encode('utf8')) != script['resultSha256']:
            if digest(text.encode('utf8')) != script['originalSha256']:
                raise ValueError('Script has custom changes: ' + script['path'])
            for replacement in script['replacements']:
                if text.count(replacement['from']) != replacement['count']:
                    raise ValueError('Script replacement count mismatch')
                text = text.replace(replacement['from'], replacement['to'])
            if digest(text.encode('utf8')) != script['resultSha256']:
                raise ValueError('Script output checksum failed')
        plan[script['path']] = text.encode('utf8')
    for patch in manifest['dataPatches']:
        path = safe(root, patch['path'])
        if path.exists():
            raw = path.read_bytes()
            allowed = (patch['baselineSha256'], patch['r1Sha256'])
        elif patch['source'] == 'file':
            raise ValueError('Missing original data: ' + patch['path'])
        else:
            with zipfile.ZipFile(safe(root, patch['jar'])) as jar:
                raw = jar.read(patch['entry'])
            allowed = (patch['baselineSha256'],)
        if digest(raw) not in allowed:
            raise ValueError('Data has custom changes: ' + patch['path'])
        obj = json.loads(raw.decode('utf-8-sig'))
        for edit in patch['edits']:
            node = obj
            for key in edit['path'][:-1]:
                node = node[key]
            key = edit['path'][-1]
            if node[key] not in (edit['from'], edit['to']):
                raise ValueError('Data translation mismatch: ' + patch['path'])
            node[key] = edit['to']
        plan[patch['path']] = (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf8')
    for relative in plan:
        writable(safe(root, relative))
    return plan


def install(root, manifest, plan):
    backup_root = safe(root, BACKUPS)
    backup_root.mkdir(mode=0o700, exist_ok=True)
    directory = safe(backup_root, datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8])
    directory.mkdir(mode=0o700)
    records = []
    for relative, data in sorted(plan.items()):
        path = safe(root, relative)
        before = hash_file(path)
        mode = stat.S_IMODE(path.stat().st_mode) if before is not None else 0o644
        if before is not None:
            backup = safe(directory, 'originals/' + relative)
            atomic_write(backup, path.read_bytes(), 0o600)
            if hash_file(backup) != before:
                raise ValueError('Backup checksum failed')
        records.append(dict(path=relative, before=before, after=digest(data) if data is not None else None, mode=mode))
    state = dict(schema=1, target=str(root), side='server', release=manifest['release'], status='prepared', files=records)
    save_state(directory, state)
    applied = set()
    try:
        for entry in records:
            path = safe(root, entry['path'])
            if hash_file(path) != entry['before']:
                raise ValueError('File changed during installation: ' + entry['path'])
            data = plan[entry['path']]
            applied.add(entry['path'])
            if data is None:
                if path.exists():
                    path.unlink()
            else:
                atomic_write(path, data, entry['mode'])
            if hash_file(path) != entry['after']:
                raise ValueError('Installed checksum failed')
        state['status'] = 'installed'
        save_state(directory, state)
    except BaseException:
        restore(root, directory, state, rollback=True, applied=applied)
        raise
    print('Installed successfully. Backup: ' + str(directory))


def main():
    if sys.platform != 'linux' or sys.version_info < (3, 8):
        raise ValueError('This installer requires Linux and Python 3.8+')
    parser = argparse.ArgumentParser(description='ATM10A 0.7.1 Linux server Chinese translation. Stop the server first.')
    parser.add_argument('target', type=Path, help='Server directory containing mods, config and server.properties')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--check', action='store_true', help='Validate without writing to the server')
    actions.add_argument('--restore', action='store_true', help='Restore the latest active backup')
    args = parser.parse_args()
    root = Path(os.path.abspath(args.target.expanduser()))
    safe(root, 'mods')
    if not (root / 'mods').is_dir() or root == PACKAGE or PACKAGE in root.parents:
        raise ValueError('Select a server directory, not this package')
    manifest = load(safe(PACKAGE, 'manifest.json'))
    if manifest['side'] != 'server':
        raise ValueError('Only the server package is supported')
    with stopped(root):
        active = []
        backup_root = safe(root, BACKUPS)
        for path in sorted(backup_root.glob('*/backup.json'), reverse=True):
            state = load(safe(root, path.relative_to(root).as_posix()))
            if state['status'] != 'restored':
                active.append((path.parent, state))
        if len(active) > 1:
            raise ValueError('Multiple active backups; inspect before proceeding')
        if args.restore:
            if not active:
                raise ValueError('No active Linux backup found')
            restore(root, *active[0])
            print('Restored successfully. Backup retained.')
        elif active:
            state = active[0][1]
            if state['target'] != str(root) or state['status'] != 'installed' or state['release'] != manifest['release']:
                raise ValueError('Restore the previous/interrupted installation first')
            for entry in state['files']:
                if hash_file(safe(root, entry['path'])) != entry['after']:
                    raise ValueError('Installed file changed: ' + entry['path'])
            print('Already installed; no files changed.')
        else:
            for path in safe(root, '.atm10a-zh-r2-backups').glob('*/backup.json'):
                if load(path)['status'] != 'restored':
                    raise ValueError('Active Windows r2 backup found; restore with its original installer first')
            plan = plan_install(root, manifest)
            if args.check:
                print('Checks passed: {} files; no server files written.'.format(len(plan)))
            else:
                install(root, manifest, plan)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: sys.exit('Interrupted'))
    try:
        main()
    except (Exception, KeyboardInterrupt) as error:
        print('Operation stopped: ' + str(error), file=sys.stderr)
        sys.exit(1)
