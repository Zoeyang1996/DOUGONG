/* 木构之间 · 图版绘制
   全部内联 SVG，无外部图片；线条用墨，重点用朱
   ------------------------------------------------------------------ */

const INK = "#3a3026";
const INK_FAINT = "rgba(58,48,38,0.42)";
const INK_GHOST = "rgba(58,48,38,0.2)";
const VERMILION = "#9e3527";
const WOOD = "#d3b184";
const WOOD_MID = "#bc9463";
const WOOD_DARK = "#a07b4c";
const WASH = "rgba(38,69,79,0.07)";
const FONT = 'font-family="Songti SC, STSong, serif"';

function frame(inner, label) {
  return `<svg viewBox="0 0 320 460" preserveAspectRatio="xMidYMid meet" role="img" aria-label="${label}">${inner}</svg>`;
}

/* ------------------------------------------------------------ 河姆渡干栏 */

function hemudu() {
  return frame(`
    <g stroke="${INK}" fill="none" stroke-width="1.1">
      <path d="M20 96 L160 58 L300 96"/>
      <path d="M28 108 L160 74 L292 108" stroke-width="0.8"/>
      <path d="M60 84 L74 74 M100 74 L114 64 M140 66 L154 56 M186 64 L200 74 M226 74 L240 84"
            stroke-width="0.7" stroke="${INK_FAINT}"/>
      <rect x="44" y="196" width="232" height="10" fill="${WOOD}" stroke="${INK}" stroke-width="1"/>
      <line x1="62" y1="206" x2="62" y2="330" stroke-width="1.2"/>
      <line x1="112" y1="206" x2="112" y2="342" stroke-width="1.2"/>
      <line x1="208" y1="206" x2="208" y2="342" stroke-width="1.2"/>
      <line x1="258" y1="206" x2="258" y2="330" stroke-width="1.2"/>
      <path d="M40 250 H280 M40 300 H280" stroke-width="0.8" stroke="${INK_FAINT}"/>
      <path d="M40 336 H280" stroke-width="0.8" stroke="${INK_FAINT}" stroke-dasharray="5 5"/>
      <circle cx="112" cy="196" r="17" fill="none" stroke="${VERMILION}" stroke-width="1" stroke-dasharray="3 3"/>
      <circle cx="208" cy="196" r="17" fill="none" stroke="${VERMILION}" stroke-width="1" stroke-dasharray="3 3"/>
      <path d="M112 196 V150 H208 V196" stroke="${INK}" stroke-width="1" fill="${WASH}"/>
    </g>
    <g ${FONT} font-size="9" fill="${INK_FAINT}">
      <text x="24" y="140">底层架空，人居其上；</text>
      <text x="24" y="156">江南潮湿，故架而居之。</text>
    </g>
    <g transform="translate(40,362)">
      <line x1="0" y1="0" x2="240" y2="0" stroke="${INK_GHOST}"/>
      <g ${FONT} font-size="10" fill="${INK}">
        <text x="0" y="20">方榫</text>
        <text x="62" y="20">圆榫</text>
        <text x="124" y="20">燕尾榫</text>
        <text x="192" y="20">企口榫</text>
      </g>
      <g stroke="${INK}" fill="${WOOD}" stroke-width="1">
        <rect x="2" y="26" width="34" height="16"/>
        <circle cx="78" cy="34" r="8"/>
        <path d="M126 42 L134 26 L158 26 L166 42 Z" fill="${WOOD_MID}"/>
        <path d="M196 28 h30 v6 h-30 z M196 38 h30 v6 h-30 z" fill="${WOOD_DARK}"/>
      </g>
    </g>
  `, "河姆渡干栏与榫卯类型示意");
}

/* ------------------------------------------------------------ 力：拉、剪、拔 */

function forceRow(y, name, note, arrow, shape) {
  return `<g transform="translate(0,${y})">
    <line x1="26" y1="20" x2="294" y2="20" stroke="${INK_GHOST}"/>
    <text x="26" y="40" ${FONT} font-size="16" fill="${VERMILION}" font-weight="600">${name}</text>
    <text x="26" y="58" ${FONT} font-size="10" fill="${INK_FAINT}">${note}</text>
    <g transform="translate(160,0)">${shape}</g>
    ${arrow}
  </g>`;
}

