#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把启动器左侧菜单脚本（side_menu.js）的语言块转为简体。

用法:
    python patch_menu.py            # 应用
    python patch_menu.py --dry-run  # 只统计
    python patch_menu.py --restore  # 从备份还原

原理:
    启动器左侧菜单的文字不在安装目录，而在用户数据目录:
      %APPDATA%\\CELSYSUserData\\CELSYS\\CLIPStudioVer1_5_0\\MENU\\1\\assets\\side_menu.js

    该文件里有**两套**语言块（前面一套供启动器主界面、后面一套供其他页面），
    每套都含 ja-jp / en-us / zh-tw / ko-kr / fr-fr / es-es / de-de。
    简体中文系统会落到 zh-tw 块，所以本脚本把两套的 zh-tw 与 en-us 块
    中的中文逐字转为简体（JS 里没有长度前缀，但逐字转换最安全）。
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

BACKUP_FILE = os.path.join(os.path.expanduser("~"), ".csp-l10n-backup",
                           "side_menu.js")

LANGS = ("zh-tw", "en-us")


def find_object(text, brace):
    """从 { 起找到配对的 }，跳过字符串字面量。"""
    depth = 0
    i = brace
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == '"':
                    break
                i += 1
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("括号不平衡")


def find_blocks(text, lang):
    key = '"%s":{' % lang
    out = []
    i = 0
    while True:
        k = text.find(key, i)
        if k < 0:
            break
        b = k + len(key) - 1
        e = find_object(text, b)
        out.append((k, e + 1))
        i = e + 1
    return out


def to_simplified_block(block, cc):
    """逐字转简体，保证 UTF-8 字节长度不变。"""
    out = []
    for ch in block:
        if "\u4e00" <= ch <= "\u9fff":
            out.append(cc.convert(ch))
        else:
            out.append(ch)
    new = "".join(out)
    assert len(new.encode("utf-8")) == len(block.encode("utf-8"))
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    path = common.userdata_menu_js()
    print(f"菜单脚本: {path}")

    if args.restore:
        if not os.path.isfile(BACKUP_FILE):
            common.die(f"没有找到备份: {BACKUP_FILE}")
        shutil.copy2(BACKUP_FILE, path)
        print("已从备份还原")
        return

    CharConverter = common.load_opencc()
    cc = CharConverter()

    with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
        js = f.read()
    original_len = len(js)

    blocks = []
    for lang in LANGS:
        for s, e in find_blocks(js, lang):
            blocks.append((s, e, lang))
    if not blocks:
        common.die("未找到任何语言块，文件格式可能已变化")

    print(f"找到 {len(blocks)} 个语言块: " +
          ", ".join(f"{l}@{s}" for s, _, l in sorted(blocks)))

    if args.dry_run:
        changed = 0
        for s, e, lang in blocks:
            nb = to_simplified_block(js[s:e], cc)
            if nb != js[s:e]:
                changed += 1
        print(f"[试运行] {changed} 个块需要转换，未写入。")
        return

    # 备份（仅首次）
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    if not os.path.isfile(BACKUP_FILE):
        shutil.copy2(path, BACKUP_FILE)
        print(f"已备份 -> {BACKUP_FILE}")

    # 从后往前替换，避免偏移失效
    new_js = js
    for s, e, lang in sorted(blocks, reverse=True):
        nb = to_simplified_block(new_js[s:e], cc)
        if nb != new_js[s:e]:
            new_js = new_js[:s] + nb + new_js[e:]
            print(f"  转换 {lang} 块 @{s}")

    with open(path, "w", encoding="utf-8", errors="surrogateescape",
              newline="") as f:
        f.write(new_js)

    print(f"\n完成：{original_len} -> {len(new_js)} 字符")
    print("提示：重启 CLIP STUDIO 启动器查看效果。")


if __name__ == "__main__":
    main()
