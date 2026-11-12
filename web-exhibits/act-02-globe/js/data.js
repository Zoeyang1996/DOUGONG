/**
 * 数据加载与筛选。data.json 为本幕独立资料，未改动其他幕共用的数据。
 */

let cache = null;

export async function loadBuildings() {
  if (cache) return cache;
  const res = await fetch('./data.json');
  if (!res.ok) throw new Error('资料载入失败');
  cache = await res.json();
  return cache;
}

export function filterBuildings(all, { country, era }) {
  return all.filter((d) => {
    if (country && d.region !== country) return false;
    if (country === '中国' && era && era !== '全部' && d.era !== era) return false;
    return true;
  });
}

/** 地表标签优先展示的代表性条目，避免同代点位挤在一处。 */
const FEATURED_IDS = [
  'tang-02',
  'wudai-05',
  'liao-03',
  'liao-04',
  'song-01',
  'song-04',
  'yuan-01',
  'mingqing-01',
];

export function featuredPoints(points, limit) {
  if (points.length <= limit) return points.slice(0, limit);
  const picked = FEATURED_IDS.map((prefix) => points.find((d) => d.id.startsWith(prefix))).filter(Boolean);
  const rest = points.filter((d) => !picked.includes(d));
  return [...picked, ...rest].slice(0, limit);
}

export function centroid(points) {
  if (!points.length) return null;
  const lat = points.reduce((sum, d) => sum + d.lat, 0) / points.length;
  const lon = points.reduce((sum, d) => sum + d.lon, 0) / points.length;
  return [lat, lon];
}
