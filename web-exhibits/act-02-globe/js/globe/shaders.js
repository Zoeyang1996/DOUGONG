/**
 * 地球表面着色器：屏幕空间半调网点 + 程序化山势 + 烘入的经纬网。
 * 采用印刷语汇而非写实地表，与整页的版画气质保持一致。
 */

export const EARTH_VERTEX = /* glsl */ `
  varying vec2 vUv;
  varying vec3 vObjNormal;
  varying vec3 vViewNormal;

  void main() {
    vUv = uv;
    vObjNormal = normalize(position);
    vViewNormal = normalize(normalMatrix * normal);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

export const EARTH_FRAGMENT = /* glsl */ `
  precision highp float;

  varying vec2 vUv;
  varying vec3 vObjNormal;
  varying vec3 vViewNormal;

  uniform sampler2D uMap;
  uniform vec3 uInk;
  uniform vec3 uSepia;
  uniform vec3 uBaseHi;
  uniform vec3 uBaseLo;
  uniform vec3 uSea;
  uniform float uCell;
  uniform float uReveal;

  // ── 程序化噪声：为大陆内部制造山势与肌理 ──
  float hash(vec3 p) {
    p = fract(p * 0.3183099 + vec3(0.71, 0.113, 0.419));
    p *= 17.0;
    return fract(p.x * p.y * p.z * (p.x + p.y + p.z));
  }

  float noise(vec3 x) {
    vec3 i = floor(x);
    vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(mix(hash(i), hash(i + vec3(1.0, 0.0, 0.0)), f.x),
          mix(hash(i + vec3(0.0, 1.0, 0.0)), hash(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),
      mix(mix(hash(i + vec3(0.0, 0.0, 1.0)), hash(i + vec3(1.0, 0.0, 1.0)), f.x),
          mix(hash(i + vec3(0.0, 1.0, 1.0)), hash(i + vec3(1.0, 1.0, 1.0)), f.x), f.y),
      f.z);
  }

  float fbm(vec3 p) {
    float sum = 0.0;
    float amp = 0.5;
    for (int i = 0; i < 3; i++) {
      sum += amp * noise(p);
      p *= 2.03;
      amp *= 0.5;
    }
    return sum;
  }

  float ridged(vec3 p) {
    float sum = 0.0;
    float amp = 0.55;
    for (int i = 0; i < 3; i++) {
      float n = 1.0 - abs(noise(p) * 2.0 - 1.0);
      sum += amp * n * n;
      p *= 2.17;
      amp *= 0.5;
    }
    return sum;
  }

  void main() {
    vec3 tex = texture2D(uMap, vUv).rgb;
    float land = smoothstep(0.32, 0.68, tex.r);
    float interior = tex.g;
    float graticule = tex.b;

    // 山势：大尺度明暗 + 分形脊线，低地疏点、山脊密点
    float belt = smoothstep(0.04, 0.55, interior);
    float broad = fbm(vObjNormal * 2.4 + 11.0);
    float ridge = ridged(vObjNormal * 7.0 + 4.0);
    float relief = clamp(belt * (0.16 + 1.05 * broad) * (0.55 + 0.85 * ridge), 0.0, 1.0);
    relief = pow(relief, 1.35);

    // 光：自左上方来，塑造体积
    vec3 lightDir = normalize(vec3(-0.44, 0.58, 0.69));
    float lambert = max(dot(vViewNormal, lightDir), 0.0);
    float facing = max(dot(vViewNormal, vec3(0.0, 0.0, 1.0)), 0.0);
    float shade = mix(0.88, 1.0, pow(lambert, 1.15)) * mix(0.80, 1.0, smoothstep(0.0, 0.30, facing));

    // 陆地掩膜取硬阈值，确保海面彻底留白；柔边只用于海岸墨线
    float landSolid = smoothstep(0.46, 0.56, tex.r);

    // 网点覆盖率：整幅保留一层细点，作为印刷肌理；陆地略密
    float cov = (0.05 + 0.09 * relief + 0.05 * landSolid) * shade;
    // 球缘处网点收干净，让轮廓由细线而非模糊点阵定义
    cov *= smoothstep(0.002, 0.035, facing);

    // 屏幕空间半调
    // 网点屏旋转 45°：印刷制版的老规矩，可消除"格子布"观感
    mat2 screenAngle = mat2(0.7071, -0.7071, 0.7071, 0.7071);
    vec2 cellUv = (screenAngle * gl_FragCoord.xy) / uCell;
    vec2 cellId = floor(cellUv);
    vec2 g = fract(cellUv) - 0.5;
    // 轻微抖动网点中心，避免出现呆板的正方格
    vec2 jitter = (vec2(hash(vec3(cellId, 1.7)), hash(vec3(cellId, 9.3))) - 0.5) * 0.30;
    float dist = length(g - jitter);
    float radius = 0.50 * sqrt(clamp(cov, 0.0, 1.0));
    float aa = fwidth(dist) * 0.9 + 0.0015;
    float dotMask = 1.0 - smoothstep(radius - aa, radius + aa, dist);
    // 覆盖率为零处不得留点：否则抗锯齿带会在每格中央留一枚微点，整球成了网
    dotMask *= smoothstep(0.006, 0.03, cov);

    // 海岸线：在陆地掩膜的零点处收一道墨线
    float coastWidth = fwidth(tex.r) * 1.15 + 0.0035;
    float coast = (1.0 - smoothstep(0.0, coastWidth, abs(tex.r - 0.5))) * 0.85;

    // 球缘：勾出一道极细的轮廓
    float edge = 1.0 - smoothstep(0.0, 0.03, facing);

    // 底色：受光的暖黄，边缘转深
    vec3 base = mix(uBaseHi, uBaseLo, smoothstep(0.0, 1.0, 1.0 - facing));
    base *= mix(0.975, 1.02, lambert);

    vec3 col = base;
    // 陆地网点用暖褐，与纸同族；海岸与轮廓仍用墨
    // 海面略压一层暖灰：与陆地网点拉开层次，也让「留白」有海的意思
    col = mix(col, uSea, (1.0 - landSolid) * 0.18);
    col = mix(col, uSepia, landSolid * 0.30 * (0.4 + shade));
    col = mix(col, uInk, graticule * 0.016 * (0.4 + shade));
    col = mix(col, uSepia, clamp(dotMask * 0.42, 0.0, 1.0));
    col = mix(col, uInk, coast * (0.42 + 0.36 * shade));
    col = mix(col, uInk, edge * 0.62);

    gl_FragColor = vec4(col, uReveal);
  }
`;
