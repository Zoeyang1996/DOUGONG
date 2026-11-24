from pathlib import Path
import json,re,shutil,base64,subprocess,tempfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/Users/yangzhe/Desktop/浙江工商/DOUGONG/web-exhibits/act-02-globe')
SHARED=SOURCE.parent/'shared'
ESBUILD=Path('/Users/yangzhe/.npm/_npx/7bbf1cbb8e5ae33e/node_modules/@esbuild/darwin-arm64/bin/esbuild')
BEFORE=ROOT/'01_镜头未拉近'
AFTER=ROOT/'02_镜头穿梭已完善'
assert not BEFORE.exists() and not AFTER.exists(),'演示目录已存在，停止以免覆盖练习代码'
BEFORE.mkdir(parents=True)
for name in ('js','css'):shutil.copytree(SOURCE/name,BEFORE/name)
shutil.copytree(SHARED/'vendor',BEFORE/'vendor')
shutil.copy2(SOURCE/'data.json',BEFORE/'data.json');shutil.copy2(SOURCE/'favicon.svg',BEFORE/'favicon.svg')
(BEFORE/'assets/data').mkdir(parents=True)
shutil.copy2(SOURCE/'assets/data/china-provinces.json',BEFORE/'assets/data/china-provinces.json')
shutil.copy2(SHARED/'data/land.geojson',BEFORE/'assets/data/land.geojson')
data=json.loads((SOURCE/'data.json').read_text());credits=[]
for item in data:
 image=item['image'];target=BEFORE/image;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SOURCE/image,target)
 credit=SOURCE/image;source_file=credit.parent/'_source.txt'
 credits.append({'id':item['id'],'name':item['name'],'image':image,'source_note':source_file.read_text() if source_file.exists() else '沿用项目现有图册资料'})
(BEFORE/'assets/data/图片资料来源.json').write_text(json.dumps(credits,ensure_ascii=False,indent=2))
model_dir=BEFORE/'assets/models-js';model_dir.mkdir()
for p in sorted((SOURCE/'assets/models').glob('*.glb')):
 encoded=base64.b64encode(p.read_bytes()).decode()
 (model_dir/(p.stem+'.js')).write_text('window.__MODEL_B64=window.__MODEL_B64||{};window.__MODEL_B64['+json.dumps(p.stem)+']='+json.dumps(encoded)+';')
d=SHARED/'vendor/draco'
payload={'wrapper':base64.b64encode((d/'draco_wasm_wrapper.js').read_bytes()).decode(),'wasm':base64.b64encode((d/'draco_decoder.wasm').read_bytes()).decode()}
(BEFORE/'vendor/draco-inline.js').write_text('window.__DRACO_LIB='+json.dumps(payload,separators=(',',':'))+';')

