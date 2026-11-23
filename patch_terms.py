"""对启动器的 JS 界面脚本执行台湾用语本地化。

    resource\\<lang>\\*.res 这类二进制资源包的用语替换由 patch_resource.py
    一起完成（那边要重算资源包内部的 offset/length，见 varlen.py）。
    本脚本只处理 **纯文本 JS**：没有长度前缀，替换可以自由增减字数。

用法:
    python patch_terms.py --dry-run   # 预览改动样例
    python patch_terms.py --apply     # 应用
    python patch_terms.py --restore   # 从备份还原
"""

import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from terms_tw2cn import build_table, has_japanese, localize_text  # noqa: E402

BACKUP_DIR = os.path.join(os.path.expanduser("~"), ".csp-l10n-backup", "terms_js")


def js_targets(root):
    return [
        os.path.join(root, "CLIP STUDIO", "Settings", "CLIP STUDIO2", "1.0.9",
                     "HTML", "resource", "page.js"),
        common.userdata_menu_js(),
    ]


def process_js_file(path, table, dry_run):
    """按字符串字面量逐个替换。

    不能整文件判断是否含日文——JS 里同时有 ja-jp / zh-tw / en-us 等
    多个语言块。也不能按行判断——压缩后的 side_menu.js 整个文件只有
    3 行，一行里混着多个语言块的字符串。

    这里用正则匹配引号字面量（而不是手写状态机）：
    压缩 JS 里存在撇号、正则字面量等，手写扫描器容易失去同步，
    导致其后所有字符串都漏处理。
    """
    with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
        txt = f.read()

    LITERAL = re.compile(r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'')

    total = 0
    samples = []

    def repl(m):
        nonlocal total
        raw = m.group(0)
        inner = raw[1:-1]
        if has_japanese(inner):
            return raw                  # 日文条目不处理
        new_inner, cnt = localize_text(inner, table)
        if cnt == 0 or new_inner == inner:
            return raw
        total += cnt
        if len(samples) < 5:
            samples.append((inner, new_inner))
        q = raw[0]
        return f"{q}{new_inner}{q}"

    new_txt = LITERAL.sub(repl, txt)

    if total and not dry_run:
        with open(path, "w", encoding="utf-8", errors="surrogateescape",
                  newline="") as f:
            f.write(new_txt)
    return total, samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    root = common.find_clipstudio_root()
    targets = [p for p in js_targets(root) if os.path.isfile(p)]

    if not targets:
        common.die("找不到启动器 JS 脚本，请先运行一次 CLIP STUDIO 启动器。")

    if args.restore:
        if not os.path.isdir(BACKUP_DIR):
            common.die(f"没有找到备份: {BACKUP_DIR}")
        for p in targets:
            b = os.path.join(BACKUP_DIR, os.path.basename(p))
            if os.path.isfile(b):
                shutil.copy2(b, p)
                print(f"  已还原 {os.path.basename(p)}")
            else:
                print(f"  跳过 {os.path.basename(p)}（无备份）")
        return

    if not args.dry_run:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        for p in targets:
            b = os.path.join(BACKUP_DIR, os.path.basename(p))
            if not os.path.isfile(b):
                shutil.copy2(p, b)
                print(f"已备份 {os.path.basename(p)}")

    table = build_table()
    print(f"\n替换规则 {len(table)} 条（含变长）")
    print(f"模式: {'试运行' if args.dry_run else '应用'}\n")

    total_all = 0
    all_samples = []
    for p in targets:
        n, samples = process_js_file(p, table, args.dry_run)
        print(f"  {os.path.basename(p)}: {n} 处")
        total_all += n
        all_samples.extend(samples)

    print(f"\n合计: {total_all} 处")
    if all_samples:
        print("\n=== 改动样例 ===")
        for old, new in all_samples[:8]:
            print(f"  旧: {old[:70]}")
            print(f"  新: {new[:70]}")
            print()


if __name__ == "__main__":
    main()
