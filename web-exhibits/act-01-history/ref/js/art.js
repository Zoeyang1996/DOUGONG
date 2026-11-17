/* 木构之间 · 样张插图
   白描线稿：燕尾榫剖面（带剖面线）、斗拱立面（示意）
   一律只用线条，不用填色块，保持版画的「刀口」质感。
   ------------------------------------------------------------------ */

const INK = "#2a1d13";
const INK_SOFT = "rgba(42,29,19,0.55)";
const CINNABAR = "#9b2f22";

/* ---------------------------------------------------------- 燕尾榫剖面 */

function tailEdge(baseX, tipX, centers, baseHalf, tipHalf, dir) {
  // dir = 1：榫头向 +x 伸出；dir = -1：卯口向 -x 凹入
  return centers
    .map((c) => {
      const a = c - baseHalf;
      const b = c - tipHalf;
      const d = c + tipHalf;
      const e = c + baseHalf;
      return dir > 0
        ? `L${tipX},${b} L${tipX},${d} L${baseX},${e}`
        : `L${tipX},${b} L${tipX},${d} L${baseX},${e}`;
    })
    .join(" ");
}

export function dovetailArt() {
  const top = 110;
  const bottom = 300;
  const centers = [140, 205, 270];

  const tenon =
    `M40,${top} H300 ` +
    centers
      .map((c) => `L300,${c - 24} L372,${c - 30} L372,${c + 30} L300,${c + 24}`)
      .join(" ") +
    ` L300,${bottom} H40 Z`;

  const mortise =
    `M470,${top} ` +
    centers
      .map((c) => `L470,${c - 24} L398,${c - 30} L398,${c + 30} L470,${c + 24}`)
      .join(" ") +
    ` L470,${bottom} H700 V${top} Z`;

  return `
  <svg class="art art--dovetail" viewBox="0 0 740 380" role="img" aria-label="燕尾榫剖面示意">
    <defs>
      <pattern id="hatch" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
        <line x1="0" y1="0" x2="0" y2="7" stroke="${INK}" stroke-width="0.75" opacity="0.42"/>
      </pattern>
    </defs>

    <g fill="url(#hatch)">
      <path d="${tenon}"/>
      <path d="${mortise}"/>
    </g>
    <g fill="none" stroke="${INK}" stroke-width="1.7" stroke-linejoin="round">
      <path d="${tenon}"/>
      <path d="${mortise}"/>
    </g>

    <!-- 木纹：几笔顺纹的短线，位置错落 -->
    <g stroke="${INK_SOFT}" stroke-width="0.8" fill="none">
      <path d="M56 148 q40 -4 78 2 t74 1"/>
      <path d="M56 196 q48 3 92 -2"/>
      <path d="M56 262 q36 4 70 -1"/>
      <path d="M520 132 q46 3 88 -2 t68 1"/>
      <path d="M520 178 q40 -3 82 2"/>
      <path d="M520 250 q52 4 96 -1"/>
    </g>

    <!-- 推入方向 -->
    <g stroke="${CINNABAR}" fill="none" stroke-width="1.1">
      <path d="M382 208 H406" stroke-dasharray="5 4"/>
      <path d="M400 203 L408 208 L400 213"/>
    </g>

    <g font-family="inherit" font-size="13" fill="${CINNABAR}" letter-spacing="1">
      <text x="300" y="352">榫头 · 出而受之</text>
      <text x="470" y="352">卯眼 · 入而纳之</text>
    </g>
    <g stroke="${CINNABAR}" stroke-width="0.8" fill="none" opacity="0.8">
      <path d="M368 340 V318"/>
      <path d="M500 340 V318"/>
    </g>
  </svg>`;
}

/* ---------------------------------------------------------- 斗拱立面 */

export function bracketArt() {
  const cx = 240;
  const parts = [];

  const bar = (y, half, thick, taper = 0) =>
    `<path d="M${cx - half + taper},${y} H${cx + half - taper} L${cx + half},${y + thick} H${cx - half} Z" fill="none"/>`;

  // 柱头
  parts.push(`<path d="M${cx - 26},320 V232 M${cx + 26},320 V232" />`);

  // 栌斗
  parts.push(`<path d="M${cx - 34},232 H${cx + 34} L${cx + 26},208 H${cx - 26} Z" />`);
  parts.push(`<path d="M${cx - 40},208 H${cx + 40} L${cx + 33},186 H${cx - 33} Z" />`);

  // 一跳华拱
  parts.push(bar(186, 96, 15));
  // 二跳华拱
  parts.push(bar(158, 68, 14));
  // 令拱
  parts.push(bar(132, 52, 12));

  // 泥道拱（与华拱十字相交，立面见其断面）
  parts.push(`<path d="M${cx - 14},186 V150 M${cx + 14},186 V150" />`);

  // 下昂：两侧斜下
  parts.push(`<path d="M${cx - 60},158 L${cx - 120},196 L${cx - 108},204 L${cx - 48},166 Z" />`);
  parts.push(`<path d="M${cx + 60},158 L${cx + 120},196 L${cx + 108},204 L${cx + 48},166 Z" />`);

  // 散斗
  const dou = (x, y, w = 15, h = 9) =>
    `<path d="M${x - w},${y} H${x + w} L${x + w - 3},${y + h} H${x - w + 3} Z" />`;
  [120, 168, 240, 312, 360].forEach((x) => parts.push(dou(x, 132)));
  [176, 240, 304].forEach((x) => parts.push(dou(x, 158, 13, 8)));
  [150, 240, 330].forEach((x) => parts.push(dou(x, 186, 16, 10)));

  // 撩檐枋与檐口
  parts.push(`<path d="M${cx - 150},120 H${cx + 150} V104 H${cx - 150} Z" />`);
  parts.push(`<path d="M${cx - 172},104 H${cx + 172} L${cx + 158},92 H${cx - 158} Z" />`);

  return `
  <svg class="art art--bracket" viewBox="0 0 480 340" role="img" aria-label="斗拱立面示意">
    <g stroke="${INK}" stroke-width="1.35" fill="none" stroke-linejoin="round" stroke-linecap="round">
      ${parts.join("\n      ")}
    </g>
  </svg>`;
}
