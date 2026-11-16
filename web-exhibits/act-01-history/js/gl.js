/* 木构之间 · 三维展台
   一个对话框一次只跑一个 WebGL 上下文：打开时创建，关闭时释放
   ------------------------------------------------------------------ */

import * as THREE from "three";
import { OrbitControls } from "../../shared/vendor/OrbitControls.js";

const KEY_LIGHT = 0xffe9c8;
const RIM_LIGHT = 0xbcd6de;
const SKY = 0xfff2dc;
const GROUND = 0x3a3126;

export function createStage(host, { distance = 4.2, target = [0, 0, 0] } = {}) {
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, 1, 0.05, 120);
  camera.position.set(distance * 0.72, distance * 0.5, distance);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  renderer.shadowMap.enabled = false;
  host.append(renderer.domElement);

  scene.add(new THREE.HemisphereLight(SKY, GROUND, 1.5));

  const key = new THREE.DirectionalLight(KEY_LIGHT, 2.6);
  key.position.set(3.4, 5.2, 3.8);
  scene.add(key);

  const fill = new THREE.DirectionalLight(KEY_LIGHT, 0.9);
  fill.position.set(-4, 1.6, 2.4);
  scene.add(fill);

  const rim = new THREE.DirectionalLight(RIM_LIGHT, 1.4);
  rim.position.set(-2.2, 2.6, -5);
  scene.add(rim);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enablePan = false;
  controls.rotateSpeed = 0.82;
  controls.zoomSpeed = 0.7;
  controls.minDistance = distance * 0.45;
  controls.maxDistance = distance * 2.1;
  controls.minPolarAngle = Math.PI * 0.12;
  controls.maxPolarAngle = Math.PI * 0.86;
  controls.target.set(target[0], target[1], target[2]);

  const resize = () => {
    const w = host.clientWidth;
    const h = host.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  };
  const observer = new ResizeObserver(resize);
  observer.observe(host);
  resize();

  const hooks = [];
  renderer.setAnimationLoop((time) => {
    controls.update();
    for (const fn of hooks) fn(time);
    renderer.render(scene, camera);
  });

  return {
    scene,
    camera,
    renderer,
    controls,
    onFrame(fn) {
      hooks.push(fn);
    },
    resetView() {
      camera.position.set(distance * 0.72, distance * 0.5, distance);
      controls.target.set(target[0], target[1], target[2]);
      controls.update();
    },
    dispose() {
      renderer.setAnimationLoop(null);
      observer.disconnect();
      controls.dispose();
      scene.traverse((obj) => {
        if (obj.isMesh) {
          obj.geometry?.dispose();
          const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
          mats.forEach((m) => {
            if (!m) return;
            Object.values(m).forEach((v) => {
              if (v && v.isTexture) v.dispose();
            });
            m.dispose();
          });
        }
      });
      renderer.dispose();
      renderer.domElement.remove();
    },
  };
}

/* 让任意对象框入视野：按外接球尺寸移动相机 */
export function frameObject(camera, controls, object, padding = 1.5) {
  const box = new THREE.Box3().setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const radius = Math.max(size.x, size.y, size.z) * 0.5 || 1;
  const distance = (radius * padding) / Math.tan((camera.fov * Math.PI) / 360);
  controls.target.copy(center);
  const dir = new THREE.Vector3(0.5, 0.31, 1).normalize();
  camera.position.copy(center).addScaledVector(dir, distance);
  camera.near = distance / 60;
  camera.far = distance * 12;
  camera.updateProjectionMatrix();
  controls.minDistance = distance * 0.42;
  controls.maxDistance = distance * 1.9;
  controls.update();
}

/* 木色材质：程序化模型统一用它 */
export function woodMaterial(color = 0xc9a173, roughness = 0.72) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness,
    metalness: 0.02,
    flatShading: false,
  });
}
