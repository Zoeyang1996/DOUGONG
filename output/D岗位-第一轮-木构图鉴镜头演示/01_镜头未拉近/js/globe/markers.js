import * as THREE from 'three';

/**
 * 建筑点位：朱点 + 细环 + 呼吸涟漪。
 * 用 Points 单次绘制，背面点由球体深度与朝向共同遮挡。
 */

const VERTEX = /* glsl */ `
  attribute float aShow;
  attribute float aActive;
  attribute float aPhase;
  uniform float uTime;
  uniform float uPixelRatio;
  uniform float uSize;
  varying float vShow;
  varying float vActive;
  varying float vFacing;
  varying float vPhase;

  void main() {
    vec3 n = normalize(position);
    vec4 world = modelMatrix * vec4(position, 1.0);
    vec3 viewDir = normalize(cameraPosition - world.xyz);
    vFacing = dot(n, viewDir);
    vShow = aShow;
    vActive = aActive;
    vPhase = aPhase;

    vec4 mv = viewMatrix * world;
    float scale = 1.0 + aActive * 0.5;
    gl_PointSize = uSize * uPixelRatio * scale * min(1.5, 5.0 / max(1.2, -mv.z));
    gl_Position = projectionMatrix * mv;
  }
`;

const FRAGMENT = /* glsl */ `
  precision highp float;
  uniform vec3 uColor;
  uniform vec3 uHalo;
  uniform float uTime;
  varying float vShow;
  varying float vActive;
  varying float vFacing;
  varying float vPhase;

  void main() {
    if (vShow < 0.5 || vFacing < 0.12) discard;

    vec2 p = (gl_PointCoord - 0.5) * 2.0;
    float d = length(p);

    float coreR = mix(0.13, 0.19, vActive);
    float core = 1.0 - smoothstep(coreR, coreR + 0.05, d);
    float halo = (1.0 - smoothstep(0.20, 0.30, d)) * 0.85;
    float ring = smoothstep(0.30, 0.34, d) * (1.0 - smoothstep(0.42, 0.46, d));

    float t = fract(uTime * 0.00016 + vPhase);
    float pulseR = 0.22 + t * 0.74;
    float pulse = (1.0 - smoothstep(0.0, 0.045, abs(d - pulseR))) * (1.0 - t);
    pulse *= mix(0.45, 1.0, vActive);

    float alpha = max(max(core, halo * 0.85), max(ring * mix(0.38, 0.9, vActive), pulse * mix(0.3, 0.85, vActive)));
    if (alpha <= 0.01) discard;

    vec3 col = mix(uHalo, uColor, max(core, ring * 0.9));
    gl_FragColor = vec4(col, alpha);
  }
`;

export function createMarkers({ items, positions, pixelRatio }) {
  const count = items.length;
  const show = new Float32Array(count);
  const active = new Float32Array(count);
  const phase = new Float32Array(count).map((_, i) => (i * 0.37) % 1);

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('aShow', new THREE.BufferAttribute(show, 1));
  geometry.setAttribute('aActive', new THREE.BufferAttribute(active, 1));
  geometry.setAttribute('aPhase', new THREE.BufferAttribute(phase, 1));

  const material = new THREE.ShaderMaterial({
    vertexShader: VERTEX,
    fragmentShader: FRAGMENT,
    uniforms: {
      uTime: { value: 0 },
      uPixelRatio: { value: pixelRatio },
      uSize: { value: 14 },
      uColor: { value: new THREE.Color('#bf3a1e') },
      uHalo: { value: new THREE.Color('#fdf0d8') },
    },
    transparent: true,
    depthWrite: false,
    depthTest: true,
  });

  const object3D = new THREE.Points(geometry, material);
  object3D.frustumCulled = false;

  return {
    object3D,
    setVisible(visibleItems) {
      const wanted = new Set(visibleItems.map((item) => item.id));
      items.forEach((item, i) => {
        show[i] = wanted.has(item.id) ? 1 : 0;
      });
      geometry.attributes.aShow.needsUpdate = true;
    },
    setActive(item) {
      items.forEach((_, i) => {
        active[i] = item && items[i].id === item.id ? 1 : 0;
      });
      geometry.attributes.aActive.needsUpdate = true;
    },
    setPixelRatio(ratio) {
      material.uniforms.uPixelRatio.value = ratio;
    },
    update(time) {
      material.uniforms.uTime.value = time;
    },
  };
}
