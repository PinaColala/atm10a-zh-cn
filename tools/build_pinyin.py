"""SPDX-License-Identifier: GPL-3.0-or-later. Optional client addon, independent of translation backups."""
import hashlib
from pathlib import Path
import shutil
import zipfile
R=Path(__file__).resolve().parents[1]
OUT=R/'dist/atm10a-client-pinyin-4.5.29'

def copy_addon(out):
    shutil.copytree(R/'optional/pinyin',out,dirs_exist_ok=True)
    (out/'install.ps1').write_text((R/'optional/pinyin/install.ps1').read_text('utf8'),encoding='utf-8-sig',newline='\r\n')
    shutil.copyfile(R/'LICENSE-GPL-3.0',out/'LICENSE-installer-GPL-3.0.txt')
    for name,action in [('install','Install'),('check','Check'),('remove','Remove')]:
        text='@echo off\nsetlocal\nchcp 65001 >nul\n"%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Action '+action+' %*\nset "result=%errorlevel%"\npause\nexit /b %result%\n'
        (out/(name+'-pinyin-windows.bat')).write_text(text,encoding='ascii',newline='\r\n')

if __name__=='__main__':
    copy_addon(OUT)
    dest=OUT.parent/(OUT.name+'.zip')
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(OUT.parent).as_posix())
    (OUT.parent/'SHA256SUMS-pinyin.txt').write_text(hashlib.sha256(dest.read_bytes()).hexdigest()+'  '+dest.name+'\n',encoding='ascii')
    print(dest.name)
