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
| 云端页面 | 復原應用程式設定 | **恢复**应用程序设置 |
| 按钮与提示 | 您是否遇到困難 | 您是否遇到困难 |

### 已完成的工作

除了繁→简逐字转换，还做了**台湾用语本地化**（1654 处，72 条规则）：

| 台湾用语 | 大陆用语 | 处数 |
|---|---|---|
| 设定 | 设置 | 394 |
| 执行 | 运行 | 207 |
| 资料 | 数据 | 126 |
| 资料夹 | 文件夹 | 121 |
| 档案 | 文件 | 120 |
| 建立 | 创建 | 120 |
| 程式 | 程序 | 114 |
| 资讯 | 信息 | 55 |
| 素材集 | 素材库 | 50 |
| 物件 | 对象 | 49 |
| 支援 | 支持 | 40 |
| 开启 | 打开 | 38 |
| 向量 | 矢量 | 35 |
| 渐层 | 渐变 | 31 |
| 复原 | 恢复 | 28 |
| 选单 | 菜单 | 24 |
| 预设 | 默认 | 22 |
| 记忆体 | **内存** | 4 |
| 彩度 | **饱和度** | 8 |
| 缩图 | **缩略图** | 13 |
| 点阵图 | **栅格图** | 10 |
| 外挂程式 | **插件** | 16 |
| 范本 | **模板** | 12 |
| 专案 | **项目** | 10 |
| 磁碟机 | **磁盘** | 9 |
| 图示 | **图标** | 6 |
| 滑鼠 | **鼠标** | 3 |

完整词表（含每条替换的取舍理由）见 [`terms_tw2cn.py`](terms_tw2cn.py)。

### v1.4.0：字符串长度终于可以变化了

v1.3.0 及以前只能做**等字数**替换，所以「记忆体→内存」（3→2）、
「彩度→饱和度」（2→3）这类词只能放弃。

v1.4.0 弄清了资源包的真实结构——**它本来就允许长度变化**：

```
任意节点 = [u32 子节点数 N][N × {u32 id, u32 绝对 offset, u32 长度}]
叶子     = [u32 字节长度][UTF-8 文本]
```

每一层都自带 `offset` / `length`，所以改完字符串只要**自底向上把所有
offset/长度重算一遍**即可，不需要长度相等。早期版本只替换了文本字节、
没有同步父节点的三元组，才会一改就崩（`0xC0000005`）。

**证据一：CELSYS 自己的语言包长度就不一样。**
同一个 GUID 在 8 种语言下结构完全相同，但体积不同——这只有在加载器
运行期解析 offset/length 时才可能：

| GUID | 英文 | 繁体中文 | 日文 | 法文 |
|---|---|---|---|---|
| `DD705E0D` | 294494 | 294494 | 306132 | 306587 |
| `E79C2AC5` | 1224794 | 1224794 | 1263178 | 1268520 |
| `7F9F9530` | 435893 | 435893 | 439673 | 439035 |

（英文与繁体中文恰好一样大，是因为本补丁用的就是等长替换。）

**证据二：逐字节往返验证。** 20 个资源包解析后原样重建，
**20/20 与原始文件逐字节完全一致**，说明解析器对文件结构的理解是对的。

**证据三：真机实测。** 把左侧菜单里可见的「设置3D素材」改成长度多出
5 个字的字符串，重启启动器后菜单上真实显示出改动后的文字，界面排版
正常、无崩溃。

因此 v1.4.0 新增了 [`varlen.py`](varlen.py)（资源包解析/重建器），
并把 `patch_resource.py` 改成「繁简转换 + 台湾用语替换」一趟完成。

### 为什么有的词**故意**不改

| 台湾用语 | 候选大陆用语 | 不改的原因 |
|---|---|---|
| 透明度 | 不透明度 | 日文原文就是「透明度影響/透明度置換」，指的是**透明度**而非不透明度；且文中已有 43 处「不透明度」，盲目替换会变成「不不透明度」 |
| 中断 | 断开 | 「中断」在大陆中文里同样成立（「线不会中断」） |
| 扩充 | 扩展 | 「扩充」在大陆中文里同样成立（「拉丁字母扩充-A」） |

「全萤幕／浮水印／锐利化／功能表／素材夹」在启动器资源包中**0 处出现**
（可能只在 PAINT / MODELER 的资源里），所以本次不涉及。

### 已知限制

