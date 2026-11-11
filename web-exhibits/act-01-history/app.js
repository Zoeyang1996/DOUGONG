import * as THREE from 'three';
import { GLTFLoader } from './vendor/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';

/* ============================================================
   一木相接 · 第一幕
   滚动驱动相机 · 六幕三维叙事
============================================================ */

const MAT = 'materials-3d';
const MODEL_DEFS = {
  G1: { file: `${MAT}/G1_榫卯初见/G1.glb`, asm: `${MAT}/G1_榫卯初见/assembly.json`, size: 3.1 },
  G2: { file: `${MAT}/G2_走入生活/G2.glb`, asm: `${MAT}/G2_走入生活/assembly.json`, size: 3.4 },
  G3: { file: `${MAT}/G3_斗拱之始/G3.glb`, asm: `${MAT}/G3_斗拱之始/assembly.json`, size: 3.2 },
  G4: { file: `${MAT}/G4_唐代铺作/G4.glb`, asm: `${MAT}/G4_唐代铺作/assembly.json`, size: 3.4 },
  G5: { file: `${MAT}/G5_保国寺宋构/G5.glb`, asm: `${MAT}/G5_保国寺宋构/assembly.json`, size: 3.4 },
  G6: { file: `${MAT}/G6_清式斗科/G6.glb`, asm: `${MAT}/G6_清式斗科/assembly.json`, size: 3.4 },
  K1: { file: `${MAT}/K1_斗/K1.glb`, asm: `${MAT}/K1_斗/assembly.json`, size: 1.5 },
  K2: { file: `${MAT}/K2_拱栱/K2.glb`, asm: `${MAT}/K2_拱栱/assembly.json`, size: 1.7 },
  K3: { file: `${MAT}/K3_升/K3.glb`, asm: `${MAT}/K3_升/assembly.json`, size: 1.3 },
  K4: { file: `${MAT}/K4_昂/K4.glb`, asm: `${MAT}/K4_昂/assembly.json`, size: 2.0 },
  K5: { file: `${MAT}/K5_翘/K5.glb`, asm: `${MAT}/K5_翘/assembly.json`, size: 1.8 },
};

/* 六幕与相机的对应 */
const CHAPTERS = [
  { models: ['G1'] },
  { models: ['G2'] },
  { models: ['G3'] },
  { models: ['G4', 'G5', 'G6'], era: true },
  { models: ['K1', 'K2', 'K3', 'K4', 'K5'], arc: true },
  { models: ['G5'], rise: true },
];

/* 相机关键帧：首屏 + 六幕 */
const KEYS = [
  { pos: [0.0, 2.4, 12.5], look: [0, 1.3, 0] },
  { pos: [3.8, 1.7, 5.6], look: [0, 1.0, 0] },
  { pos: [-4.0, 2.3, 5.0], look: [0, 1.0, 0] },
  { pos: [3.2, 3.2, 5.4], look: [0, 1.4, 0] },
  { pos: [0.0, 2.0, 7.4], look: [0, 1.2, 0] },
  { pos: [0.0, 2.4, 10.2], look: [0, 0.5, 0] },
  { pos: [1.4, 0.5, 4.8], look: [0, 2.8, 0] },
];

const PART_ARC = [
  [-3.4, 0, -0.9], [-1.7, 0, -0.2], [0, 0, 0.1], [1.7, 0, -0.2], [3.4, 0, -0.9],
];

const WOODS = [0xd8c0a2, 0xc9b190, 0xdfc9ab, 0xc2a887, 0xb89d7d];

/* 程序化木纹：柔色底 + 深淺木丝 */
const woodTex = (() => {
  const c = document.createElement('canvas');
  c.width = c.height = 512;
  const g = c.getContext('2d');
  g.fillStyle = '#8d7257';
  g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 170; i++) {
    const x = Math.random() * 512;
    const dark = Math.random() < 0.55;
    g.strokeStyle = dark
      ? `rgba(58,40,24,${0.05 + Math.random() * 0.13})`
      : `rgba(226,196,158,${0.04 + Math.random() * 0.09})`;
    g.lineWidth = 0.6 + Math.random() * 2.6;
    g.beginPath();
    for (let y = -8; y <= 520; y += 14) g.lineTo(x + Math.sin(y * 0.018 + i * 1.7) * 5, y);
    g.stroke();
  }
  for (let i = 0; i < 26; i++) { // 零星木节
    const x = Math.random() * 512, y = Math.random() * 512, r = 2 + Math.random() * 7;
    const gr = g.createRadialGradient(x, y, 0.5, x, y, r);
    gr.addColorStop(0, 'rgba(52,36,20,0.5)');
    gr.addColorStop(1, 'rgba(52,36,20,0)');
    g.fillStyle = gr;
    g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 4;
  return t;
})();

