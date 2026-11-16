#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把第二幕打包成「双击即可离线运行」的单文件网页。

为什么不能直接拷 index.html：
本地 file:// 协议下浏览器禁止 fetch 本地文件，而这一页由 ES 模块 + fetch
组成。所以打包时做三件事：
  1. data.json / land.geojson / china-provinces.json 改成静态 import，随代码打成一份；
  2. CSS 与打包后的 JS 全部内联进 HTML；
  3. 12 个 GLB 转成 base64 存成普通 .js（脚本加载不受 file:// 限制），
     Draco 解码器（wrapper + wasm）也内联，点开时按需注入再 loader.parse。

用法：python3 tools/build_offline.py
产物：~/Downloads/木构星图-离线版/
"""

import base64
import glob
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # web-exhibits/
ACT = os.path.join(ROOT, "act-02-globe")
BUILD = "/tmp/act02_offline_build"
MIRROR = os.path.join(BUILD, "web-exhibits")
OUT = os.path.expanduser("~/Downloads/木构星图-离线版")
NODE_BIN = os.path.expanduser("~/.workbuddy/binaries/node/versions/22.22.2-6/bin")
ESBUILD = os.path.join(NODE_BIN, "npx")


def run(cmd, **kw):
    env = dict(os.environ)
    env["PATH"] = NODE_BIN + ":" + env.get("PATH", "/usr/bin:/bin")
    print("  $", " ".join(cmd[:6]), "…" if len(cmd) > 6 else "")
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, **kw)
    if result.returncode != 0:
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        sys.exit(f"命令失败: {cmd[0]}")
    return result


def mirror():
    if os.path.isdir(BUILD):
        shutil.rmtree(BUILD)
    os.makedirs(os.path.join(MIRROR, "shared"))
    ignore = shutil.ignore_patterns("node_modules", ".git", "*.glb", "models")
    shutil.copytree(ACT, os.path.join(MIRROR, "act-02-globe"), ignore=ignore)
    shutil.copytree(os.path.join(ROOT, "shared", "vendor"), os.path.join(MIRROR, "shared", "vendor"))
    shutil.copytree(os.path.join(ROOT, "shared", "data"), os.path.join(MIRROR, "shared", "data"))


def patch_sources():
    src = os.path.join(MIRROR, "act-02-globe")

    # 1) 资料：fetch → 静态 import
    p = os.path.join(src, "js", "data.js")
    s = open(p, encoding="utf-8").read()
    s = s.replace(
        """let cache = null;

export async function loadBuildings() {
  if (cache) return cache;
  const res = await fetch('./data.json');
  if (!res.ok) throw new Error('资料载入失败');
  cache = await res.json();
  return cache;
}""",
        """import BUILDINGS from '../data.json';

export async function loadBuildings() {
  return BUILDINGS;
}""",
    )
    assert "fetch(" not in s, "data.js 仍有 fetch"
    open(p, "w", encoding="utf-8").write(s)

    # 2) 地理轮廓 + 省界：同样改成静态 import
    p = os.path.join(src, "js", "globe", "globe.js")
    s = open(p, encoding="utf-8").read()
    s = s.replace(
        """  const landGeoJson = await fetch('../shared/data/land.geojson').then((res) => {
    if (!res.ok) throw new Error('地理轮廓载入失败');
    return res.json();
  });""",
        "  const landGeoJson = LAND;",
    )
    s = s.replace(
        """  let data = null;
  try {
    const res = await fetch('./assets/data/china-provinces.json');
    if (res.ok) data = await res.json();
  } catch (error) {
    console.warn('省界数据未载入，主场景不受影响', error);
  }""",
        "  const data = PROVINCES;",
    )
    if "import LAND" not in s:
        s = s.replace(
            "import { createMarkers } from './markers.js';",
            "import { createMarkers } from './markers.js';\n"
            "import LAND from '../../../shared/data/land.geojson';\n"
            "import PROVINCES from '../../assets/data/china-provinces.json';",
        )
    assert "fetch(" not in s, "globe.js 仍有 fetch"
    open(p, "w", encoding="utf-8").write(s)
    print("  资料、地理轮廓、省界 已改为静态引入")


def bundle():
    out = os.path.join(BUILD, "bundle.js")
    src = os.path.join(MIRROR, "act-02-globe")
    run([
        ESBUILD, "--yes", "esbuild@0.25.0", "js/main.js",
        "--bundle", "--format=esm", "--loader:.geojson=json",
        "--alias:three=../shared/vendor/three.module.js",
        f"--outfile={out}", "--minify", "--legal-comments=none",
    ], cwd=src)
    print("  打包完成 %d KB" % (os.path.getsize(out) // 1024))
    return out


def write_model_scripts():
    """GLB → base64 → 普通 .js，用 <script src> 注入，绕开 file:// 的 fetch 限制"""
    dst = os.path.join(OUT, "assets", "models-js")
    os.makedirs(dst, exist_ok=True)
    total = 0
    for glb in sorted(glob.glob(os.path.join(ACT, "assets", "models", "*.glb"))):
        key = os.path.splitext(os.path.basename(glb))[0]
        b64 = base64.b64encode(open(glb, "rb").read()).decode()
        payload = (
            'window.__MODEL_B64=window.__MODEL_B64||{};'
            f'window.__MODEL_B64["{key}"]="{b64}";'
        )
        path = os.path.join(dst, key + ".js")
        open(path, "w", encoding="utf-8").write(payload)
        total += os.path.getsize(glb)
        print("  %-42s %6.2fMB → %6.2fMB" % (key, os.path.getsize(glb) / 1048576,
                                             os.path.getsize(path) / 1048576))
    print("  模型合计 %.1f MB（原 GLB）" % (total / 1048576))