- **资讯区仍显示繁体**：新闻、活动等文字来自 CELSYS 服务器推送，
  不在本地文件里，本工具无法转换。
- 界面已经全部是简体、台湾用语基本本地化，但**不是官方译文**：
  个别句子仍是繁体版的行文习惯。
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

### 1. 界面文字来自三处

| 位置 | 内容 |
|---|---|
| `<安装目录>\CLIP STUDIO\resource\<语言>\<GUID>` | 主内容资源包（无扩展名，二进制） |
| `<安装目录>\CLIP STUDIO\Settings\CLIP STUDIO2\<ver>\HTML\resource\page.js` | **页面文字**（云端设置、版本信息、素材管理等） |
| `%APPDATA%\CELSYSUserData\CELSYS\CLIPStudioVer1_5_0\MENU\1\assets\side_menu.js` | 左侧菜单 |

**两个大坑**：

- 安装目录里的 `Settings\CLIP STUDIO2\<ver>\` 下的 `side_menu.js`
  **不是**启动器读取的那份。真正的菜单脚本在**用户数据目录**。
- `page.js` 里按语言分块（`langText['ja-jp']` / `['en-us']` / `['zh-tw']` …），
  但简体中文系统实际加载的是 **`zh-tw` 块**，不是 `en-us` 块。

简体中文系统会被映射到 `resource\english\` 目录（国际版没有 `chinese_sc`）。
所以资源补丁的做法是：把 `resource\chinese_tc\` 的内容转成简体后写进 `resource\english\`。

### 2. 资源文件是「自描述」的段树

`resource\<语言>\` 下的 GUID 命名文件（无扩展名）不是平铺的字符串池，
而是一棵**带绝对偏移的段树**：

```
任意节点 = [u32 子节点数 N] [N × { u32 id, u32 绝对offset, u32 长度 }]
叶子     = [u32 字节长度] [UTF-8 文本]
```

整个文件本身就是一个节点：文件开头就是根节点的子节点表（通常是 3 个
子段），同层子节点**首尾相接、无空隙**，`offset` 是相对整个文件的绝对
偏移。

这意味着：

- **字符串长度可以自由变化**。改完文本后自底向上重算每一层的
  `offset` / `长度` 即可（见 [`varlen.py`](varlen.py)）。
  早期版本以为「长度一变就崩」，其实是因为只替换了文本字节、
  没有维护父节点的三元组——那确实会崩（`0xC0000005`）。
- **解析时不能靠扫描猜**。按长度前缀在二进制里逐字节试，会把二进制
  数据误判成字符串（实测覆盖率极低）；必须按段树解析。
- **无法识别的节点原样保留**。资源包里大约 90% 字节是二进制数据
  （着色器、属性表等），解析器遇到不认识的节点会当作不透明数据
  整段复制，因此重建结果永远字节级安全。

自检方式（只读，不写入）：

```cmd
python varlen.py "D:\Program Files\CELSYS\CLIP STUDIO 1.5\CLIP STUDIO\resource\english"
python patch_resource.py --verify
```

第一条会做「解析 → 原样重建 → 与原始字节比较」的往返验证。

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

Interface strings live in three places:

- `<install>\CLIP STUDIO\resource\<lang>\<GUID>` — main content resource packs
- `<install>\CLIP STUDIO\Settings\CLIP STUDIO2\<ver>\HTML\resource\page.js`
  — cloud/settings pages
- `%APPDATA%\CELSYSUserData\...\MENU\1\assets\side_menu.js` — left menu
  (**not** the copy under the install dir)

Resource packs are **self-describing segment trees**, not flat string pools:

```
node = [u32 child_count N] [N × { u32 id, u32 absolute_offset, u32 length }]
leaf = [u32 byte_length] [UTF-8 text]
```

Every level carries its own offsets, so string lengths may change freely —
you just recompute all offsets bottom-up (`varlen.py`). CELSYS' own language
packs prove this: the same GUID has an identical tree in 8 languages but a
different file size in each (e.g. `DD705E0D` is 294494 bytes in English and
306132 in Japanese).

v1.4.0 uses this to also localize Taiwanese vocabulary whose mainland
equivalent has a different character count (`記憶體 → 内存`, `彩度 → 饱和度`,
`縮圖 → 缩略图`, `外掛程式 → 插件`, …).

### License

MIT for the scripts. CLIP STUDIO is a trademark of CELSYS, Inc.
Please buy the software: [clipstudio.net](https://www.clipstudio.net/)
