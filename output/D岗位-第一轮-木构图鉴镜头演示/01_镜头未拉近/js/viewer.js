import * as THREE from 'three';
import { OrbitControls } from '../vendor/OrbitControls.js';
import { GLTFLoader } from '../vendor/GLTFLoader.js';
import { DRACOLoader } from '../vendor/DRACOLoader.js';

/**
 * 三级详情页里的"看三维"预览层。
 * 一个全屏窗口、一个常驻渲染器；每次打开只换模型，关掉即释放几何与贴图。
 */
/* ── 离线包（file://）──────────────────────────────────────────
   浏览器在 file:// 下禁止 fetch 本地文件，模型与解码器都读不到。
   所以离线包把 GLB 转成 base64 存成普通 .js，用 <script src> 注入
   （脚本加载不受该限制），再直接交给 loader.parse 解析。
   ───────────────────────────────────────────────────────────── */
const OFFLINE = true; // 两种本地打开方式均读取包内模型脚本与解码器
const b64Cache = new Map();

function b64ToBuffer(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
  return bytes.buffer;
}

function modelKey(url) {
  const name = url.split('/').pop() || '';
  return name.replace(/\.glb(\?.*)?$/i, '');
}

/** 注入 assets/models-js/<key>.js，等它把 window.__MODEL_B64[key] 填好 */
function loadB64(key) {
  if (b64Cache.has(key)) return Promise.resolve(b64Cache.get(key));
  const store = (window.__MODEL_B64 = window.__MODEL_B64 || {});
  if (store[key]) {
    b64Cache.set(key, store[key]);
    return Promise.resolve(store[key]);
  }
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = `assets/models-js/${key}.js`;
    script.onload = () => {
      const value = store[key];
      if (value) {
        b64Cache.set(key, value);
        resolve(value);
      } else {
        reject(new Error('模型数据为空'));
      }
    };
    script.onerror = () => reject(new Error('模型数据载入失败'));
    document.head.append(script);
  });
}

