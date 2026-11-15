# three.js 实现要点（含可跑骨架）

> 用途：学生动手开发的起点。这份文档里的代码是**可直接跑通**的最小骨架，不是伪代码。
> 环境：Vite + 原生 three.js，不引入任何 UI 框架。

---

## 一、项目结构

```
dougong/
├── index.html
├── src/
│   ├── main.js            # 入口
│   ├── scene.js           # 场景/相机/光照/渲染器
│   ├── loader.js          # GLB 加载 + 构件索引
│   ├── explode.js         # 爆炸视图
│   ├── picking.js         # 点击拾取 + 高亮
│   ├── ui.js              # DOM 界面同步
│   └── data/parts.js      # 构件释义（与模型 userData 对应）
├── public/
│   ├── models/puzuo.glb
│   └── decoders/draco/    # 必须本地化，不要用 CDN
└── vite.config.js
```

`vite.config.js` 关键一行：`base: './'`（相对路径，才能部署到任意子目录）。

---

## 二、最小可跑骨架（index.html）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no" />
<title>榫卯智言 · 斗拱</title>
<style>
  html, body { margin:0; height:100%; background:#131315; overflow:hidden;
               -webkit-user-select:none; user-select:none; }
  #app { position:fixed; inset:0; }
  canvas { display:block; touch-action:none; }  /* 关键：禁用浏览器默认手势 */
  #tip { position:fixed; left:24px; bottom:24px; color:#e8e0d4;
         font:16px/1.6 system-ui,sans-serif; pointer-events:none; }
  #panel { position:fixed; right:24px; top:24px; width:320px; padding:20px;
           background:rgba(28,26,24,.92); color:#e8e0d4; border-radius:12px;
           font:15px/1.7 system-ui,sans-serif; display:none; }
  #panel h3 { margin:0 0 8px; font-size:20px; color:#e6b06a; }
  .btn { position:fixed; right:24px; bottom:24px; display:flex; gap:12px; }
  .btn button { min-width:88px; height:64px; border:0; border-radius:12px;
                background:#e6b06a; color:#1a1a1a; font-size:17px; font-weight:600; }
</style>
</head>
<body>
<div id="app"></div>
<div id="tip">拖动旋转 · 双指缩放 · 点击构件查看说明</div>
<div id="panel"><h3></h3><p></p><small></small></div>
<div class="btn">
  <button id="explode">拆解</button>
  <button id="reset">复位</button>
</div>

<script type="importmap">
{ "imports": {
    "three": "https://unpkg.com/three@0.169.0/build/three.module.js",
    "three/addons/": "https://unpkg.com/three@0.169.0/examples/jsm/"
} }
</script>

<script type="module">
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

// ---------- 1. 基础三件套 ----------
const app = document.getElementById('app');
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));   // 大屏必限 2，否则显存爆
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
app.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x131315);
scene.fog = new THREE.Fog(0x131315, 8, 22);

const camera = new THREE.PerspectiveCamera(42, innerWidth/innerHeight, 0.05, 100);
camera.position.set(2.2, 1.6, 3.2);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.enablePan = false;
controls.minDistance = 0.8;
controls.maxDistance = 8;
controls.maxPolarAngle = Math.PI * 0.85;
controls.target.set(0, 0.6, 0);

// ---------- 2. 光照（展厅低照度：少量光源 + 环境光，不要堆灯）----------
scene.add(new THREE.HemisphereLight(0xf5e6d0, 0x2a241f, 1.1));
const key = new THREE.DirectionalLight(0xfff2dd, 2.0);
key.position.set(3, 5, 4);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.near = 1; key.shadow.camera.far = 20;
key.shadow.camera.left = -4; key.shadow.camera.right = 4;
key.shadow.camera.top = 4;   key.shadow.camera.bottom = -4;
key.shadow.bias = -0.0005;   // 防阴影痤疮
scene.add(key);
const fill = new THREE.DirectionalLight(0xbcd0e8, 0.5);
fill.position.set(-4, 2, -3);
scene.add(fill);

