import * as THREE from 'three';
import { OrbitControls } from '../../../shared/vendor/OrbitControls.js';
import { buildEarthTexture } from './texture.js';
import { EARTH_VERTEX, EARTH_FRAGMENT } from './shaders.js';
import { createMarkers } from './markers.js';

const RADIUS = 2;
const MARKER_RADIUS = 2.008;
const PROVINCE_RADIUS = 2.004;
const MIN_DIST = 4.6;
const MAX_DIST = 11;
/** 贴面距离：允许镜头压到球面上方，用于省域尺度的特写 */
const DETAIL_DIST = RADIUS * 1.08;
const BASE_FOV = 44;
const TWEEN_MS = 1100;
const IDLE_DELAY = 5000;
const UP = new THREE.Vector3(0, 1, 0);

export function sphPoint(lat, lon, r = RADIUS) {
  const a = THREE.MathUtils.degToRad(lat);
  const b = THREE.MathUtils.degToRad(lon);
  return new THREE.Vector3(r * Math.cos(a) * Math.sin(b), r * Math.sin(a), r * Math.cos(a) * Math.cos(b));
}

/**
 * 建立地球场景。返回控制接口：聚焦、缩放、点位显隐与每帧回调。
 */
export async function createGlobe({ host, items, onPick, onFrame }) {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(BASE_FOV, 1, 0.1, 100);
  camera.position.copy(sphPoint(28, 85, 7.4));

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  host.append(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enablePan = false;
  controls.enableDamping = true;
  controls.dampingFactor = 0.075;
  controls.minDistance = MIN_DIST;
  controls.maxDistance = MAX_DIST;
  controls.rotateSpeed = 0.52;
  controls.zoomSpeed = 0.62;
  controls.enableZoom = false; // 滚轮与双指缩放由下方自定义，避免与 pinch 重复
  controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_ROTATE };

  const landGeoJson = await fetch('../shared/data/land.geojson').then((res) => {
    if (!res.ok) throw new Error('地理轮廓载入失败');
    return res.json();
  });

  const texture = await buildEarthTexture(landGeoJson);
  texture.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());

  const uniforms = {
    uMap: { value: texture },
    uInk: { value: new THREE.Color('#1c1712') },
    uSepia: { value: new THREE.Color('#6f4a24') },
    uBaseHi: { value: new THREE.Color('#f5d5a5') },
    uBaseLo: { value: new THREE.Color('#e5b57f') },
    uSea: { value: new THREE.Color('#d9b184') },
    uCell: { value: 4.6 * renderer.getPixelRatio() },
    uReveal: { value: 1 },
  };

  const material = new THREE.ShaderMaterial({
    vertexShader: EARTH_VERTEX,
    fragmentShader: EARTH_FRAGMENT,
    uniforms,
    extensions: { derivatives: true },
  });

  const earth = new THREE.Mesh(new THREE.SphereGeometry(RADIUS, 144, 96), material);
  earth.rotation.y = -Math.PI / 2;
  scene.add(earth);

  const positions = new Float32Array(items.length * 3);
  items.forEach((item, i) => {
    const p = sphPoint(item.lat, item.lon, MARKER_RADIUS);
    positions.set([p.x, p.y, p.z], i * 3);
  });

  const markers = createMarkers({ items, positions, pixelRatio: renderer.getPixelRatio() });
  scene.add(markers.object3D);

  // ── 省界：只在中国境内、且镜头压到省域尺度时才显形 ──
  const provinceLayer = await createProvinceLayer();
  scene.add(provinceLayer.object);

  const view = {
    width: 0,
    height: 0,
    stageTop: 0,
    stageHeight: 0,
    stageRight: 0,
    stageWidth: 0,
    bleed: 0,
    radius() {
      const distance = camera.position.length();
      const halfFov = THREE.MathUtils.degToRad(camera.fov) / 2;
      return (RADIUS / (distance * Math.tan(halfFov))) * (view.height / 2);
    },
    project(lat, lon) {
      const p = sphPoint(lat, lon, MARKER_RADIUS);
      const projected = p.clone().project(camera);
      return {
        x: ((projected.x + 1) / 2) * view.width,
        y: ((1 - projected.y) / 2) * view.height,
        front: isFront(lat, lon),
      };
    },
  };

  function isFront(lat, lon) {
    const n = sphPoint(lat, lon, 1);
    return n.dot(camera.position.clone().normalize()) > 0.08;
  }

  let tween = null;
  let idleAllowed = false;
  let paused = false;
  let lastInteraction = performance.now();
  /**
   * 镜头阶梯：以“球在屏幕上不越界的最大半径”为 1。
   * 全球 → 地区 → 朝代 → 单座，逐级放大。
   * 单座这一级会越过“整球可见”的边界，直接压到球面上方，
   * 目的是让省界与地势在画面里展开——此时球边出血是刻意的。
   */
  const LENS = { overview: 0.6, region: 0.86, era: 0.94, province: 1, closeup: 1.9, building: 2.6 };
  let maxRadius = 240;
  let fitDistance = MIN_DIST;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const tanHalfFov = () => Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
  const distanceForRadius = (r) => (RADIUS * view.height) / (2 * Math.max(1, r) * tanHalfFov());
  const nearestDistance = () => Math.max(MIN_DIST, distanceForRadius(maxRadius));
  const farthestDistance = () => Math.max(nearestDistance() + 0.6, distanceForRadius(maxRadius * 0.34));
  /** 允许压到球面上的最近距离（单座特写用，会让球边出血） */
  const detailFloor = () => DETAIL_DIST;

  function lensDistance(level) {
    if (typeof level === 'number') return level;
    const ratio = LENS[level] ?? LENS.building;
    return distanceForRadius(maxRadius * ratio);
  }

  /** 按层级取最近距离：单座特写（以及显式传入的距离）允许越过“整球可见”的边界 */
  function floorFor(level) {
    const close = level === 'building' || level === 'closeup' || typeof level === 'number';
    return close ? detailFloor() : nearestDistance();
  }

  controls.addEventListener('start', () => {
    tween = null;
    lastInteraction = performance.now();
  });

  function focus(lat, lon, level = 'building', { instant = false } = {}) {
    const targetDir = sphPoint(lat, lon, 1);
    const toDistance = THREE.MathUtils.clamp(
      lensDistance(level), floorFor(level), farthestDistance(),
    );
    if (instant || reduced) {
      camera.position.copy(targetDir.multiplyScalar(toDistance));
      controls.update();
      tween = null;
      return;
    }
    tween = {
      fromDir: camera.position.clone().normalize(),
      toDir: targetDir,
      rotation: new THREE.Quaternion().setFromUnitVectors(camera.position.clone().normalize(), targetDir),
      fromDistance: camera.position.length(),
      toDistance,
      start: performance.now(),
    };
  }

  function zoom(factor) {
    tween = null;
    lastInteraction = performance.now();
    const next = THREE.MathUtils.clamp(
      camera.position.length() * factor, detailFloor(), farthestDistance(),
    );
    camera.position.setLength(next);
    controls.update();
  }

  // ── 尺寸与焦距 ──
  const stageEl = host.parentElement;

  /** 只算舞台边界与镜头上限，不重设画布 */
  function layoutMetrics() {
    if (!view.width || !view.height) return;
    const box = host.getBoundingClientRect();
    const stage = stageEl.getBoundingClientRect();
    view.stageTop = stage.top - box.top;
    view.stageHeight = stage.height;
    view.stageRight = stage.right - box.left;
    view.stageWidth = stage.width;
    view.bleed = Math.max(0, stage.left - box.left);

    // 球可用的最大半径：上下不越出视口、右侧不压导航、整球仍在画布内
    const midY = stage.top + stage.height / 2;
    const viewportH = window.innerHeight || stage.height * 2;
    const roomAbove = midY - 12;
    const roomBelow = viewportH - midY - 12;
    const roomRight = stage.width / 2 + view.bleed / 2 - 16;
    const roomCanvas = view.height / 2 - 6;
    maxRadius = Math.max(120, Math.min(roomAbove, roomBelow, roomRight, roomCanvas));
    fitDistance = distanceForRadius(maxRadius);

    view.maxRadius = maxRadius;

    // 让轨道控制器与镜头阶梯共用同一组上下限，避免滚轮/双指越界
    controls.minDistance = detailFloor();
    controls.maxDistance = farthestDistance();

    if (camera.position.length() < detailFloor()) {
      camera.position.setLength(detailFloor());
      controls.update();
    }
  }

  function resize() {
    const width = host.clientWidth;
    const height = host.clientHeight;
    if (!width || !height) return;

    view.width = width;
    view.height = height;

    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.fov = THREE.MathUtils.radToDeg(
      2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(BASE_FOV) / 2) / Math.min(1, camera.aspect)),
    );
    camera.updateProjectionMatrix();
    uniforms.uCell.value = 4.6 * renderer.getPixelRatio();

    layoutMetrics();
  }

  new ResizeObserver(resize).observe(host);
  new ResizeObserver(layoutMetrics).observe(stageEl);
  resize();

  // ── 交互：滚轮、双指、轻触 ──
  const pointers = new Map();
  let tap = null;
  let pinchStart = null;

  host.addEventListener('wheel', (event) => {
    event.preventDefault();
    zoom(event.deltaY > 0 ? 1.06 : 0.94);
  }, { passive: false });

  host.addEventListener('pointerdown', (event) => {
    pointers.set(event.pointerId, [event.clientX, event.clientY]);
    lastInteraction = performance.now();
    if (pointers.size === 1) {
      tap = { x: event.clientX, y: event.clientY, moved: false };
      pinchStart = null;
    } else {
      tap = null;
      const pts = [...pointers.values()];
      pinchStart = { dist: Math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]), length: camera.position.length() };
    }
  });

  host.addEventListener('pointermove', (event) => {
    if (!pointers.has(event.pointerId)) return;
    pointers.set(event.pointerId, [event.clientX, event.clientY]);
    if (tap && Math.hypot(event.clientX - tap.x, event.clientY - tap.y) > 8) tap.moved = true;
    if (pinchStart && pointers.size === 2) {
      const pts = [...pointers.values()];
      const dist = Math.hypot(pts[0][0] - pts[1][0], pts[0][1] - pts[1][1]);
      if (dist > 0 && pinchStart.dist > 0) {
        const next = THREE.MathUtils.clamp(
          pinchStart.length * (pinchStart.dist / dist),
          detailFloor(),
          farthestDistance(),
        );
        camera.position.setLength(next);
        controls.update();
      }
    }
  });

  const endPointer = (event) => {
    pointers.delete(event.pointerId);
    if (pointers.size < 2) pinchStart = null;
    if (pointers.size === 0 && tap && !tap.moved) pick(event);
    tap = null;
  };

  host.addEventListener('pointerup', endPointer);
  host.addEventListener('pointercancel', (event) => {
    pointers.delete(event.pointerId);
    pinchStart = null;
    tap = null;
  });

  function pick(event) {
    const rect = host.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    let best = null;
    let bestDist = 30;

    items.forEach((item) => {
      if (!isFront(item.lat, item.lon)) return;
      const p = view.project(item.lat, item.lon);
      if (!p.front) return;
      const dist = Math.hypot(p.x - x, p.y - y);
      if (dist < bestDist) {
        bestDist = dist;
        best = item;
      }
    });

    if (best) onPick(best);
  }

  // ── 每帧 ──
  let lastTime = performance.now();
  renderer.setAnimationLoop((time) => {
    if (paused) return;
    const dt = time - lastTime;
    lastTime = time;

    if (tween) {
      const progress = Math.min(1, (time - tween.start) / TWEEN_MS);
      const eased = progress * progress * (3 - 2 * progress);
      const dir = tween.fromDir.clone().applyQuaternion(new THREE.Quaternion().slerp(tween.rotation, eased));
      const distance = THREE.MathUtils.lerp(tween.fromDistance, tween.toDistance, eased);
      camera.position.copy(dir.multiplyScalar(distance));
      if (progress >= 1) tween = null;
    } else if (idleAllowed && !reduced && time - lastInteraction > IDLE_DELAY) {
      camera.position.applyAxisAngle(UP, 0.00006 * dt);
    }

    controls.update();
    markers.update(reduced ? 0 : time);
    onFrame?.(view, { time, scene, camera });
    renderer.render(scene, camera);
  });

  return {
    view,
    focus,
    zoom,
    reset: () => focus(28, 85, 'overview'),
    setVisible: (list) => markers.setVisible(list),
    setActive: (item) => markers.setActive(item),
    /** 省界显隐与高亮。highlight 传省份名（可带或不带“省/市”后缀） */
    setProvinceOverlay: (options = {}) => {
      if ('show' in options) provinceLayer.show(options.show);
      if ('highlight' in options) provinceLayer.highlight(options.highlight);
    },
    setIdleSpin: (value) => {
      idleAllowed = value;
      lastInteraction = performance.now();
    },
    setPaused: (value) => {
      paused = value;
      lastInteraction = performance.now();
      lastTime = performance.now();
    },
    dispose() {
      renderer.setAnimationLoop(null);
      renderer.dispose();
      geometryDispose(scene);
      host.querySelector('canvas')?.remove();
    },
  };
}

