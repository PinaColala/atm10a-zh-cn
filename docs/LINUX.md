# Linux 服务端安装

适配 ATM10: Aeronautics **0.7.1**。此包只安装服务端汉化，客户端继续使用 r2 客户端包。需要 Linux 和 Python **3.8+**，只使用 Python 标准库，无需 pip、PowerShell 或 Windows。

下载并解压 `atm10a-zh_cn-server-linux-r2.1-atm0.7.1.tar.gz`，进入解压目录。ZIP 版内容相同，可用面板文件管理器解压。

完全关闭服务器，包括面板里的自动重启。用运行服务器的同一用户执行，路径换成实际服务端目录（其中有 `mods`、`config`、`server.properties`）：

```sh
sh install.sh --check "/srv/minecraft/ATM10A"
sh install.sh "/srv/minecraft/ATM10A"
```

第一条只检查，不修改实例；第二条会备份原文件并安装。完成后从原面板或启动脚本开服。安装器不会启动或停止服务器，不需要 root；若提示权限不足，应使用服务器文件的所属用户。

撤销时先关服，再从同一安装包执行：

```sh
sh install.sh --restore "/srv/minecraft/ATM10A"
```

备份位于服务器目录的 `.atm10a-zh-linux-backups/`。保留安装包和备份；文件恢复时检查哈希，发现安装后手动修改会停止。它不会还原已经保存进世界的蜜蜂名字，因此请保留自己的存档备份。

本包会校验目标模组、任务结构、原脚本与数据，只修改汉化显示内容。任务语言统一生成 `lang/zh_cn.snbt`，兼容首次启动前的分散文件与启动后合并的文件；旧的分散中文文件逐个备份并移出加载范围，`*.snbt_merged` 保留，未知的已有译文键保留。任务定义和章节顺序不改动。

安装时检查 Java 的世界文件锁，并拒绝实例目录中仍在运行的 Java 进程；同一目录的安装互斥。面板启动期间尚未创建世界锁的情况仍需服主先停服并关闭自动重启。实例路径和安装涉及的路径不能是符号链接；`level-name` 必须是未转义的相对路径。

支持 r1 译文文件升级。若从 Windows r2 安装迁移过来且存在活动备份，请先用原安装器还原；不会混用两种平台的备份格式。两端 r2 / r2.1 的译文内容相同，不需要重新安装客户端。

验收记录见 `reports/linux-verification.json`（发布包附带）。测试只检查离线安装、结构与还原，不代表真实开服或多人联机测试。

原作者署名及许可见 `CREDITS.txt` 和 `LICENSE`。项目：https://github.com/PinaColala/atm10a-zh-cn
