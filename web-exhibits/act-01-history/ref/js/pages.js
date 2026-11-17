/* 木构之间 · 样张页面
   六页：封面 · 扉页 · 序 · 卷首 · 图版 · 正文
   一切文字直排，右起左行；版框、界行、版心、书耳皆按宋版样式。
   ------------------------------------------------------------------ */

import { dovetailArt, bracketArt } from "./art.js";

/* 句读：把标点换成朱点，像后人读书时用朱笔点的 */
const PUNCT = { "。": "dot", "，": "dot dot--small", "、": "dot dot--small", "；": "dot" };

function ju(text) {
  return text.replace(/[。，、；]/g, (ch) => `<i class="${PUNCT[ch]}" aria-hidden="true"></i>`);
}

function seal(text, kind = "bai", extra = "") {
  return `<span class="seal seal--${kind} ${extra}"><span class="seal__chars" style="--n:${text.length}">${text}</span></span>`;
}

/* ------------------------------------------------------------ 版心 */

function banxin(vol, folio) {
  return `
    <aside class="banxin" aria-hidden="true">
      <span class="banxin__title">木构之间</span>
      <span class="banxin__vol">${vol}</span>
      <svg class="banxin__fish" viewBox="0 0 20 34" aria-hidden="true">
        <path d="M10 0 L20 12 H0 Z" fill="#2a1d13"/>
        <path d="M0 22 H20 L10 34 Z" fill="#2a1d13"/>
      </svg>
      <span class="banxin__folio">${folio}</span>
    </aside>`;
}

function block(b) {
  if (typeof b === "string") return `<p class="p">${ju(b)}</p>`;
  if (b.t === "h") return `<h2 class="h">${b.s}</h2>`;
  if (b.t === "lead") return `<p class="p p--lead">${ju(b.s)}</p>`;
  if (b.t === "note") return `<span class="note">${ju(b.s)}</span>`;
  if (b.t === "sign") return `<p class="p p--sign">${b.s}</p>`;
  return `<p class="p">${ju(b.s)}</p>`;
}

/* ------------------------------------------------------------ 直排版面 */

function textPage({ side, vol, folio, body, shuer, sealText = "守", art = "" }) {
  return `
  <div class="page page--text" data-side="${side}">
    <div class="page__paper"></div>
    <div class="plate">
      <div class="plate__frame"></div>
      <div class="plate__in">
        ${banxin(vol, folio)}
        <div class="body">${body.map(block).join("")}</div>
      </div>
    </div>
    ${shuer ? `<div class="shuer">${shuer}</div>` : ""}
    ${art}
    ${seal(sealText, "bai", "page__seal")}
  </div>`;
}

/* ------------------------------------------------------------ 封面 */

const cover = () => `
  <div class="page page--cover" data-side="recto">
    <div class="cover__board"></div>
    <div class="cover__binder" aria-hidden="true">
      <svg viewBox="0 0 120 1360" preserveAspectRatio="none">
        <g stroke="rgba(238,220,186,0.38)" stroke-width="1.2" fill="none">
          <path d="M20 250 q30 12 46 0"/>
          <path d="M20 250 C 6 300 6 420 20 470"/>
          <path d="M20 470 q30 12 46 0"/>
          <path d="M20 470 C 6 520 6 640 20 690"/>
          <path d="M20 690 q30 12 46 0"/>
          <path d="M20 690 C 6 740 6 860 20 910"/>
          <path d="M20 910 q30 12 46 0"/>
          <path d="M20 910 C 6 960 6 1080 20 1130"/>
          <path d="M20 1130 q30 12 46 0"/>
        </g>
        <g fill="#170f09">
          <circle cx="66" cy="250" r="5.2"/>
          <circle cx="66" cy="470" r="5.2"/>
          <circle cx="66" cy="690" r="5.2"/>
          <circle cx="66" cy="910" r="5.2"/>
          <circle cx="66" cy="1130" r="5.2"/>
        </g>
      </svg>
    </div>

    <div class="cover__label">
      <div class="cover__label-frame">
        <h1 class="cover__title">木构之间</h1>
        <p class="cover__sub">从一榫一卯，到一朵斗拱</p>
      </div>
      ${seal("木作", "bai", "cover__seal")}
    </div>

    <div class="cover__foot">
      <span>中国古代木构科普读本</span>
      <span class="cover__sep">·</span>
      <span>五卷</span>
    </div>
  </div>`;