camera_source='''/** 镜头参数读取与飞行进度。现场只修改根目录 camera-config.js。 */
export function cameraSettings() {
  const config = window.ATLAS_CAMERA || {};
  const number = (key, fallback, low, high) => {
    const value = Number(config[key]);
    return Number.isFinite(value) ? Math.max(low, Math.min(high, value)) : fallback;
  };
  return { detailZoom: number('DETAIL_ZOOM', 1.05, 0.9, 6), flightMs: number('FLIGHT_MS', 900, 400, 6000) };
}
export function flightProgress(progress) {
  const smooth = (t) => { const x = Math.max(0, Math.min(1, t)); return x * x * (3 - 2 * x); };
  // 前段先对准建筑所在方向，后段沿球面法向贴近，形成连续穿梭感。
  return { direction: smooth(progress / 0.72), distance: smooth(progress) };
}
export function flightDistance(from, to, progress, radius) {
  const a = Math.max(0.02, from - radius);
  const b = Math.max(0.02, to - radius);
  return radius + Math.exp(Math.log(a) + (Math.log(b) - Math.log(a)) * progress);
}
'''
(BEFORE/'js/camera.js').write_text(camera_source)
p=BEFORE/'js/globe/globe.js';s=p.read_text().replace("../../../shared/vendor/","../../vendor/").replace("fetch('../shared/data/land.geojson')","fetch('./assets/data/land.geojson')")
s=s.replace("import { createMarkers } from './markers.js';", "import { createMarkers } from './markers.js';\nimport { cameraSettings, flightProgress, flightDistance } from '../camera.js';")
s=s.replace('const TWEEN_MS = 1100;','// 飞行时长统一由根目录 camera-config.js 控制。')
s=s.replace('BASE_FOV, 1, 0.1, 100','BASE_FOV, 1, 0.02, 100')
s=s.replace('const ratio = LENS[level] ?? LENS.building;',"const ratio = (level === 'building' || level === 'closeup')\n      ? cameraSettings().detailZoom : (LENS[level] ?? LENS.building);")
s=s.replace("    const targetDir = sphPoint(lat, lon, 1);", "    const targetDir = sphPoint(lat, lon, 1);\n    host.dataset.cameraLevel = String(level);")
s=s.replace('      start: performance.now(),', "      start: performance.now(),\n      duration: (level === 'building' || level === 'closeup') ? cameraSettings().flightMs : 1100,")
s=s.replace('const progress = Math.min(1, (time - tween.start) / TWEEN_MS);\n      const eased = progress * progress * (3 - 2 * progress);', 'const progress = Math.min(1, (time - tween.start) / tween.duration);\n      const eased = flightProgress(progress);')
s=s.replace('slerp(tween.rotation, eased)', 'slerp(tween.rotation, eased.direction)')
s=s.replace('THREE.MathUtils.lerp(tween.fromDistance, tween.toDistance, eased)', 'flightDistance(tween.fromDistance, tween.toDistance, eased.distance, RADIUS)')
s=s.replace('    controls.update();\n    markers.update(reduced ? 0 : time);', "    controls.update();\n    host.dataset.cameraDistance = camera.position.length().toFixed(5);\n    host.dataset.cameraFlying = String(!!tween);\n    markers.update(reduced ? 0 : time);")
s=s.replace("  let pinchStart = null;", "  let pinchStart = null;\n  let visibleItems = new Set(items);")
s=s.replace('      if (!isFront(item.lat, item.lon)) return;', '      if (!visibleItems.has(item) || !isFront(item.lat, item.lon)) return;')
s=s.replace('setVisible: (list) => markers.setVisible(list),', 'setVisible: (list) => { visibleItems = new Set(list); markers.setVisible(list); },')
assert 'TWEEN_MS' not in s and 'eased.direction' in s
p.write_text(s)
p=BEFORE/'js/viewer.js';s=p.read_text().replace('../../shared/vendor/','../vendor/').replace("const OFFLINE = location.protocol === 'file:';", 'const OFFLINE = true; // 两种本地打开方式均读取包内模型脚本与解码器')
s=s.replace("new URL('../vendor/draco/', import.meta.url)", "new URL('./vendor/draco/', location.href)")
p.write_text(s)
p=BEFORE/'js/main.js';s=p.read_text().replace("  $('#globe').classList.add('is-ready');", "  $('#globe').classList.add('is-ready');\n  document.body.dataset.atlasReady = 'true';")
p.write_text(s)

config='''// D 交互设计师的现场修改入口：只改下面两个数字，保存后刷新网页。
// DETAIL_ZOOM：三级建筑详情的目标倍率；数字越大，镜头越靠近球面。
// FLIGHT_MS：飞行时长，单位毫秒；2400 表示 2.4 秒。
// 改前：1.05、900。改后：3.4、2400。其余代码与资料完全一致。
window.ATLAS_CAMERA = {
  DETAIL_ZOOM: %s,
  FLIGHT_MS: %s
};
'''
(BEFORE/'camera-config.js').write_text(config%('1.05','900'))
html=(SOURCE/'index.html').read_text()
html=html.replace('href="../index.html"','href="#top"').replace('"three":"../shared/vendor/three.module.js"','"three":"./vendor/three.module.js"')
html=html.replace('<script type="module" src="js/main.js?v=20261116d"></script>', '<script src="camera-config.js"></script>\n<script src="vendor/draco-inline.js"></script>\n<script type="module" src="js/main.js"></script>')
assert 'camera-config.js' in html and '../shared/' not in html
(BEFORE/'开发预览.html').write_text(html)