const smooth = (t) => t * t * (3 - 2 * t);
const clamp01 = (v) => Math.min(1, Math.max(0, v));

/* ------------------------------------------------------------
   场景
------------------------------------------------------------ */
const stage = document.getElementById('stage');
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
} catch (e) {
  document.querySelector('.veil-sub').textContent = '当前浏览器无法启动三维场景';
  throw e;
}
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
renderer.outputColorSpace = THREE.SRGBColorSpace;
stage.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0906);
scene.fog = new THREE.FogExp2(0x0b0906, 0.045);

const camera = new THREE.PerspectiveCamera(38, innerWidth / innerHeight, 0.1, 120);
camera.position.set(...KEYS[0].pos);

/* 光：暖金主光 + 冷色轮廓 */
scene.add(new THREE.AmbientLight(0x3a2f22, 0.6));
const key = new THREE.SpotLight(0xffd2a0, 120, 40, 0.62, 1, 1.4);
key.position.set(7, 10, 5);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.bias = -0.0004;
scene.add(key);
const rim = new THREE.DirectionalLight(0x5a708c, 1.5);
rim.position.set(-7, 5, -7);
scene.add(rim);
const fill = new THREE.DirectionalLight(0xffe6c4, 0.35);
fill.position.set(-3, 2, 6);
scene.add(fill);

/* 地面 */
const ground = new THREE.Mesh(
  new THREE.CircleGeometry(46, 64),
  new THREE.MeshStandardMaterial({ color: 0x0e0c08, roughness: 0.96, metalness: 0 })
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

/* 展台光晕 */
{
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 128, 8, 128, 128, 128);
  grad.addColorStop(0, 'rgba(255,196,130,0.32)');
  grad.addColorStop(0.55, 'rgba(255,178,110,0.10)');
  grad.addColorStop(1, 'rgba(255,178,110,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  const disc = new THREE.Mesh(
    new THREE.CircleGeometry(3.6, 48),
    new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false })
  );
  disc.rotation.x = -Math.PI / 2;
  disc.position.y = 0.012;
  scene.add(disc);
}

/* 浮尘 */
const dust = (() => {
  const n = 320;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    pos[i * 3] = (Math.random() - 0.5) * 22;
    pos[i * 3 + 1] = Math.random() * 8;
    pos[i * 3 + 2] = (Math.random() - 0.5) * 22;
  }
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({
    color: 0xd8b98a, size: 0.035, transparent: true, opacity: 0.4,
    blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true,
  }));
  scene.add(pts);
  return pts;
})();

/* ------------------------------------------------------------
   模型载入
------------------------------------------------------------ */
const veilBar = document.getElementById('veil-progress');
const manager = new THREE.LoadingManager();
manager.onProgress = (_u, done, total) => { veilBar.style.width = (done / total * 100) + '%'; };
const loader = new GLTFLoader(manager);
const draco = new DRACOLoader();
draco.setDecoderPath('./vendor/draco/');
loader.setDRACOLoader(draco);
const models = {}; // id -> {group, mats, parts:[{node,base,dir,note,name}], title}

function normalize(obj, size) {
  const box = new THREE.Box3().setFromObject(obj);
  const dim = box.getSize(new THREE.Vector3());
  const s = size / Math.max(dim.x, dim.y, dim.z);
  obj.scale.setScalar(s);
  const box2 = new THREE.Box3().setFromObject(obj);
  const ctr = box2.getCenter(new THREE.Vector3());
  obj.position.x -= ctr.x;
  obj.position.z -= ctr.z;
  obj.position.y -= box2.min.y;
}

