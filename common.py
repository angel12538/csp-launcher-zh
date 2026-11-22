#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLIP STUDIO 启动器简体中文补丁 —— 共用工具函数。

从繁体资源生成简体资源，严格保持字节长度不变。
原因：CELSYS 的本地化资源包采用 [4字节大端长度][UTF-8 文本] 紧凑排列，
长度一变就会破坏结构，导致启动器崩溃（0xC0000005）。
"""

import os
import struct
import sys


def die(msg):
    print(f"[错误] {msg}", file=sys.stderr)
    sys.exit(1)


def find_clipstudio_root():
    """定位 CLIP STUDIO 1.5 安装根目录。"""
    candidates = []

    # 1) 环境变量覆盖
    env = os.environ.get("CELSYS_ROOT")
    if env:
        candidates.append(env)

    # 2) 常见安装位置
    for base in (
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
    ):
        if base:
            candidates.append(os.path.join(base, "CELSYS", "CLIP STUDIO 1.5"))

    for drive in "CDEFGH":
        candidates.append(f"{drive}:\\Program Files\\CELSYS\\CLIP STUDIO 1.5")
        candidates.append(f"{drive}:\\CELSYS\\CLIP STUDIO 1.5")

    # 3) 从 ProgramData 的安装记录读取
    try:
        p = os.path.join(
            os.environ.get("ProgramData", r"C:\ProgramData"),
            "CELSYS", "CLIPStudio", "InstallPath", "clipstudio15.txt",
        )
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
            if content:
                d = os.path.dirname(os.path.dirname(content.strip())) \
                    if content.lower().endswith(".exe") else content
                candidates.insert(0, d)
    except Exception:
        pass

    for c in candidates:
        if c and os.path.isfile(os.path.join(c, "CLIP STUDIO", "CLIPStudio.exe")):
            return os.path.abspath(c)

    die("找不到 CLIP STUDIO 1.5 安装目录。\n"
        "       请设置环境变量 CELSYS_ROOT 指向安装根目录，例如：\n"
        '         set CELSYS_ROOT=D:\\Program Files\\CELSYS\\CLIP STUDIO 1.5')


def userdata_menu_js():
    """启动器左侧菜单脚本的真实路径（在用户数据目录，不是安装目录）。"""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        die("找不到 APPDATA 环境变量")
    p = os.path.join(
        appdata, "CELSYSUserData", "CELSYS",
        "CLIPStudioVer1_5_0", "MENU", "1", "assets", "side_menu.js",
    )
    if not os.path.isfile(p):
        die(f"找不到启动器菜单脚本：{p}\n"
            "       请先运行一次 CLIP STUDIO 启动器，让它生成该文件。")
    return p


class CharConverter:
    """内置繁简逐字转换器（零依赖）。

    只做 1 字对 1 字的映射，因此转换前后 UTF-8 字节长度必然不变——
    这是资源文件带长度前缀所要求的硬约束。

    词典来自 opencc-python 的 TSCharacters.txt（Apache-2.0），
    已过滤为单一映射（4057 条）。
    """

    def __init__(self, dict_path=None):
        here = os.path.dirname(os.path.abspath(__file__))
        if dict_path is None:
            dict_path = os.path.join(here, "data", "t2s_characters.txt")
        if not os.path.isfile(dict_path):
            die(f"找不到繁简词典: {dict_path}")
        self.table = {}
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                if "\t" not in line:
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) == 2 and len(parts[0]) == 1 and len(parts[1]) == 1:
                    self.table[parts[0]] = parts[1]

    def convert(self, text):
        """逐字转简体。非字典内字符原样保留。"""
        return "".join(self.table.get(ch, ch) for ch in text)


def load_opencc():
    """返回内置转换器（保留旧名字，方便调用方无需改动）。"""
    return CharConverter


# ---------------------------------------------------------------- 资源包处理

def is_ok_text(s):
    return sum(1 for c in s if ord(c) < 32 and c not in "\r\n\t") == 0


def parse_string_pool(data):
    """扫描 [4字节大端长度][UTF-8 文本] 结构。

    重要：字符串池是紧凑排列的，遇到合法结构后必须直接跳到下一段，
    不能跳过任何零字节——否则会吃掉下一个长度头的 4 个 0x00，
    导致其后所有字符串被漏读（实测会让覆盖率掉到 65%）。
    """
    out = []
    i = 0
    n = len(data)
    while i < n - 4:
        length = struct.unpack_from(">I", data, i)[0]
        if 2 <= length < 0x4000 and i + 4 + length <= n:
            chunk = data[i + 4:i + 4 + length]
            try:
                s = chunk.decode("utf-8")
                if is_ok_text(s):
                    out.append((i, length, s))
                    i += 4 + length
                    continue
            except UnicodeDecodeError:
                pass
        i += 1
    return out


def convert_resource(src, dst, cc):
    """逐字转简体并写回，保持字节长度。返回统计。"""
    data = open(src, "rb").read()
    entries = parse_string_pool(data)
    out = bytearray(data)
    seg = chars = skipped = 0

    for off, length, s in entries:
        s2 = cc.convert(s)
        if s2 == s:
            continue
        nb = s2.encode("utf-8")
        if len(nb) != length:
            skipped += 1
            continue
        out[off + 4:off + 4 + length] = nb
        seg += 1
        chars += sum(1 for a, b in zip(s, s2) if a != b)

    assert len(out) == len(data), "字节长度发生变化，已中止"
    open(dst, "wb").write(out)
    return len(entries), seg, chars, skipped
