/* 木构之间 · 构件小图与图标
   全部为内联 SVG，viewBox 统一 0 0 100 100，墨线 + 木色
   ------------------------------------------------------------------ */

const INK = "rgba(52,42,30,0.72)";
const WOOD = "#cda878";
const WOOD_DARK = "#a9814f";
const WOOD_LIGHT = "#e0c69c";

/* 斗：口大底小，上开卯口，分耳、平、欹三段 */
function dou() {
  return `
    <path d="M30 20 H70 V40 H30 Z" fill="${WOOD_LIGHT}" stroke="${INK}" stroke-width="1.4"/>
    <path d="M24 40 H76 L68 58 H32 Z" fill="${WOOD}" stroke="${INK}" stroke-width="1.4"/>
    <path d="M32 58 H68 L60 76 H40 Z" fill="${WOOD_DARK}" stroke="${INK}" stroke-width="1.4"/>
    <path d="M46 20 H54 V40 H46 Z" fill="rgba(52,42,30,0.16)"/>
    <text x="76" y="30" font-size="9" fill="${INK}" font-family="serif">耳</text>
    <text x="80" y="52" font-size="9" fill="${INK}" font-family="serif">平</text>
    <text x="72" y="74" font-size="9" fill="${INK}" font-family="serif">欹</text>`;
}

/* 拱：两端卷杀，上开卯口 */
function gong() {
  return `
    <path d="M14 46
             C20 40 30 44 34 44
             H66
             C70 44 80 40 86 46
             L86 58
             C80 53 70 58 66 58
             H34
             C30 58 20 53 14 58 Z"
          fill="${WOOD}" stroke="${INK}" stroke-width="1.4"/>
    <rect x="44" y="36" width="12" height="12" fill="${WOOD_LIGHT}" stroke="${INK}" stroke-width="1.1"/>
    <path d="M14 58 C22 62 30 58 34 58" stroke="${INK}" stroke-width="1" fill="none"/>
    <text x="50" y="82" font-size="9" fill="${INK}" font-family="serif" text-anchor="middle">卷杀</text>`;
}

/* 昂：斜置，昂嘴在下，昂尾在上 */
function ang() {
  return `
    <path d="M12 66 L34 40 L88 40 L88 52 L44 52 L22 76 Z"
          fill="${WOOD}" stroke="${INK}" stroke-width="1.4"/>
    <path d="M12 66 L22 76 L30 70 L20 62 Z" fill="${WOOD_DARK}" stroke="${INK}" stroke-width="1.2"/>
    <line x1="40" y1="40" x2="40" y2="52" stroke="${INK}" stroke-width="1"/>
    <text x="14" y="88" font-size="9" fill="${INK}" font-family="serif">昂嘴</text>
    <text x="70" y="32" font-size="9" fill="${INK}" font-family="serif">昂尾</text>`;
}

/* 翘：清式沿进深出跳，相当于宋式华拱 */
function qiao() {
  return `
    <path d="M16 44 H76 L84 50 L76 56 H16 L10 50 Z"
          fill="${WOOD}" stroke="${INK}" stroke-width="1.4"/>
    <rect x="30" y="36" width="10" height="8" fill="${WOOD_LIGHT}" stroke="${INK}" stroke-width="1"/>
    <rect x="52" y="36" width="10" height="8" fill="${WOOD_LIGHT}" stroke="${INK}" stroke-width="1"/>
    <path d="M18 50 H74" stroke="rgba(52,42,30,0.18)" stroke-width="1"/>
    <text x="50" y="76" font-size="9" fill="${INK}" font-family="serif" text-anchor="middle">进深方向</text>`;
}

/* 耍头：最上层端头，头上有卷杀 */
function shuatou() {
  return `
    <path d="M14 42 H62 C72 42 78 46 80 50 C78 54 72 58 62 58 H14 Z"
          fill="${WOOD}" stroke="${INK}" stroke-width="1.4"/>
    <path d="M62 42 C68 44 70 47 70 50 C70 53 68 56 62 58"
          fill="${WOOD_LIGHT}" stroke="${INK}" stroke-width="1.1"/>
    <text x="10" y="34" font-size="9" fill="${INK}" font-family="serif">出跳端</text>`;
}

/* 枋：横枋，端部露出断面 */
function fang() {
  return `
    <path d="M10 46 H74 V58 H10 Z" fill="${WOOD}" stroke="${INK}" stroke-width="1.4"/>
    <ellipse cx="78" cy="52" rx="7" ry="6" fill="${WOOD_LIGHT}" stroke="${INK}" stroke-width="1.3"/>
    <ellipse cx="78" cy="52" rx="3" ry="2.4" fill="none" stroke="${INK}" stroke-width="0.8"/>
    <text x="42" y="76" font-size="9" fill="${INK}" font-family="serif" text-anchor="middle">联系各朵</text>`;
}

export const PART_ICONS = {
  dou,
  gong,
  ang,
  qiao,
  shuatou,
  fang,
};

/* 书耳按钮用的单字图标：用汉字更贴古籍，这里只提供字 */
export const RAIL_GLYPH = {
  index: "目",
  model: "器",
  notes: "注",
  sources: "引",
};
