"""SPDX-License-Identifier: GPL-3.0-or-later. Python 3.10+, standard library only."""
import pathlib,json,zipfile,hashlib,shutil
from build_pinyin import copy_addon
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def copy_tree(src,dst):shutil.copytree(src,dst,dirs_exist_ok=True)
def archive(src,dest):
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(src.rglob('*')):
   if p.is_file():
    info=zipfile.ZipInfo(p.relative_to(src.parent).as_posix(),(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
for side in ['client','server']:
 out=ROOT/'dist'/f'atm10a-zh_cn-{side}-r2-atm0.7.1';payload=out/'payload';payload.mkdir(parents=True,exist_ok=True)
 copy_tree(ROOT/'src/common/files',payload)
 if (ROOT/'src'/side/'files').exists():copy_tree(ROOT/'src'/side/'files',payload)
 (payload/'mods').mkdir(exist_ok=True);shutil.copyfile(ROOT/'third_party/vaultpatcher/vaultpatcher.jar',payload/'mods/vaultpatcher.jar')
 shutil.copyfile(ROOT/'third_party/vaultpatcher/LICENSE',payload/'mods/LICENSE-vaultpatcher.txt')
 copy_tree(ROOT/'third_party',out/'third_party')
 pack='ATM10A-zh_CN-0.7.1-r2.zip'
 if side=='client':
  copy_addon(out/'optional-pinyin')
  (payload/'resourcepacks').mkdir(exist_ok=True)
  with zipfile.ZipFile(payload/'resourcepacks'/pack,'w',zipfile.ZIP_DEFLATED) as z:
   for p in sorted((ROOT/'src/resourcepack').rglob('*')):
    if p.is_file():
     info=zipfile.ZipInfo(p.relative_to(ROOT/'src/resourcepack').as_posix(),(2026,10,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
 scripts=load(ROOT/'src/server/script-patches.json')
 if side=='client':scripts+=load(ROOT/'src/client/script-patches.json')
 guards=load(ROOT/'src/guards.json')
 manifest={'format':2,'side':side,'version':'0.7.1','release':'r2','resourcePack':pack,
  'files':[{'path':p.relative_to(payload).as_posix(),'sha256':sha(p)} for p in sorted(payload.rglob('*')) if p.is_file()],
  'scripts':scripts,'dataPatches':load(ROOT/'src/common/data-patches.json'),
  'requiredMods':guards['requiredMods'],'questGuards':guards['questGuards'],'imageGuards':guards['imageGuards'] if side=='client' else []}
 dump(out/'manifest.json',manifest)
 (out/'install.ps1').write_text((ROOT/'installer/install.ps1').read_text('utf8'),encoding='utf-8-sig',newline='\r\n')
 for name,action in [('双击安装-Windows.bat','Install'),('install-windows.bat','Install'),('仅检查-Windows.bat','Check'),('还原汉化-Windows.bat','Restore')]:
  bat='@echo off\nsetlocal\nchcp 65001 >nul\n"%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Action '+action+' %*\nset "result=%errorlevel%"\necho.\npause\nexit /b %result%\n'
  (out/name).write_text(bat,encoding='ascii',newline='\r\n')
 for name in ['LICENSE','LICENSE-GPL-3.0','LICENSE-UPSTREAM','CREDITS.txt']:shutil.copyfile(ROOT/name,out/name)
 shutil.copyfile(ROOT/'docs/INSTALL.txt',out/'先读我.txt')
 copy_tree(ROOT/'reports',out/'reports')
 archive(out,out.parent/(out.name+'.zip'))
 print(side,len(manifest['files']),'payload files;',len(scripts),'script patches;',len(manifest['dataPatches']),'data patches')
hashes=[sha(p)+'  '+p.name for p in sorted((ROOT/'dist').glob('*.zip'))]
(ROOT/'dist/SHA256SUMS.txt').write_text('\n'.join(hashes)+'\n',encoding='ascii')
