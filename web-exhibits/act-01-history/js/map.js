/* 木构之间 · 东亚木构圈地图
   取 shared/data/land.geojson 的海岸线，等距圆柱投影后绘成古地图样式
   ------------------------------------------------------------------ */

const BBOX = { lon0: 100, lon1: 146, lat0: 12, lat1: 46 };
const VIEW = { w: 320, h: 460 };
const LAT_COS = Math.cos((25 * Math.PI) / 180);

const INK = "#3a3026";
const INK_FAINT = "rgba(58,48,38,0.35)";
const VERMILION = "#9e3527";
const LAND = "rgba(196,170,127,0.6)";
const SEA = "rgba(38,69,79,0.1)";
const FONT = 'font-family="Songti SC, STSong, serif"';

let landCache = null;

export async function loadLand() {
  if (landCache) return landCache;
  const res = await fetch("../shared/data/land.geojson");
  landCache = await res.json();
  return landCache;
}

function project(lon, lat) {
  const spanX = (BBOX.lon1 - BBOX.lon0) * LAT_COS;
  const spanY = BBOX.lat1 - BBOX.lat0;
  const k = Math.min(VIEW.w / spanX, VIEW.h / spanY);
  const x = (lon - BBOX.lon0) * LAT_COS * k + (VIEW.w - spanX * k) / 2;
  const y = (BBOX.lat1 - lat) * k + (VIEW.h - spanY * k) / 2;
  return [x, y];
}

function ringPath(ring) {
  let d = "";
  for (let i = 0; i < ring.length; i += 1) {
    const [x, y] = project(ring[i][0], ring[i][1]);
    d += (i === 0 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1);
  }
  return d + "Z";
}

/* 环的外接框：必须整环判交，否则像中国大陆这种首点在视野外的环会被整块丢掉 */
function ringBox(ring) {
  let minLon = 180;
  let maxLon = -180;
  let minLat = 90;
  let maxLat = -90;
  for (const [lon, lat] of ring) {
    if (lon < minLon) minLon = lon;
    if (lon > maxLon) maxLon = lon;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
  }
  return { minLon, maxLon, minLat, maxLat };
}

function landPaths(geo) {
  const out = [];
  const padLon = 6;
  const padLat = 6;
  for (const feature of geo.features) {
    const g = feature.geometry || feature;
    const polys = g.type === "Polygon" ? [g.coordinates] : g.type === "MultiPolygon" ? g.coordinates : [];
    for (const poly of polys) {
      for (const ring of poly) {
        if (ring.length < 3) continue;
        const box = ringBox(ring);
        if (box.maxLon < BBOX.lon0 - padLon || box.minLon > BBOX.lon1 + padLon) continue;
        if (box.maxLat < BBOX.lat0 - padLat || box.minLat > BBOX.lat1 + padLat) continue;
        out.push(ringPath(ring));
      }
    }
  }
  return out;
}