function forces() {
  return frame(`
    ${forceRow(
      40, "拉", "构件被拽开",
      `<g stroke="${VERMILION}" fill="none" stroke-width="1.4">
         <path d="M126 92 H96" marker-end="url(#ar)"/>
         <path d="M194 92 H224" marker-end="url(#ar)"/>
       </g>`,
      `<path d="M-34 80 H34 L24 102 H-24 Z" fill="${WOOD}" stroke="${INK}" stroke-width="1"/>
       <path d="M-10 102 H10" stroke="${INK_FAINT}" stroke-width="1.4"/>`
    )}
    ${forceRow(
      170, "剪", "两块木头错动",
      `<g stroke="${VERMILION}" fill="none" stroke-width="1.4">
         <path d="M104 228 H74" marker-end="url(#ar)"/>
         <path d="M216 212 H246" marker-end="url(#ar)"/>
       </g>`,
      `<rect x="-38" y="204" width="36" height="20" fill="${WOOD}" stroke="${INK}" stroke-width="1"/>
       <rect x="2" y="204" width="36" height="20" fill="${WOOD_MID}" stroke="${INK}" stroke-width="1"/>
       <path d="M2 214 H38" stroke="${INK}" stroke-width="1.2"/>`
    )}
    ${forceRow(
      300, "拔", "构件被向上提起",
      `<g stroke="${VERMILION}" fill="none" stroke-width="1.4">
         <path d="M160 352 V320" marker-end="url(#ar)"/>
       </g>`,
      `<rect x="-30" y="360" width="60" height="14" fill="${WOOD_MID}" stroke="${INK}" stroke-width="1"/>
       <path d="M-14 360 a14 10 0 0 1 28 0 z" fill="${WOOD}" stroke="${INK}" stroke-width="1"/>`
    )}
    <defs>
      <marker id="ar" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0 0 L6 3 L0 6 Z" fill="${VERMILION}"/>
      </marker>
    </defs>
    <text x="24" y="436" ${FONT} font-size="9" fill="${INK_GHOST}">形状由要限制的方向决定</text>
  `, "拉剪拔三种受力与榫卯形状");
}

/* ------------------------------------------------------------ 三个台阶 */

function stepPanel(y, ordinal, title, body, art) {
  return `<g transform="translate(0,${y})">
    <line x1="24" y1="0" x2="296" y2="0" stroke="${INK_GHOST}"/>
    <text x="24" y="22" ${FONT} font-size="11" fill="${VERMILION}" letter-spacing="2">${ordinal}</text>
    <text x="24" y="42" ${FONT} font-size="14" fill="${INK}">${title}</text>
    <text x="24" y="60" ${FONT} font-size="9.5" fill="${INK_FAINT}">${body}</text>
    <g transform="translate(24,72)">${art}</g>
  </g>`;
}

function steps() {
  return frame(`
    ${stepPanel(
      20, "其一", "装柄工具",
      "刃部插入木柄浅槽，或穿孔加绳绑缚",
      `<path d="M18 36 L48 14 L92 14 L96 34 L34 42 Z" fill="${WOOD_MID}" stroke="${INK}" stroke-width="1"/>
       <rect x="90" y="18" width="96" height="12" fill="${WOOD}" stroke="${INK}" stroke-width="1"/>
       <path d="M120 30 q10 14 0 26 M148 30 q10 14 0 26" stroke="${INK}" stroke-width="1" fill="none" stroke-dasharray="3 3"/>`
    )}
    ${stepPanel(
      176, "其二", "木工工具",
      "凿开卯、锯开榫，墨斗弹线",
      `<g stroke="${INK}" stroke-width="1" fill="${WOOD}">
         <path d="M14 44 l46 -10 l6 14 l-46 10 z"/>
         <rect x="60" y="30" width="14" height="26" fill="${WOOD_DARK}"/>
         <path d="M108 22 h70 l-4 26 h-66 z" fill="${WOOD_MID}"/>
         <path d="M108 34 h70 M108 44 h66" stroke="${INK_FAINT}" stroke-width="0.8"/>
       </g>
       <path d="M96 70 H200" stroke="${VERMILION}" stroke-width="0.9" stroke-dasharray="6 4"/>`
    )}
    ${stepPanel(
      332, "其三", "建筑",
      "柱网、梁架与檐下斗拱",
      `<g stroke="${INK}" stroke-width="1" fill="none">
         <path d="M20 82 H200"/>
         <path d="M34 82 V54 M96 82 V54 M164 82 V54"/>
       </g>
       <g fill="${WOOD}" stroke="${INK}" stroke-width="1">
         <rect x="28" y="44" width="12" height="10"/>
         <rect x="90" y="44" width="12" height="10"/>
         <rect x="158" y="44" width="12" height="10"/>
       </g>
       <path d="M14 44 L108 12 L206 44" stroke="${INK}" stroke-width="1" fill="none"/>`
    )}
  `, "三个台阶：工具到建筑");
}

