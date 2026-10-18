"""SPDX-License-Identifier: GPL-3.0-or-later. Offline Windows installer integration tests.
Inputs: official ATM10A 0.7.1 overrides directory and the exact target mod jars.
Never point --reference at a running instance; no game process is launched.
"""
import argparse, copy, hashlib, json, os, pathlib, re, shutil, subprocess, tempfile, zipfile
R=pathlib.Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text('utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snap(root):return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and '.atm10a-zh-r2-backups' not in p.parts}
def read_snbt(p):
    # This pack's language SNBT is a flat mapping of strings and string lists.
    s=p.read_text('utf-8-sig');i=0;out={};dec=json.JSONDecoder()
    def ws():
        nonlocal i
        while i<len(s) and (s[i].isspace() or s[i]==','):i+=1
    def value():
        nonlocal i
        ws()
        if s[i]=='[':
            i+=1;a=[];ws()
            while s[i]!=']':a.append(value());ws()
            i+=1;return a
        if s[i] in ('"',"'"):
            quote=s[i];i+=1;chars=[]
            while s[i]!=quote:
                if s[i]=='\\':
                    i+=1
                    if s[i] in ('\\','"',"'"):chars.append(s[i]);i+=1
                    else:chars.extend(('\\',s[i]));i+=1
                else:chars.append(s[i]);i+=1
            i+=1;return ''.join(chars)
        v,n=dec.raw_decode(s[i:]);i+=n;return v
    ws();assert s[i]=='{';i+=1;ws()
    while s[i]!='}':
        if s[i]=='"':k=value()
        else:
            start=i
            while s[i]!=':':i+=1
            k=s[start:i].strip()
        ws();assert s[i]==':';i+=1;out[k]=value();ws()
    return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--reference',type=pathlib.Path,required=True);ap.add_argument('--mod-dir',type=pathlib.Path,required=True);a=ap.parse_args()
    jars={sha(p):p for p in a.mod_dir.glob('*.jar')};results={};counts={}
    testroot=R/'.test-runs';testroot.mkdir(exist_ok=True)
    for side in ['client','server']:
        pkg=R/'dist'/f'atm10a-zh_cn-{side}-r2-atm0.7.1';m=load(pkg/'manifest.json')
        root=pathlib.Path(tempfile.mkdtemp(prefix=side+' 中文 空格 ',dir=testroot))
        for name in ['config','kubejs']:shutil.copytree(a.reference/name,root/name)
        (root/'mods').mkdir();(root/'world').mkdir();(root/'world/level.dat').write_bytes(b'OFFLINE TEST SENTINEL')
        (root/'server.properties').write_text('level-name=world\n',encoding='utf8')
        for mod in m['requiredMods']:shutil.copyfile(jars[mod['sha256']],root/mod['path'])
        (root/'options.txt').write_text('lang:en_us\nresourcePacks:["vanilla","file/personal.zip","file/ATM10A-zh_CN-0.7.1-r1.zip"]\nfov:0.75\n',encoding='utf8')
        def run(action,ok=True):
            r=subprocess.run([str(pathlib.Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(pkg/'install.ps1'),'-Action',action,'-TargetPath',str(root)],capture_output=True)
            assert (r.returncode==0)==ok,(side,action,r.stdout.decode('utf8',errors='replace'),r.stderr.decode('utf8',errors='replace'))
            print(side,action,'PASS' if ok else 'REFUSED AS EXPECTED',flush=True)
        original=snap(root);run('Check');assert snap(root)==original
        for rel,change in [('config/bcc-common.toml',lambda b:b.replace(b'0.7.1',b'0.7.2')),(m['scripts'][0]['path'],lambda b:b+b'\n// custom edit\n')]:
            p=root/rel;old=p.read_bytes();p.write_bytes(change(old));before=snap(root);run('Install',False);assert snap(root)==before;p.write_bytes(old)
        extra=root/'mods/vaultpatcher-duplicate.jar';extra.write_bytes(b'test');before=snap(root);run('Install',False);assert snap(root)==before;extra.unlink()
        run('Install');installed=snap(root)
        if side=='client':
            options=(root/'options.txt').read_text('utf8');packs=json.loads(re.search(r'^resourcePacks:(.*)$',options,re.M)[1]);assert packs==['vanilla','file/personal.zip','file/'+m['resourcePack']],packs
        for f in m['files']:assert installed[f['path']]==f['sha256'],f['path']
        for s in m['scripts']:assert installed[s['path']]==s['resultSha256'],s['path']
        edits=0
        for d in m['dataPatches']:
            if d['source']=='file':baseline=load(a.reference/d['path'])
            else:
                with zipfile.ZipFile(root/d['jar']) as z:baseline=json.loads(z.read(d['entry']))
            expected=copy.deepcopy(baseline)
            for e in d['edits']:
                node=expected
                for key in e['path'][:-1]:node=node[key]
                assert node[e['path'][-1]]==e['from'];node[e['path'][-1]]=e['to'];edits+=1
            assert load(root/d['path'])==expected,d['path']
        allowed={f['path'] for f in m['files']}|{s['path'] for s in m['scripts']}|{d['path'] for d in m['dataPatches']}
        if side=='client':allowed.add('options.txt')
        assert all(installed.get(p)==h for p,h in original.items() if p not in allowed)
        run('Install');assert snap(root)==installed
        p=root/m['scripts'][0]['path'];old=p.read_bytes();p.write_bytes(old+b'\n// user edit\n');before=snap(root);run('Restore',False);assert snap(root)==before;p.write_bytes(old)
        run('Restore');assert snap(root)==original
        if side=='client':
            run('Install');p=root/'options.txt';txt=p.read_text('utf8').replace('fov:0.75','fov:0.95').replace('"file/personal.zip"','"file/personal.zip","file/new.zip"');p.write_text(txt,encoding='utf8');run('Restore');txt=p.read_text('utf8');assert 'fov:0.95' in txt and 'file/new.zip' in txt and 'lang:en_us' in txt and m['resourcePack'] not in txt and 'r1.zip' in txt
        results[side]={'checks':'passed','payloadFiles':len(m['files']),'scriptPatches':len(m['scripts']),'dataFiles':len(m['dataPatches']),'displayEdits':edits,'fileWrites':len(allowed)}
    en={};zh={};folder='config/ftbquests/quests/lang/'
    for p in (a.reference/(folder+'en_us')).rglob('*.snbt'):en.update(read_snbt(p))
    paths=list((R/'src/common/files'/(folder+'zh_cn')).rglob('*.snbt'))
    for p in paths:zh.update(read_snbt(p))
    assert en.keys()==zh.keys(),(len(en),len(zh))
    for k,v in en.items():
        assert type(v)==type(zh[k]),k
        if isinstance(v,list):assert all(isinstance(x,str) for x in zh[k]),k
    for k in ['quest.0B11EAB8D76529E0.quest_desc','quest.0104C2E2E30B966B.quest_desc']:
        for marker in re.findall(r'\{image:[^}]+\}','\n'.join(en[k])):assert marker in zh[k],(k,marker)
    jsonfiles=list((R/'src/resourcepack').rglob('*.json'))
    for p in jsonfiles:load(p)
    report={'target':'ATM10: Aeronautics 0.7.1','installer':'Windows PowerShell 5.1','checks':results,'questFiles':len(paths),'questFields':len(zh),'resourceJsonFilesParsed':len(jsonfiles),'questImageRepairs':2,'gameStarted':False,'multiplayerTested':False,'runtimeTesting':'Deferred at user request; offline fixture directories only.'}
    (R/'reports/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
