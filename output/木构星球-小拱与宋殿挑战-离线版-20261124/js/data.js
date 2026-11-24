/**
 * 数据加载、筛选与省级统计。data.json 为本幕独立资料，未改动其他幕共用的数据。
 */

let cache = null;

export async function loadBuildings() {
  if (cache) return cache;
  const res = await fetch('./data.json');
  if (!res.ok) throw new Error('资料载入失败');
  cache = await res.json();
  return cache;
}

export function filterBuildings(all, { country, era, province }) {
  return all.filter((d) => {
    if (country && d.region !== country) return false;
    if (country === '中国' && era && era !== '全部' && d.era !== era) return false;
    if (province && d.province !== province) return false;
    return true;
  });
}

/** 省名去后缀，只用于显示：山西省 → 山西，北京市 → 北京 */
export function shortProvince(name = '') {
  return name.replace(/(维吾尔自治区|壮族自治区|回族自治区|自治区|省|市)$/, '');
}

/** 省级收录统计，按数目降序；同数按名称排，避免每次刷新顺序跳动 */
export function provinceCounts(items) {
  const tally = new Map();
  items.forEach((item) => {
    if (!item.province) return;
    tally.set(item.province, (tally.get(item.province) || 0) + 1);
  });

  return [...tally.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-Hans-CN'));
}

/** 某省收录条目的年代跨度，按数据实际出现顺序 */
export function eraSpan(items) {
  const order = ['唐', '五代', '辽', '宋', '金', '元', '明清'];
  const present = new Set(items.map((item) => item.era));
  return order.filter((era) => present.has(era));
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
