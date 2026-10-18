"""SPDX-License-Identifier: GPL-3.0-or-later. Build a separate Linux server release."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist/atm10a-zh_cn-server-linux-r2.1-atm0.7.1'


def main():
    payload = OUT / 'payload'
    payload.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'src/common/files', payload, dirs_exist_ok=True)
    (payload / 'mods').mkdir(exist_ok=True)
    shutil.copyfile(ROOT / 'third_party/vaultpatcher/vaultpatcher.jar', payload / 'mods/vaultpatcher.jar')
    shutil.copyfile(ROOT / 'third_party/vaultpatcher/LICENSE', payload / 'mods/LICENSE-vaultpatcher.txt')
    shutil.copytree(ROOT / 'third_party', OUT / 'third_party', dirs_exist_ok=True)
    guards = json.loads((ROOT / 'src/guards.json').read_text('utf-8-sig'))
    manifest = dict(format=2, side='server', version='0.7.1', release='r2.1-linux',
                    files=[dict(path=p.relative_to(payload).as_posix(), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                           for p in sorted(payload.rglob('*')) if p.is_file()],
                    scripts=json.loads((ROOT / 'src/server/script-patches.json').read_text('utf-8-sig')),
                    dataPatches=json.loads((ROOT / 'src/common/data-patches.json').read_text('utf-8-sig')),
                    requiredMods=guards['requiredMods'],
                    questStructure=json.loads((ROOT / 'src/server/linux-quest-guards.json').read_text('utf8')))
    (OUT / 'manifest.json').write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2)+'\n').encode('utf8'))
    for source, target in [('install-linux.sh', 'install.sh'), ('install-linux.py', 'install.py'), ('snbt.py', 'snbt.py')]:
        (OUT / target).write_bytes((ROOT / 'installer' / source).read_text('utf8').encode('utf8'))
    for name in ['LICENSE', 'LICENSE-GPL-3.0', 'LICENSE-UPSTREAM', 'CREDITS.txt']:
        shutil.copyfile(ROOT / name, OUT / name)
    shutil.copyfile(ROOT / 'docs/LINUX.md', OUT / 'README-Linux.md')
    shutil.copytree(ROOT / 'reports', OUT / 'reports', dirs_exist_ok=True)
    files = sorted(p for p in OUT.rglob('*') if p.is_file())
    zip_path = OUT.parent / (OUT.name + '.zip')
    tar_path = OUT.parent / (OUT.name + '.tar.gz')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(OUT.parent).as_posix(), (2026, 10, 17, 0, 0, 0))
            info.create_system = 3
            info.external_attr = ((0o100755 if path.name == 'install.sh' else 0o100644) << 16)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    with tar_path.open('wb') as output, gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=1792195200) as compressed, tarfile.open(fileobj=compressed, mode='w') as archive:
        for path in files:
            data = path.read_bytes()
            info = tarfile.TarInfo(path.relative_to(OUT.parent).as_posix())
            info.size = len(data)
            info.mode = 0o755 if path.name == 'install.sh' else 0o644
            info.mtime = 1792195200
            archive.addfile(info, io.BytesIO(data))
    (OUT.parent / 'SHA256SUMS-linux.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in (zip_path, tar_path)), encoding='ascii')
    print('Built Linux server ZIP and tar.gz:', OUT.name)


if __name__ == '__main__':
    main()
