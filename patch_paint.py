#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLIP STUDIO PAINT 繁体中文界面补丁（1.11.6）。

⚠️ 请先阅读本目录下的 PAINT_PATCH_RISKS.md

用法:
    python patch_paint.py --check       # 只检查文件与版本，不改动
    python patch_paint.py --apply       # 应用补丁
    python patch_paint.py --restore     # 从备份还原
"""

import argparse
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402

# 已验证的原版哈希（CLIP STUDIO PAINT 1.11.6.0, 2021-12-13）
KNOWN_ORIGINAL = {
    "A52F438426BCA11651A1581816F4DC921B2E95AC4A5BE86FB9A51F5A3225C9E7":
        "1.11.6.0 (2021-12-13)",
}

BACKUP_DIR = os.path.join(os.path.expanduser("~"), ".csp-l10n-backup", "paint")

# 补丁点定义
# (文件偏移, 原值, 新值, 说明)
PATCHES = [
    (0x12B7D20, 0x04, 0x05,
     "LCID 0x0804(简体中国) 的资源 case 从 chinese_sc 改为 chinese_tc"),
    (0x12B791F, 0x75, 0xEB,
     "区域检查 jne -> jmp：跳过中国区分支，避免「非工作對象」锁区提示"),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def find_paint_exe():
    root = common.find_clipstudio_root()
    exe = os.path.join(root, "CLIP STUDIO PAINT", "CLIPStudioPaint.exe")
    if not os.path.isfile(exe):
        common.die(f"找不到 CLIPStudioPaint.exe：{exe}")
    return exe


def read_byte(path, offset):
    with open(path, "rb") as f:
        f.seek(offset)
        return f.read(1)[0]


def check_state(exe):
    """返回 (每个补丁点的状态列表, 是否完全打补丁, 是否完全原版)。"""
    actual = [read_byte(exe, off) for off, _, _, _ in PATCHES]
    states = []
    for (off, old, new, desc), cur in zip(PATCHES, actual):
        if cur == new:
            states.append("patched")
        elif cur == old:
            states.append("original")
        else:
            states.append("unknown")

    print(f"文件: {exe}")
    print(f"大小: {os.path.getsize(exe):,} 字节")
    print(f"SHA256: {sha256(exe)}")
    print()
    label = {"patched": "已打补丁", "original": "原版", "unknown": "未知"}
    for (off, old, new, desc), cur, st in zip(PATCHES, actual, states):
        print(f"  0x{off:X}: 0x{cur:02X}  (原 0x{old:02X} / 新 0x{new:02X})  [{label[st]}]")
        print(f"      {desc}")

    all_patched = all(s == "patched" for s in states)
    all_original = all(s == "original" for s in states)
    return states, all_patched, all_original


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只检查，不改动")
    ap.add_argument("--apply", action="store_true", help="应用补丁")
    ap.add_argument("--restore", action="store_true", help="从备份还原")
    ap.add_argument("--allow-region-bypass", action="store_true",
                    help="同时应用区域锁绕过（默认只做语言转换）")
    args = ap.parse_args()

    if not any([args.check, args.apply, args.restore]):
        ap.print_help()
        return

    exe = find_paint_exe()
    backup = os.path.join(BACKUP_DIR, "CLIPStudioPaint.exe")

    # ---------------------------------------------------------- 还原
    if args.restore:
        if not os.path.isfile(backup):
            common.die(f"没有找到备份：{backup}")
        print(f"从备份还原：{backup}")
        shutil.copy2(backup, exe)
        print("已还原为原版")
        return

    # ---------------------------------------------------------- 检查
    states, all_patched, all_original = check_state(exe)
    print()

    if args.check:
        if all_patched:
            print("状态：已完整打补丁")
        elif all_original:
            print("状态：未打补丁（原版）")
        else:
            print("状态：部分打补丁（可继续应用剩余部分）")
        return

    # ---------------------------------------------------------- 应用
    if all_patched:
        print("已经是完整打过补丁的状态，无需重复操作。")
        return

    # 需要改动哪些点
    wanted = PATCHES if args.allow_region_bypass else [PATCHES[0]]
    todo = []
    for idx, (off, old, new, desc) in enumerate(PATCHES):
        if (off, old, new, desc) not in wanted:
            continue
        if states[idx] == "patched":
            continue
        if states[idx] == "unknown":
            common.die(f"0x{off:X} 处字节为 0x{read_byte(exe, off):02X}，"
                       f"既非原版 0x{old:02X} 也非补丁值 0x{new:02X}。\n"
                       "       为避免损坏，已中止（文件未改动）。")
        todo.append((off, old, new, desc))

    if not todo:
        print("目标补丁点均已应用，无需操作。")
        return

    # 版本校验：只在完全原版时强制校验哈希
    if all_original:
        cur_hash = sha256(exe)
        if cur_hash not in KNOWN_ORIGINAL:
            print("[拒绝执行] 当前文件不是已验证的原版。")
            print(f"  当前 SHA256: {cur_hash}")
            print("  已知原版 SHA256:")
            for h, v in KNOWN_ORIGINAL.items():
                print(f"    {h}  ({v})")
            print()
            print("为避免损坏未知版本，本次不做任何改动。")
            print("如果你确认版本正确，请提交 issue 附上 SHA256，我们会评估适配。")
            sys.exit(1)
        print(f"版本校验通过：{KNOWN_ORIGINAL[cur_hash]}")

        # 备份
        os.makedirs(BACKUP_DIR, exist_ok=True)
        if not os.path.isfile(backup):
            shutil.copy2(exe, backup)
            print(f"已备份原版 -> {backup}")

    if not args.allow_region_bypass and len(todo) == 1 and "区域检查" in todo[0][3]:
        pass
    if len(PATCHES) > len(wanted):
        print("注意：只应用语言转换，未应用区域锁绕过。")
        print("      若出现「非工作對象的作業系統」提示，需加 --allow-region-bypass")

    # 应用
    data = bytearray(open(exe, "rb").read())
    for off, old, new, desc in todo:
        if data[off] != old:
            common.die(f"0x{off:X} 处字节为 0x{data[off]:02X}，"
                       f"期望 0x{old:02X}，已中止（文件未改动）")
        data[off] = new
        print(f"  已修改 0x{off:X}: 0x{old:02X} -> 0x{new:02X}")

    open(exe, "wb").write(data)
    print("\n补丁已写入。")
    print(f"新 SHA256: {sha256(exe)}")
    print("请启动 CLIP STUDIO PAINT 验证。")


if __name__ == "__main__":
    main()
