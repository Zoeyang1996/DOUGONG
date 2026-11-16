/* 木构之间 · 四种榫卯的程序化模型
   用"截面挤出"建：卯口是带孔的板，榫是同一截面的柱
   合拢方向统一为局部 +Z / +Y，便于滑杆控制
   ------------------------------------------------------------------ */

import * as THREE from "three";

const MAT_BLOCK = new THREE.MeshStandardMaterial({ color: 0xc8a878, roughness: 0.74, metalness: 0.02 });
const MAT_TENON = new THREE.MeshStandardMaterial({ color: 0xb08756, roughness: 0.7, metalness: 0.02 });
const MAT_EDGE = new THREE.LineBasicMaterial({ color: 0x4a3a26, transparent: true, opacity: 0.5 });

function shape(points) {
  const s = new THREE.Shape();
  points.forEach(([x, y], i) => (i === 0 ? s.moveTo(x, y) : s.lineTo(x, y)));
  s.closePath();
  return s;
}

function holeShape(points) {
  const p = new THREE.Path();
  points.forEach(([x, y], i) => (i === 0 ? p.moveTo(x, y) : p.lineTo(x, y)));
  p.closePath();
  return p;
}

function extrude(outer, holes, depth, material) {
  const outerShape = shape(outer);
  holes.forEach((h) => outerShape.holes.push(holeShape(h)));
  const geo = new THREE.ExtrudeGeometry(outerShape, {
    depth,
    bevelEnabled: false,
    curveSegments: 28,
  });
  geo.translate(0, 0, -depth / 2);
  const mesh = new THREE.Mesh(geo, material);
  mesh.add(
    new THREE.LineSegments(new THREE.EdgesGeometry(geo, 24), MAT_EDGE)
  );
  return mesh;
}

function roundedRect(halfW, halfH, radius) {
  const pts = [];
  const steps = 6;
  const corners = [
    [halfW - radius, halfH - radius, 0],
    [-halfW + radius, halfH - radius, Math.PI / 2],
    [-halfW + radius, -halfH + radius, Math.PI],
    [halfW - radius, -halfH + radius, Math.PI * 1.5],
  ];
  corners.forEach(([cx, cy, start]) => {
    for (let i = 0; i <= steps; i += 1) {
      const a = start + (i / steps) * (Math.PI / 2);
      pts.push([cx + Math.cos(a) * radius, cy + Math.sin(a) * radius]);
    }
  });
  return pts;
}

function trapezoid(halfTop, halfBottom, halfH) {
  return [
    [-halfTop, halfH],
    [halfTop, halfH],
    [halfBottom, -halfH],
    [-halfBottom, -halfH],
  ];
}

/* ------------------------------------------------------------ 直榫 */

function straightTenon() {
  const group = new THREE.Group();

  const block = extrude(
    [[-0.85, 0.5], [0.85, 0.5], [0.85, -0.5], [-0.85, -0.5]],
    [[[-0.19, 0.19], [0.19, 0.19], [0.19, -0.19], [-0.19, -0.19]]],
    0.56,
    MAT_BLOCK
  );
  group.add(block);

  const moving = new THREE.Group();
  const tenon = extrude(
    [[-0.17, 0.17], [0.17, 0.17], [0.17, -0.17], [-0.17, -0.17]],
    [],
    1.35,
    MAT_TENON
  );
  tenon.position.z = 0.62;
  moving.add(tenon);

  const shoulder = extrude(
    [[-0.55, 0.5], [0.55, 0.5], [0.55, -0.5], [-0.55, -0.5]],
    [],
    0.26,
    MAT_BLOCK
  );
  shoulder.position.z = 1.42;
  moving.add(shoulder);

  group.add(moving);

  return {
    group,
    moving,
    closed: 0,
    open: 1.28,
    axis: "z",
    hint: "榫头方直，一插到底；侧壁抵抗错动，抗拉抗剪",
  };
}

/* ------------------------------------------------------------ 燕尾榫 */

function dovetail() {
  const group = new THREE.Group();

  // 卯件：上窄下宽的燕尾槽，由两块斜颊与底板围合
  const base = extrude(
    [[-0.85, -0.52], [0.85, -0.52], [0.85, -0.22], [-0.85, -0.22]],
    [],
    0.9,
    MAT_BLOCK
  );
  group.add(base);

  const cheekGeo = new THREE.BoxGeometry(0.16, 0.62, 0.9);
  const leftCheek = new THREE.Mesh(cheekGeo, MAT_BLOCK);
  leftCheek.position.set(-0.46, -0.1, 0);
  leftCheek.rotation.z = -0.19;
  leftCheek.add(new THREE.LineSegments(new THREE.EdgesGeometry(cheekGeo), MAT_EDGE));
  const rightCheek = leftCheek.clone();
  rightCheek.position.x = 0.46;
  rightCheek.rotation.z = 0.19;
  group.add(leftCheek, rightCheek);

  // 榫件：上窄下宽的燕尾头，从上方落入即锁死
  const tailProfile = trapezoid(0.16, 0.34, 0.3);
  const tail = extrude(tailProfile, [], 0.9, MAT_TENON);
  const cap = extrude(
    [[-0.5, 0.3], [0.5, 0.3], [0.5, 0.62], [-0.5, 0.62]],
    [],
    0.35,
    MAT_BLOCK
  );
  cap.position.y = 0.62;

  const moving = new THREE.Group();
  moving.add(tail, cap);
  moving.position.y = 0.1;
  group.add(moving);

  return {
    group,
    moving,
    closed: 0,
    open: 1.15,
    axis: "y",
    hint: "端部梯形，越拉越紧；斜面把拔出的力变成挤压力",
  };
}