export const DRAWINGS = {
  hemudu,
  forces,
  steps,
};
/* ------------------------------------------------------------ 出檐（可动） */

function eave() {
  return frame(`
    <g stroke="${INK}" stroke-width="1" fill="none">
      <path d="M20 384 H300"/>
      <path d="M90 384 V250 M170 384 V250 M250 384 V250"/>
    </g>
    <g fill="${WOOD}" stroke="${INK}" stroke-width="1">
      <rect x="84" y="238" width="12" height="12"/>
      <rect x="164" y="238" width="12" height="12"/>
      <rect x="244" y="238" width="12" height="12"/>
    </g>

    <g id="fig-eave-tip" style="transition: transform 460ms cubic-bezier(.2,.9,.2,1)">
      <g stroke="${INK}" stroke-width="1.1" fill="none">
        <path d="M150 238 h-26 M150 226 h-38 M150 214 h-46 M150 202 h-54"/>
      </g>
      <g fill="${WOOD}" stroke="${INK}" stroke-width="1">
        <rect x="100" y="196" width="10" height="8"/>
        <rect x="86" y="186" width="10" height="8"/>
        <rect x="70" y="176" width="10" height="8"/>
      </g>
      <path d="M64 168 H300 L268 142 H52 Z" fill="${WOOD_MID}" fill-opacity="0.55" stroke="${INK}" stroke-width="1"/>
      <path d="M120 142 V118" stroke="${INK}" stroke-width="0.8" stroke-dasharray="3 3"/>
      <text id="fig-eave-label" x="126" y="116" ${FONT} font-size="9.5" fill="${VERMILION}">出檐</text>
    </g>

    <g id="fig-eave-moment" stroke="${VERMILION}" fill="none" stroke-width="1.2">
      <path d="M170 258 q36 4 58 20" stroke-dasharray="4 3"/>
      <path d="M228 278 l-8 -2 M228 278 l-3 -8"/>
      <text x="236" y="272" ${FONT} font-size="9" fill="${VERMILION}">倾覆力矩</text>
    </g>

    <g ${FONT} font-size="9" fill="${INK_GHOST}">
      <text x="24" y="420">檐口越远，柱头承受的倾覆力矩越大</text>
      <text x="24" y="436">斗拱把它一层层分解，再送回柱子</text>
    </g>
  `, "出檐与力矩示意");
}

/* ------------------------------------------------------------ 早期四段线稿 */

function stripPanel(y, era, caption, art) {
  return `<g transform="translate(0,${y})">
    <line x1="24" y1="0" x2="296" y2="0" stroke="${INK_GHOST}"/>
    <text x="24" y="20" ${FONT} font-size="12" fill="${INK}">${era}</text>
    <text x="24" y="35" ${FONT} font-size="8.5" fill="${INK_FAINT}">${caption}</text>
    <g transform="translate(190,52)" stroke="${INK}" fill="none" stroke-width="1">${art}</g>
  </g>`;
}

