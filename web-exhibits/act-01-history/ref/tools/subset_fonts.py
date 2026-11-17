#!/usr/bin/env python3
"""把本机字体裁成页面实际用到的字符，输出到 assets/fonts/。

用法：python3 tools/subset_fonts.py
缺字时页面会退回 Songti SC / Kaiti SC，不会出现方块。
"""

import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "assets", "fonts")

SRC = {
    "xiangcui.ttf": "/Users/yangzhe/Library/Fonts/XiangcuiDengcusong.ttf",
    "zhuokai.ttf": "/Users/yangzhe/Library/Fonts/江西拙楷2.0.ttf",
}

EXTRA = "　·—〇《》「」（）．，。、；：？！0123456789"


def collect_chars():
    chars = set(EXTRA)
    for sub in ("js",):
        for name in sorted(os.listdir(os.path.join(ROOT, sub))):
            if not name.endswith(".js"):
                continue
            with open(os.path.join(ROOT, sub, name), encoding="utf-8") as fh:
                chars.update(fh.read())
    # 只保留非 ASCII 的可见字符 + 中文标点
    keep = {c for c in chars if ord(c) > 0x2000 or c in EXTRA}
    return "".join(sorted(keep))


def main():
    os.makedirs(OUT, exist_ok=True)
    text = collect_chars()
    txt_path = os.path.join(OUT, "_chars.txt")
    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"字符数：{len(text)}")

    for name, src in SRC.items():
        if not os.path.exists(src):
            print("跳过（找不到源字体）：", src)
            continue
        out = os.path.join(OUT, name)
        cmd = [
            "python3", "-m", "fontTools.subset", src,
            f"--text-file={txt_path}",
            f"--output-file={out}",
            "--layout-features=*",
            "--glyph-names",
            "--symbol-cmap",
            "--legacy-cmap",
            "--notdef-glyph",
            "--notdef-outline",
            "--recommended-glyphs",
            "--name-IDs=*",
            "--drop-tables+=DSIG",
        ]
        subprocess.run(cmd, check=True)
        print(f"{name}: {os.path.getsize(out) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