async function loadModel(id, def) {
  const [gltf, asm] = await Promise.all([
    loader.loadAsync(def.file),
    fetch(def.asm).then((r) => r.json()).catch(() => null),
  ]);
  const root = gltf.scene;
  const mats = [];
  let ci = 0;
  root.traverse((ob) => {
    if (ob.isMesh) {
      ob.material = new THREE.MeshStandardMaterial({
        color: WOODS[ci++ % WOODS.length], map: woodTex, bumpMap: woodTex, bumpScale: 0.6,
        roughness: 0.82, metalness: 0,
        transparent: true, opacity: 0,
      });
      ob.castShadow = ob.receiveShadow = true;
      mats.push(ob.material);
    }
  });
  const group = new THREE.Group();
  group.add(root);
  normalize(root, def.size);
  group.visible = false;
  scene.add(group);

  const parts = [];
  if (asm && asm.parts) {
    for (const p of asm.parts) {
      let node = root.getObjectByName(p.id);
      if (!node) root.traverse((ob) => { if (!node && ob.name && ob.name.includes(p.id)) node = ob; });
      if (!node) continue;
      const off = new THREE.Vector3(...(p.appear?.offset || [0, 1, 0]));
      const dir = off.lengthSq() > 1e-6 ? off.clone().normalize() : new THREE.Vector3(0, 1, 0);
      node.userData.part = { name: (p.name_cn || p.id).replace(/_/g, ' '), note: p.note || '' };
      parts.push({ node, base: node.position.clone(), dir, info: node.userData.part });
    }
  }
  models[id] = { group, mats, parts, title: asm?.title || id, note: asm?.notes?.[0] || '' };
}

/* ------------------------------------------------------------
   滚动 → 章节进度
------------------------------------------------------------ */
const panels = [...document.querySelectorAll('.panel')];
const railBtns = [...document.querySelectorAll('.rail button')];
const railFill = document.getElementById('rail-fill');
const eraBar = document.getElementById('era');
const eraSpans = [...eraBar.querySelectorAll('span')];

let s = 0; // 0..6，首屏为 0，第 c 幕中心为 c+1
function readScroll() {
  const max = document.documentElement.scrollHeight - innerHeight;
  const p = clamp01(scrollY / max);
  s = p * (KEYS.length - 1);
  railFill.style.height = p * 100 + '%';
  const active = Math.round(s);
  panels.forEach((pn, i) => pn.classList.toggle('on', i === active));
  railBtns.forEach((b, i) => b.classList.toggle('on', i === active - 1));
}
addEventListener('scroll', readScroll, { passive: true });
railBtns.forEach((b) => b.addEventListener('click', () => {
  const pn = panels[+b.dataset.step + 1];
  window.scrollTo({ top: pn.offsetTop, behavior: 'smooth' });
}));

/* 章节淡入淡出区间 */
function chapterFade(c) {
  const center = c + 1;
  const fin = smooth(clamp01((s - (center - 0.72)) / 0.45));
  const fout = 1 - smooth(clamp01((s - (center + 0.72)) / 0.45));
  return fin * fout;
}
/* 第四章内部 唐→宋→清 */
function eraFade(i) {
  const u = clamp01((s - 3.35) / 1.3); // 幕内进度
  const seg = 1 / 3;
  const a = smooth(clamp01((u - i * seg + seg * 0.4) / (seg * 0.4)));
  const b = 1 - smooth(clamp01((u - (i + 1) * seg + seg * 0.4) / (seg * 0.4)));
  return i === 2 ? a : a * b;
}

/* ------------------------------------------------------------
   拾取
------------------------------------------------------------ */
const ray = new THREE.Raycaster();
const noteEl = document.getElementById('note');
const noteName = document.getElementById('note-name');
const noteText = document.getElementById('note-text');
const noteEyebrow = document.getElementById('note-eyebrow');
let downAt = null;

addEventListener('pointerdown', (e) => { downAt = [e.clientX, e.clientY]; });
addEventListener('pointerup', (e) => {
  if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 6) return;
  const ch = Math.round(s) - 1;
  if (ch < 0 || ch > 5) return;
  const ids = CHAPTERS[ch].models;
  const targets = ids.filter((id) => models[id] && models[id].group.visible)
    .map((id) => models[id].group);
  if (!targets.length) return;
  ray.setFromCamera(new THREE.Vector2(e.clientX / innerWidth * 2 - 1, -(e.clientY / innerHeight) * 2 + 1), camera);
  const hits = ray.intersectObjects(targets, true);
  if (!hits.length) { noteEl.hidden = true; return; }
  let ob = hits[0].object, info = null, mid = null;
  while (ob && !info) {
    if (ob.userData.part) info = ob.userData.part;
    else ob = ob.parent;
  }
  for (const id of ids) if (models[id].group === hits[0].object || models[id].group.getObjectById(hits[0].object.id)) mid = id;
  const m = models[mid] || models[ids[0]];
  noteEyebrow.textContent = m.title;
  noteName.textContent = info ? info.name : m.title;
  noteText.textContent = (info && info.note) || m.note || '木构构件，名称与做法以史料核定为准。';
  noteEl.hidden = false;
  const x = Math.min(e.clientX + 18, innerWidth - 330);
  const y = Math.min(e.clientY - 20, innerHeight - 240);
  noteEl.style.left = Math.max(16, x) + 'px';
  noteEl.style.top = Math.max(80, y) + 'px';
});
document.getElementById('note-close').addEventListener('click', () => { noteEl.hidden = true; });
addEventListener('keydown', (e) => { if (e.key === 'Escape') noteEl.hidden = true; });