build='"""课后修改 js 后可重新生成双击离线页。现场改 camera-config.js 无需运行此工具。"""\nfrom pathlib import Path\nimport shutil,tempfile,re,subprocess,os\nROOT=Path(__file__).resolve().parent\nwith tempfile.TemporaryDirectory(prefix=\'atlas-offline-\') as work:\n    w=Path(work)\n    shutil.copytree(ROOT/\'js\',w/\'js\');shutil.copytree(ROOT/\'vendor\',w/\'vendor\')\n    (w/\'assets/data\').mkdir(parents=True)\n    for name in (\'china-provinces.json\',\'land.geojson\'):shutil.copy2(ROOT/\'assets/data\'/name,w/\'assets/data\'/name)\n    shutil.copy2(ROOT/\'data.json\',w/\'data.json\')\n    p=w/\'js/data.js\';s=p.read_text();start=s.index(\'let cache = null;\');end=s.index(\'export function filterBuildings\')\n    s=s[:start]+"import BUILDINGS from \'../data.json\';\\nexport async function loadBuildings(){ return BUILDINGS; }\\n\\n"+s[end:];p.write_text(s)\n    p=w/\'js/globe/globe.js\';s=p.read_text()\n    s=re.sub(r"const landGeoJson = await fetch\\(\'\\./assets/data/land\\.geojson\'\\)\\.then\\(\\(res\\) => \\{.*?\\n  \\}\\);",\'const landGeoJson = LAND;\',s,flags=re.S)\n    start=s.index(\'  let data = null;\')\n    end=s.index(\'  const features =\',start)\n    s=s[:start]+\'  const data = PROVINCES;\\n\\n\'+s[end:]\n    s="import LAND from \'../../assets/data/land.geojson\';\\nimport PROVINCES from \'../../assets/data/china-provinces.json\';\\n"+s\n    assert \'fetch(\' not in s;p.write_text(s)\n    exe=os.environ.get(\'ESBUILD_BIN\') or shutil.which(\'esbuild\')\n    command=[exe] if exe else [\'npx\',\'--no-install\',\'esbuild\']\n    subprocess.run(command+[str(w/\'js/main.js\'),\'--bundle\',\'--format=esm\',\'--minify\',\'--legal-comments=none\',\'--loader:.geojson=json\',\'--alias:three=\'+str(w/\'vendor/three.module.js\'),\'--outfile=\'+str(w/\'bundle.js\')],check=True)\n    html=(ROOT/\'开发预览.html\').read_text();js=(w/\'bundle.js\').read_text().replace(\'</script\',\'<\'+chr(92)+\'/script\')\n    html=re.sub(r\'<script type="importmap">.*?</script>\',\'\',html,flags=re.S)\n    html=html.replace(\'<script type="module" src="js/main.js"></script>\',\'<script type="module">\'+js+\'</script>\')\n    (ROOT/\'index.html\').write_text(html)\nprint(\'已更新 index.html。现场只改 camera-config.js 不用重新打包。\')\n'
(BEFORE/'build_offline.py').write_text(build)
server='''"""标准库本地服务器：只监听本机，无需安装第三方模块。"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
import webbrowser,sys
ROOT=Path(__file__).resolve().parent
class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store');super().end_headers()
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(ROOT)))
page='开发预览.html' if '--source' in sys.argv else 'index.html'
from urllib.parse import quote
url='http://127.0.0.1:'+str(server.server_port)+'/'+quote(page)
print('本地地址：'+url,flush=True);print('请保持本窗口打开；Ctrl+C 停止。',flush=True);webbrowser.open(url)
try: server.serve_forever()
except KeyboardInterrupt: pass
finally: server.server_close()
'''
(BEFORE/'start_server.py').write_text(server)
(BEFORE/'启动-Windows.bat').write_bytes(b'@echo off\r\ncd /d "%~dp0"\r\nwhere py >nul 2>nul\r\nif %errorlevel% equ 0 (py -3 start_server.py) else (python start_server.py)\r\npause\r\n')
(BEFORE/'启动-Mac.command').write_text('#!/bin/zsh\ncd -- "$(dirname "$0")"\nexec python3 start_server.py\n');(BEFORE/'启动-Mac.command').chmod(0o755)
(BEFORE/'导出原始GLB.py').write_text('''from pathlib import Path\nimport base64,re,json\nroot=Path(__file__).resolve().parent;out=root/'导出的原始GLB';out.mkdir(exist_ok=True)\nfor p in (root/'assets/models-js').glob('*.js'):\n    encoded=re.search(r']="([A-Za-z0-9+/=]+)";',p.read_text()).group(1)\n    (out/(p.stem+'.glb')).write_bytes(base64.b64decode(encoded))\nprint('12座模型已导出：'+str(out))\n''')
notes='''D 岗位 · 第一轮 · 现存木构建筑图鉴镜头演示

一、打开成品
将整个文件夹解压到电脑本地。双击根目录 index.html，可在 Chrome / Edge 中离线运行。
不要在 ZIP 预览里直接打开 HTML，不要只拷贝 index.html。
无需联网，也无需安装 Python、Node 或 VS Code 插件即可查看离线成品。
两个包都有同样的 39 条建筑资料、39 张正在使用的照片、12 座现有三维建筑模型和省界数据。
中国、日本、欧洲与朝代、省份筛选、三级建筑详情、12 座三维预览均保留。
没有模型的条目保留图文，并没有虚构或强行对应其他模型。

二、D 现场只修改一个文件
使用 VS Code“打开文件夹”，选择“01_镜头未拉近”解压后的文件夹。
打开根目录 camera-config.js，将：
  DETAIL_ZOOM: 1.05   改为   DETAIL_ZOOM: 3.4
  FLIGHT_MS: 900      改为   FLIGHT_MS: 2400
保存（Ctrl+S），回到浏览器按 Ctrl+F5 刷新。
这两处分别控制三级建筑详情的近景目标倍率与过渡时长，国家和朝代总览的过渡保持原样。地球半径与安全距离已在底层限制，不会钻进球体。
现场不需要修改 index.html 里的打包脚本，不需要重新生成网页。
“02_镜头穿梭已完善”是核对用的完成版本；除了以上两个数字，其他文件与第一包完全一致。
第一包可以直接在现场改成完成版，不需要换包冒充修改。

三、建议演示路径
1. 全局页面点击“中国”。
2. 点击“唐”，打开“建筑名录”，选择“佛光寺东大殿”。也可点地球上的同名标签。
3. 修改前展示：镜头只是小幅聚焦，建筑位置与全球、地区之间的层级差异不明显。
4. 同伴提出：“点击具体建筑后，能否飞得更近，让观众感觉从全球进入到建筑所在位置？”
5. D 打开 camera-config.js，修改上面的两个数字，保存、刷新。
6. 重新按“中国 → 唐 → 佛光寺东大殿”操作，展示先对准方位、再连续贴近球面的过程。
7. 点左侧照片上的“三维”，打开这座建筑现有的三维模型；拖动旋转、滚轮或双指缩放，Esc 关闭。
8. 返回上一层或点全球复位，证明不是播放视频，数据筛选与交互仍能继续操作。
推荐先练习同一条路径，避免修改前后选择了不同建筑导致效果不易比较。

四、简短解说参考
“我把 A 提供的低保真页面落实成左侧图文、中央地球、右侧地区与朝代导航。
现在选择一座具体建筑，发现镜头只做了轻微放大，空间层级还不够清楚。
我把近景倍率从 1.05 调到 3.4，把飞行时长从 900 毫秒调到 2400 毫秒。
底层程序先对准建筑坐标，再平滑贴近球面；保存刷新后，我们重新选择佛光寺东大殿。
现在能从全球尺度逐步进入到建筑所在区域，再点图版进入三维模型，游客可以自己旋转观察。”

五、代码与资源位置
camera-config.js：现场唯一需要修改的参数文件。
js/main.js：地区、朝代、省份、建筑详情与三维预览的页面联动。
js/camera.js：参数读取与平滑飞行算法。
js/globe/globe.js：Three.js 地球、镜头、光点与触摸交互。
js/viewer.js：三维建筑模型加载与旋转缩放。
js/views/：首屏、地区列表和建筑详情的图文组件。
css/：可直接修改的网页排版和样式。
data.json：39 条图册资料。
assets/data/：陆地、省界和照片资料来源。
assets/buildings/：网页实际用到的 39 张照片。
assets/models-js/：12 座 GLB 的无损 Base64 脚本版本，供双击离线打开按需读取。
vendor/：Three.js、模型解析与 Draco 解码器，均随包携带。
导出原始GLB.py：如需原始模型，装有 Python 的电脑运行此文件，可从模型脚本无损还原 12 个 GLB。

六、需要本地 HTTP 部署时
电脑已安装 Python 3：Windows 双击“启动-Windows.bat”，Mac 在终端执行 python3 start_server.py。
服务器只监听 127.0.0.1，浏览器会自动打开本机地址。保持命令窗口开启。
也可在本文件夹运行 python3 -m http.server 8022 --bind 127.0.0.1，然后访问 http://127.0.0.1:8022/ 。
若要从可读的 js 模块直接调试，运行 python3 start_server.py --source；它打开“开发预览.html”。
“开发预览.html”需要 HTTP，“index.html”可直接双击；二者都读取同一份 camera-config.js。
修改 css 或 camera-config.js 后保存刷新即可。
课后修改 js、data.json 或地图数据后，在已配好 Node/esbuild 的电脑运行 python3 build_offline.py，重新生成 index.html。
build_offline.py 使用本机已安装的 esbuild，或 npx --no-install esbuild，不会自动下载安装。
比赛现场修改这两个数字不依赖上述构建环境。

七、触屏与演示注意
支持单指拖动、双指缩放、光点与名录点击，保持原有触屏按钮热区。
点击具体建筑才进入本次修改的三级镜头；选择国家或朝代仍是总览。
模型为现有教学/预览资源，资料仍按原图册口径保留，不宣称为精确测绘复原。
若电脑系统已关闭动画效果，网页会尊重“减少动态效果”设置，直接显示最终近景；演示穿梭时请使用系统默认动画设置。
本包只对应你本次要求的第一轮图鉴演示，不混入第二轮 120s 组装游戏代码。
'''
(BEFORE/'先看这里-D现场操作.txt').write_text(notes)
# Original overview is retained in product UI; no extra teaching/debug labels are inserted.
env=None
import os
env=dict(os.environ,ESBUILD_BIN=str(ESBUILD))
subprocess.run(['python3',str(BEFORE/'build_offline.py')],env=env,check=True)
shutil.copytree(BEFORE,AFTER)
(AFTER/'camera-config.js').write_text(config%('3.4','2400'))
checks=[]
for p in sorted(BEFORE.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(BEFORE);same=hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((AFTER/rel).read_bytes()).digest()
 checks.append({'file':str(rel),'identical':same})
assert [c['file'] for c in checks if not c['identical']]==['camera-config.js']
(ROOT/'验证记录/两版差异与资源核对.json').write_text(json.dumps({'source':str(SOURCE),'buildings':len(data),'models':len(list(model_dir.glob('*.js'))),'referenced_photos':len(data),'different_files':['camera-config.js'],'config_before':{'DETAIL_ZOOM':1.05,'FLIGHT_MS':900},'config_after':{'DETAIL_ZOOM':3.4,'FLIGHT_MS':2400},'file_count_per_package':len(checks),'checks':checks},ensure_ascii=False,indent=2))
print('PACKAGES_BUILT',len(checks),'files each; difference: camera-config.js only')
