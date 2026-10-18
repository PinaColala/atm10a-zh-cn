# SPDX-License-Identifier: GPL-3.0-or-later
[CmdletBinding()]
param([ValidateSet('Install','Check','Remove')][string]$Action='Install',[string]$TargetPath='')
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$Utf8=New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding=$Utf8
$JarName='jecharacters-1.21.1-neoforge-4.5.29.jar'
$JarHash='b622c1ec7860bf776012fa8262d5425bd128889661b325028a1f407b35621dff'
function Safe([string]$Base,[string]$Rel){
 if([IO.Path]::IsPathRooted($Rel) -or $Rel -match '(^|[/\\])\.\.([/\\]|$)|:'){throw '非法路径'}
 $p=[IO.Path]::GetFullPath((Join-Path $Base $Rel));$prefix=[IO.Path]::GetFullPath($Base).TrimEnd('\','/')+'\'
 if(-not $p.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw '路径越界'}
 $walk=$p;while($walk){if(Test-Path -LiteralPath $walk){if((Get-Item -LiteralPath $walk -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw '不支持符号链接或目录联接'}};$walk=[IO.Path]::GetDirectoryName($walk)}
 return $p
}
function Hash([string]$Path){if(Test-Path -LiteralPath $Path -PathType Leaf){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()};return $null}
function Save($State){[IO.File]::WriteAllText($StatePath,(ConvertTo-Json -InputObject $State -Depth 10),$Utf8)}
function Stopped{if(Get-CimInstance Win32_Process -Filter "Name='java.exe' OR Name='javaw.exe'"){throw '请先退出 Minecraft 和崩溃助手；检测到 Java 进程仍在运行'}}
function RemoveOwned($State){
 if($State.target -ne $Root){throw '安装记录属于其他实例'}
 foreach($f in $State.files){
  if($f.path -eq ('mods/'+$JarName)){$expected=$JarHash}
  elseif($f.path -eq 'mods/LICENSE-atm10a-jecharacters-4.5.29.txt'){$expected=Hash (Safe $PSScriptRoot 'LICENSE-just-enough-characters.txt')}
  else{throw '安装记录包含未知文件，停止卸载'}
  if($f.sha256 -ne $expected){throw '安装记录校验失败'}
  $p=Safe $Root $f.path;$h=Hash $p;if($null -ne $h -and $h -ne $f.sha256){throw "组件已被修改，停止卸载：$($f.path)"}
 }
 foreach($f in $State.files){$p=Safe $Root $f.path;if(Test-Path -LiteralPath $p){Remove-Item -LiteralPath $p}}
 $State.status='removed';Save $State
}
try{
 if(-not $TargetPath){$TargetPath=Read-Host '请输入 ATM10A 实例目录（含 mods 和 config）'}
 $Root=[IO.Path]::GetFullPath($TargetPath.Trim().Trim('"')).TrimEnd('\','/')
 $Mods=Safe $Root 'mods';if(-not(Test-Path -LiteralPath $Mods -PathType Container)){throw '目标缺少 mods 目录'}
 $StatePath=Safe $Root '.atm10a-pinyin-install.json';$State=$null
 if(Test-Path -LiteralPath $StatePath){$State=ConvertFrom-Json -InputObject ([IO.File]::ReadAllText($StatePath,$Utf8))}
 if($Action -eq 'Remove'){
  if($null -eq $State -or $State.status -eq 'removed'){throw '没有由此补装器安装的拼音搜索记录'}
  Stopped;RemoveOwned $State;Write-Host '拼音搜索已卸载，原汉化和模组配置保持不变。';exit 0
 }
 $bcc=[IO.File]::ReadAllText((Safe $Root 'config/bcc-common.toml'),$Utf8)
 if($bcc -notmatch '(?m)^\s*modpackName\s*=\s*"ATM10: Aeronautics"\s*$' -or $bcc -notmatch '(?m)^\s*modpackVersion\s*=\s*"0\.7\.1"\s*$'){throw '此补装包只适配 ATM10A 0.7.1'}
 $Source=Safe $PSScriptRoot $JarName;if((Hash $Source) -ne $JarHash){throw '拼音搜索 JAR 校验失败'}
 if($null -ne $State -and $State.status -ne 'removed'){
  if($State.target -ne $Root -or $State.status -ne 'installed'){throw '存在未完成的安装，请先运行卸载入口'}
  foreach($f in $State.files){if((Hash (Safe $Root $f.path)) -ne $f.sha256){throw '已安装组件被修改，请先处理修改'}}
  Write-Host '拼音搜索已安装，无需重复写入。';exit 0
 }
 Add-Type -AssemblyName System.IO.Compression.FileSystem
 foreach($j in Get-ChildItem -LiteralPath $Mods -Filter '*.jar' -File){
  $present=$j.Name -match '^jecharacters(?:-|\.)';$zip=[IO.Compression.ZipFile]::OpenRead($j.FullName)
  try{foreach($name in @('META-INF/neoforge.mods.toml','META-INF/mods.toml')){$entry=$zip.GetEntry($name);if($null -ne $entry){$reader=New-Object IO.StreamReader($entry.Open());try{$text=$reader.ReadToEnd();if($text -match '(?m)^\s*modId\s*=\s*["'']jecharacters["'']'){$present=$true}}finally{$reader.Dispose()}}}}finally{$zip.Dispose()}
  if($present){Write-Host "已有拼音搜索：$($j.Name)，保留现有版本，跳过安装。";exit 0}
 }
 $files=@();foreach($pair in @(@($JarName,('mods/'+$JarName)),@('LICENSE-just-enough-characters.txt','mods/LICENSE-atm10a-jecharacters-4.5.29.txt'))){
  $source=Safe $PSScriptRoot $pair[0];$h=Hash $source;if($null -eq $h){throw "缺少组件：$($pair[0])"};$dest=Safe $Root $pair[1]
  if(Test-Path -LiteralPath $dest){if((Hash $dest) -ne $h){throw "目标文件已存在且不同：$($pair[1])"};continue}
  $files+=@{path=$pair[1];sha256=$h;source=$pair[0]}
 }
 if($Action -eq 'Check'){Write-Host '兼容和重复模组检查通过；未写入实例。';exit 0}
 Stopped
 $State=@{version='4.5.29';target=$Root;status='prepared';files=@($files)};Save $State
 try{
  foreach($f in $files){$dest=Safe $Root $f.path;if(Test-Path -LiteralPath $dest){throw '目标文件在检查后出现，安装停止'};$stream=[IO.File]::Open($dest,'CreateNew','Write','None');try{$bytes=[IO.File]::ReadAllBytes((Safe $PSScriptRoot $f.source));$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()};if((Hash $dest) -ne $f.sha256){throw '安装后校验失败'}}
  $State.status='installed';Save $State
 }catch{RemoveOwned $State;throw}
 Write-Host 'Just Enough Characters 4.5.29 已安装。下次启动游戏后生效。' -ForegroundColor Green
}catch{Write-Host ('操作未完成：'+$_.Exception.Message) -ForegroundColor Red;exit 1}