function geometryDispose(scene) {
  scene.traverse((node) => {
    if (node.geometry) node.geometry.dispose();
    if (node.material) {
      const materials = Array.isArray(node.material) ? node.material : [node.material];
      materials.forEach((m) => m.dispose());
    }
  });
}

/** 把 GeoJSON 多边形里任意层级的 ring 摊平出来 */
function collectRings(coords, out) {
  if (!Array.isArray(coords) || !coords.length) return;
  if (typeof coords[0][0] === 'number') {
    out.push(coords);
    return;
  }
  coords.forEach((child) => collectRings(child, out));
}

/** “山西省”“内蒙古自治区”“北京市”统一成短名，便于和 data.json 对齐 */
export function normalizeProvince(name) {
  if (!name) return '';
  return String(name).replace(/(壮族|回族|维吾尔|特别行政区|自治区|省|市)/g, '');
}

/**
 * 省级界线的球面线框。
 * 底图一条线（所有省），高亮一条线（当前省），两个 draw call。
 */
async function createProvinceLayer() {
  const group = new THREE.Group();
  group.visible = false;

  const baseMat = new THREE.LineBasicMaterial({
    color: 0x3b2f22, transparent: true, opacity: 0.22, depthWrite: false,
  });
  const hiMat = new THREE.LineBasicMaterial({
    color: 0xb4432a, transparent: true, opacity: 1, depthWrite: false,
  });

  let data = null;
  try {
    const res = await fetch('./assets/data/china-provinces.json');
    if (res.ok) data = await res.json();
  } catch (error) {
    console.warn('省界数据未载入，主场景不受影响', error);
  }

  const features = data?.features || [];
  const all = [];
  features.forEach((feature) => {
    const rings = [];
    collectRings(feature.geometry?.coordinates, rings);
    const buf = [];
    rings.forEach((ring) => {
      for (let i = 0; i < ring.length - 1; i += 1) {
        const a = sphPoint(ring[i][1], ring[i][0], PROVINCE_RADIUS);
        const b = sphPoint(ring[i + 1][1], ring[i + 1][0], PROVINCE_RADIUS);
        buf.push(a.x, a.y, a.z, b.x, b.y, b.z);
      }
    });
    feature._buf = buf;
    all.push(...buf);
  });

  const baseGeom = new THREE.BufferGeometry();
  baseGeom.setAttribute('position', new THREE.Float32BufferAttribute(all, 3));
  const base = new THREE.LineSegments(baseGeom, baseMat);
  base.frustumCulled = false;
  group.add(base);

  const hiGeom = new THREE.BufferGeometry();
  const hi = new THREE.LineSegments(hiGeom, hiMat);
  hi.frustumCulled = false;
  group.add(hi);

  // 高亮省份的面填充：只看线不容易认出是哪个省，填一层薄色就清楚了
  const fillGeom = new THREE.BufferGeometry();
  const fillMat = new THREE.MeshBasicMaterial({
    color: 0x9c3a22, transparent: true, opacity: 0.26,
    depthWrite: false, side: THREE.DoubleSide,
  });
  const fill = new THREE.Mesh(fillGeom, fillMat);
  fill.frustumCulled = false;
  group.add(fill);

  function buildFill(feature) {
    const out = [];
    if (!feature) return out;
    const rings = [];
    collectRings(feature.geometry?.coordinates, rings);
    rings.forEach((ring) => {
      if (ring.length < 4) return;
      const flat = ring.map(([lon, lat]) => new THREE.Vector2(lon, lat));
      let faces = [];
      try {
        faces = THREE.ShapeUtils.triangulateShape(flat, []);
      } catch (error) {
        return;
      }
      const verts = ring.map(([lon, lat]) => sphPoint(lat, lon, PROVINCE_RADIUS - 0.0015));
      faces.forEach((face) => {
        face.forEach((index) => {
          const v = verts[index];
          if (v) out.push(v.x, v.y, v.z);
        });
      });
    });
    return out;
  }

  function highlight(name) {
    const key = normalizeProvince(name);
    const feature = key ? features.find((f) => normalizeProvince(f.name) === key) : null;
    const buf = feature?._buf || [];
    hiGeom.setAttribute('position', new THREE.Float32BufferAttribute(buf, 3));
    hiGeom.computeBoundingSphere();

    const filled = buildFill(feature);
    fillGeom.setAttribute('position', new THREE.Float32BufferAttribute(filled, 3));
    fillGeom.computeBoundingSphere();
    fill.visible = filled.length > 0;
  }

  return {
    object: group,
    show(value) { group.visible = !!value; },
    highlight,
  };
}
