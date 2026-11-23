#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 CLIP STUDIO 启动器的本地化资源从繁体转为简体，并本地化台湾用语。

用法:
    python patch_resource.py            # 应用
    python patch_resource.py --dry-run  # 只统计不写入
    python patch_resource.py --verify   # 只检查当前 english 目录
    python patch_resource.py --restore  # 从本仓库外的备份还原

原理:
    启动器按系统语言查 resource\\<lang>\\ 目录。简体中文系统被映射到
    "english"（因为国际版没有 chinese_sc 目录）。本脚本读取
    resource\\chinese_tc\\ 的繁体内容，逐字转成简体、再把台湾用语换成
    大陆用语，写到 resource\\english\\。

    资源包不是「长度不可变」的：
        任意节点 = [u32 子节点数 N][N × {u32 id, u32 绝对offset, u32 长度}]
        叶子     = [u32 字节长度][UTF-8 文本]
    每一层都自带 offset/length，所以改了字符串长度后，只要自底向上
    重算所有 offset/length 即可。CELSYS 自己发布的日/法/德/西/韩/其他
    语言包对同一 GUID 的长度就各不相同（例如 DD705E0D：英文 294494、
    日文 306132 字节），足以证明加载器是运行期解析这些字段的。

    替换前会自动备份到 <本仓库外> 的 .csp-l10n-backup/ 目录。
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import varlen  # noqa: E402
from terms_tw2cn import build_table, has_japanese  # noqa: E402

BACKUP_DIR = os.path.join(os.path.expanduser("~"), ".csp-l10n-backup", "resource")


def convert_pack(data, cc, table):
    """解析一个资源包，返回 (重建后的字节, 统计字典)。

    对每个文本叶子：先逐字转简体，再做台湾用语替换。
    含日文假名的叶子只做逐字转换（历史行为），不做用语替换，避免误伤。
    """
    root = varlen.parse_tree(data, 0, len(data))
    leaves = varlen.collect_leaves(root)

    mapping = {}
    n_cjk = n_term = 0
    for k, lf in enumerate(leaves):
        if lf.text is None:
            continue
        new = cc.convert(lf.text)
        chars = sum(1 for a, b in zip(lf.text, new) if a != b)
        n_cjk += chars
        if not has_japanese(lf.text) and table:
            new2, cnt = _apply_terms(new, table)
            if cnt:
                n_term += cnt
                new = new2
        if new != lf.text:
            mapping[k] = new

    out = varlen.build(data, root, mapping)
    stats = {
        "leaves": len(leaves),
        "changed": len(mapping),
        "cjk": n_cjk,
        "terms": n_term,
        "old_size": len(data),
        "new_size": len(out),
    }
    return out, mapping, stats


def _apply_terms(text, table):
    changed = 0
    for tw, cn in table:
        if tw in text:
            n = text.count(tw)
            text = text.replace(tw, cn)
            changed += n
    return text, changed


def check_result(data, mapping, out):
    """校验重建结果：结构自洽 + 除目标外所有叶子原样保留。"""
    errs = varlen.validate_tree(out, 0, len(out))
    root1 = varlen.parse_tree(data, 0, len(data))
    root2 = varlen.parse_tree(out, 0, len(out))
    l1 = varlen.collect_leaves(root1)
    l2 = varlen.collect_leaves(root2)
    if len(l1) != len(l2):
        errs.append(f"叶子数变化 {len(l1)} -> {len(l2)}")
        return errs
    for k in range(len(l1)):
        expect = mapping.get(k, l1[k].text)
        if l2[k].text != expect:
            errs.append(f"叶子{k} 内容不符")
            if len(errs) > 5:
                break
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只统计，不写入")
    ap.add_argument("--verify", action="store_true", help="只校验当前 english 目录")
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

    cc = common.CharConverter()
    table = build_table()

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

    # ---------------------------------------------------------- 校验
    if args.verify:
        return verify_dir(dst, cc, table)

    # ---------------------------------------------------------- 备份
    if not args.dry_run:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        for d in ("english", "other"):
            target = os.path.join(res, d)
            backup = os.path.join(BACKUP_DIR, d)
            if os.path.isdir(target) and not os.path.isdir(backup):
                shutil.copytree(target, backup)
                print(f"已备份 {d} -> {backup}")
            elif os.path.isdir(backup):
                print(f"备份已存在，跳过: {backup}")

    print(f"\n替换规则 {len(table)} 条（含变长）"
          f"{'　[试运行]' if args.dry_run else ''}\n")

    total = {"changed": 0, "cjk": 0, "terms": 0, "old": 0, "new": 0}
    for name in sorted(os.listdir(src)):
        sp = os.path.join(src, name)
        if not os.path.isfile(sp):
            continue
        dp = os.path.join(dst, name)
        data = open(sp, "rb").read()
        out, mapping, st = convert_pack(data, cc, table)

        errs = check_result(data, mapping, out)
        if errs:
            common.die(f"{name[:8]} 重建校验失败: {errs[:3]}\n"
                       "       已中止，未写入任何文件。")

        for k in total:
            key = {"old": "old_size", "new": "new_size"}.get(k, k)
            total[k] += st[key]

        delta = st["new_size"] - st["old_size"]
        print(f"  {name[:8]}  ～{st['changed']:>4} 条串  "
              f"简繁 {st['cjk']:>5} 字  用语 {st['terms']:>3} 处  "
              f"{delta:+6d} 字节")

        if not args.dry_run:
            open(dp, "wb").write(out)

    print()
    if args.dry_run:
        print(f"[试运行] 需改 {total['changed']} 条字符串 / "
              f"{total['cjk']} 字简繁 / {total['terms']} 处用语，未写入。")
    else:
        print(f"完成：{total['changed']} 条字符串、{total['cjk']} 字简繁、"
              f"{total['terms']} 处台湾用语；总体积 "
              f"{total['old']} -> {total['new']} 字节 "
              f"({total['new'] - total['old']:+d})。")
        print("提示：重启 CLIP STUDIO 启动器查看效果。")


def verify_dir(dst, cc, table):
    """校验目标目录：结构合法、无繁体残留、无台湾用语残留。"""
    bad = 0
    for name in sorted(os.listdir(dst)):
        p = os.path.join(dst, name)
        if not os.path.isfile(p):
            continue
        data = open(p, "rb").read()
        errs = varlen.validate_tree(data, 0, len(data))
        if errs:
            print(f"  {name[:8]} 结构错误: {errs[:2]}")
            bad += 1
            continue
        root = varlen.parse_tree(data, 0, len(data))
        n_trad = n_term = 0
        for lf in varlen.collect_leaves(root):
            if not lf.text:
                continue
            if has_japanese(lf.text):
                continue
            if any(ch in cc.table for ch in lf.text):
                n_trad += 1
            _, cnt = _apply_terms(lf.text, table)
            n_term += cnt
        flag = "" if (n_trad == 0 and n_term == 0) else "  <-- 待处理"
        if flag:
            bad += 1
        print(f"  {name[:8]}  繁体残留 {n_trad:>3} 条  用语残留 {n_term:>3} 处{flag}")
    print()
    print("全部干净。" if bad == 0 else f"{bad} 个文件仍需处理。")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    main()
