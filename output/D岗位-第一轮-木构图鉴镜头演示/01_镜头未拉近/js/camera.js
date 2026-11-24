/** 镜头参数读取与飞行进度。现场只修改根目录 camera-config.js。 */
export function cameraSettings() {
  const config = window.ATLAS_CAMERA || {};
  const number = (key, fallback, low, high) => {
    const value = Number(config[key]);
    return Number.isFinite(value) ? Math.max(low, Math.min(high, value)) : fallback;
  };
  return { detailZoom: number('DETAIL_ZOOM', 1.05, 0.9, 6), flightMs: number('FLIGHT_MS', 900, 400, 6000) };
}
export function flightProgress(progress) {
  const smooth = (t) => { const x = Math.max(0, Math.min(1, t)); return x * x * (3 - 2 * x); };
  // 前段先对准建筑所在方向，后段沿球面法向贴近，形成连续穿梭感。
  return { direction: smooth(progress / 0.72), distance: smooth(progress) };
}
export function flightDistance(from, to, progress, radius) {
  const a = Math.max(0.02, from - radius);
  const b = Math.max(0.02, to - radius);
  return radius + Math.exp(Math.log(a) + (Math.log(b) - Math.log(a)) * progress);
}
