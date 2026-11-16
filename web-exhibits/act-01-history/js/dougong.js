/* 木构之间 · 一朵斗拱
   载入保国寺柱头铺作草模，按构件大类分色隔离 / 拆解 / 点选识别
   ------------------------------------------------------------------ */

import * as THREE from "three";
import { GLTFLoader } from "../../shared/vendor/GLTFLoader.js";

const MODEL_URL = "../shared/models/baoguosi-bracket.glb";

export const CATEGORIES = [
  { key: "all", label: "整朵" },
  { key: "dou", label: "斗" },
  { key: "gong", label: "拱" },
  { key: "ang", label: "昂" },
  { key: "qiao", label: "翘" },
  { key: "shuatou", label: "耍头" },
  { key: "fang", label: "枋" },
];

/* 统一的木色：让六个大类在三维里一眼可分 */
const PALETTE = {
  dou: 0xdcbf8c,
  gong: 0xc59a63,
  ang: 0x8d6741,
  shuatou: 0xb5874f,
  fang: 0xa8865c,
  context: 0x9c8f7a,
};

const CATEGORY_NOTE = {
  qiao: "宋式称华栱，清式称翘：同一件木头，沿进深方向出跳。",
};

/* 构件名：按模型里的英文命名还原中文 */
const NAME_CN = [
  [/^dou_ludou/, "栌斗", "dou"],
  [/^dou_jiaohu/, "交互斗", "dou"],
  [/^dou_sandou/, "散斗", "dou"],
  [/^dou_ang_head/, "昂头斗", "dou"],
  [/^gong_huagong/, "华栱", "gong"],
  [/^gong_nidaogong/, "泥道栱", "gong"],
  [/^gong_guazigong/, "瓜子栱", "gong"],
  [/^gong_mangong/, "慢栱", "gong"],
  [/^gong_linggong/, "令栱", "gong"],
  [/^ang_xiaang/, "下昂", "ang"],
  [/shuatou/, "耍头", "shuatou"],
  [/^fang_context/, "柱头枋", "fang"],
  [/^tuan_context/, "梁栿", "context"],
  [/^context_gualeng_column/, "瓜棱柱", "context"],
];

function classify(name) {
  for (const [re, cn, cat] of NAME_CN) {
    if (re.test(name)) return { cn, cat };
  }
  return { cn: "构件", cat: "context" };
}

function matches(category, meshCat, meshName) {
  if (!category || category === "all") return true;
  if (category === "qiao") return /^gong_huagong/.test(meshName);
  return meshCat === category;
}

let gltfPromise = null;

function loadGltf() {
  if (!gltfPromise) {
    gltfPromise = new GLTFLoader().loadAsync(MODEL_URL);
  }
  return gltfPromise;
}

export async function createBracket({ onReady } = {}) {
  const gltf = await loadGltf();
  const root = gltf.scene;

  const group = new THREE.Group();
  const pivot = new THREE.Group();
  pivot.add(root);
  pivot.rotation.y = -0.42;
  group.add(pivot);

  const meshes = [];
  root.traverse((obj) => {
    if (!obj.isMesh) return;
    const { cn, cat } = classify(obj.name);
    obj.material = new THREE.MeshStandardMaterial({
      color: PALETTE[cat] ?? PALETTE.context,
      roughness: 0.76,
      metalness: 0.02,
    });
    const home = obj.position.clone();
    meshes.push({ mesh: obj, cn, cat, home });
    obj.userData.cn = cn;
    obj.userData.cat = cat;
  });

  // 居中并缩放到统一视野
  const box = new THREE.Box3().setFromObject(root);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  root.position.sub(center);
  const scale = 3.1 / Math.max(size.x, size.y, size.z);
  root.scale.setScalar(scale);

  // 重新取相对位置，供拆解使用（缩放后再取一次基准）
  const center2 = new THREE.Vector3();
  root.getWorldPosition(center2);

  let currentCategory = "all";

  const applyCategory = (category) => {
    currentCategory = category;
    const isolating = category && category !== "all";
    meshes.forEach(({ mesh, cat }) => {
      const on = matches(category, cat, mesh.name);
      const hideContext = isolating && cat === "context";
      mesh.visible = !hideContext || category === "context";
      mesh.material.transparent = isolating && !on;
      mesh.material.opacity = isolating && !on ? 0.17 : 1;
      mesh.material.depthWrite = !(isolating && !on);
      mesh.material.emissive = new THREE.Color(isolating && on ? 0x4a1d12 : 0x000000);
      mesh.material.emissiveIntensity = isolating && on ? 0.55 : 0;
      mesh.material.needsUpdate = true;
    });
  };

  const setExplode = (t) => {
    const amount = Math.max(0, Math.min(1, t));
    meshes.forEach(({ mesh, home, cat }) => {
      if (cat === "context") return;
      const dir = home.clone();
      if (dir.lengthSq() < 1e-6) dir.set(0, 0.2, 0);
      dir.normalize();
      const lift = cat === "dou" ? 0.55 : cat === "ang" ? 0.9 : 0.7;
      mesh.position.copy(home).addScaledVector(dir, amount * lift);
    });
  };

  const highlightMesh = (mesh) => {
    meshes.forEach((item) => {
      item.mesh.material.emissive = new THREE.Color(0x000000);
      item.mesh.material.emissiveIntensity = 0;
    });
    if (mesh) {
      mesh.material.emissive = new THREE.Color(0x8f2f1f);
      mesh.material.emissiveIntensity = 0.75;
    }
  };

  applyCategory("all");
  if (onReady) onReady();

  return {
    group,
    meshes: meshes.map((m) => m.mesh),
    setCategory: applyCategory,
    getCategory: () => currentCategory,
    setExplode,
    highlightMesh,
    categoryNote: (key) => CATEGORY_NOTE[key] || "",
  };
}

export { classify };
