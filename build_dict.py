"""从 opencc 的 TSCharacters.txt 生成精简逐字映射表。

关键：同一繁体字可能有**多个**简体候选（如「開」→「开 𫔭」），
取第一个（最常用）即可，不能因为值不是单字就整条丢弃。
"""

import sys, os

sys.stdout.reconfigure(encoding="utf-8")

SRC = r"C:\Users\Administrator\AppData\Local\Temp\opencc_redownload\opencc\dictionary\TSCharacters.txt"
DST = r"C:\Users\Administrator\Documents\deepseek-harness\default-workspace\csp-l10n-zh\data\t2s_characters.txt"

out = []
stats = {"kept": 0, "multi_pick_first": 0, "skipped_identity": 0, "bad": 0}

for line in open(SRC, encoding="utf-8"):
    line = line.rstrip("\n")
    if "\t" not in line:
        continue
    parts = line.split("\t")
    if len(parts) != 2:
        stats["bad"] += 1
        continue
    trad, vals = parts
    if len(trad) != 1:
        stats["bad"] += 1
        continue

    # 候选值可能以空格分隔多个
    candidates = [v for v in vals.split() if v]
    if not candidates:
        stats["bad"] += 1
        continue

    # 取第一个候选
    simp = candidates[0]
    if len(candidates) > 1:
        stats["multi_pick_first"] += 1

    if len(simp) != 1:
        stats["bad"] += 1
        continue

    if simp == trad:
        stats["skipped_identity"] += 1
        continue

    out.append(f"{trad}\t{simp}")
    stats["kept"] += 1

open(DST, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")

print(f"源文件: {SRC}")
print(f"输出:   {DST}")
print(f"  保留单字映射: {stats['kept']}")
print(f"  多候选取首个: {stats['multi_pick_first']}")
print(f"  繁简相同跳过: {stats['skipped_identity']}")
print(f"  异常跳过:     {stats['bad']}")
print()

# 验证关键常用字
verify = {}
for line in out:
    t, s = line.split("\t")
    verify[t] = s

print("关键字符验证:")
for ch in "開始定開關這們時會發現種說選確認語讀寫繪顏筆層變換試環境資訊軟體檔案設定備份載輸數據傳檔":
    if ch in verify:
        print(f"  {ch} -> {verify[ch]}  ✓")
    else:
        print(f"  {ch} -> 无映射（可能繁简相同）")
