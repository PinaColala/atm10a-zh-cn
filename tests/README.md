# 离线复验

安装器测试需要 Windows PowerShell 5.1、Python 3.10+、官方 ATM10AERO 0.7.1 的 overrides 目录和 `src/guards.json` 中的 11 个目标 JAR。输入路径只读；测试会复制输入到 `.test-runs/` 的独立目录。不包含整合包本体，也不启动 Minecraft。

```powershell
python tools/build.py
python tests/verify.py --reference D:/test/overrides --mod-dir D:/test/mods
```

字节码测试需要 JDK 21，以下 Maven Central 依赖放在 `.test-inputs/lib/`：

| 库 | Maven 坐标 |
| --- | --- |
| ASM | org.ow2.asm:asm:9.8 |
| ASM Tree | org.ow2.asm:asm-tree:9.8 |
| Gson | com.google.code.gson:gson:2.11.0 |
| fastutil | it.unimi.dsi:fastutil:8.5.15 |

```powershell
New-Item -ItemType Directory -Force .test-inputs/classes
javac -cp 'third_party/vaultpatcher/vaultpatcher.jar;.test-inputs/lib/*' -d .test-inputs/classes tests/TransformAudit.java
java -cp '.test-inputs/classes;third_party/vaultpatcher/vaultpatcher.jar;.test-inputs/lib/*' TransformAudit src/common/files/vaultpatcher/modules D:/test/mods
```

测试逐条构造静态 TranslationInfo，使用官方 VPClassTransformer 转换真实类文件，检查目标中文出现，并写出和重新解析字节码。成功结果为 449 条匹配、449 条实际改变、无失败。它验证匹配与转换，不能替代整个模组加载器启动、游戏运行或联机验证。

如果保留了 r1 客户端与服务端包，还可复验升级与 BAT 入口：

```powershell
python tests/upgrade.py --reference D:/test/overrides --mod-dir D:/test/mods --r1-client D:/test/r1-client --r1-server D:/test/r1-server
```

`reports/verification.json` 与 `reports/transformer.json` 是本次本地离线验收的结果，`reports/fixes.json` 记录相对于输入汉化包的修复。复验结果可能覆盖本地报告。