/* 地名节点：经纬度 + 图文 */
export const MAP_NODES = [
  {
    id: "ningbo",
    name: "宁波",
    sub: "保国寺 · 1013",
    lon: 121.55,
    lat: 29.87,
    anchor: "end",
    text: "本书的起点。长江以南最古老、保存最完整的木构之一，外檐七铺作双杪双下昂，第一跳偷心。",
    detail: "16 根柱皆为瓜棱柱，其中四根为四段拼合；栌斗随柱做八瓣，是现存遗构中的孤例。斗拱用材断面高宽比 3:2，与九十年后成书的《营造法式》高度吻合。",
    links: [
      { label: "第二幕 · 木构星图", href: "../act-02-globe/" },
      { label: "构建档案", href: "../../docs/02-内容/02-保国寺-结构与斗拱形制.md" },
    ],
  },
  {
    id: "wutai",
    name: "五台山",
    sub: "佛光寺 · 857",
    lon: 113.39,
    lat: 38.87,
    anchor: "start",
    text: "唐大中十一年建。斗拱几近柱高一半，单栱出挑约两米，屋面出檐三至四米，是理解唐代出檐尺度的基准。",
    detail: "1937 年由梁思成、林徽因等营造学社成员发现，直接打破了「中国境内已无唐代木构」的论断。殿内建筑、彩塑、壁画、题记「四绝」并存。",
    links: [{ label: "第二幕 · 木构星图", href: "../act-02-globe/" }],
  },
  {
    id: "nara",
    name: "奈良",
    sub: "法隆寺 · 唐招提寺",
    lon: 135.8,
    lat: 34.65,
    anchor: "end",
    text: "6—8 世纪，寺院营造把大陆的木作技术整体带入日本。法隆寺创建于 607 年，现存金堂、五重塔为 670 年火灾后重建。",
    detail: "日本斗拱称「組物（kumimono）」，方块与横臂交替叠出，已发展出自己的比例与命名方式。唐招提寺金堂（759，鉴真创建）最接近唐代做法。",
    links: [{ label: "第二幕 · 木构星图", href: "../act-02-globe/" }],
  },
  {
    id: "kamakura",
    name: "镰仓",
    sub: "东大寺南大门 · 大佛样",
    lon: 139.55,
    lat: 35.32,
    anchor: "start",
    dy: -2,
    text: "12 世纪末东大寺重建，南大门采用「大佛样（daibutsuyō）」，由宋元工匠参与，插入大量横木与贯。",
    detail: "「大佛样」与和样、禅宗样并列为日本中世三大样式，是宋元技术东传最直接的一处物证。",
    links: [],
  },
  {
    id: "gyeongju",
    name: "庆州 · 安东",
    sub: "凤停寺极乐殿 · 柱心包",
    lon: 128.72,
    lat: 36.57,
    anchor: "start",
    text: "朝鲜半岛高丽后期从中国南方引入「柱心包（Jusimpo）」，只在柱头置斗拱，不设补间。",
    detail: "凤停寺极乐殿是柱心包现存最重要的实例，斗拱只做柱头一朵，与宋式补间铺作密布的做法形成对比。",
    links: [],
  },
  {
    id: "seoul",
    name: "汉城",
    sub: "景福宫勤政殿 · 多包",
    lon: 126.97,
    lat: 37.58,
    anchor: "end",
    dy: -4,
    text: "朝鲜王朝从中国北方与元代引入「多包（Dapo）」，柱头之间加设补间，斗拱连成一排。",
    detail: "景福宫勤政殿为多包代表。柱心包与多包并列为韩国传统木构的两大样式。",
    links: [],
  },
  {
    id: "shuri",
    name: "首里",
    sub: "琉球 · 首里城",
    lon: 127.72,
    lat: 26.22,
    anchor: "start",
    text: "琉球皇家建筑的檐下托架语汇与东亚大陆相似，但具体源流需个案研究。",
    detail: "本书只作「语汇相似」提示，不主张直接传入关系；首里城现存建筑多为战后复原。",
    links: [],
  },
  {
    id: "hue",
    name: "顺化",
    sub: "越南 · 顺化皇城",
    lon: 107.58,
    lat: 16.47,
    anchor: "start",
    text: "越南皇家建筑同样可见类似檐下托架，做法与闽粤一带的南方体系更接近。",
    detail: "顺化皇城在 19 世纪营建，时间晚于东亚木构圈的形成期，属于同一语汇的后期延续。",
    links: [],
  },
  {
    id: "shanghai",
    name: "上海",
    sub: "2010 世博会中国馆",
    lon: 121.47,
    lat: 31.23,
    anchor: "start",
    dy: 13,
    text: "「东方之冠」高 69 米、总建筑面积 16 万平方米，造型取意于斗拱与青铜器。",
    detail: "它是现代钢混结构，不是传统斗拱结构。这一点必须讲清：它与斗拱的关系是「取意」，不是「同类」。",
    links: [{ label: "第二幕 · 木构星图", href: "../act-02-globe/" }],
  },
];

