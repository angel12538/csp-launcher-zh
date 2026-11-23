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

本项目把软件自带的**繁体中文资源转换为简体**、并把台湾用语和日式行文改写为大陆中文，让你的启动器显示简体中文。

### 效果

| 部位 | 转换前 | 转换后 |
|---|---|---|
| 左侧菜单 | Manage works / 作品管理 | 管理作品 |
| 主内容区 | 製作同人 / Manage works | 制作同人 |
| 云端页面 | 復原應用程式設定 | **恢复**应用程序设置 |
| 按钮与提示 | 您是否遇到困難 | 您是否遇到困难 |

### 已完成的工作

除了繁→简逐字转换，还做了**台湾用语与行文本地化**（2796 处，163 条词级
+ 36 条整句规则）：

| 台湾用语 | 大陆用语 | 处数 |
|---|---|---|
| 设定 | 设置 | 394 |
| 变更 | 更改 | 241 |
| 执行 | 运行 | 207 |
| 资料 | 数据 | 126 |
| 档案 / 资料夹 | 文件 / 文件夹 | 241 |
| 参照 | 参考 | 85 |
| 点选 | 点击 | 65 |
| 拖拽 | 拖动 | 55 |
| 套用 | 应用 | 46 |
| 对白框 / 对话方块 | 对话框 | 37 |
| 写出 | 导出 | 30 |
| 摄影机 | 摄像机 | 27 |
| 清单 / 一览 | 列表 | 33 |
| 图元 | 像素 | 26 |
| 元件 | 部件 | 21 |
| 装置 | 设备 | 20 |
| 取得 | 获取 | 20 |
| 传送 | 发送 | 19 |
| 记忆体 | **内存** | 4 |
| 彩度 | **饱和度** | 8 |
| 缩图 | **缩略图** | 13 |
| 点阵图 | **栅格图** | 10 |

**行文层面**的例子（v1.5.0 起）：

| 原（繁体版行文） | 现（大陆中文） |
|---|---|
| 结束的话编辑内容将会消失 | 如果结束，编辑内容将会消失 |
| 请搁置一段时间后运行 | 请稍后重试 |
| 烦请协助配合 | 感谢您的配合 |
| 由于服务器有发生异常的可能性 | 由于服务器可能发生异常 |
| 会介意的用户请稍待至同步结束 | 如果介意，请等到同步结束 |
| 写入中・・・ | 写入中…… |
| 正在复制缩略图跟范例 | 正在复制缩略图和示例 |

完整词表（含每条替换的取舍理由）见 [`terms_tw2cn.py`](terms_tw2cn.py)。

### 为什么有的词**故意**不改

| 台湾用语 | 候选大陆用语 | 不改的原因 |
|---|---|---|
| 透明度 | 不透明度 | 原文指的就是**透明度**，不是不透明度；而且文中已有 43 处「不透明度」，盲目替换会变成「不不透明度」 |
| 中断 | 断开 | 「中断」在大陆中文里同样成立（「线不会中断」） |
| 扩充 | 扩展 | 「扩充」在大陆中文里同样成立（「拉丁字母扩充-A」） |

「全萤幕／浮水印／锐利化／功能表／素材夹」在启动器里没有出现过，
所以本次不涉及。

### 已知限制

- **资讯区仍显示繁体**：新闻、活动等文字来自 CELSYS 服务器推送，
  不在本地文件里，本工具无法转换。
- **「设置3D素材」页的素材分类名仍是台湾用词**（如「身体元件」「渐层」
  「对白框」）。这些名字来自 **CLIP STUDIO MODELER 的资源包**，
  不在启动器资源里，本补丁不处理。
- 界面已经全部是简体、台湾用语与行文都做过本地化，但**不是官方译文**：
  个别长句仍保留繁体版的行文习惯。
- 资源包里 174 条本来就是日文的文本（着色器注释、日文素材名）
  一律跳过，不参与任何替换。
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

| 改动 | 作用 | 性质 |
|---|---|---|
| 语言映射 | 简体系统加载繁体资源 | 语言转换 |
| 区域检查 | 跳过「非工作对象操作系统」提示 | **区域锁绕过** |

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

这个补丁改的是可执行文件内部，改错了程序就废了。所以脚本宁可拒绝执行，
也不冒险。

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

### What it does

The launcher ships a Traditional Chinese localization but no Simplified one,
so on a Simplified Chinese Windows it falls back to English. This patch
rewrites the launcher's own localization data into Simplified Chinese:

- Traditional → Simplified conversion
- Taiwanese vocabulary → mainland vocabulary (e.g. 记忆体 → 内存)
- Japanese-flavoured / Taiwanese sentence patterns → natural mainland phrasing

It also localizes the launcher's page scripts and left menu.

The merchant-visible news feed is pushed from CELSYS servers and stays in
Traditional Chinese.

### License

MIT for the scripts. CLIP STUDIO is a trademark of CELSYS, Inc.
Please buy the software: [clipstudio.net](https://www.clipstudio.net/)