function strip() {
  return frame(`
    ${stripPanel(
      16, "西周", "青铜器上的大斗形象",
      `<rect x="-12" y="-24" width="24" height="14" fill="${WOOD}"/>
       <rect x="-24" y="-8" width="48" height="10" fill="${WOOD_MID}"/>
       <path d="M-24 2 v14 M24 2 v14" stroke-width="1"/>`
    )}
    ${stripPanel(
      124, "战国", "斗与斜拱的组合",
      `<rect x="-10" y="-30" width="20" height="12" fill="${WOOD}"/>
       <rect x="-28" y="-18" width="56" height="8" fill="${WOOD_MID}"/>
       <path d="M-8 -30 L-34 -50 M8 -30 L34 -50" stroke-width="1.4"/>
       <path d="M-28 -10 v16 M28 -10 v16" stroke-width="1"/>`
    )}
    ${stripPanel(
      232, "汉代", "一斗二升，孤立托架",
      `<rect x="-12" y="-16" width="24" height="12" fill="${WOOD}"/>
       <path d="M-28 -16 h16 v12 h-16 z M12 -16 h16 v12 h-16 z" fill="${WOOD_MID}"/>
       <rect x="-32" y="-32" width="64" height="8" fill="${WOOD_DARK}"/>
       <path d="M-20 -32 v-12 M20 -32 v-12" stroke-width="1"/>`
    )}
    ${stripPanel(
      340, "南北朝", "人字拱与一斗三升",
      `<rect x="-10" y="-6" width="20" height="12" fill="${WOOD}"/>
       <path d="M-28 -22 L0 -40 L28 -22" stroke-width="1.4" fill="none"/>
       <path d="M-36 -40 h72" stroke-width="1"/>
       <path d="M-36 -40 v8 M0 -40 v8 M36 -40 v8" stroke-width="1"/>`
    )}
    <text x="24" y="448" ${FONT} font-size="9" fill="${INK_GHOST}">形象的每一步，都对应一个新出现的结构需求</text>
  `, "西周战国汉南北朝斗拱形象");
}

/* ------------------------------------------------------------ 三个时代同比例 */

function eraColumn(x, era, bracketRatio, eaveLen, note) {
  const baseY = 372;
  const colTop = 300;
  const bh = 96 * bracketRatio;
  return `<g transform="translate(${x},0)">
    <line x1="0" y1="${baseY}" x2="0" y2="${colTop}" stroke="${INK}" stroke-width="3"/>
    <g fill="${WOOD}" stroke="${INK}" stroke-width="0.9">
      <rect x="-15" y="${colTop - bh}" width="30" height="${bh * 0.34}"/>
      <rect x="-25" y="${colTop - bh * 0.68}" width="50" height="${bh * 0.28}"/>
      <rect x="-33" y="${colTop - bh * 0.4}" width="66" height="${bh * 0.24}"/>
    </g>
    <path d="M${-eaveLen} ${colTop - bh - 10} H${eaveLen} L${eaveLen - 14} ${colTop - bh - 32} H${-eaveLen + 14} Z"
          fill="${WOOD_MID}" fill-opacity="0.6" stroke="${INK}" stroke-width="1"/>
    <text x="0" y="${baseY + 22}" ${FONT} font-size="12" fill="${INK}" text-anchor="middle">${era}</text>
    <text x="0" y="${baseY + 38}" ${FONT} font-size="8.5" fill="${INK_FAINT}" text-anchor="middle">${note}</text>
  </g>`;
}

function compare() {
  return frame(`
    <g id="fig-cmp-0" style="transition: opacity 280ms" opacity="1">
      ${eraColumn(160, "唐", 1, 96, "约半柱高")}
    </g>
    <g id="fig-cmp-1" style="transition: opacity 280ms" opacity="0">
      ${eraColumn(160, "北宋", 0.7, 70, "约 2/7 柱高")}
    </g>
    <g id="fig-cmp-2" style="transition: opacity 280ms" opacity="0">
      ${eraColumn(160, "明清", 0.4, 46, "更小、更密")}
    </g>
    <text x="24" y="434" ${FONT} font-size="9" fill="${INK_GHOST}">同一根柱子，三个时代（示意比例）</text>
  `, "唐宋明清斗拱比例对照");
}

/* ------------------------------------------------------------ 结构 vs 装饰 */

