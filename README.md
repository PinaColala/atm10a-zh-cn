# ATM10A 简体中文汉化

适配 **All the Mods 10: Aeronautics 0.7.1**，Minecraft 1.21.1 / NeoForge 21.1.250。基于[星野夢華的 ATM10 汉化](https://github.com/chiba233/atm10-zh-cn) r27-beta1（ATM10 8.2）制作的第三方衍生适配。

**[Windows 客户端 r2](https://github.com/PinaColala/atm10a-zh-cn/releases/tag/r2-atm0.7.1)** · **[Linux 服务端 r2.1](https://github.com/PinaColala/atm10a-zh-cn/releases/tag/r2.1-linux-atm0.7.1)** · [Linux 安装说明](docs/LINUX.md) · [修复记录](reports/fixes.json) · [许可证与署名](CREDITS.txt)

## 安装

**可选拼音搜索：**原 ATM10 汉化包附带的 Just Enough Characters 4.5.29 已补回，下载 [拼音搜索独立补装包](https://github.com/PinaColala/atm10a-zh-cn/releases/tag/pinyin-4.5.29-atm0.7.1)，退出游戏后解压，双击 `install-pinyin-windows.bat` 并输入实例目录。已有 r2 汉化无需重装。支持全拼及声母组合搜索；提供检查、独立卸载与重复模组检测。此组件仅用于客户端。原先发布的 r2 ZIP 不含它，仍需单独下载；从当前源码构建的客户端包会包含 `optional-pinyin` 文件夹，需自行运行其中的安装入口。

原包功能对照及尚未迁移项目见 [功能差异清单](docs/UPSTREAM-FEATURE-AUDIT.md)。当前适配尚未完整保留原包的全部附加功能。

**Linux 云端服务器：**下载 [Linux 服务端包](https://github.com/PinaColala/atm10a-zh-cn/releases/tag/r2.1-linux-atm0.7.1)，解压后停服，用服务端文件的所属用户执行（Python 3.8+）：

```sh
sh install.sh --check "/srv/minecraft/ATM10A"
sh install.sh "/srv/minecraft/ATM10A"
# 需要还原时先停服：
sh install.sh --restore "/srv/minecraft/ATM10A"
```

路径换成自己的实例目录。Linux 版兼容 FTB Quests 分散／合并语言文件，检查 Java 世界文件锁并保留文件权限，支持失败回滚。详见 [Linux 说明](docs/LINUX.md)与 [Ubuntu 自动测试](https://github.com/PinaColala/atm10a-zh-cn/actions/workflows/linux.yml)。r2.1 服务端译文与 r2 客户端一致，无需重装客户端。

**Windows 客户端／Windows 服务端：**

1. 在 Release 中下载 `atm10a-zh_cn-client-r2-atm0.7.1.zip`；专用服务端下载 `server` 包。
2. 完全退出游戏／关闭服务器，将 ZIP 解压到独立文件夹。
3. 双击 **双击安装-Windows.bat**，输入实例目录。客户端目录应包含 `mods` 和 `config`；服务端还需要 `server.properties`。
4. 客户端安装器会启用资源包并选择简体中文。联机时客户端和服务端分别安装对应包。

可先运行 **仅检查-Windows.bat**，它不会写入实例。撤销使用 **还原汉化-Windows.bat**。无需管理员权限、Python 或额外 PowerShell；支持 Windows 自带的 PowerShell 5.1。BAT 安装器不适用于 Linux。

安装器只接受 0.7.1 的任务与目标模组基准，备份保存在实例的 `.atm10a-zh-r2-backups`。已修改的脚本、配方或不匹配的模组会被拦截。升级自 r1 时保留 r1 状态；还原 r2 会回到安装 r2 之前的状态。请勿手动将 `payload` 整包覆盖到游戏目录，部分脚本和数据需要由安装器生成。

## 内容与 r2 修复

- 对齐航空版的 73 个任务语言文件、8,447 个字段；补译航空版任务及附属模组语言，保留任务编号、解锁关系和奖励。
- 客户端补上原先仅服务端携带的 10 个定向字节码翻译模块，使 RFTools / McJty 客户端界面也能应用补丁。
- 补回远古城市、巨型血箱任务中的两处插图引用。
- 修正 27 条带动态参数的拼接文本匹配，合并重复项，统一 3 处重复译法；移除目标版本中不存在的 `Positioned` 项。最终保留 **449 条有效的类／原文匹配项**。
- 两端共用任务、蜜蜂、法术书等译文。客户端同时包含单人模式所需的 3 个服务端显示脚本补丁；客户端合计 23 个脚本补丁。
- 对 65 个 JSON 数据文件仅修改 161 个显示字段。安装时读取用户的原文件或目标模组 JAR，保留配方材料、法术组成等非显示数据。
- 使用官方 VaultPatcher 1.5.3-fix-all；随包提供原始二进制、对应源码和许可证。

本项目迁移了基础汉化中的部分内容并补译航空版；**不承诺整合包每个模组的全部英文均已汉化，也未完整迁移原包全部功能**。字节码补丁限于选定的 10 个模块，其他已确认差异见功能差异清单。

## 验证范围

[Windows 安装验收报告](reports/verification.json)覆盖仅检查不写入、版本／自定义脚本／重复模组拦截、安装结果、重复安装、安装后文件修改保护、逐字节还原，以及还原时保留用户新改的视野等选项和个人资源包。[升级报告](reports/upgrade.json)验证 r1 升级、还原回 r1，以及含空格路径下的 BAT 入口。测试在独立临时实例中执行。

[转换器报告](reports/transformer.json)来自官方 VaultPatcher 对目标版本真实模组类文件的离线转换，449/449 项触发替换。测试没有加载 Minecraft。

**尚未进行真实启动、游戏界面检查或多人联机验证。** 因而 r2 以预发布版本提供。存档中的蜜蜂名字迁移无法通过文件还原撤销，使用前请保留存档备份。

## 构建与复验

Python 3.10+，仅用标准库：

```powershell
python tools/build.py
# 仅构建客户端拼音补装包：
python tools/build_pinyin.py
# Linux 服务端包（此构建脚本支持 Python 3.8+）：
python tools/build_linux.py
```

输出到 `dist/`，包括客户端／服务端 ZIP 和 `SHA256SUMS.txt`。使用官方 0.7.1 的 `overrides` 及 `src/guards.json` 指定的目标模组 JAR，可运行 Windows 离线安装测试：

```powershell
python tests/verify.py --reference D:/test/ATM10AERO-0.7.1/overrides --mod-dir D:/test/mods
```

测试只向仓库内 `.test-runs/` 新建的目录写入，不启动游戏。[字节码测试说明](tests/README.md)列出了所需依赖与命令。官方整合包和测试用目标模组 JAR 不包含在仓库中。

## 来源与许可

- 基础汉化：星野夢華（Hoshino Yumeka），[chiba233/atm10-zh-cn](https://github.com/chiba233/atm10-zh-cn)，以及 CFPA 社区。译文按 **CC BY-NC-SA 4.0** 共享，须署名、非商业性使用、相同方式共享。
- 安装、构建与测试代码：**GPL-3.0-or-later**；VaultPatcher：**GPL-3.0-only**。
- 可选 Just Enough Characters 4.5.29：**MIT**，原始二进制、许可与来源位于 `optional/pinyin/`。安装器离线测试见 [报告](reports/pinyin-verification.json)，Windows 上执行 `python tests/verify_pinyin.py` 复验；先构建补装包并退出 Java 程序。未进行真实游戏搜索验证。
- 整合包：[AllTheMods/ATM-10-a](https://github.com/AllTheMods/ATM-10-a)。此项目不是 AllTheMods 或基础汉化作者的官方发布。

详细范围见 [LICENSE](LICENSE)、[上游许可](LICENSE-UPSTREAM)、[CREDITS.txt](CREDITS.txt)。
