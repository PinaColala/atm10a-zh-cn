# SPDX-License-Identifier: GPL-3.0-or-later
# Only local translation files are changed. Game/mod code is patched from the user's installation.
[CmdletBinding()]
param([ValidateSet('Install','Check','Restore')][string]$Action='Install',[string]$TargetPath='')
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
[Console]::OutputEncoding=New-Object Text.UTF8Encoding($false)
$U=New-Object Text.UTF8Encoding($false)
$Package=[IO.Path]::GetFullPath($PSScriptRoot)
function Safe([string]$Base,[string]$Rel) {
 if ([IO.Path]::IsPathRooted($Rel) -or $Rel -match '(^|[/\\])\.\.([/\\]|$)|:') {throw "非法路径：$Rel"}
 $prefix=[IO.Path]::GetFullPath($Base).TrimEnd('\','/')+'\';$p=[IO.Path]::GetFullPath((Join-Path $Base $Rel))
 if (-not $p.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw '路径越界'}
 $walk=$p
 while($walk){if(Test-Path -LiteralPath $walk){if((Get-Item -LiteralPath $walk -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw "不支持目录联接或链接：$walk"}};$walk=[IO.Path]::GetDirectoryName($walk)}
 return $p
}
function Digest([byte[]]$Bytes) {$a=[Security.Cryptography.SHA256]::Create();try{return ([BitConverter]::ToString($a.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$a.Dispose()}}
function Hash([string]$Path) {if(Test-Path -LiteralPath $Path -PathType Leaf){return Digest ([IO.File]::ReadAllBytes($Path))};return $null}
function ReadText([string]$Path){return [IO.File]::ReadAllText($Path,$U)}
function Put([string]$Path,[byte[]]$Bytes){[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Path))|Out-Null;[IO.File]::WriteAllBytes($Path,$Bytes)}
function WriteState($State,[string]$Dir){Put (Safe $Dir 'backup.json') ($U.GetBytes((ConvertTo-Json -InputObject $State -Depth 40)))}
function Option([string]$Text,[string]$Key){$m=[regex]::Match($Text,'(?m)^'+[regex]::Escape($Key)+':([^\r\n]*)');if($m.Success){return $m.Groups[1].Value};return $null}
function SetOption([string]$Text,[string]$Key,$Value){
 $pat='(?m)^'+[regex]::Escape($Key)+':[^\r\n]*(?:\r?\n|$)';$line='';if($null -ne $Value){$line=$Key+':'+$Value+"`n"}
 if([regex]::IsMatch($Text,$pat)){return [regex]::Replace($Text,$pat,[Text.RegularExpressions.MatchEvaluator]{param($m)$line})}
 if($Text -and -not $Text.EndsWith("`n")){$Text+="`n"};return $Text+$line
}
function Packs($Text){if(-not $Text){return};if(-not $Text.TrimStart().StartsWith('[')){throw 'resourcePacks 格式不正确'};foreach($item in (ConvertFrom-Json -InputObject $Text)){if($item -isnot [string]){throw 'resourcePacks 必须是字符串数组'};Write-Output ([string]$item)}}
function Stopped {
 if($M.side -eq 'server'){
  $props=Safe $Root 'server.properties';if(-not(Test-Path -LiteralPath $props)){throw '请选择含 server.properties 的服务端目录'}
  $world='world';$txt=ReadText $props;if($txt -match '(?m)^level-name=(.+)\r?$'){$world=$Matches[1].Trim()}
  $lock=Safe $Root ($world+'/session.lock');if(Test-Path -LiteralPath $lock){try{$s=[IO.File]::Open($lock,'Open','ReadWrite','None');$s.Dispose()}catch{throw '请先完全关闭服务器'}}
 }
}
function Restore($St,[string]$Dir,[bool]$Rollback=$false){
 if($St.target -ne $Root -or $St.side -ne $M.side){throw '备份所属实例或类型不匹配'}
 foreach($e in $St.files){
  if($e.existed -and (Hash (Safe $Dir ('originals/'+$e.path))) -ne $e.before){throw "备份损坏：$($e.path)"}
  $p=Safe $Root $e.path;$h=Hash $p
  if(-not $Rollback -and $e.path -ne 'options.txt' -and $h -ne $e.after -and $h -ne $e.before){throw "安装后文件已被修改，还原已停止：$($e.path)"}
 }
 $merged=$null;$opt=Safe $Root 'options.txt';$entry=@($St.files|Where-Object {$_.path -eq 'options.txt'})
 if($entry.Count -and (Test-Path -LiteralPath $opt) -and (Hash $opt) -ne $entry[0].after -and -not $Rollback){
  $merged=ReadText $opt;$list=@(Packs (Option $merged 'resourcePacks')|Where-Object {$_ -ne ('file/'+$M.resourcePack)})
  foreach($p in $St.disabledPacks){if($list -notcontains $p){$list+=$p}}
  $merged=SetOption $merged 'resourcePacks' (ConvertTo-Json -InputObject @($list) -Compress)
  if((Option $merged 'lang') -eq 'zh_cn'){$merged=SetOption $merged 'lang' $St.language}
 }
 foreach($e in $St.files){$p=Safe $Root $e.path
  if($e.path -eq 'options.txt' -and $null -ne $merged){Put $p ($U.GetBytes($merged))}
  elseif($e.existed){Put $p ([IO.File]::ReadAllBytes((Safe $Dir ('originals/'+$e.path))))}
  elseif(Test-Path -LiteralPath $p -PathType Leaf){Remove-Item -LiteralPath $p -Force}
 }
 $St.status='restored';WriteState $St $Dir
}
try {
 $M=ConvertFrom-Json -InputObject (ReadText (Safe $Package 'manifest.json'))
 Write-Host "ATM10A 0.7.1 汉化 r2 [$($M.side)]；请先完全退出游戏／服务器。"
 if(-not $TargetPath){$parent=Split-Path $Package -Parent;if(Test-Path -LiteralPath (Join-Path $parent 'mods')){$TargetPath=$parent}else{$TargetPath=Read-Host '请输入实例目录（含 mods 和 config）'}}
 $Root=[IO.Path]::GetFullPath($TargetPath.Trim().Trim('"')).TrimEnd('\','/')
 if($Root -eq $Package -or $Root.StartsWith($Package+'\',[StringComparison]::OrdinalIgnoreCase)){throw '目标不能是汉化包自身目录'}
 if(-not(Test-Path -LiteralPath (Safe $Root 'mods') -PathType Container)){throw '目标目录没有 mods 文件夹'}
 Stopped
 $backupRoot=Safe $Root '.atm10a-zh-r2-backups';$active=@()
 if(Test-Path -LiteralPath $backupRoot){foreach($d in Get-ChildItem -LiteralPath $backupRoot -Directory|Sort-Object Name -Descending){$p=Safe $d.FullName 'backup.json';if(Test-Path -LiteralPath $p){$st=ConvertFrom-Json -InputObject (ReadText $p);if($st.status -ne 'restored'){$active+=@{dir=$d.FullName;state=$st}}}}}
 if($Action -eq 'Restore'){if(-not $active.Count){throw '没有待还原的 r2 备份'};Restore $active[0].state $active[0].dir;Write-Host '还原完成。备份已保留。';exit 0}
 if($active.Count){if($active[0].state.status -ne 'installed'){throw '存在未完成的安装，请先还原'}
  foreach($e in $active[0].state.files){if($e.path -ne 'options.txt' -and (Hash (Safe $Root $e.path)) -ne $e.after){throw "已安装的文件被修改：$($e.path)。请先处理修改并还原"}}
  Write-Host '已安装同一版本，无需重复写入。';exit 0
 }
 $bcc=ReadText (Safe $Root 'config/bcc-common.toml')
 if($bcc -notmatch '(?m)^\s*modpackName\s*=\s*"ATM10: Aeronautics"\s*$' -or $bcc -notmatch '(?m)^\s*modpackVersion\s*=\s*"0\.7\.1"\s*$'){throw '只支持 ATM10: Aeronautics 0.7.1'}
 foreach($g in $M.requiredMods){if((Hash (Safe $Root $g.path)) -ne $g.sha256){throw "模组版本不匹配：$($g.path)"}}
 foreach($g in $M.questGuards){if((Hash (Safe $Root $g.path)) -ne $g.sha256){throw "任务基准不匹配：$($g.path)"}}
 foreach($j in Get-ChildItem -LiteralPath (Safe $Root 'mods') -Filter '*vaultpatcher*.jar'){if($j.Name -ne 'vaultpatcher.jar'){throw "发现其他 VaultPatcher 文件，请先移出实例：$($j.Name)"}}
 $langDir=Safe $Root 'config/ftbquests/quests/lang/zh_cn'
 if(Test-Path -LiteralPath $langDir){foreach($f in Get-ChildItem -LiteralPath $langDir -File -Recurse){$rel=$f.FullName.Substring($Root.Length+1).Replace('\','/');if($rel -notin @($M.files.path)){throw "存在不属于此版本的任务译文：$rel"}}}
 $plan=@{}
 foreach($f in $M.files){$src=Safe (Safe $Package 'payload') $f.path;$bytes=[IO.File]::ReadAllBytes($src);if((Digest $bytes) -ne $f.sha256){throw "包文件损坏：$($f.path)"};$null=Safe $Root $f.path;$plan[$f.path]=$bytes}
 foreach($g in $M.imageGuards){$h=Hash (Safe $Root $g.path);if($h -ne $g.expectedOriginalSha256 -and $h -ne $g.sha256){throw "菜单图片已有修改：$($g.path)"}}
 foreach($s in $M.scripts){
  $text=(ReadText (Safe $Root $s.path)).Replace("`r`n","`n");$h=Digest ($U.GetBytes($text))
  if($h -ne $s.resultSha256){
   if($h -ne $s.originalSha256){throw "脚本已有修改：$($s.path)"}
   foreach($r in $s.replacements){$count=([regex]::Matches($text,[regex]::Escape($r.from))).Count;if($count -ne $r.count){throw "文本匹配数量错误：$($s.path)"};$text=$text.Replace($r.from,$r.to)}
   if((Digest ($U.GetBytes($text))) -ne $s.resultSha256){throw "脚本结果校验失败：$($s.path)"}
  };$plan[$s.path]=$U.GetBytes($text)
 }
 Add-Type -AssemblyName System.IO.Compression.FileSystem
 foreach($d in $M.dataPatches){
  $dest=Safe $Root $d.path
  if(Test-Path -LiteralPath $dest){$raw=[IO.File]::ReadAllBytes($dest);if((Digest $raw) -notin @($d.baselineSha256,$d.r1Sha256)){throw "数据文件已有修改：$($d.path)"}}
  elseif($d.source -eq 'file'){throw "缺少原数据：$($d.path)"}
  else{
   $zip=[IO.Compression.ZipFile]::OpenRead((Safe $Root $d.jar))
   try{$entry=$zip.GetEntry($d.entry);if($null -eq $entry){throw "模组内缺少数据：$($d.entry)"};$stream=$entry.Open();$mem=New-Object IO.MemoryStream;try{$stream.CopyTo($mem);$raw=$mem.ToArray()}finally{$stream.Dispose();$mem.Dispose()}}finally{$zip.Dispose()}
   if((Digest $raw) -ne $d.baselineSha256){throw "模组数据基准错误：$($d.path)"}
  }
  $obj=ConvertFrom-Json -InputObject ($U.GetString($raw).TrimStart([char]0xFEFF))
  foreach($edit in $d.edits){$node=$obj;for($i=0;$i -lt $edit.path.Count-1;$i++){$key=$edit.path[$i];if($key -is [string]){$node=$node.$key}else{$node=$node[$key]}}
   $key=$edit.path[-1];if($node.$key -notin @($edit.from,$edit.to)){throw "数据译文基准错误：$($d.path)"};$node.$key=$edit.to
  };$plan[$d.path]=$U.GetBytes((ConvertTo-Json -InputObject $obj -Depth 100))
 }
 $oldOptions='';$disabled=@();$language=$null
 if($M.side -eq 'client'){
  $opt=Safe $Root 'options.txt';if(Test-Path -LiteralPath $opt){$oldOptions=ReadText $opt};$language=Option $oldOptions 'lang';$list=@(Packs (Option $oldOptions 'resourcePacks'))
  $disabled=@($list|Where-Object {$_ -match '^file/(ATM10汉化包|ATM10A-zh_CN-).*\.zip$'})
  $list=@($list|Where-Object {$_ -notin $disabled});if(-not $list.Count){$list=@('vanilla')};$list+=('file/'+$M.resourcePack)
  $new=SetOption $oldOptions 'lang' 'zh_cn';$new=SetOption $new 'resourcePacks' (ConvertTo-Json -InputObject @($list) -Compress);$plan['options.txt']=$U.GetBytes($new)
 }
 foreach($rel in $plan.Keys){$path=Safe $Root $rel;if(Test-Path -LiteralPath $path){if(-not(Test-Path -LiteralPath $path -PathType Leaf) -or ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReadOnly)){throw "文件不可写：$rel"}}}
 if($Action -eq 'Check'){Write-Host "全部检查通过，将处理 $($plan.Count) 个文件。未写入实例。";exit 0}
 $dir=Safe $backupRoot ((Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8));[IO.Directory]::CreateDirectory($dir)|Out-Null
 $records=@();foreach($rel in $plan.Keys|Sort-Object){$path=Safe $Root $rel;$before=Hash $path;$exists=$null -ne $before;if($exists){Put (Safe $dir ('originals/'+$rel)) ([IO.File]::ReadAllBytes($path));if((Hash (Safe $dir ('originals/'+$rel))) -ne $before){throw '备份校验失败'}};$records+=@{path=$rel;existed=$exists;before=$before;after=(Digest $plan[$rel])}}
 $state=@{status='prepared';target=$Root;side=$M.side;files=$records;language=$language;disabledPacks=@($disabled)};WriteState $state $dir
 try{Stopped;foreach($e in $records){$p=Safe $Root $e.path;if((Hash $p) -ne $e.before){throw "文件在备份后变更：$($e.path)"};Put $p $plan[$e.path];if((Hash $p) -ne $e.after){throw '写入校验失败'}};$state.status='installed';WriteState $state $dir}
 catch{$failure=$_.Exception.Message;Restore $state $dir $true;throw "安装失败，已还原：$failure"}
 Write-Host "安装完成。备份：$dir" -ForegroundColor Green
}catch{Write-Host ('操作未完成：'+$_.Exception.Message) -ForegroundColor Red;exit 1}