const ROUTES = [
  { from: "ningbo", to: "nara", label: "遣唐使与宋元工匠" },
  { from: "ningbo", to: "gyeongju", label: "高丽后期 · 柱心包" },
  { from: "ningbo", to: "shuri", label: "琉球 · 檐下语汇" },
  { from: "ningbo", to: "hue", label: "越南 · 南方体系" },
];

function nodeMarkup(node, index, mode) {
  const [x, y] = project(node.lon, node.lat);
  const dx = node.anchor === "end" ? -9 : 9;
  const anchor = node.anchor === "end" ? "end" : "start";
  const size = mode === "routes" ? 3.4 : 4;
  return `<g class="map-node" data-node="${node.id}" role="button" tabindex="0"
        aria-label="${node.name}${node.sub}" transform="translate(${x.toFixed(1)},${y.toFixed(1)})">
      <circle class="halo" r="6" style="animation-delay:${(index * 0.32).toFixed(2)}s"/>
      <circle class="core" r="${size}"/>
      <text x="${dx}" y="${node.dy ?? 3}" text-anchor="${anchor}">${node.name}</text>
    </g>`;
}

function routeMarkup(route) {
  const a = MAP_NODES.find((n) => n.id === route.from);
  const b = MAP_NODES.find((n) => n.id === route.to);
  if (!a || !b) return "";
  const [x1, y1] = project(a.lon, a.lat);
  const [x2, y2] = project(b.lon, b.lat);
  const mx = (x1 + x2) / 2 + (y2 - y1) * 0.16;
  const my = (y1 + y2) / 2 - Math.abs(x2 - x1) * 0.12;
  return `<path class="map-route" d="M${x1.toFixed(1)} ${y1.toFixed(1)} Q${mx.toFixed(1)} ${my.toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)}"/>`;
}

export function buildMapSvg(geo, mode = "nodes") {
  const paths = landPaths(geo)
    .map((d) => `<path d="${d}" fill="${LAND}" stroke="${INK}" stroke-width="0.5" stroke-opacity="0.55"/>`)
    .join("");

  const routes = mode === "routes" ? ROUTES.map(routeMarkup).join("") : "";
  const nodes = MAP_NODES.map((n, i) => nodeMarkup(n, i, mode)).join("");

  return `<svg viewBox="0 0 ${VIEW.w} ${VIEW.h}" preserveAspectRatio="xMidYMid meet" role="img"
      aria-label="东亚木构圈地图">
    <rect width="${VIEW.w}" height="${VIEW.h}" fill="${SEA}"/>
    <g fill="none" stroke="${INK}" stroke-opacity="0.5">
      <rect x="2" y="2" width="${VIEW.w - 4}" height="${VIEW.h - 4}" stroke-width="1"/>
      <rect x="6" y="6" width="${VIEW.w - 12}" height="${VIEW.h - 12}" stroke-width="0.4"/>
    </g>
    ${paths}
    <g stroke="${INK_FAINT}" stroke-width="0.4" stroke-dasharray="2 6" fill="none">
      <path d="M20 60 H300 M20 120 H300 M20 180 H300 M20 240 H300 M20 300 H300 M20 360 H300 M20 420 H300"/>
    </g>
    ${routes}
    ${nodes}
    <g ${FONT} font-size="8.5" fill="rgba(38,69,79,0.5)">
      <text x="30" y="196" transform="rotate(-90 30 196)">东 海</text>
      <text x="176" y="330" transform="rotate(-90 176 330)">南 海</text>
      <text x="286" y="150" transform="rotate(-90 286 150)">日 本 海</text>
    </g>
    <g ${FONT} font-size="8" fill="${VERMILION}" fill-opacity="0.7">
      <text x="16" y="446">示意投影 · 不用于定位</text>
    </g>
  </svg>`;
}

export function nodeById(id) {
  return MAP_NODES.find((n) => n.id === id);
}
