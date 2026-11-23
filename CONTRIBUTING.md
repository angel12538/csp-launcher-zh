# 贡献指南

感谢愿意帮忙！这个项目不大，几条约定即可。

## 能做什么

- **报告问题**：用 [Issue 模板](.github/ISSUE_TEMPLATE/bug_report.md)
- **补充术语修正**：见下方「术语表」
- **补充行文改写**：见下方「整句规则」
- **适配新版本**：CLIP STUDIO 升级后文件结构可能变化
- **改文档**：README 有错或不清楚的地方

## 不能做什么

- **不要提交任何 CELSYS 的文件**（exe、资源包、JS 脚本、截图里的界面素材等）
- 不要把转换后的资源文件上传到仓库
- 不要提交从网盘等渠道获取的第三方汉化包

判断标准很简单：**只要不是你/我能自己写出来的代码或文档，就不要提交。**

---

# 开发者笔记

以下内容只是给要改代码的人看的，普通用户不需要了解。

## 界面文字在哪里

| 位置 | 内容 |
|---|---|
| `<安装目录>\CLIP STUDIO\resource\<语言>\<GUID>` | 主内容资源包（无扩展名，二进制） |
| `<安装目录>\CLIP STUDIO\Settings\CLIP STUDIO2\<ver>\HTML\resource\page.js` | 页面文字（云端设置、版本信息、素材管理等） |
| `%APPDATA%\CELSYSUserData\CELSYS\CLIPStudioVer1_5_0\MENU\1\assets\side_menu.js` | 左侧菜单 |

两个坑：

- 安装目录里 `Settings\CLIP STUDIO2\<ver>\` 下的 `side_menu.js` **不是**
  启动器读取的那份，真正生效的在**用户数据目录**。
- `page.js` 按语言分块（`langText['ja-jp']` / `['en-us']` / `['zh-tw']` …），
  但简体系统实际加载的是 **`zh-tw` 块**。

简体中文系统被映射到 `resource\english\`（国际版没有 `chinese_sc`），
所以资源补丁的做法是：把 `resource\chinese_tc\` 转成简体后写进
`resource\english\`。

## 资源包格式

GUID 文件不是平铺的字符串池，而是一棵**带绝对偏移的段树**：

```
任意节点 = [u32 子节点数 N] [N × { u32 id, u32 绝对 offset, u32 长度 }]
叶子     = [u32 字节长度] [UTF-8 文本]
```

整个文件就是根节点，同层子节点首尾相接、无空隙。每一层都自带
`offset` / `length`，所以**字符串长度可以自由变化**——改完文本后
自底向上重算所有偏移即可（[`varlen.py`](varlen.py)）。

注意三点：

- 按长度前缀在二进制里逐字节扫描会误判（覆盖率很低），必须按段树解析。
- 不认识的节点当作不透明数据整段保留，因此重建永远字节级安全。
- 含日文假名的叶子要跳过，资源包里混着 GLSL 注释和日文素材名。

自检（只读）：

```cmd
python varlen.py "D:\Program Files\CELSYS\CLIP STUDIO 1.5\CLIP STUDIO\resource\english"
python patch_resource.py --verify
```

## 术语表与整句规则

词表在 [`terms_tw2cn.py`](terms_tw2cn.py)，分两张表：

- `TERM_MAP`：词级替换，长词优先
- `SENTENCE_MAP`：整句重写，跑在词级替换**之后**

为什么要分两阶段：整句的键是在词级替换**之后**的文本上匹配的。
例如原句「請執行下記任一項步驟」，词级先把「執行」变成「运行」，
整句规则才能匹配到「请运行下记任一项步骤」。混在一张表里按长度排序时，
「下记→下列」会把整句的键提前改坏。

同理，凡是键里含旧规则替换目标（如「行动网路」里的「网路」会被
`网路→网络` 改掉），键必须写**原始形态**。

加规则时请顺便自测：

```cmd
python terms_tw2cn.py                 # 列出全部规则
python patch_resource.py --dry-run    # 统计改动量
python patch_terms.py --dry-run       # JS 侧
```

改完规则后建议检查两条不变式（本项目就是这么抓 bug 的）：

1. **幂等性**：替换文本再跑一遍规则不应被二次改动
   （例如「将可 → 将可以」会在「将可以」上叠加成「将可以以」）。
2. **活规则**：每条键都应能在「繁→简后」的语料里命中，
   否则说明键写成了替换后的形态。

## 代码风格

- Python 遵循 PEP 8，4 空格缩进
- 中文注释没问题，这个项目就是中文项目
- 关键逻辑写注释说明「为什么」，别只写「做了什么」

## 提交前自测

```cmd
python patch_resource.py --dry-run
python patch_menu.py --dry-run
python patch_pagejs.py --dry-run
python patch_terms.py --dry-run
```

然后实际跑一次补丁，确认：

1. 启动器能正常启动（不崩溃）
2. 界面是简体中文、没有乱码或空白
3. `还原原版.cmd` 能成功还原
