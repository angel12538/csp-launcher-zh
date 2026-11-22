#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把启动器的页面语言表（page.js）从繁体转为简体。

用法:
    python patch_pagejs.py            # 应用
    python patch_pagejs.py --dry-run  # 只统计
    python patch_pagejs.py --restore  # 从备份还原

背景:
    启动器里很多页面（云端设置、版本信息、素材管理等）的文字不在资源包里，
    而在 JS 语言表:
      Settings\\CLIP STUDIO2\\<ver>\\HTML\\resource\\page.js

    该文件按语言分块: langText['ja-jp'] / ['en-us'] / ['zh-tw'] / ...
    有趣的是，简体中文系统实际加载的是 **zh-tw 块**（实测确认），
    而不是 en-us 块。

本脚本的做法:
    en-us 块通常已被同其他工具转成简体（或本身接近中文），
    所以把 en-us 块的文字逐条复制到 zh-tw 块，实现简体显示。
    两个块的 key 完全对应（langText 211 条 + langLink 1 条）。

    如果 en-us 块不是简体，会自动退化为「逐字转换 zh-tw 块」。
"""

import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

BACKUP_FILE = os.path.join(os.path.expanduser("~"), ".csp-l10n-backup",
                           "page.js")

# 用于判断「是否已经是简体」的繁体特征字
TRAD_MARKERS = set("雲設復備應證軟資訊覽單體類數據開關樣們時會發現種說選確認語讀寫繪顏筆層變換試驗環境")


def find_page_js():
    root = common.find_clipstudio_root()
    settings = os.path.join(root, "CLIP STUDIO", "Settings", "CLIP STUDIO2")
    if not os.path.isdir(settings):
        common.die(f"找不到 Settings 目录: {settings}")
    # 取最高版本号目录
    versions = [d for d in os.listdir(settings)
                if os.path.isdir(os.path.join(settings, d))]
    if not versions:
        common.die("Settings 目录下没有版本目录")
    versions.sort(key=lambda v: [int(x) for x in re.findall(r"\d+", v)] or [0],
                  reverse=True)
    for v in versions:
        p = os.path.join(settings, v, "HTML", "resource", "page.js")
        if os.path.isfile(p):
            return p, v
    common.die("找不到 page.js")


def block_range(lines, table, lang):
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^%s\['%s'\]\s*=\s*\{" % (re.escape(table), re.escape(lang)), ln):
            start = i
            break
    if start is None:
        return None
    for j in range(start + 1, len(lines)):
        if lines[j].strip() in ("};", "}"):
            return (start, j)
    return None


def parse_entries(lines, rng):
    out = {}
    for i in range(rng[0] + 1, rng[1]):
        m = re.match(r"^'([^']+)'\s*:", lines[i])
        if m:
            out[m.group(1)] = i
    return out


def count_trad(lines, rng):
    n = 0
    for i in range(rng[0] + 1, rng[1]):
        if any(c in TRAD_MARKERS for c in lines[i]):
            n += 1
    return n


def do_copy(lines, table):
    """把 en-us 块的值复制到 zh-tw 块。返回替换条数。"""
    en = block_range(lines, table, "en-us")
    tw = block_range(lines, table, "zh-tw")
    if not en or not tw:
        return 0, "块缺失"

    en_map = parse_entries(lines, en)
    tw_map = parse_entries(lines, tw)
    if set(en_map) != set(tw_map):
        return 0, f"键不一致（en {len(en_map)} / tw {len(tw_map)}）"

    changed = 0
    for key, tw_idx in tw_map.items():
        src = lines[en_map[key]]
        m_src = re.match(r"^('([^']+)'\s*:\s*)(['\"])(.*)\3([,]?)\s*$", src, re.S)
        m_dst = re.match(r"^('([^']+)'\s*:\s*)(['\"])(.*)\3([,]?)(\s*)$",
                         lines[tw_idx], re.S)
        if not m_src or not m_dst:
            continue
        value = m_src.group(4)
        prefix, _, q, old, comma, tail = m_dst.groups()
        if value == old:
            continue
        line = f"{prefix}{q}{value}{q}{comma}{tail}"
        if not line.endswith("\n"):
            line += "\n"
        lines[tw_idx] = line
        changed += 1
    return changed, "ok"


def do_convert(lines, table, cc):
    """逐字转换 zh-tw 块（当 en-us 不是简体时的退化方案）。"""
    tw = block_range(lines, table, "zh-tw")
    if not tw:
        return 0
    changed = 0
    for i in range(tw[0] + 1, tw[1]):
        old = lines[i]
        new = "".join(cc.convert(c) if "\u4e00" <= c <= "\u9fff" else c
                      for c in old)
        if new != old:
            lines[i] = new
            changed += 1
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    path, ver = find_page_js()
    print(f"语言表: {path}  (版本目录 {ver})")

    if args.restore:
        if not os.path.isfile(BACKUP_FILE):
            common.die(f"没有找到备份: {BACKUP_FILE}")
        shutil.copy2(BACKUP_FILE, path)
        print("已从备份还原")
        return

    with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
        lines = f.readlines()

    # 检查现状
    tw = block_range(lines, "langText", "zh-tw")
    en = block_range(lines, "langText", "en-us")
    if not tw or not en:
        common.die("找不到 langText 的语言块，文件结构可能已变化")

    tw_trad = count_trad(lines, tw)
    en_trad = count_trad(lines, en)
    print(f"  zh-tw 块: 含繁体字 {tw_trad} 行")
    print(f"  en-us 块: 含繁体字 {en_trad} 行")

    if tw_trad == 0:
        print("\nzh-tw 块已是简体，无需操作。")
        return

    # 决定策略
    use_copy = en_trad == 0
    if use_copy:
        print("\n策略: en-us 块已是简体，直接复制其文字到 zh-tw 块")
    else:
        print("\n策略: en-us 块也含繁体，改为逐字转换 zh-tw 块")
        CharConverter = common.load_opencc()
        cc = CharConverter()

    if args.dry_run:
        print("[试运行] 未写入任何文件。")
        return

    # 备份
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    if not os.path.isfile(BACKUP_FILE):
        shutil.copy2(path, BACKUP_FILE)
        print(f"已备份 -> {BACKUP_FILE}")

    total = 0
    for table in ("langText", "langLink"):
        if use_copy:
            n, msg = do_copy(lines, table)
            print(f"  {table}: 替换 {n} 条 ({msg})")
        else:
            n = do_convert(lines, table, cc)
            print(f"  {table}: 转换 {n} 行")
        total += n

    with open(path, "w", encoding="utf-8", errors="surrogateescape",
              newline="") as f:
        f.writelines(lines)

    print(f"\n完成：共处理 {total} 处")
    print("提示：重启 CLIP STUDIO 启动器，进入云端设置等页面查看效果。")


if __name__ == "__main__":
    main()
