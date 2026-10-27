---
name: disk-cleanup
description: 磁盘空间清理（macOS 开发机）。先只读扫描列出全部可清理内容与大小（包管理器缓存、Xcode/模拟器、Docker、日志、废纸篓、项目 node_modules 等，按安全/谨慎分级），经用户本轮确认后才执行，绝不动确认清单之外的东西。Use whenever 用户说 磁盘清理、清理缓存、清理垃圾、空间不足、磁盘满了、腾点空间、释放磁盘、看看什么东西占地方、deep clean、free up disk space。Also triggered as /disk-cleanup。
---

# 磁盘清理（macOS 开发机）

一句话流程：**只读扫描 → 分级清单 → 确认门 → 白名单执行 → 前后对比复盘**。与用户交流用中文。

## 铁律（凌驾于本文件其余部分）

1. **任何删除动作执行前，必须经过本轮确认门**（见下）。上一轮或历史会话的"全部清理"授权不延续——用户说"再清一次"也要重新过门。
2. 扫描（`scan.py`）纯只读、随时可跑、无需确认。
3. 只清理扫描报告中列出的类别；删除一律通过 `scripts/clean.py` 的内置白名单执行。agent **不得手写 rm/rmdir 删任何路径**，不得用 sudo，不得绕过 clean.py 直接调 brew/npm/docker 的删除命令。
4. 用户数据永不触碰：Documents / Desktop / Downloads / 图片 / 视频 / 代码源文件。Downloads 再大也只在用户点名时"列出大文件"报告，本技能不删。
5. 谨慎类（docker-prune / xcode-archives / user-logs / trash）默认不勾选，必须用户主动点名。
6. `clean.py` 只有带 `--yes` 才真删；带 `--yes` 的前提且唯一前提是确认门已在本轮通过。

## 流程

### 1. 扫描（只读）

```bash
python3 <技能基目录>/scripts/scan.py          # 人读表格（进度走 stderr，大目录可能要 1~3 分钟）
python3 <技能基目录>/scripts/scan.py --json   # 需要机器可读时
```

### 2. 汇报

把扫描结果整理给用户：按【安全类 / 谨慎类 / node_modules】三组列出 `类别 id、大小、一句话代价`，并给三组合计。跳过项（未安装工具、Docker 未运行）一并说明。

### 3. 确认门（GATE，每次执行前必须过）

用 AskUserQuestion 提问（单选 + Other，选项不超过 4 个）：

> 问题：「扫描完成：安全类共 X，谨慎类共 Y，node_modules 共 Z。本轮清理范围？」
> - 「全部安全类（推荐）」— 清理上表全部安全类（约 X）
> - 「安全类 + 挑谨慎类」— 先清安全类，下一问勾选谨慎类
> - 「仅报告，不清理」— 到此为止，不执行任何删除
> 用户也可在 Other 里直接点名类别 id（如 `gradle-cache docker-prune`）。

后续追问（按需）：
- 选了"挑谨慎类"或 Other 点了谨慎 id → 第二问 multiSelect（恰好 4 项）：`docker-prune` / `xcode-archives` / `user-logs` / `trash`。
- 扫到 node_modules → 再问一次 multiSelect：按大小列前 4 个路径；更多路径让用户写在 Other。

门规：
- 用户没有明确选择（取消 / 仅报告 / 无回应）→ 只输出报告，流程结束，**绝不执行**。
- 用户点名的 id 不在扫描表中 → 原样复述并让用户改选，绝不猜测类推。
- Docker 要删所有未使用镜像（`-a`）必须用户在 Other 里明说，不主动加。

### 4. 执行

```bash
# 先预演给用户看动作（可选但推荐）：
python3 <技能基目录>/scripts/clean.py --category gradle-cache --category npm-cache
# 确认门已过，真执行：
python3 <技能基目录>/scripts/clean.py --category gradle-cache --category npm-cache --yes
# node_modules 逐路径执行：
python3 <技能基目录>/scripts/clean.py --node-modules /Users/me/ZCodeProject/foo/node_modules --yes
```

一次确认的批次可合并成一条命令；批内逐类输出 OK / PARTIAL / SKIP / FAIL。

### 5. 复盘

汇总：各类释放量、失败/跳过项及原因、卷可用空间前后对比。随后给最多 2~3 条建议（如"APFS 本地快照占用见下"、"该项目 node_modules 4GB，重建 install 一次代价不小"）。到此结束，不追加任何未经确认的清理。

## 类别清单（与 common.py 注册表一致）

安全类（纯缓存，可再生）：`brew-cache` Homebrew 缓存 · `npm-cache` · `pnpm-store` · `yarn-cache` · `pip-cache` · `uv-cache` · `gradle-cache` · `cocoapods-cache` · `cargo-cache` · `huggingface-cache`（跳过登录 token）· `playwright-cache` · `xcode-deriveddata` · `core-sim-caches` · `ios-devicesupport` · `sim-unavailable` 失效模拟器。

谨慎类（默认不勾选）：`docker-prune`（停止容器的数据会丢；volume 永不删）· `xcode-archives`（历史符号化）· `user-logs`（排障证据）· `trash`（不可恢复）。

项目构建产物：node_modules，仅限 `~/ZCodeProject ~/dev ~/Projects ~/code ~/work ~/workspace ~/workspaces ~/src` 之下、目录名恰为 node_modules，清后需重新 install。dist/build/.venv 等产物不在此技能范围内。

## 边界与惯例

- 官方命令优先：brew/npm/pnpm/pip/uv 用各自 cache 清理命令，失败时回退清缓存目录（brew 回退清 `~/Library/Caches/Homebrew` 下载缓存——brew cleanup 常因缓存里损坏的半截下载包启动失败，回退顺带修掉）；docker/simctl 失败只报告不回退。npm 的 `_npx`（npx 包缓存）官方命令不覆盖，走 always_clear_dirs 顺带清。
- 清理后空间没涨 → 查 APFS 本地快照：`tmutil listlocalsnapshots /`，**只报告**并建议用户自己跑 `sudo tmutil thinlocalsnapshots / 999999999999 4`，不代跑（需 sudo）。
- `clean.py --list` 可随时列白名单；`clean.py` 拒绝任意路径参数与 root 运行。
- Linux 上跑：脚本兼容，但只有跨平台缓存类（npm/pnpm/gradle/HF…）会命中，macOS 专属路径自然跳过。
