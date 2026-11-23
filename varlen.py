#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CELSYS 资源包变长重建器。

资源包的真实格式（已用 8 种语言资源互相印证）：

    任意节点 = [大端 u32 子节点数 N][N × {u32 id, u32 绝对offset, u32 长度}]
    叶子     = [大端 u32 字节长度][UTF-8 文本]

即：整个文件本身就是一个节点（根节点 = 顶部段表），子节点的 offset
是相对于「整个文件」的绝对偏移，且同层子节点首尾相接、无空隙。
因为每一层都自带 offset/length，所以**改字符串长度完全合法**——只要
自底向上把每层的 offset/长度重新算一遍即可。

这一点很关键：早期版本认为「长度一变就崩」，是因为只替换了文本字节，
没有同步维护父节点的 offset/length 三元组。

无法识别的节点会作为「不透明数据」原样保留，因此哪怕部分子格式没解析
出来，重建结果依然字节级安全。
"""

import struct
import sys


class Node:
    __slots__ = ("idx", "start", "length", "children", "is_leaf", "text",
                 "start_out", "length_out")

    def __init__(self, idx, start, length):
        self.idx = idx
        self.start = start
        self.length = length
        self.children = []
        self.is_leaf = False
        self.text = None          # None = 不透明二进制数据
        self.start_out = 0
        self.length_out = 0


def u32(b, p):
    return struct.unpack_from(">I", b, p)[0]


def _looks_like_leaf(b, start, length):
    """以 [u32 长度][恰好铺满整段的 UTF-8 文本] 判定叶子。"""
    if length < 4:
        return None
    n = u32(b, start)
    if n == 0 or start + 4 + n != start + length:
        return None
    chunk = b[start + 4:start + 4 + n]
    try:
        t = chunk.decode("utf-8")
    except UnicodeDecodeError:
        return None
    for ch in t:
        o = ord(ch)
        if o < 0x20 and ch not in "\t\n\r":
            return None
    return t


def _parse_children(b, start, length):
    """尝试按内部节点解析，成功返回 [(id, off, len)]，失败返回 None。"""
    if length < 4:
        return None
    count = u32(b, start)
    if not (0 < count <= 100000):
        return None
    if 4 + count * 12 > length:
        return None
    p = start + 4
    kids = []
    expect = None
    for _ in range(count):
        i = u32(b, p)
        o = u32(b, p + 4)
        ln = u32(b, p + 8)
        p += 12
        if o + ln > len(b) or ln > length:
            return None
        if expect is not None and o != expect:
            return None
        expect = o + ln
        kids.append((i, o, ln))
    # 子节点必须恰好铺满本节点（首尾相接，父区间 = 子区间之和 + 表头）
    if kids and kids[0][1] != start + 4 + count * 12:
        return None
    return kids


def parse_tree(b, start=0, length=None, idx=-1, depth=0):
    """解析节点树。叶子判定优先，失败再尝试内部节点，最后原样保留。"""
    if length is None:
        length = len(b)
    node = Node(idx, start, length)

    if depth > 64:
        node.is_leaf = True
        return node

    text = _looks_like_leaf(b, start, length)
    if text is not None:
        node.is_leaf = True
        node.text = text
        return node

    kids = _parse_children(b, start, length)
    if kids:
        for i, o, ln in kids:
            node.children.append(parse_tree(b, o, ln, i, depth + 1))
        return node

    # 不认识 —— 不透明数据，原样保留
    node.is_leaf = True
    node.text = None
    return node


def collect_leaves(node, out=None):
    """按文件内出现顺序收集全部叶子。"""
    if out is None:
        out = []
    if node.is_leaf:
        out.append(node)
    else:
        for c in node.children:
            collect_leaves(c, out)
    return out


def build(b, root, new_texts):
    """new_texts: {叶子序号: 新文本}。自底向上重算全部 offset/length。

    返回重建后的完整文件字节。未指定新文本的叶子（含不透明数据）原样保留。
    """
    leaves = collect_leaves(root, [])
    leaf_bytes = {}
    for k, lf in enumerate(leaves):
        if lf.text is None:
            leaf_bytes[id(lf)] = b[lf.start:lf.start + lf.length]
            continue
        t = new_texts.get(k, lf.text)
        nb = t.encode("utf-8")
        leaf_bytes[id(lf)] = struct.pack(">I", len(nb)) + nb

    out = bytearray()

    def emit(node):
        data = None
        if node.is_leaf:
            data = leaf_bytes[id(node)]
        if data is not None:
            node.start_out = len(out)
            node.length_out = len(data)
            out.extend(data)
            return
        header_pos = len(out)
        out.extend(b"\x00" * (4 + len(node.children) * 12))
        node.start_out = header_pos
        kids_info = []
        for c in node.children:
            emit(c)
            kids_info.append((c.idx, c.start_out, c.length_out))
        node.length_out = len(out) - header_pos
        struct.pack_into(">I", out, header_pos, len(node.children))
        for k, (i, o, ln) in enumerate(kids_info):
            struct.pack_into(">III", out, header_pos + 4 + k * 12, i, o, ln)

    emit(root)
    return bytes(out)


# ------------------------------------------------------------------ 自检工具

def validate_tree(b, start=0, length=None, depth=0, errs=None):
    """独立于 Node 的结构校验：所有节点自洽、子节点连续、无越界。"""
    if errs is None:
        errs = []
    if length is None:
        length = len(b)
    if depth > 64:
        errs.append(f"嵌套过深 @0x{start:x}")
        return errs
    if _looks_like_leaf(b, start, length) is not None:
        return errs
    kids = _parse_children(b, start, length)
    if not kids:
        # 不透明数据 —— 只要求不越界即可，属于允许的兜底
        if start + length > len(b):
            errs.append(f"不透明数据越界 @0x{start:x}")
        return errs
    p = start + 4
    for _ in range(u32(b, start)):
        o = u32(b, p + 4)
        ln = u32(b, p + 8)
        p += 12
        validate_tree(b, o, ln, depth + 1, errs)
    kids_end = kids[-1][1] + kids[-1][2]
    if kids_end != start + length:
        errs.append(
            f"节点 @0x{start:x} 子节点末尾 0x{kids_end:x} != 0x{start + length:x}")
    return errs


def leaf_coverage(node):
    """统计：文本叶子数 / 不透明数据字节数 / 解析出的总字节数。"""
    leaves = collect_leaves(node)
    n_text = sum(1 for lf in leaves if lf.text is not None)
    n_raw = sum(1 for lf in leaves if lf.text is None)
    raw_bytes = sum(lf.length for lf in leaves if lf.text is None)
    return n_text, n_raw, raw_bytes


def roundtrip(data):
    """不改内容重建，返回 (是否字节级完全相同, 叶子数, 文本叶子数)。"""
    root = parse_tree(data, 0, len(data))
    out = build(data, root, {})
    leaves = collect_leaves(root)
    n_text = sum(1 for lf in leaves if lf.text is not None)
    return out == data, len(leaves), n_text


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    import glob
    import os

    base = sys.argv[1] if len(sys.argv) > 1 else "."
    ok = bad = 0
    for p in sorted(glob.glob(os.path.join(base, "*"))):
        if not os.path.isfile(p):
            continue
        data = open(p, "rb").read()
        same, nleaf, ntext = roundtrip(data)
        tag = "OK  " if same else "DIFF"
        if same:
            ok += 1
        else:
            bad += 1
        print(f"  {tag} {os.path.basename(p)[:8]}  {len(data):>8}B  "
              f"叶子={nleaf:>5}  文本={ntext:>5}")
    print(f"\n字节级往返一致: {ok}/{ok + bad}")
