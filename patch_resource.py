#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 CLIP STUDIO 启动器的本地化资源从繁体转为简体。

用法:
    python patch_resource.py            # 应用
    python patch_resource.py --dry-run  # 只统计不写入
    python patch_resource.py --restore  # 从本仓库外的备份还原

原理:
    启动器按系统语言查 resource\\<lang>\\ 目录。简体中文系统被映射到
    "english"（因为国际版没有 chinese_sc 目录）。本脚本把
    resource\\chinese_tc\\ 的繁体内容逐字转成简体，写入 resource\\english\\。

    替换前会自动备份到 <本仓库外> 的 .csp-l10n-backup/ 目录。
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

BACKUP_DIR = os.path.join(os.path.expanduser("~"), ".csp-l10n-backup", "resource")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只统计，不写入")
    ap.add_argument("--restore", action="store_true", help="从备份还原")
    args = ap.parse_args()

    root = common.find_clipstudio_root()
    res = os.path.join(root, "CLIP STUDIO", "resource")
    src = os.path.join(res, "chinese_tc")
    dst = os.path.join(res, "english")

    print(f"安装目录: {root}")

    if not os.path.isdir(src):
        common.die(f"找不到繁体资源目录: {src}\n"
                   "       请确认安装的是含繁体中文本地化的国际版。")

    # ---------------------------------------------------------- 还原
    if args.restore:
        if not os.path.isdir(BACKUP_DIR):
            common.die(f"没有找到备份: {BACKUP_DIR}")
        print(f"从备份还原: {BACKUP_DIR}")
        for d in ("english", "other"):
            target = os.path.join(res, d)
            backup = os.path.join(BACKUP_DIR, d)
            if not os.path.isdir(backup):
                print(f"  跳过 {d}（无备份）")
                continue
            os.makedirs(target, exist_ok=True)
            for name in os.listdir(backup):
                shutil.copy2(os.path.join(backup, name),
                             os.path.join(target, name))
            print(f"  已还原 {d}")
        return

    # ---------------------------------------------------------- 备份
    if not args.dry_run:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        for d in ("english", "other"):
            target = os.path.join(res, d)
            backup = os.path.join(BACKUP_DIR, d)
            if os.path.isdir(target) and not os.path.isdir(backup):
                shutil.copytree(target, backup)
                print(f"已备份 {d} -> {backup}")

    # ---------------------------------------------------------- 转换
    CharConverter = common.load_opencc()
    cc = CharConverter()  # 逐字转换，严格保持字数（= 字节长度）

    total_seg = total_chars = total_skip = 0
    print("\n开始转换（逐字，保持字节长度）:")
    for name in sorted(os.listdir(src)):
        sp = os.path.join(src, name)
        if not os.path.isfile(sp):
            continue
        dp = os.path.join(dst, name)

        if args.dry_run:
            data = open(sp, "rb").read()
            entries = common.parse_string_pool(data)
            n_changed = sum(1 for _, _, s in entries if cc.convert(s) != s)
            print(f"  {name[:8]}  字符串 {len(entries):<5} 需转换 {n_changed}")
            total_seg += n_changed
            continue

        n, seg, chars, skip = common.convert_resource(sp, dp, cc)
        total_seg += seg
        total_chars += chars
        total_skip += skip
        if seg or skip:
            print(f"  {name[:8]}  串 {n:<5} 转换 {seg:<4} 字 {chars:<5} 跳过 {skip}")

    print()
    if args.dry_run:
        print(f"[试运行] 需转换字符串约 {total_seg} 条，未写入任何文件。")
    else:
        print(f"完成：转换 {total_seg} 段 / {total_chars} 字，"
              f"因长度不符跳过 {total_skip} 段。")
        print("提示：重启 CLIP STUDIO 启动器查看效果。")


if __name__ == "__main__":
    main()
