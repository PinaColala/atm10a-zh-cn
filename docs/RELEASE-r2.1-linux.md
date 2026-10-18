补上 **Linux 云端服务端安装支持**，适配 ATM10: Aeronautics 0.7.1。客户端继续使用 r2，无需重装。

下载 `atm10a-zh_cn-server-linux-r2.1-atm0.7.1.tar.gz` 或同名 ZIP，解压后先停服，再执行：

```sh
sh install.sh --check "/srv/minecraft/ATM10A"
sh install.sh "/srv/minecraft/ATM10A"
# 还原前也要先停服
sh install.sh --restore "/srv/minecraft/ATM10A"
```

将示例路径换成自己的服务端目录。需要 Python 3.8+，无需 PowerShell 或 pip。使用运行服务器的同一用户，不需要 root。

- Linux 世界文件锁与并发安装检查、权限检查、原文件备份、逐文件哈希校验、失败回滚与还原。
- 兼容 FTB Quests 启动前的分散语言文件和启动后的合并格式，保留既有自定义译文键、任务结构与文件权限。
- 保持两端相同的 449 条有效字节码文本补丁和法术书、蜜蜂等译文。
- Ubuntu / Python 3.8 与 3.12 的自动化测试覆盖真实 Java FileChannel 世界锁、安装／还原、权限、符号链接、文件篡改及故障回滚；报告随包提供。

此版本做了 Linux 离线安装验证，未连接用户云端服务器，也未启动 Minecraft 或进行联机测试，仍标记为预发布。

备份在 `.atm10a-zh-linux-backups/`，请保留安装包和备份，并另存世界备份。Windows r2 的活动备份需要先用原安装器还原，不与 Linux 备份混用。完整说明见包内 `README-Linux.md`。

基础译文由星野夢華（Hoshino Yumeka）与 CFPA 社区提供，按 CC BY-NC-SA 4.0 共享；代码 GPL-3.0-or-later；VaultPatcher GPL-3.0-only，包含对应源码。
