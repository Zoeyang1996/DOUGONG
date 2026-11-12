import * as THREE from 'three';

/**
 * 把陆地轮廓、内陆权重与经纬网烘成一张等距圆柱投影的数据贴图：
 *   R = 陆地覆盖（抗锯齿）
 *   G = 内陆权重（离海岸越远越高，用作山势起伏的基础）
 *   B = 经纬网
 * 着色器据此绘制半调网点，无需任何外部影像。
 */

const CHANNELS = { land: 0, interior: 1, grat: 2 };

function pickSize() {
  const compact = Math.min(window.innerWidth, window.innerHeight) < 760;
  return compact ? { width: 2048, height: 1024 } : { width: 4096, height: 2048 };
}

export async function buildEarthTexture(landGeoJson) {
  const { width: W, height: H } = pickSize();

  const landCanvas = makeCanvas(W, H);
  const landCtx = landCanvas.getContext('2d');
  landCtx.fillStyle = '#000';
  landCtx.fillRect(0, 0, W, H);
  landCtx.fillStyle = '#fff';
  landCtx.strokeStyle = '#fff';
  landCtx.lineWidth = Math.max(1, W / 2048);
  landCtx.lineJoin = 'round';

  for (const feature of landGeoJson.features) {
    const polygons =
      feature.geometry.type === 'Polygon' ? [feature.geometry.coordinates] : feature.geometry.coordinates;
    for (const rings of polygons) {
      const path = new Path2D();
      for (const ring of rings) {
        ring.forEach(([lon, lat], i) => {
          const x = ((lon + 180) / 360) * W;
          const y = ((90 - clampLat(lat)) / 180) * H;
          if (i === 0) path.moveTo(x, y);
          else path.lineTo(x, y);
        });
        path.closePath();
      }
      landCtx.fill(path, 'evenodd');
      landCtx.stroke(path);
    }
  }

  const interiorCanvas = buildInterior(landCanvas, W, H);
  const gratCanvas = buildGraticule(W, H);

  const landData = landCtx.getImageData(0, 0, W, H).data;
  const interiorData = interiorCanvas.getContext('2d').getImageData(0, 0, W, H).data;
  const gratData = gratCanvas.getContext('2d').getImageData(0, 0, W, H).data;

  // DataTexture 不做 flipY，因此写入时上下翻转一次：贴图第 0 行对应北极。
  const out = new Uint8Array(W * H * 4);
  for (let y = 0; y < H; y += 1) {
    const srcRow = (H - 1 - y) * W;
    const dstRow = y * W;
    for (let x = 0; x < W; x += 1) {
      const s = (srcRow + x) * 4;
      const d = (dstRow + x) * 4;
      out[d + CHANNELS.land] = landData[s];
      out[d + CHANNELS.interior] = interiorData[s];
      out[d + CHANNELS.grat] = gratData[s];
      out[d + 3] = 255;
    }
  }

  const texture = new THREE.DataTexture(out, W, H, THREE.RGBAFormat, THREE.UnsignedByteType);
  texture.colorSpace = THREE.NoColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.magFilter = THREE.LinearFilter;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.generateMipmaps = true;
  texture.anisotropy = 8;
  texture.needsUpdate = true;
  return texture;
}

/** 多级降采样得到柔和的内陆权重：海岸为 0，大陆腹地接近 1。 */
function buildInterior(landCanvas, W, H) {
  const steps = [
    [Math.round(W / 6), Math.round(H / 6)],
    [Math.round(W / 18), Math.round(H / 18)],
    [Math.round(W / 54), Math.round(H / 54)],
  ];

  let source = landCanvas;
  for (const [w, h] of steps) {
    const small = makeCanvas(Math.max(8, w), Math.max(4, h));
    const ctx = small.getContext('2d');
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(source, 0, 0, small.width, small.height);
    source = small;
  }

  const out = makeCanvas(W, H);
  const ctx = out.getContext('2d');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(source, 0, 0, W, H);
  return out;
}

function buildGraticule(W, H) {
  const canvas = makeCanvas(W, H);
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#000';
  ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = Math.max(1.5, W / 1800);

  for (let lon = -180; lon <= 180; lon += 15) {
    if (lon === 0) continue;
    const x = ((lon + 180) / 360) * W;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, H);
    ctx.stroke();
  }

  for (let lat = -75; lat <= 75; lat += 15) {
    if (lat === 0) continue;
    const y = ((90 - lat) / 180) * H;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }

  ctx.lineWidth = Math.max(2.4, W / 1100);
  ctx.beginPath();
  ctx.moveTo(0, H / 2);
  ctx.lineTo(W, H / 2);
  ctx.moveTo(W / 2, 0);
  ctx.lineTo(W / 2, H);
  ctx.stroke();

  return canvas;
}

function makeCanvas(width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

function clampLat(lat) {
  return Math.max(-89.9, Math.min(89.9, lat));
}
