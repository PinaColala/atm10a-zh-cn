"""SPDX-License-Identifier: GPL-3.0-or-later. Windows 5.1 addon lifecycle tests; no game launch."""
import hashlib,json,os,pathlib,shutil,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parents[1]
P=R/'dist/atm10a-client-pinyin-4.5.29'
PS=pathlib.Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
J='jecharacters-1.21.1-neoforge-4.5.29.jar'
(R/'.test-runs').mkdir(exist_ok=True)
root=pathlib.Path(tempfile.mkdtemp(prefix='pinyin 中文 ',dir=R/'.test-runs'))
(root/'mods').mkdir();(root/'config').mkdir()
(root/'config/bcc-common.toml').write_text('modpackName = "ATM10: Aeronautics"\nmodpackVersion = "0.7.1"\n')
(root/'options.txt').write_bytes(b'unchanged options')
(root/'.atm10a-zh-r2-backups').mkdir()
(root/'.atm10a-zh-r2-backups/sentinel').write_bytes(b'unchanged backup')
checks=[]
def snapshot():
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
def run(action,ok=True):
    env={k:v for k,v in os.environ.items() if k.lower()!='psmodulepath'}
    p=subprocess.run([str(PS),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(P/'install.ps1'),'-Action',action,'-TargetPath',str(root)],capture_output=True,env=env)
    assert (p.returncode==0)==ok,p.stdout.decode('utf8',errors='replace')+p.stderr.decode('utf8',errors='replace')
before=snapshot();run('Check');assert before==snapshot();checks.append('check leaves instance unchanged')
run('Install');assert (root/'mods'/J).read_bytes()==(P/J).read_bytes();checks.append('exact upstream binary installed')
installed=snapshot();run('Install');assert snapshot()==installed;checks.append('repeat install is no-op')
jar=root/'mods'/J;jar.write_bytes(jar.read_bytes()+b'tampered');tampered=snapshot();run('Remove',False);assert snapshot()==tampered;checks.append('modified file blocks removal without partial deletion')
shutil.copyfile(P/J,jar);run('Remove');assert not jar.exists();checks.append('remove deletes owned files')
assert (root/'options.txt').read_bytes()==b'unchanged options'
assert (root/'.atm10a-zh-r2-backups/sentinel').read_bytes()==b'unchanged backup';checks.append('translation backup and options preserved')
shutil.copyfile(P/J,root/'mods/renamed.jar');before=snapshot();run('Install');assert snapshot()==before;checks.append('renamed existing mod detected through modId')
(root/'mods/renamed.jar').unlink();run('Install');checks.append('reinstall after removal')
state=root/'.atm10a-pinyin-install.json';original=state.read_bytes();s=json.loads(original)
s['files'].append({'path':'options.txt','sha256':hashlib.sha256((root/'options.txt').read_bytes()).hexdigest()})
state.write_text(json.dumps(s),encoding='utf8');before=snapshot();run('Remove',False);assert before==snapshot();checks.append('forged ownership record rejected')
state.write_bytes(original);run('Remove')
report={'result':'passed','checks':checks,'shell':'Windows PowerShell 5.1','gameStarted':False,'jarSha256':hashlib.sha256((P/J).read_bytes()).hexdigest()}
(R/'reports/pinyin-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
