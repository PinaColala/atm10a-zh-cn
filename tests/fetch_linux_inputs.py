"""SPDX-License-Identifier: GPL-3.0-or-later. Fetch checksum-pinned public test inputs."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.test-inputs'
OUT.mkdir(exist_ok=True)
sources = json.loads((ROOT / 'tests/linux-inputs.json').read_text('utf8'))


def fetch(entry, path):
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
        request = urllib.request.Request(entry['url'], headers={'User-Agent': 'ATM10A-translation-offline-tests'})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != entry['sha256']:
            raise ValueError('Download checksum mismatch: ' + path.name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


archive = OUT / 'ATM10AERO-0.7.1.zip'
fetch(sources['pack'], archive)
with zipfile.ZipFile(archive) as pack:
    for name in pack.namelist():
        if name.startswith(('overrides/config/', 'overrides/kubejs/')) and not name.endswith('/'):
            parts = name.split('/')
            if any(p in ('', '..', '.') for p in parts):
                raise ValueError('Unsafe ZIP path')
            path = OUT.joinpath(*parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pack.read(name))
for entry in sources['mods']:
    fetch(entry, OUT / 'mods' / (entry['slug'] + '.jar'))
print('Pinned overrides and 11 target mods downloaded; no game started.')
