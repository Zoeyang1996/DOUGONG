import * as THREE from 'three';

// 小拱：由栌斗、层叠拱臂与方榫组成的真实三维角色。
// 全部几何与木纹在本机生成，不依赖远程模型或图片。
export function createCharacter(host) {
  const canvas = document.createElement('canvas');
  canvas.setAttribute('aria-hidden', 'true');
  host.append(canvas);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.6));
  renderer.setSize(112, 140);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(34, 112 / 140, .1, 20);
  camera.position.set(0, 1.25, 4.8); camera.lookAt(0, .94, 0);
  scene.add(new THREE.HemisphereLight(0xfff1da, 0x5a3c26, 2.6));
  const key = new THREE.DirectionalLight(0xffedcf, 3.5); key.position.set(-3, 5, 4); scene.add(key);
  const rim = new THREE.DirectionalLight(0xffffff, 1.8); rim.position.set(4, 3, -2); scene.add(rim);

  const texCanvas = document.createElement('canvas'); texCanvas.width = texCanvas.height = 256;
  const ctx = texCanvas.getContext('2d'); ctx.fillStyle = '#bc8952'; ctx.fillRect(0, 0, 256, 256);
  let seed = 713;
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  for (let i = 0; i < 125; i++) {
    const y = random() * 256; ctx.strokeStyle = `rgba(83,43,19,${.025 + random() * .13})`;
    ctx.lineWidth = .4 + random() * 1.5; ctx.beginPath(); ctx.moveTo(0, y);
    ctx.bezierCurveTo(80, y + random() * 10, 185, y - random() * 10, 256, y); ctx.stroke();
  }
  const grain = new THREE.CanvasTexture(texCanvas); grain.colorSpace = THREE.SRGBColorSpace;
  const wood = new THREE.MeshStandardMaterial({ map: grain, roughness: .62, color: 0xe6ba80 });
  const dark = new THREE.MeshStandardMaterial({ map: grain, roughness: .75, color: 0x83522e });
  const red = new THREE.MeshStandardMaterial({ color: 0xa3402c, roughness: .62 });
  const white = new THREE.MeshStandardMaterial({ color: 0xfff2d4, roughness: .38 });
  const black = new THREE.MeshStandardMaterial({ color: 0x241c14, roughness: .15 });
  const shine = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const root = new THREE.Group(); scene.add(root);
  function mesh(geometry, material, x, y, z, parent = root) {
    const item = new THREE.Mesh(geometry, material); item.position.set(x, y, z); parent.add(item); return item;
  }
  function box(w, h, d, x, y, z, mat = wood, parent = root) {
    const geo = new THREE.BoxGeometry(w, h, d);
    return mesh(geo, mat, x, y, z, parent);
  }
  function ball(rx, ry, rz, x, y, z, mat, parent = root) {
    const item = mesh(new THREE.SphereGeometry(1, 24, 16), mat, x, y, z, parent); item.scale.set(rx, ry, rz); return item;
  }
  function line(points, radius, mat, parent = root) {
    return mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points.map(p => new THREE.Vector3(...p))), 28, radius, 8, false), mat, 0, 0, 0, parent);
  }
  // 柱足、层叠铺作身体与交叉拱肩。
  box(.26, .19, .35, -.22, .19, .02, dark); box(.26, .19, .35, .22, .19, .02, dark);
  box(.42, .2, .35, 0, .4, 0); box(.64, .15, .4, 0, .56, 0, dark);
  box(.74, .14, .42, 0, .72, 0); box(.86, .12, .46, 0, .86, 0, dark);
  box(.42, .13, .39, 0, .99, 0);
  const arms = [];
  for (const side of [-1, 1]) {
    const arm = new THREE.Group(); arm.position.set(side * .4, .85, 0); root.add(arm); arms.push(arm);
    const shape = new THREE.Shape(); shape.moveTo(0, .08); shape.lineTo(side * .35, .08);
    shape.quadraticCurveTo(side * .48, .1, side * .49, .28);
    shape.lineTo(side * .61, .27); shape.quadraticCurveTo(side * .6, -.09, side * .34, -.13);
    shape.lineTo(0, -.13); shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, { depth: .21, bevelEnabled: true, bevelSegments: 2, steps: 1, bevelSize: .018, bevelThickness: .018 });
    mesh(geo, wood, 0, 0, -.1, arm);
    box(.22, .2, .25, side * .55, .23, .015, dark, arm);
    box(.1, .12, .12, side * .55, .36, .015, wood, arm);
  }
  const head = new THREE.Group(); head.position.y = 1.39; root.add(head);
  mesh(new THREE.CylinderGeometry(.51, .37, .55, 64, 1, true), wood, 0, 0, 0, head);
  const rimTop = mesh(new THREE.RingGeometry(.38, .51, 64), wood, 0, .275, 0, head); rimTop.rotation.x = -Math.PI / 2;
  mesh(new THREE.CylinderGeometry(.38, .32, .2, 64, 1, true), dark, 0, .17, 0, head).material.side = THREE.DoubleSide;
  mesh(new THREE.CylinderGeometry(.32, .32, .03, 64), dark, 0, .075, 0, head);
  mesh(new THREE.CylinderGeometry(.508, .495, .048, 64, 1, true), red, 0, .23, 0, head);
  mesh(new THREE.CylinderGeometry(.37, .34, .07, 48), dark, 0, -.28, 0, head);
  line([[.06,.2,-.03],[.08,.44,-.03],[.22,.53,-.03],[.27,.43,-.03],[.19,.4,-.03]], .045, wood, head);
  const eyes = [];
  for (const side of [-1, 1]) {
    const eye = new THREE.Group(); eye.position.set(side * .205, .015, .435); head.add(eye); eyes.push(eye);
    ball(.127,.15,.055,0,0,0,white,eye); ball(.094,.123,.049,side * -.006,0,.041,black,eye);
    ball(.027,.037,.015,-.029,.044,.085,shine,eye); ball(.012,.015,.01,.03,-.04,.085,shine,eye);
    ball(.08,.038,.015,side * .34,-.125,.335,red,head);
  }
  line([[-.09,-.13,.45],[0,-.18,.46],[.09,-.13,.45]], .014, dark, head);
  root.rotation.y = -.16;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let active = false, last = 0, animation;
  function frame(time) {
    animation = requestAnimationFrame(frame);
    if (time - last < 32 || document.hidden) return; last = time;
    if (!reduced) {
      root.position.y = Math.sin(time * .0018) * .035;
      root.rotation.y = -.16 + Math.sin(time * .0006) * .16;
      head.rotation.z = active ? Math.sin(time * .002) * .055 : 0;
      arms[1].rotation.z = active ? .2 + Math.sin(time * .008) * .22 : .02;
      const blink = time % 5200 > 5020 ? .12 : 1; eyes.forEach(eye => eye.scale.y = blink);
    }
    renderer.render(scene, camera);
  }
  frame(0);
  host.dataset.character = 'three-dimensional';
  return { setActive(value) { active = value; }, destroy() { cancelAnimationFrame(animation); renderer.dispose(); } };
}