/* ------------------------------------------------------------
   渲染循环
------------------------------------------------------------ */
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const vPos = new THREE.Vector3(), vLook = new THREE.Vector3();
const pA = new THREE.Vector3(), pB = new THREE.Vector3(), lA = new THREE.Vector3(), lB = new THREE.Vector3();
let mx = 0, my = 0;
addEventListener('pointermove', (e) => {
  mx = (e.clientX / innerWidth - 0.5);
  my = (e.clientY / innerHeight - 0.5);
});
const clock = new THREE.Clock();

function frame() {
  const dt = Math.min(clock.getDelta(), 0.05);
  const t = clock.elapsedTime;

  /* 相机：关键帧平滑插值 + 呼吸感 */
  const i = Math.min(KEYS.length - 2, Math.floor(s));
  const f = smooth(s - i);
  pA.set(...KEYS[i].pos); pB.set(...KEYS[i + 1].pos);
  lA.set(...KEYS[i].look); lB.set(...KEYS[i + 1].look);
  vPos.lerpVectors(pA, pB, f);
  vLook.lerpVectors(lA, lB, f);
  if (!reduced) {
    vPos.x += Math.sin(t * 0.4) * 0.08 + mx * 0.5;
    vPos.y += Math.cos(t * 0.53) * 0.06 - my * 0.3;
  }
  camera.position.lerp(vPos, 0.08);
  camera.lookAt(vLook);

  /* 各幕模型 */
  CHAPTERS.forEach((ch, c) => {
    const fade = chapterFade(c);
    ch.models.forEach((id, mi) => {
      const m = models[id];
      if (!m) return;
      let op = fade;
      if (ch.era) op *= eraFade(mi);
      const on = op > 0.015;
      m.group.visible = on;
      if (!on) return;
      m.mats.forEach((mt) => { mt.opacity = op; });
      /* 入场装配：零件从偏移处归位 */
      const tin = smooth(clamp01((s - (c + 0.28)) / 0.5));
      for (const p of m.parts) {
        p.node.position.copy(p.base).addScaledVector(p.dir, (1 - tin) * 1.6);
      }
      /* 缓慢旋转 */
      if (!reduced) m.group.rotation.y += dt * (ch.arc ? 0.05 : 0.12) * op;
    });
  });

  /* 伍 · 构件弧线排布 */
  if (models.K1) {
    CHAPTERS[4].models.forEach((id, k) => {
      const m = models[id];
      if (!m || !m.group.visible) return;
      const [x, , z] = PART_ARC[k];
      m.group.position.x = x;
      m.group.position.z = z;
      if (!reduced) m.group.position.y = Math.sin(t * 0.9 + k * 1.3) * 0.12 + 0.35;
      else m.group.position.y = 0.35;
    });
  }

  /* 时代标签 */
  const eraOn = s > 3.15 && s < 4.85;
  eraBar.classList.toggle('on', eraOn);
  if (eraOn) {
    const u = clamp01((s - 3.35) / 1.3);
    const ai = Math.min(2, Math.floor(u * 3));
    eraSpans.forEach((sp, k) => sp.classList.toggle('on', k === ai));
  }

  /* 浮尘 */
  if (!reduced) {
    dust.rotation.y = t * 0.012;
    dust.position.y = Math.sin(t * 0.11) * 0.3;
  }

  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

/* ------------------------------------------------------------
   启动
------------------------------------------------------------ */
(async () => {
  try {
    await loadModel('G1', MODEL_DEFS.G1); // 先载第一幕，尽快揭幕
    readScroll();
    frame();
    document.getElementById('veil').classList.add('off');
    /* 其余后台载入 */
    await Promise.all(Object.entries(MODEL_DEFS).filter(([id]) => id !== 'G1')
      .map(([id, def]) => loadModel(id, def)));
    window.demoReady = true;
    window.__demo = { models, camera, scene, getS: () => s, THREE };
  } catch (e) {
    document.querySelector('.veil-sub').textContent = '素材载入失败，请检查模型文件';
    console.error(e);
  }
})();
