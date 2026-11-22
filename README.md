# CLIP STUDIO 启动器汉化补丁（简体中文）

把 **CLIP STUDIO 启动器** 的繁体中文界面转为简体中文。

> 适用于 **国际版 CLIP STUDIO 1.5**（含繁体中文资源的版本）。
> 不懂技术也能用：双击 `应用补丁.cmd` 即可。

[English](#english) below.

---

## ⚠️ 重要声明

**本项目不包含、也不分发任何 CELSYS 的版权文件。**

仓库里只有我自己写的转换脚本。补丁在**你自己的电脑上**运行，从你已安装的软件中读取繁体资源、生成简体资源。

- 本工具仅供学习和个人使用
- 请支持正版：[clipstudio.net](https://www.clipstudio.net/)
- CLIP STUDIO PAINT / CLIP STUDIO 是 CELSYS, Inc. 的商标
- 因使用本工具产生的一切后果由使用者自行承担

---

## 适用范围

本仓库包含两个**独立**的补丁，按需选用：

| 补丁 | 作用 | 风险 |
|---|---|---|
| **启动器汉化** | CLIP STUDIO 启动器：繁→简 | 低，可一键还原 |
| **PAINT 汉化** | CLIP STUDIO PAINT：繁→简 + 绕过区域锁 | ⚠️ 高，改可执行文件，见 [风险说明](PAINT_PATCH_RISKS.md) |

先看下面的启动器部分。需要 PAINT 的话跳到 [PAINT 补丁](#paint-补丁)。

---

## 这是什么（启动器）

CLIP STUDIO 的界面语言由系统语言决定。简体中文 Windows 上，国际版会因为
找不到简体资源而**回落到英文界面**。

本项目通过把软件自带的**繁体中文资源逐字转换为简体**，让你的启动器显示简体中文。

### 效果

| 部位 | 转换前 | 转换后 |
|---|---|---|
| 左侧菜单 | Manage works / 作品管理 | 管理作品 |
| 主内容区 | 製作同人 / Manage works | 制作同人 |
| 按钮与提示 | 您是否遇到困難 | 您是否遇到困难 |

### 已知限制

- **资讯区仍显示繁体**：新闻、活动等文字来自 CELSYS 服务器推送，
  不在本地文件里，本工具无法转换。
- 国际版本身没有简体资源，本工具是从繁体**逐字转换**的，
  个别词汇会保留台湾用法（如「软体」「资讯」而非「软件」「信息」）。
- **软件升级会覆盖补丁**，升级后需重新运行一次。
- 仅测试过 1.11.6 版本，其他版本可能结构不同。

---

## 使用方法

### 前提

- Windows
- 已安装国际版 CLIP STUDIO 1.5（含繁体中文资源）
- Python 3.9+（[下载](https://www.python.org/downloads/)）

### 步骤

1. 下载本仓库（点 Code → Download ZIP，或 `git clone`）
2. 双击 **`应用补丁.cmd`**
3. 按提示操作，完成后启动 CLIP STUDIO 查看效果

### 还原

双击 **`还原原版.cmd`**，会从备份恢复。

备份位置：`%USERPROFILE%\.csp-l10n-backup\`

### 找不到安装目录？

工具会自动搜索常见位置。若失败，手动指定：

```cmd
set CELSYS_ROOT=D:\Program Files\CELSYS\CLIP STUDIO 1.5
python patch_resource.py
```

### 只预览不改动

```cmd
python patch_resource.py --dry-run
python patch_menu.py --dry-run
```

---

## 技术原理

想改别的东西的话，这部分可能有用。

### 1. 界面文字来自两处

| 位置 | 内容 |
|---|---|
| `<安装目录>\CLIP STUDIO\resource\<语言>\*.js` | 主内容区、对话框、按钮 |
| `%APPDATA%\CELSYSUserData\CELSYS\CLIPStudioVer1_5_0\MENU\1\assets\side_menu.js` | 左侧菜单 |

**注意**：安装目录里的 `Settings\CLIP STUDIO2\<ver>\` 下的 `side_menu.js`
**不是**启动器读取的那份。真正的菜单脚本在**用户数据目录**。这一点如果不注意，
改多久都不会生效。

简体中文系统会被映射到 `resource\english\` 目录（国际版没有 `chinese_sc`）。
所以补丁的做法是：把 `resource\chinese_tc\` 的内容转成简体后写进 `resource\english\`。

### 2. 资源文件是带长度前缀的字符串池

`resource\<语言>\` 下的 GUID 命名文件，结构是：

```
[4 字节大端长度] [UTF-8 文本] [4 字节大端长度] [UTF-8 文本] ...
```

紧凑排列，**没有分隔符**。

这意味着：

- **必须逐字转换**。用词组转换（如「縮圖 → 缩略图」，2 字变 3 字）会改变
  字节长度，破坏后面的长度头，启动器会直接崩溃（`0xC0000005`）。
- 解析时**不能跳过零字节**。跳过填充零会吃掉下一个长度头的 4 个 `0x00`，
  导致其后所有字符串漏读（实测覆盖率从 100% 掉到 65%）。

这两点都是实测踩出来的坑，代码里有注释说明。

### 3. 定位真实文件的方法

如果想知道程序实际读了哪些文件，可以用 [Frida](https://frida.re/) hook `CreateFileW`：

```javascript
Interceptor.attach(Module.getExportByName('kernel32.dll', 'CreateFileW'), {
  onEnter(args) {
    console.log(args[0].readUtf16String());
  }
});
```

本项目就是这么发现「真正读的是用户数据目录」的。

---

## PAINT 补丁

> ⚠️ **使用前必读：[PAINT_PATCH_RISKS.md](PAINT_PATCH_RISKS.md)**
>
> 这个补丁会**修改可执行文件**，并且包含**区域锁绕过**，
> 法律与技术风险都和启动器补丁不同。

### 它解决什么问题

国际版 CLIP STUDIO PAINT 在简体中文系统上：

1. 找不到 `chinese_sc` 资源 → 界面回落英文
2. 即使手工造出 `chinese_sc` 目录 → 触发「以非工作對象的作業系統啟動了程式」锁区提示

### 补丁内容

改 `CLIPStudioPaint.exe` 的 2 个字节：

| 偏移 | 原值 | 新值 | 作用 | 性质 |
|---|---|---|---|---|
| `0x12B7D20` | `04` | `05` | 简体系统加载 `chinese_tc` 资源 | 语言映射 |
| `0x12B791F` | `75` | `EB` | 区域检查 `jne`→`jmp` | **区域锁绕过** |

**默认只应用第一处**（语言转换）。第二处需显式加参数：

```cmd
python patch_paint.py --apply                            # 只转语言
python patch_paint.py --apply --allow-region-bypass      # 同时绕过区域锁
```

### 使用方法

双击 **`PAINT补丁.cmd`**，按提示操作。

手动方式：

```cmd
python patch_paint.py --check    # 先看状态
python patch_paint.py --apply    # 应用
python patch_paint.py --restore  # 还原
```

### 安全机制

- **SHA-256 强校验**：只对已验证的原版（1.11.6.0）执行，其他版本直接拒绝
- **自动备份**：`%USERPROFILE%\.csp-l10n-backup\paint\`
- **可增量应用**：先转语言、发现锁区再加绕过，不会走进死路
- **可还原**：`--restore` 一键回退

### 为什么这么谨慎

这个补丁改的是 62.6 MB 可执行文件的内部指令。偏移写错了，
程序就废了。所以脚本宁可拒绝执行，也不冒险。

而且——**如果条件允许，升级软件比打补丁更好**：CELSYS 在 2025 年 7 月的
版本里已经正式支持简体中文，不需要任何补丁。

---

## 依赖

- [opencc-python-reimplemented](https://github.com/yichen0831/opencc-python)
  （Apache-2.0）—— 繁简转换词典

```cmd
pip install opencc-python-reimplemented
```

---

## 开源协议

脚本部分采用 **MIT License**，详见 [LICENSE](LICENSE)。

再次强调：协议只覆盖本项目作者编写的代码。CELSYS 的软件资源不在其中。

---

---

# English

A tool that converts the **CLIP STUDIO (launcher)** interface from
Traditional Chinese to Simplified Chinese.

**This repository contains NO copyrighted CELSYS files.** It only ships
conversion scripts; the patch runs on your own machine against your own
installed copy.

### Requirements

- Windows
- CLIP STUDIO 1.5 (International version, with Traditional Chinese resources)
- Python 3.9+

### Usage

1. Download this repo
2. Double-click `应用补丁.cmd` (apply patch)
3. Restart CLIP STUDIO

To restore: double-click `还原原版.cmd`

Backups are stored in `%USERPROFILE%\.csp-l10n-backup\`.

### Why it works

Interface strings live in two places:

- `<install>\CLIP STUDIO\resource\<lang>\*` — main content
- `%APPDATA%\CELSYSUserData\...\MENU\1\assets\side_menu.js` — left menu
  (**not** the copy under the install dir)

Resource files are length-prefixed UTF-8 string pools. Conversion must be
**character-by-character** so byte lengths never change, otherwise the
launcher crashes.

### License

MIT for the scripts. CLIP STUDIO is a trademark of CELSYS, Inc.
Please buy the software: [clipstudio.net](https://www.clipstudio.net/)
