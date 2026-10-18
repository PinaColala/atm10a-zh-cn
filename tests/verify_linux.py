"""SPDX-License-Identifier: GPL-3.0-or-later. Actual Linux offline integration tests."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[1]
PKG = R / 'dist/atm10a-zh_cn-server-linux-r2.1-atm0.7.1'
sys.path.insert(0, str(PKG))
from snbt import parse, language_bytes


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text('utf-8-sig'))


def snapshot(root):
    return {p.relative_to(root).as_posix(): (sha(p), stat.S_IMODE(p.stat().st_mode))
            for p in root.rglob('*') if p.is_file() and '.atm10a-zh-linux-backups' not in p.parts}


def main():
    assert sys.platform == 'linux', 'Run these tests on Linux, not a Windows compatibility shim'
    ap = argparse.ArgumentParser()
    ap.add_argument('--reference', type=Path, default=R / '.test-inputs/overrides')
    ap.add_argument('--mod-dir', type=Path, default=R / '.test-inputs/mods')
    args = ap.parse_args()
    manifest = load(PKG / 'manifest.json')
    jars = {sha(p): p for p in args.mod_dir.glob('*.jar')}
    runs = R / '.test-runs'
    runs.mkdir(exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='Linux 中文 空格 ', dir=str(runs)))
    for name in ('config', 'kubejs'):
        shutil.copytree(args.reference / name, root / name)
    (root / 'mods').mkdir()
    for guard in manifest['requiredMods']:
        shutil.copyfile(jars[guard['sha256']], root / guard['path'])
    (root / 'server.properties').write_text('level-name=world\n', encoding='utf8')
    (root / 'world').mkdir()
    (root / 'world/level.dat').write_bytes(b'WORLD SENTINEL; NOT A MINECRAFT WORLD')
    (root / 'world/session.lock').write_bytes(b'\xe2\x98\x83')
    (root / 'options.txt').write_bytes(b'CLIENT OPTIONS MUST NOT BE TOUCHED')
    merged_file = root / 'config/ftbquests/quests/lang/zh_cn.snbt'
    original_zh = parse(merged_file.read_text('utf-8-sig'))
    original_zh['custom.test.title'] = '"保留自定义译文"'
    merged_file.write_bytes(language_bytes(original_zh))
    script = root / manifest['scripts'][0]['path']
    script.chmod(0o640)
    checks = []

    def run(flag='', ok=True):
        cmd = ['sh', str(PKG / 'install.sh')]
        if flag:
            cmd.append(flag)
        cmd.append(str(root))
        proc = subprocess.run(cmd, capture_output=True, text=True)
        assert (proc.returncode == 0) == ok, (cmd, proc.stdout, proc.stderr)
        return proc

    def passed(name):
        checks.append(name)
        print('PASS ' + name, flush=True)

    original = snapshot(root)
    run('--check')
    assert snapshot(root) == original
    passed('check writes no server files; shell handles Unicode and spaces')
    mutations = [
        (root / 'config/bcc-common.toml', lambda b: b.replace(b'0.7.1', b'0.7.2')),
        (script, lambda b: b + b'\n// custom edit\n'),
        (root / manifest['requiredMods'][0]['path'], lambda b: b + b'tamper'),
        (root / manifest['questStructure'][0]['path'], lambda b: b.replace(b'id:', b'changed_id:', 1)),
    ]
    for path, mutate in mutations:
        data = path.read_bytes()
        path.write_bytes(mutate(data))
        before = snapshot(root)
        run(ok=False)
        assert snapshot(root) == before
        path.write_bytes(data)
    passed('wrong version, custom script, wrong mod and changed quest rejected without writes')
    script.chmod(0o440)
    before = snapshot(root)
    run(ok=False)
    assert snapshot(root) == before
    script.chmod(0o640)
    passed('read-only destination rejected before backup or writes')
    mod = root / manifest['requiredMods'][0]['path']
    moved = mod.with_suffix('.test-original')
    mod.rename(moved)
    mod.symlink_to(moved)
    run(ok=False)
    mod.unlink()
    moved.rename(mod)
    passed('symlink destination rejected')
    subprocess.run(['javac', '-d', str(runs), str(R / 'tests/LockWorld.java')], check=True)
    holder = subprocess.Popen(['java', '-cp', str(runs), 'LockWorld', str(root / 'world/session.lock')],
                              cwd=str(runs), stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline().strip() == 'LOCKED'
        before = snapshot(root)
        result = run(ok=False)
        assert 'running' in result.stderr and snapshot(root) == before
    finally:
        holder.communicate('\n', timeout=10)
    passed('real Java FileChannel world lock prevents installation')
    run()
    installed = snapshot(root)
    state_path = sorted((root / '.atm10a-zh-linux-backups').glob('*/backup.json'))[-1]
    state = load(state_path)
    for entry in state['files']:
        path = root / entry['path']
        assert (sha(path) if path.exists() else None) == entry['after'], entry['path']
    for entry in manifest['scripts']:
        assert sha(root / entry['path']) == entry['resultSha256']
    displays = 0
    for patch in manifest['dataPatches']:
        if patch['source'] == 'file':
            baseline = load(args.reference / patch['path'])
        else:
            with zipfile.ZipFile(root / patch['jar']) as jar:
                baseline = json.loads(jar.read(patch['entry']))
        expected = copy.deepcopy(baseline)
        for edit in patch['edits']:
            node = expected
            for key in edit['path'][:-1]:
                node = node[key]
            node[edit['path'][-1]] = edit['to']
            displays += 1
        assert load(root / patch['path']) == expected, patch['path']
    for guard in manifest['questStructure']:
        assert installed[guard['path']] == original[guard['path']]
    translated = parse(merged_file.read_text('utf8'))
    assert translated['custom.test.title'] == '"保留自定义译文"'
    expected_keys = set()
    for path in (PKG / 'payload/config/ftbquests/quests/lang/zh_cn').rglob('*.snbt'):
        for key, value in parse(path.read_text('utf-8-sig')).items():
            assert translated[key] == value
            expected_keys.add(key)
    assert not list((root / 'config/ftbquests/quests/lang/zh_cn').rglob('*.snbt'))
    assert installed['options.txt'] == original['options.txt']
    assert installed['world/level.dat'] == original['world/level.dat']
    assert stat.S_IMODE(script.stat().st_mode) == 0o640
    passed('install hashes; 65 data files preserve non-display values; merged quest text; modes and world preserved')
    run()
    assert snapshot(root) == installed
    passed('repeat install is a no-op')
    data = script.read_bytes()
    script.write_bytes(data + b'\n// user change\n')
    before = snapshot(root)
    run('--restore', ok=False)
    assert snapshot(root) == before
    script.write_bytes(data)
    backup = state_path.parent / 'originals' / next(e['path'] for e in state['files'] if e['before'] is not None)
    data = backup.read_bytes()
    backup.write_bytes(b'tampered backup')
    run('--restore', ok=False)
    assert snapshot(root) == installed
    backup.write_bytes(data)
    passed('restore rejects user edits and corrupted backups')
    run('--restore')
    assert snapshot(root) == original
    passed('restore is byte-exact and preserves original modes')
    spec = importlib.util.spec_from_file_location('installer_under_test', PKG / 'install.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    plan = module.plan_install(root, manifest)
    real_write = module.atomic_write
    calls = 0

    def fail_once(path, data, mode=0o644):
        nonlocal calls
        if root in path.parents and '.atm10a-zh-linux-backups' not in path.parts:
            calls += 1
            if calls == 2:
                raise OSError('Injected write failure')
        return real_write(path, data, mode)

    module.atomic_write = fail_once
    try:
        module.install(root, manifest, plan)
        raise AssertionError('Expected write failure')
    except OSError as error:
        assert 'Injected' in str(error)
    assert snapshot(root) == original
    passed('mid-install write failure rolls back already-written files')
    # Reproduce FTB Quests' post-launch split-to-merged layout and reordered chapter keys.
    lang_dir = root / 'config/ftbquests/quests/lang/zh_cn'
    merged = parse(merged_file.read_text('utf8'))
    for path in sorted(lang_dir.rglob('*.snbt')):
        merged.update(parse(path.read_text('utf-8-sig')))
        path.rename(path.with_suffix('.snbt_merged'))
    merged_file.write_bytes(language_bytes(merged))
    chapter = root / 'config/ftbquests/quests/chapters/aeronautics.snbt'
    value = parse(chapter.read_text('utf8'))
    text = chapter.read_text('utf8')
    import re
    text = re.sub(r'(?m)^\torder_index: .*$', '\torder_index: 999', text)
    chapter.write_text(text, encoding='utf8')
    merged_before = snapshot(root)
    run('--check')
    run()
    assert parse(merged_file.read_text('utf8'))['custom.test.title'] == '"保留自定义译文"'
    run('--restore')
    assert snapshot(root) == merged_before
    passed('post-launch merged SNBT and changed chapter order install and restore')
    report = dict(platform=platform.platform(), python=platform.python_version(), checks=checks,
                  result='passed', translatedQuestKeys=len(expected_keys), dataFiles=65, displayEdits=displays,
                  actualJavaFileLockTest=True, gameStarted=False, cloudServerAccessed=False)
    (R / 'reports/linux-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