/* ------------------------------------------------------------ 扉页 */

const titlePage = () => `
  <div class="page page--title" data-side="verso">
    <div class="page__paper"></div>
    <div class="title__inner">
      <h1 class="title__main">木构之间</h1>
      <p class="title__sub">从一榫一卯，到一朵斗拱</p>
      <div class="title__rule"></div>
      <p class="title__meta">浙江工商职业技术学院　数字媒体技术　编</p>
      <p class="title__meta title__meta--year">二〇二六年　秋</p>
      <div class="title__seals">${seal("木构", "zhu")}${seal("样张", "bai")}</div>
    </div>
  </div>`;

/* ------------------------------------------------------------ 卷首 */

const chapter = () => `
  <div class="page page--chapter" data-side="recto">
    <div class="page__paper"></div>
    <div class="chapter__mark">卷一</div>
    <div class="chapter__big">接</div>
    <div class="chapter__motto">一凸一凹，木头握手</div>
    <div class="chapter__art">${bracketArt()}</div>
    <div class="chapter__note">榫卯者，木构之关节也。不入一钉，不施一胶，而能历千年不散。</div>
    ${seal("接", "zhu", "chapter__seal")}
  </div>`;

/* ------------------------------------------------------------ 图版 */

const platePage = () => `
  <div class="page page--plate" data-side="verso">
    <div class="page__paper"></div>
    <div class="plate">
      <div class="plate__frame"></div>
      <div class="plate__in">
        ${banxin("卷一", "三")}
        <div class="plate__canvas">
          <div class="cartouche"><span>燕尾图</span></div>
          <div class="plate__art">${dovetailArt()}</div>
          <p class="plate__caption">图中所绘，为三枚燕尾榫抽送之势。榫头外宽内窄，入卯之后受拉不脱，故家具与屋架皆用之。</p>
        </div>
      </div>
    </div>
    <div class="margin-note">拉则不脱</div>
    ${seal("榫", "zhu", "plate__seal")}
  </div>`;

/* ------------------------------------------------------------ 页面清单 */

export const PAGES = [
  { id: "cover", render: cover },
  { id: "title", render: titlePage },
  {
    id: "preface",
    render: () =>
      textPage({
        side: "verso",
        vol: "卷首",
        folio: "一",
        shuer: "卷首",
        sealText: "识",
        body: [
          { t: "h", s: "序" },
          { t: "lead", s: "木之相合，不假一钉。" },
          "七千年前，河姆渡人在潮湿的沼泽边凿出第一枚榫头。木头自此学会伸出手去，握住另一块木头。",
          { t: "note", s: "榫者，出而受之；卯者，入而纳之。见《营造法式》卷四。" },
          "一凸一凹，各让一寸，又各自守住一寸。此后七千年，中国房子的骨节，都是这样长起来的。",
          "到了唐宋，这法子长成了屋檐下的一朵斗拱：层层叠出，把屋顶的分量一分一分收拢，再送回柱子里面。",
          "所以读中国木构，要从两块木头的握手读起。",
          { t: "sign", s: "二〇二六年秋　识于明州" },
        ],
      }),
  },
  { id: "chapter", render: chapter },
  { id: "plate", render: platePage },
  {
    id: "body",
    render: () =>
      textPage({
        side: "recto",
        vol: "卷一",
        folio: "四",
        shuer: "卷一 · 接",
        sealText: "守",
        body: [
          { t: "h", s: "一凸一凹" },
          { t: "lead", s: "榫头与卯眼，是一块木头分出的两半。" },
          "榫头凸出，如指；卯眼凹入，如掌。指入掌中，木头便不肯再分开。",
          { t: "note", s: "榫头亦谓之榫舌，卯眼亦谓之卯口，南匠呼为公母榫。" },
          "木纹顺则韧，横则脆。故榫头必顺纹而出，卯眼必横纹而凿：顺者受力不裂，横者受力不松。",
          "三枚燕尾，外宽内窄。推入时略紧，拉出时愈紧。木头的脾气，被匠人算得清清楚楚，一枚钉子也不必用。",
          "《考工记》云：材美工巧，为之时，谓之三法。木有性，工有法，时有序，缺一不可。",
        ],
      }),
  },
];

export function renderPage(page) {
  return page.render();
}