export function createModelViewer({ onOpen, onClose } = {}) {
  const root = document.createElement('div');
  root.className = 'viewer';
  root.hidden = true;
  root.setAttribute('role', 'dialog');
  root.setAttribute('aria-modal', 'true');
  root.setAttribute('aria-label', '建筑三维预览');
  root.innerHTML = `
    <div class="viewer-stage" aria-hidden="true"></div>
    <div class="viewer-head">
      <p class="viewer-name"></p>
      <p class="viewer-sub">拖动旋转 · 滚轮缩放 · Esc 关闭</p>
    </div>
    <button class="viewer-close" type="button" aria-label="关闭三维预览"><span aria-hidden="true">×</span></button>
    <p class="viewer-status" role="status"></p>
  `;
  document.body.append(root);

  const stage = root.querySelector('.viewer-stage');
  const nameEl = root.querySelector('.viewer-name');
  const statusEl = root.querySelector('.viewer-status');
  const closeBtn = root.querySelector('.viewer-close');

  let renderer = null;
  let scene = null;
  let camera = null;
  let controls = null;
  let model = null;
  let currentToken = 0;
  let resizeObserver = null;
  let rafId = 0;
  let autoSpin = true;
  let closing = false;
  let closeTimer = 0;

  function ensureRenderer() {
    if (renderer) return;
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    stage.append(renderer.domElement);

    scene = new THREE.Scene();

    // 暖色主光 + 冷色补光，尽量贴纸面配色；不投影，省一次 render pass
    const hemi = new THREE.HemisphereLight(0xfff1d8, 0x3a2c1c, 0.72);
    scene.add(hemi);

    const key = new THREE.DirectionalLight(0xfff4e2, 1.5);
    key.position.set(6, 9, 7);
    scene.add(key);

    const rim = new THREE.DirectionalLight(0x9fb6c8, 0.38);
    rim.position.set(-7, 4, -6);
    scene.add(rim);

    const fill = new THREE.DirectionalLight(0xffe6c0, 0.28);
    fill.position.set(-4, 2, 8);
    scene.add(fill);

    camera = new THREE.PerspectiveCamera(38, 1, 0.1, 500);
    camera.position.set(8, 7, 12);

    controls = new OrbitControls(camera, renderer.domElement);
    controls.enablePan = false;
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.rotateSpeed = 0.62;
    controls.zoomSpeed = 0.7;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.55;
    // 限住俯仰：太高会俯视到屋顶、太低会让台基跑出画外
    controls.minPolarAngle = 0.55;
    controls.maxPolarAngle = 1.44;
    controls.addEventListener('start', () => {
      autoSpin = false;
      controls.autoRotate = false;
    });

    const loader = new GLTFLoader();
    const draco = new DRACOLoader();
    const inlineLib = OFFLINE ? window.__DRACO_LIB : null;
    if (inlineLib) {
      // 解码器随离线包内联（wrapper + wasm），不再走网络请求
      const libs = {
        'draco_wasm_wrapper.js': new TextDecoder().decode(b64ToBuffer(inlineLib.wrapper)),
        'draco_decoder.wasm': b64ToBuffer(inlineLib.wasm),
      };
      draco._loadLibrary = (name) => Promise.resolve(libs[name]);
    } else {
      draco.setDecoderPath(new URL('./vendor/draco/', location.href).href);
    }
    loader.setDRACOLoader(draco);

    resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(stage);
    resize();

    root._loader = loader;
    loop();
  }

  function resize() {
    if (!renderer) return;
    const w = stage.clientWidth;
    const h = stage.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function loop() {
    rafId = requestAnimationFrame(loop);
    if (root.hidden) return;
    controls.update();
    renderer.render(scene, camera);
  }

  function clearModel() {
    if (!model) return;
    scene.remove(model);
    model.traverse((node) => {
      if (node.isMesh) {
        node.geometry?.dispose();
        const mats = Array.isArray(node.material) ? node.material : [node.material];
        mats.forEach((m) => {
          if (!m) return;
          Object.values(m).forEach((v) => { if (v && v.isTexture) v.dispose(); });
          m.dispose();
        });
      }
    });
    model = null;
  }

  function frameObject(object) {
    const box = new THREE.Box3().setFromObject(object);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);

    const maxDim = Math.max(size.x, size.y, size.z);
    // 按竖直 / 水平两个方向分别求能装下的距离，取较远的那个
    const halfFov = THREE.MathUtils.degToRad(camera.fov) / 2;
    const aspect = Math.max(0.35, camera.aspect);
    const fitH = size.y / (2 * Math.tan(halfFov));
    const fitW = Math.max(size.x, size.z) / (2 * Math.tan(halfFov) * aspect);
    // 竖屏时宽度是硬约束，余量收紧到 8%，否则长条画面里模型会缩成一小块
    const portrait = camera.aspect < 0.85;
    const margin = portrait ? 1.1 : 1.34;
    const dist = Math.max(fitH, fitW) * margin;

    // 视线略低于模型中心：模型在画面里上浮一些，下方留出“悬空”的余地
    const lift = portrait ? 0.12 : 0.04;
    controls.target.set(center.x, center.y - size.y * lift, center.z);
    const dir = new THREE.Vector3(0.62, 0.42, 1).normalize();
    camera.position.copy(controls.target).addScaledVector(dir, dist);
    camera.near = Math.max(0.1, dist / 90);
    camera.far = dist * 12;
    camera.updateProjectionMatrix();

    controls.minDistance = maxDim * 0.62;
    controls.maxDistance = maxDim * 3.4;
    controls.update();
  }

  async function open({ url, name }) {
    if (!url) return;
    ensureRenderer();
    const token = ++currentToken;

    // 若上一次还在收场中，立刻收尾，避免两段动画叠在一起
    if (closing) {
      clearTimeout(closeTimer);
      root.classList.remove('is-closing');
      root.hidden = true;
      closing = false;
    }

    root.hidden = false;
    document.body.classList.add('viewer-open');
    nameEl.textContent = name || '';
    statusEl.textContent = '模型载入中…';
    statusEl.classList.remove('is-error');
    autoSpin = true;
    controls.autoRotate = true;
    closeBtn.focus({ preventScroll: true });
    resize();

    try {
      let gltf;
      if (OFFLINE) {
        const buffer = b64ToBuffer(await loadB64(modelKey(url)));
        if (token !== currentToken) return;
        statusEl.textContent = '模型解析中…';
        gltf = await root._loader.parseAsync(buffer, '');
      } else {
        gltf = await root._loader.loadAsync(url, (evt) => {
          if (token !== currentToken || !evt.total) return;
          const pct = Math.min(99, Math.round((evt.loaded / evt.total) * 100));
          statusEl.textContent = `模型载入中 ${pct}%`;
        });
      }
      if (token !== currentToken) return;

      clearModel();
      model = gltf.scene;
      model.traverse((node) => {
        if (!node.isMesh) return;
        node.castShadow = false;
        node.receiveShadow = false;
        if (node.material) node.material.side = THREE.FrontSide;
      });
      scene.add(model);
      frameObject(model);
      statusEl.textContent = '';
      onOpen?.();
    } catch (err) {
      console.error(err);
      if (token !== currentToken) return;
      statusEl.textContent = '模型载入失败，可关闭后重试';
      statusEl.classList.add('is-error');
    }
  }

  function close() {
    if (root.hidden || closing) return;
    currentToken += 1;
    closing = true;
    document.body.classList.remove('viewer-open');

    // 先播收场（模型沉回、玻璃散去），动画结束再真正隐藏并释放几何
    root.classList.add('is-closing');
    closeTimer = setTimeout(() => {
      root.classList.remove('is-closing');
      root.hidden = true;
      statusEl.textContent = '';
      clearModel();
      closing = false;
      onClose?.();
    }, 230);
  }

  closeBtn.addEventListener('click', close);

  // 点背景也关，但点到画面里的模型不关
  root.addEventListener('pointerdown', (event) => {
    if (event.target === root || event.target === stage) close();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !root.hidden) {
      event.stopPropagation();
      close();
    }
  }, true);

  return { open, close, get isOpen() { return !root.hidden; } };
}