// ---------- 3. 加载模型 ----------
const draco = new DRACOLoader();
draco.setDecoderPath('/decoders/draco/');       // ⚠️ 本地路径，不要 CDN
const gltfLoader = new GLTFLoader();
gltfLoader.setDRACOLoader(draco);

let root = null;
const parts = [];            // 所有可点构件
const homePos = new Map();   // 记录初始位置，用于复位

gltfLoader.load('/models/puzuo.glb', (gltf) => {
  root = gltf.scene;
  root.traverse((o) => {
    if (!o.isMesh) return;
    o.castShadow = true;
    o.receiveShadow = true;
    o.userData.baseY = o.position.y;
    // 分层爆炸需要一个"层"标记；优先读 GLB 里自带的，否则按命名推断
    o.userData.layer = o.userData.layer ?? inferLayer(o.name);
    homePos.set(o, o.position.clone());
    parts.push(o);
  });
  scene.add(root);

  // 自动取景
  const box = new THREE.Box3().setFromObject(root);
  const size = box.getSize(new THREE.Vector3()).length();
  controls.maxDistance = size * 3;
  camera.position.set(size*0.7, size*0.55, size*0.95);
});

// 从模型名推断层号（配合命名规范 gong_/dou_/ang_/fang_...）
function inferLayer(name) {
  if (name.startsWith('dou_ludou')) return 0;      // 栌斗层
  if (name.includes('tiao1'))        return 1;      // 第一跳
  if (name.includes('tiao2'))        return 2;
  if (name.includes('tiao3'))        return 3;
  if (name.includes('tiao4'))        return 4;
  if (name.startsWith('ang_'))       return 3;
  if (name.startsWith('shuatou'))    return 5;      // 耍头层
  if (name.startsWith('chenfang'))   return 6;      // 衬枋头层
  return 2;
}

// ---------- 4. 爆炸视图（分层平移 + 缓动）----------
const LAYER_GAP = 0.34;      // 每层抬高距离，按实际尺度调
const RADIAL_K  = 0.9;       // 径向散开倍数
let explodeTarget = 0;       // 0 = 合拢，1 = 完全拆开
let explodeNow = 0;

function updateExplode() {
  if (!root) return;
  explodeNow += (explodeTarget - explodeNow) * 0.12;   // 简易缓动
  for (const o of parts) {
    const h = homePos.get(o);
    const layer = o.userData.layer ?? 0;
    o.position.y = h.y + explodeNow * layer * LAYER_GAP;
    // 径向微散：以模型中心为原点
    if (explodeNow > 0.01) {
      const dir = h.clone().setY(0).normalize();
      o.position.x = h.x + dir.x * explodeNow * RADIAL_K * (layer/6);
      o.position.z = h.z + dir.z * explodeNow * RADIAL_K * (layer/6);
    } else {
      o.position.x = h.x; o.position.z = h.z;
    }
  }
}

document.getElementById('explode').onclick = () => {
  explodeTarget = explodeTarget > 0.5 ? 0 : 1;
};
document.getElementById('reset').onclick = () => {
  explodeTarget = 0;
  controls.reset();
  hidePanel();
};

// ---------- 5. 点击拾取 + 高亮 ----------
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const panel = document.getElementById('panel');
let selected = null;

// 统一的指针坐标换算（鼠标 / 触摸通用）
function toNDC(e) {
  const r = renderer.domElement.getBoundingClientRect();
  pointer.x = ((e.clientX - r.left) / r.width) * 2 - 1;
  pointer.y = -((e.clientY - r.top) / r.height) * 2 + 1;
}

function pick(e) {
  toNDC(e);
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObjects(parts, false)[0];
  if (hit) select(hit.object);
}

function select(obj) {
  if (selected) {
    selected.material.emissive?.setHex(0x000000);
  }
  selected = obj;
  // 高亮：给 emissive 一个暖色，注意材质需共享则要 clone
  if (obj.material.emissive) obj.material.emissive.setHex(0x5a3a10);
  showPanel(obj.userData);
}