def draco_inline():
    d = os.path.join(MIRROR, "shared", "vendor", "draco")
    wrapper = base64.b64encode(open(os.path.join(d, "draco_wasm_wrapper.js"), "rb").read()).decode()
    wasm = base64.b64encode(open(os.path.join(d, "draco_decoder.wasm"), "rb").read()).decode()
    print("  Draco 解码器内联 %d KB" % ((len(wrapper) + len(wasm)) // 1024))
    return f'window.__DRACO_LIB={{wrapper:"{wrapper}",wasm:"{wasm}"}};'


def compose_html(bundle_path):
    src = os.path.join(MIRROR, "act-02-globe")
    html = open(os.path.join(src, "index.html"), encoding="utf-8").read()
    css_files = ["css/theme.css", "css/layout.css", "css/panel.css", "css/globe.css", "css/viewer.css"]
    css = "\n".join(open(os.path.join(src, f), encoding="utf-8").read() for f in css_files)
    js = open(bundle_path, encoding="utf-8").read()

    html = re.sub(r'\s*<link rel="stylesheet" href="css/[^"]+">', "", html)
    html = re.sub(r"\s*<script type=\"importmap\">.*?</script>", "", html, flags=re.S)
    html = re.sub(r'\s*<script type="module" src="js/main\.js[^"]*"></script>', "", html)
    html = html.replace('<a class="brand" href="../index.html">',
                        '<a class="brand" href="#top" aria-label="木构之间">')
    js = js.replace("</script", "<\\/script")

    lib = draco_inline()
    html = html.replace("</head>", f"<style>\n{css}\n</style>\n</head>")
    html = html.replace(
        "</body>",
        f'<script>{lib}</script>\n<script type="module">\n{js}\n</script>\n</body>',
    )
    out = os.path.join(OUT, "打开-木构星图.html")
    open(out, "w", encoding="utf-8").write(html)
    print("  HTML %d KB（样式、脚本、省界、解码器已内联）" % (os.path.getsize(out) // 1024))
    return out


def assemble(html_path):
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    for name in ("buildings",):
        d = os.path.join(OUT, "assets", name)
        if os.path.isdir(d):
            shutil.rmtree(d)
        shutil.copytree(os.path.join(ACT, "assets", name), d)
    # 旧的 .glb 与 draco 目录不再需要（模型已转 base64）
    for stale in (os.path.join(OUT, "assets", "models"), os.path.join(OUT, "vendor")):
        if os.path.isdir(stale):
            shutil.rmtree(stale)
    for extra in ("favicon.svg",):
        p = os.path.join(ACT, extra)
        if os.path.exists(p):
            shutil.copy2(p, OUT)


def main():
    print("[1/6] 复制镜像")
    mirror()
    print("[2/6] 改写外部读取")
    patch_sources()
    print("[3/6] 打包脚本")
    b = bundle()
    print("[4/6] 生成模型 base64 脚本")
    os.makedirs(OUT, exist_ok=True)
    write_model_scripts()
    print("[5/6] 合成单文件 HTML")
    html = compose_html(b)
    print("[6/6] 组装离线包")
    assemble(html)
    size = subprocess.run(["du", "-sh", OUT], capture_output=True, text=True).stdout.split()[0]
    print(f"\n完成：{OUT}（{size}）")


if __name__ == "__main__":
    main()
