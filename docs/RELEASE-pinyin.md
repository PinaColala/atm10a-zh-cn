# ATM10A 0.7.1 客户端拼音搜索补装包

补回基础 ATM10 r27-beta1 汉化包可选目录里的 Just Enough Characters 4.5.29。使用完全相同的 JAR，支持全拼及声母组合搜索。

下载 `atm10a-client-pinyin-4.5.29.zip`，退出游戏与崩溃助手后解压，双击 `install-pinyin-windows.bat`，输入 ATM10A 实例目录。无需重装已有汉化，不需要安装到服务器。

- `check-pinyin-windows.bat`：检查兼容性，不写入。
- `remove-pinyin-windows.bat`：只卸载此补装器添加且未被修改的文件。
- 检测同 modId 的已有组件，包括改名的 JAR；保留原版本，避免重复加载。
- 安装记录独立于 r2 汉化备份，附 MIT 许可和 SHA-256。

Windows PowerShell 5.1 的 9 项离线检查通过。未进行真实启动或游戏内搜索验证，因此作为预发布提供。此发布只补齐拼音组件；[其他已知功能差异](https://github.com/PinaColala/atm10a-zh-cn/blob/main/docs/UPSTREAM-FEATURE-AUDIT.md)仍待适配。
