import * as THREE from 'three';
import { OrbitControls } from '../../../shared/vendor/OrbitControls.js';
import { buildEarthTexture } from './texture.js';
import { EARTH_VERTEX, EARTH_FRAGMENT } from './shaders.js';
import { createMarkers } from './markers.js';

const RADIUS = 2;
const MARKER_RADIUS = 2.008;
const MIN_DIST = 4.6;
const MAX_DIST = 11;
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
  let lastInteraction = performance.now();
  /**
   * 镜头阶梯：以“球在屏幕上不越界的最大半径”为 1。
   * 全球 → 地区 → 朝代 → 省份 / 单座，逐级放大，后两级同时把目标转到画面中心。
   * 省份与单座共用最深一档：整球可见的前提下已到极限，再近就必须让球边出血。
   */
  const LENS = { overview: 0.6, region: 0.86, era: 0.94, province: 1, building: 1 };
  let maxRadius = 240;
  let fitDistance = MIN_DIST;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const tanHalfFov = () => Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
  const distanceForRadius = (r) => (RADIUS * view.height) / (2 * Math.max(1, r) * tanHalfFov());
  const nearestDistance = () => Math.max(MIN_DIST, distanceForRadius(maxRadius));
  const farthestDistance = () => Math.max(nearestDistance() + 0.6, distanceForRadius(maxRadius * 0.34));

  function lensDistance(level) {
    if (typeof level === 'number') return level;
    const ratio = LENS[level] ?? LENS.building;
    return distanceForRadius(maxRadius * ratio);
  }

  controls.addEventListener('start', () => {
    tween = null;
    lastInteraction = performance.now();
  });

  function focus(lat, lon, level = 'building', { instant = false } = {}) {
    const targetDir = sphPoint(lat, lon, 1);
    const toDistance = THREE.MathUtils.clamp(
      lensDistance(level), nearestDistance(), farthestDistance(),
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
      camera.position.length() * factor, nearestDistance(), farthestDistance(),
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
    controls.minDistance = nearestDistance();
    controls.maxDistance = farthestDistance();

    if (camera.position.length() < nearestDistance()) {
      camera.position.setLength(nearestDistance());
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
          nearestDistance(),
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
    setIdleSpin: (value) => {
      idleAllowed = value;
      lastInteraction = performance.now();
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
