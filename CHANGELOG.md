# 更新日志

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.1.0] - 2026-11-22

新增 **PAINT 补丁**（CLIP STUDIO PAINT 本体繁→简）。

### 新增

- `patch_paint.py`：改 `CLIPStudioPaint.exe` 两个字节
  - `0x12B7D20`: `04` → `05`（简体系统加载 chinese_tc）
  - `0x12B791F`: `75` → `EB`（区域检查 jne→jmp，**区域锁绕过**）
- `PAINT补丁.cmd`：交互式双击脚本
- `PAINT_PATCH_RISKS.md`：风险说明（法律 + 技术）

### 安全设计

- SHA-256 强校验，只对已验证的 1.11.6.0 原版执行
- **默认只做语言转换**，区域锁绕过需显式 `--allow-region-bypass`
- 支持增量应用（先转语言，遇锁区提示再加绕过）
- 自动备份 + `--restore` 一键还原

---

## [1.0.0] - 2026-11-22

首个可用版本。已验证 CLIP STUDIO **1.11.6**（国际版）。

### 功能

- **资源文件转换**：把 `resource\chinese_tc\` 的繁体内容逐字转为简体，
  写入 `resource\english\`（简体中文系统实际加载的目录）
- **菜单脚本转换**：处理 `%APPDATA%\CELSYSUserData\...\MENU\1\assets\side_menu.js`
  中的 4 个语言块（两套 `en-us` + 两套 `zh-tw`）
- **自动备份与还原**：首次运行自动备份到 `%USERPROFILE%\.csp-l10n-backup\`，
  可用 `还原原版.cmd` 一键回滚
- **自动探测安装路径**：支持环境变量 `CELSYS_ROOT` 覆盖

### 技术要点

这两点都是实测踩出来的，改动时务必保留：

1. **必须逐字转换**
   资源包是 `[4字节大端长度][UTF-8文本]` 紧凑字符串池。
   用词组转换（如「縮圖→缩略图」，2 字变 3 字）会改变字节长度，
   破坏后续长度头，启动器直接崩溃（`0xC0000005`）。

2. **解析时不能跳过填充零**
   跳过零字节会吃掉下一个长度头的 4 个 `0x00`，
   导致其后所有字符串漏读——实测覆盖率从 100% 掉到 65%。

### 零依赖

内置 4057 条繁简单字映射（`data/t2s_characters.txt`，源自 opencc
的 `TSCharacters.txt`，Apache-2.0，已过滤为 1 对 1 映射）。
不需要 `pip install`。

### 已知限制

- 资讯区（新闻、活动）文字来自 CELSYS 服务器推送，无法转换，仍显示繁体
- 国际版无简体资源，本工具是逐字转换，部分词汇保留台湾用法
  （「软体」「资讯」等）
- 软件升级会覆盖补丁，升级后需重新运行
- 仅测试 1.11.6，其他版本资源结构可能不同

### 致谢

- [opencc](https://github.com/BYVoid/OpenCC) / 
  [opencc-python](https://github.com/yichen0831/opencc-python) —— 繁简词典数据
- [Frida](https://frida.re/) —— 用于定位程序实际加载的资源文件
