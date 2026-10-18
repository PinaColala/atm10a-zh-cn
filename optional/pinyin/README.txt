ATM10A 0.7.1 客户端可选补装：Just Enough Characters 4.5.29

与基础 ATM10 r27-beta1 汉化包附带的是同一个文件，不需要重装汉化。
支持中文原文、全拼和声母组合搜索；JEI、部分物品存储界面和手册等场景由模组适配。
不同模组搜索框的具体兼容性以 Just Enough Characters 本身为准。

1. 完全退出 Minecraft 和崩溃助手。
2. 解压，双击 install-pinyin-windows.bat，输入含 mods 和 config 的 ATM10A 0.7.1 实例目录。
3. 下次启动后可试用拼音搜索，例如钻石可试 zuanshi 或 zs。

check-pinyin-windows.bat：只检查，不写入。
remove-pinyin-windows.bat：退出游戏后运行，仅删除本补装器添加且校验未变的文件。
安装记录在实例根目录 .atm10a-pinyin-install.json，不修改 r2 汉化备份。
已有同 modId 的模组会跳过安装，即使 JAR 被改名也会检测，防止重复加载。
这是客户端组件，不需要上传云端服务器。

来源：原 ATM10 汉化包“可选mods-拼音搜索”。
作者：Towdium、yzl210、Death-123、vfyjxf_
项目：https://github.com/Towdium/JustEnoughCharacters
发行文件：https://cdn.modrinth.com/data/I7k4B65h/versions/XPKoy65e/jecharacters-1.21.1-neoforge-4.5.29.jar
SHA-256：b622c1ec7860bf776012fa8262d5425bd128889661b325028a1f407b35621dff
模组 MIT，全文见 LICENSE-just-enough-characters.txt。安装器 GPL-3.0-or-later。

原作者将其列为可选组件，并提示其可能增加启动时的内存峰值；遇到相关问题可单独卸载。
