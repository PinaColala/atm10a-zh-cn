"""SPDX-License-Identifier: GPL-3.0-or-later. Optional upgrade tests using original r1 packages."""
import argparse,json,os,pathlib,shutil,subprocess,tempfile
from verify import R,load,sha,snap
ap=argparse.ArgumentParser();ap.add_argument('--reference',type=pathlib.Path,required=True);ap.add_argument('--mod-dir',type=pathlib.Path,required=True);ap.add_argument('--r1-client',type=pathlib.Path,required=True);ap.add_argument('--r1-server',type=pathlib.Path,required=True);a=ap.parse_args()
jars={sha(p):p for p in a.mod_dir.glob('*.jar')};report={}
for side,r1 in [('client',a.r1_client),('server',a.r1_server)]:
    pkg=R/'dist'/f'atm10a-zh_cn-{side}-r2-atm0.7.1';m=load(pkg/'manifest.json');root=pathlib.Path(tempfile.mkdtemp(prefix='r1 upgrade '+side+' ',dir=R/'.test-runs'))
    for name in ['config','kubejs']:shutil.copytree(a.reference/name,root/name)
    (root/'mods').mkdir()
    for mod in m['requiredMods']:shutil.copyfile(jars[mod['sha256']],root/mod['path'])
    shutil.copytree(r1/'payload',root,dirs_exist_ok=True)
    (root/'server.properties').write_text('level-name=world\n',encoding='utf8')
    (root/'options.txt').write_text('lang:zh_cn\nresourcePacks:["vanilla","file/ATM10A-zh_CN-0.7.1-r1.zip"]\nfov:0.8\n',encoding='utf8')
    before=snap(root)
    r=subprocess.run([os.environ['ComSpec'],'/d','/c',str(pkg/'仅检查-Windows.bat'),'-TargetPath',str(root)],input=b'\r\n',capture_output=True)
    assert r.returncode==0,(side,'BAT',r.stdout.decode('utf8',errors='replace'),r.stderr.decode('utf8',errors='replace'))
    assert snap(root)==before;print(side,'BAT check PASS',flush=True)
    for action in ['Install','Restore']:
        r=subprocess.run([str(pathlib.Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(pkg/'install.ps1'),'-Action',action,'-TargetPath',str(root)],capture_output=True)
        assert r.returncode==0,(side,action,r.stdout.decode('utf8',errors='replace'),r.stderr.decode('utf8',errors='replace'));print(side,'r1',action,'PASS',flush=True)
    assert snap(root)==before
    report[side]={'r1Upgrade':'passed','restoreR1ByteExact':'passed','batWithSpaceAndUnicodePath':'passed'}
(R/'reports/upgrade.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
