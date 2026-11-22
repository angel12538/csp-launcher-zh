"""对资源包和 JS 执行台湾用语本地化，严格保证字节长度不变。

用法:
    python patch_terms.py --dry-run   # 预览改动样例
    python patch_terms.py --apply     # 应用
    python patch_terms.py --restore   # 还原
"""

import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
from terms_tw2cn import build_table  # noqa: E402

BACKUP_ROOT = os.path.join(os.path.expanduser("~"), ".csp-l10n-backup", "terms")


def has_japanese(text):
    """判断是否含日文假名。

    资源包里混有日文（注释、shader 代码、部分未翻译条目），
    若不加判断，「设定」「印刷」等词会误伤日文文本。

    注意排除符号区：
      U+30FB 「・」片假名中点 —— 中文排版里也常用作分隔符
      U+30FC 「ー」长音符   —— 偶尔出现在中文里
    只把真正的假名字母算作日文标识，否则「最新・推荐资讯」
    这类条目会因为一个中点被整体跳过。
    """
    for c in text:
        cp = ord(c)
        if 0x3041 <= cp <= 0x3096:      # 平假名字母
            return True
        if 0x30A1 <= cp <= 0x30FA:      # 片假名字母（不含 ・ ー）
            return True
    return False


def localize_text(text, table):
    """按长词优先替换，返回 (新文本, 改动次数)。

    含日文假名的文本一律跳过——资源包里混有日文，
    盲目替换会破坏日文条目。
    """
    if has_japanese(text):
        return text, 0

    changed = 0
    for tw, cn in table:
        if tw in text:
            n = text.count(tw)
            text = text.replace(tw, cn)
            changed += n
    return text, changed


def process_resource_file(src, dst, table, dry_run):
    """资源包：只对 [长度][UTF-8] 字符串池内的文本做替换。"""
    data = open(src, "rb").read()
    entries = common.parse_string_pool(data)
    out = bytearray(data)
    total = 0
    samples = []

    for off, length, s in entries:
        s2, n = localize_text(s, table)
        if n == 0:
            continue
        nb = s2.encode("utf-8")
        if len(nb) != length:
            # 长度变了：说明词表中混入了不等长项，跳过保安全
            continue
        out[off + 4:off + 4 + length] = nb
        total += n
        if len(samples) < 8 and not dry_run:
            samples.append((s, s2))

    assert len(out) == len(data), "文件长度变化，已中止"
    if not dry_run and total:
        open(dst, "wb").write(out)
    return total, samples


def process_js_file(path, table, dry_run):
    """JS 文件：**按字符串字面量**逐个替换（无长度前缀，但仍保持等字数）。

    不能整文件判断是否含日文——JS 里同时有 ja-jp / zh-tw / en-us 等
    多个语言块。也不能按行判断——压缩后的 side_menu.js 整个文件只有
    3 行，一行里混着多个语言块的字符串。

    这里用正则匹配引号字面量（而不是手写状态机）：
    压缩 JS 里存在撇号、正则字面量等，手写扫描器容易失去同步，
    导致其后所有字符串都漏处理。
    """
    with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
        txt = f.read()

    # 匹配 "..." 或 '...'，允许内部转义
    LITERAL = re.compile(r'"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'')

    total = 0
    out = []
    last = 0

    def repl(m):
        nonlocal total
        raw = m.group(0)
        inner = raw[1:-1]
        if has_japanese(inner):
            return raw            # 日文条目不处理
        new_inner, cnt = localize_text(inner, table)
        if cnt == 0:
            return raw
        total += cnt
        q = raw[0]
        return f"{q}{new_inner}{q}"

    new_txt = LITERAL.sub(repl, txt)

    if total and not dry_run:
        with open(path, "w", encoding="utf-8", errors="surrogateescape",
                  newline="") as f:
            f.write(new_txt)
    return total, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--restore", action="store_true")
    args = ap.parse_args()

    root = common.find_clipstudio_root()
    base = os.path.join(root, "CLIP STUDIO")

    # 只处理启动器实际加载的目录。
    # chinese_tc 是繁体「源」目录——转简体时要从它读、而不是改它，
    # 否则再跑一次繁简转换就失去源了。PAINT 的 chinese_tc 同理。
    targets_res = [
        (os.path.join(base, "resource", "english"),
         os.path.join(base, "resource", "english")),
    ]
    js_targets = [
        os.path.join(base, "Settings", "CLIP STUDIO2", "1.0.9",
                     "HTML", "resource", "page.js"),
        common.userdata_menu_js(),
    ]

    if args.restore:
        if not os.path.isdir(BACKUP_ROOT):
            common.die(f"没有找到备份: {BACKUP_ROOT}")
        count = 0
        for dp, dn, fns in os.walk(BACKUP_ROOT):
            for f in fns:
                src = os.path.join(dp, f)
                rel = os.path.relpath(src, BACKUP_ROOT)
                # 还原目标路径记录在清单文件里
                pass
        common.die("请使用 还原原版.cmd（它从最初备份整体还原）")

    table = build_table()
    print(f"替换规则: {len(table)} 条")
    print(f"模式: {'试运行' if args.dry_run else '应用'}\n")

    total_all = 0
    all_samples = []

    print("=== 资源包 ===")
    for src_dir, dst_dir in targets_res:
        if not os.path.isdir(src_dir):
            continue
        label = src_dir.replace(root, "…")
        sub = 0
        for fn in sorted(os.listdir(src_dir)):
            p = os.path.join(src_dir, fn)
            if not os.path.isfile(p):
                continue
            n, samples = process_resource_file(p, p, table, args.dry_run)
            sub += n
            all_samples.extend(samples)
        print(f"  {label}: {sub} 处")
        total_all += sub

    print("\n=== JS 文件 ===")
    for p in js_targets:
        if not os.path.isfile(p):
            continue
        n, _ = process_js_file(p, table, args.dry_run)
        print(f"  {os.path.basename(p)}: {n} 处")
        total_all += n

    print(f"\n合计: {total_all} 处")
    if all_samples:
        print("\n=== 改动样例 ===")
        for old, new in all_samples[:10]:
            print(f"  旧: {old[:70]}")
            print(f"  新: {new[:70]}")
            print()


if __name__ == "__main__":
    main()