/* ------------------------------------------------------------ 企口榫 */

function tongueGroove() {
  const group = new THREE.Group();

  // 固定板：右缘开企口（凹槽）
  const fixed = extrude(
    [[-1.0, 0.34], [0.34, 0.34], [0.34, 0.1], [0.02, 0.1], [0.02, -0.1], [0.34, -0.1], [0.34, -0.34], [-1.0, -0.34]],
    [],
    0.95,
    MAT_BLOCK
  );
  group.add(fixed);

  // 活动板：左缘出凸舌
  const moving = new THREE.Group();
  const plank = extrude(
    [[-0.02, 0.1], [1.0, 0.1], [1.0, -0.1], [-0.02, -0.1]],
    [],
    0.95,
    MAT_BLOCK
  );
  const body = extrude(
    [[0.34, 0.34], [1.5, 0.34], [1.5, -0.34], [0.34, -0.34]],
    [],
    0.95,
    MAT_TENON
  );
  body.position.y = 0;
  moving.add(body, plank);
  moving.position.x = 0.0;
  group.add(moving);

  group.rotation.y = -0.12;

  return {
    group,
    moving,
    closed: 0,
    open: 1.15,
    axis: "x",
    hint: "板边一凸一凹互相嵌合；拼板、防翘、防漏",
  };
}

/* ------------------------------------------------------------ 馒头榫 */

function domeTenon() {
  const group = new THREE.Group();

  // 上：梁底开圆卯
  const beam = extrude(
    [[-0.9, 0.62], [0.9, 0.62], [0.9, 0.1], [-0.9, 0.1]],
    [roundedRect(0.3, 0.1, 0.08)],
    0.95,
    MAT_BLOCK
  );
  group.add(beam);

  // 下：柱头的圆榫
  const moving = new THREE.Group();
  const neck = new THREE.Mesh(
    new THREE.CylinderGeometry(0.17, 0.19, 0.34, 36),
    MAT_TENON
  );
  neck.position.y = -0.18;
  neck.add(new THREE.LineSegments(new THREE.EdgesGeometry(neck.geometry, 40), MAT_EDGE));
  const dome = new THREE.Mesh(new THREE.SphereGeometry(0.18, 28, 18, 0, Math.PI * 2, 0, Math.PI / 2), MAT_TENON);
  dome.position.y = -0.01;
  const column = new THREE.Mesh(
    new THREE.CylinderGeometry(0.42, 0.46, 1.1, 40),
    MAT_BLOCK
  );
  column.position.y = -0.9;
  column.add(new THREE.LineSegments(new THREE.EdgesGeometry(column.geometry, 40), MAT_EDGE));
  moving.add(neck, dome, column);
  moving.position.y = 0;
  group.add(moving);

  return {
    group,
    moving,
    closed: 0,
    open: 0.95,
    axis: "y",
    hint: "圆榫入圆卯，只限位不锁死；柱头因此可以轻微转动",
    allowRock: true,
  };
}

const BUILDERS = {
  zhisun: straightTenon,
  yanwei: dovetail,
  qikou: tongueGroove,
  mantou: domeTenon,
};

export const MORTISE_META = {
  zhisun: { name: "直榫", pinyin: "zhí sǔn", use: "抗拉、抗剪、定位" },
  yanwei: { name: "燕尾榫", pinyin: "yàn wěi sǔn", use: "抗拔，越拉越紧" },
  qikou: { name: "企口榫", pinyin: "qǐ kǒu sǔn", use: "拼板、防翘、防漏" },
  mantou: { name: "馒头榫", pinyin: "mán tou sǔn", use: "限位，允许转动" },
};

export function buildMortise(key) {
  const factory = BUILDERS[key] || straightTenon;
  const model = factory();
  model.setOpenAmount = (t) => {
    const v = model.closed + (model.open - model.closed) * Math.max(0, Math.min(1, t));
    if (model.axis === "z") model.moving.position.z = v;
    if (model.axis === "y") model.moving.position.y = v;
    if (model.axis === "x") model.moving.position.x = -v;
  };
  model.setOpenAmount(0);
  return model;
}