function bar() {
  const eras = ["汉", "唐", "宋", "元", "明", "清"];
  const struct = [0.9, 0.95, 0.8, 0.6, 0.4, 0.24];
  const orna = [0.2, 0.18, 0.35, 0.5, 0.72, 0.92];
  const colW = 44;
  let bars = "";
  eras.forEach((era, i) => {
    const x = 36 + i * colW;
    bars += `<g class="fig-era" data-era="${i}">
      <rect x="${x}" y="${380 - struct[i] * 220}" width="12" height="${struct[i] * 220}"
            fill="${WOOD_DARK}" fill-opacity="0.88"/>
      <rect x="${x + 15}" y="${380 - orna[i] * 220}" width="12" height="${orna[i] * 220}"
            fill="${VERMILION}" fill-opacity="0.48"/>
      <text x="${x + 13}" y="398" ${FONT} font-size="10" fill="${INK}" text-anchor="middle">${era}</text>
    </g>`;
  });
  return frame(`
    <line x1="24" y1="380" x2="298" y2="380" stroke="${INK_FAINT}"/>
    ${bars}
    <g transform="translate(24,26)">
      <rect x="0" y="0" width="10" height="10" fill="${WOOD_DARK}" fill-opacity="0.88"/>
      <text x="16" y="9" ${FONT} font-size="9.5" fill="${INK_FAINT}">结构贡献</text>
      <rect x="96" y="0" width="10" height="10" fill="${VERMILION}" fill-opacity="0.48"/>
      <text x="112" y="9" ${FONT} font-size="9.5" fill="${INK_FAINT}">装饰与等级</text>
    </g>
  `, "结构贡献与装饰等级趋势");
}

/* ------------------------------------------------------------ 当代三帧 */

function modernPanel(y, title, caption, art) {
  return `<g transform="translate(0,${y})">
    <rect x="24" y="0" width="272" height="104" fill="none" stroke="${INK_GHOST}"/>
    <g transform="translate(196,54)">${art}</g>
    <text x="34" y="24" ${FONT} font-size="11" fill="${INK}">${title}</text>
    <text x="34" y="40" ${FONT} font-size="8.5" fill="${INK_FAINT}">${caption}</text>
  </g>`;
}

function modern() {
  return frame(`
    ${modernPanel(
      24, "2010 世博中国馆", "取意斗拱，现代钢混结构",
      `<path d="M-56 26 H56 L34 -14 H-34 Z" fill="${VERMILION}" fill-opacity="0.32" stroke="${VERMILION}"/>
       <path d="M-34 -14 H34 L22 -32 H-22 Z" fill="${VERMILION}" fill-opacity="0.18" stroke="${VERMILION}"/>`
    )}
    ${modernPanel(
      156, "唐人街牌楼", "民间延续的檐下语汇",
      `<rect x="-48" y="-28" width="7" height="60" fill="${WOOD_DARK}"/>
       <rect x="41" y="-28" width="7" height="60" fill="${WOOD_DARK}"/>
       <path d="M-62 -28 H62 L40 -48 H-40 Z" fill="${WOOD}" stroke="${INK}" stroke-width="1"/>
       <rect x="-30" y="-24" width="60" height="8" fill="${VERMILION}" fill-opacity="0.4" stroke="${VERMILION}"/>`
    )}
    ${modernPanel(
      288, "参数化木构", "当代的节点实验",
      `<g stroke="${INK}" stroke-width="0.9" fill="none">
         <path d="M-44 26 L-16 -26 L16 26 L44 -26"/>
         <path d="M-44 -26 L-16 26 L16 -26 L44 26"/>
       </g>
       <g fill="${VERMILION}">
         <circle cx="-16" cy="-26" r="3.2"/>
         <circle cx="16" cy="26" r="3.2"/>
         <circle cx="16" cy="-26" r="3.2"/>
         <circle cx="-16" cy="26" r="3.2"/>
       </g>`
    )}
    <text x="24" y="440" ${FONT} font-size="9" fill="${INK_GHOST}">它们与斗拱的关系是「取意」，不是「同类」</text>
  `, "当代的三个斗拱回声");
}

export const MORE_DRAWINGS = {
  eave,
  strip,
  compare,
  bar,
  modern,
};
