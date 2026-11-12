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
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  controls.addEventListener('start', () => {
    tween = null;
    lastInteraction = performance.now();
  });

  function focus(lat, lon, distance, { instant = false } = {}) {
    const targetDir = sphPoint(lat, lon, 1);
    if (instant || reduced) {
      camera.position.copy(targetDir.multiplyScalar(distance));
      controls.update();
      tween = null;
      return;
    }
    tween = {
      fromDir: camera.position.clone().normalize(),
      toDir: targetDir,
      rotation: new THREE.Quaternion().setFromUnitVectors(camera.position.clone().normalize(), targetDir),
      fromDistance: camera.position.length(),
      toDistance: distance,
      start: performance.now(),
    };
  }

  function zoom(factor) {
    tween = null;
    lastInteraction = performance.now();
    const next = THREE.MathUtils.clamp(camera.position.length() * factor, MIN_DIST, MAX_DIST);
    camera.position.setLength(next);
    controls.update();
  }

  // ── 尺寸与焦距 ──
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
  }

  new ResizeObserver(resize).observe(host);
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
        const next = THREE.MathUtils.clamp(pinchStart.length * (pinchStart.dist / dist), MIN_DIST, MAX_DIST);
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
    let bestDist = 26;

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
    reset: () => focus(28, 85, 7.4),
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