function showPanel(d) {
  panel.style.display = 'block';
  panel.querySelector('h3').textContent = d.name_cn ?? '构件';
  panel.querySelector('p').textContent  = d.definition ?? '';
  panel.querySelector('small').textContent = d.source ? '依据：' + d.source : '';
}
function hidePanel() { panel.style.display = 'none'; }

// 用 pointerup 而不是 click：触屏更稳，且避免拖动误触发
let downXY = null;
renderer.domElement.addEventListener('pointerdown', (e) => {
  downXY = [e.clientX, e.clientY];
});
renderer.domElement.addEventListener('pointerup', (e) => {
  if (!downXY) return;
  const moved = Math.hypot(e.clientX - downXY[0], e.clientY - downXY[1]);
  if (moved < 8) pick(e);          // 位移 < 8px 才算"点击"
  downXY = null;
});

// ---------- 6. 循环 ----------
function tick() {
  requestAnimationFrame(tick);
  controls.update();
  if (explodeNow !== explodeTarget) updateExplode();
  renderer.render(scene, camera);
}
tick();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});
</script>
</body>
</html>
```

---

## 三、必须踩过的 8 个坑

### 1. `touch-action: none`
不写这行，双指缩放会触发浏览器页面缩放，整个 3D 场景会跟着页面一起放大。

### 2. 点击阈值
触屏上"点一下"会带 5—15 px 位移。用 `pointerup` + 位移阈值（8 px）判断，不要用 `click`。

### 3. 材质共享导致高亮全亮
如果多个构件共用同一个 material 实例，改一个的 `emissive` 会全部变色。
**解决**：建模导出时每个构件独立材质，或 `clone()` 后再改。

### 4. `setPixelRatio` 不设上限
4K 触摸屏的 devicePixelRatio 可能是 2—3，直接设置会让 GPU 渲染 3 倍像素，帧率腰斩。
**必加** `Math.min(devicePixelRatio, 2)`。

### 5. 阴影太贵
移动端 GPU 开 2048 阴影贴图 + 多光源 = 掉帧重灾区。
**策略**：只保留一盏投影光；低配设备直接 `renderer.shadowMap.enabled = false`。

### 6. 拾取时 raycast 整个场景
只对 `parts` 数组做 `intersectObjects`，不要传 `scene.children`（会命中灯光、网格辅助线）。

### 7. GLB 里没有"层"信息
GLB 不会保存你的分层意图。**解决**：在 Blender 里给每个对象名加层号（如 `gong_huagong_tiao2_01`），运行时用命名推断；或导出时写入 `extras`，three.js 会读进 `userData`。

### 8. 字体与中文
不要用 webfont（断网会 fallback 成丑陋字体）。中文用 `system-ui`，需要特殊字形就转成图片/SVG。

---

## 四、性能预算表（大屏 4K）

| 指标 | 目标 | 检测方法 |
|---|---|---|
| 三角面 | < 30 万（单场景） | `renderer.info.render.triangles` |
| Draw call | < 100 | `renderer.info.render.calls` |
| 纹理显存 | < 200 MB | `renderer.info.memory.textures` + 尺寸估算 |
| 首屏加载 | < 3 s（本地） | Performance API |
| 帧率 | 稳定 60 fps | `stats.js` 截图存档 |
| GLB 体积 | 单朵 < 3 MB | `ls -lh` |

**一个 2048×2048 的 PNG 贴图，文件可能只有 1 MB，但解码后在 GPU 里占 16 MB。** 下载小 ≠ 显存小。

---

## 五、调试与验收工具

```bash
# 看模型里到底是什么在占体积
npx gltf-transform inspect public/models/puzuo.glb

# 压缩一条龙：Draco + WebP + 降分辨率
npx gltf-transform optimize in.glb out.glb \
  --compress draco --texture-compress webp --texture-size 1024
```

现场验收时开 `stats.js` 面板截图，这份截图就是申报书要的"性能测试报告"配图。

---

## 六、信源

- three.js 官方文档 DRACOLoader / GLTFLoader / KT2Loader
- gltf-transform CLI 官方文档
- 《How to Optimize GLB and glTF 3D Models for Three.js & WebGL Rendering》
- 产品配置器 16.7MB → 2.4MB 案例（量化参数与贴图策略）
