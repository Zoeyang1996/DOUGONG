/* 木构之间 · 页面渲染
   一页 = 纸 + 版心栏 + 版框内容 + 书耳
   ------------------------------------------------------------------ */

import { VOLUMES, TOC } from "./content.js";
import { DRAWINGS, MORE_DRAWINGS } from "./drawings.js";
import { PART_ICONS } from "./icons.js";
import { buildMapSvg, loadLand } from "./map.js";
import { openMortise, openBracket, openNotes, openIndex } from "./popup.js";

const DRAW = { ...DRAWINGS, ...MORE_DRAWINGS };

/* 卷首页角的斗拱线稿，用来填住卷首的大片空白 */
const CHAPTER_ART = `
  <svg viewBox="0 0 120 150" aria-hidden="true">
    <g stroke="rgba(58,48,38,0.42)" fill="none" stroke-width="1">
      <rect x="34" y="118" width="52" height="12"/>
      <rect x="26" y="104" width="68" height="12"/>
      <rect x="18" y="90" width="84" height="12"/>
      <rect x="10" y="76" width="100" height="12"/>
      <path d="M10 76 L60 40 L110 76"/>
      <path d="M30 76 L60 56 L90 76" stroke-dasharray="3 4"/>
      <path d="M60 118 V140" stroke-dasharray="4 5"/>
      <path d="M8 70 H112" stroke-dasharray="2 6"/>
    </g>
    <g fill="rgba(158,53,39,0.5)">
      <circle cx="60" cy="40" r="2.4"/>
    </g>
  </svg>`;

export function el(tag, className, html) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (html != null) node.innerHTML = html;
  return node;
}

/* ------------------------------------------------------------ 书耳 */

function railFor(page, ctx, side) {
  const rail = el("div", "rail");
  rail.dataset.side = side;

  const add = (glyph, label, handler, pressed) => {
    const btn = el("button", "rail-btn", `${glyph}<span class="rail-label">${label}</span>`);
    btn.type = "button";
    btn.setAttribute("aria-label", label);
    if (pressed != null) btn.setAttribute("aria-pressed", String(pressed));
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      handler(btn);
    });
    rail.append(btn);
    return btn;
  };

  add("目", "目次", () => openIndex({
    items: TOC,
    current: ctx.currentIndex,
    onJump: (p) => ctx.jumpTo(p),
    anchor: rail,
  }));

  const modelTarget = ctx.modelTargetFor(page);
  if (modelTarget) {
    add("器", modelTarget.label, () => modelTarget.run(rail));
  }

  if ((page.notes && page.notes.length) || (page.sources && page.sources.length)) {
    add("注", "夹注与依据", () => openNotes({
      title: page.title || "夹注",
      notes: page.notes,
      sources: page.sources,
      anchor: rail,
    }));
  }

  return rail;
}

/* ------------------------------------------------------------ 页壳 */

function shell({ page, ctx, side, content, extraClass }) {
  const face = el("div", `page page--${page.kind} ${extraClass || ""}`.trim());
  face.append(el("div", "paper"));

  const fold = el("div", "fold-column");
  fold.innerHTML = `
    <span class="fold-title">${page.vol || ""}</span>
    <span class="fish-tail"></span>
    <span class="fish-tail fish-tail--lower"></span>
    <span class="fold-folio">${page.folio || ""}</span>`;
  face.append(fold);

  const sheet = el("div", "sheet");
  const frame = el("div", "frame");
  frame.append(content);
  sheet.append(frame);
  face.append(sheet);

  face.append(railFor(page, ctx, side));
  face.append(el("div", "gutter"));
  return face;
}

/* ------------------------------------------------------------ 封面 */

function coverPage(page) {
  const face = el("div", "page page--cover");
  face.append(el("div", "paper"));
  const cover = el("div", "cover");
  cover.innerHTML = `
    <div class="cover-sub">中国古代木构科普读本</div>
    <div class="cover-title">木构之间</div>
    <div class="cover-sub">从一榫一卯，到一朵斗拱</div>
    <div class="seal seal--cover">木作</div>
    <div class="cover-hint">轻 触 翻 开</div>`;
  face.append(cover);
  return face;
}

/* ------------------------------------------------------------ 竖排正文 */

export function verse(paragraphs, className) {
  const box = el("div", `verso ${className || ""}`.trim());
  paragraphs.forEach((text) => {
    const p = el("p");
    p.innerHTML = text;
    box.append(p);
  });
  return box;
}

function titleRow(page) {
  const row = el("div", "title-row");
  if (page.kicker) row.append(el("div", "page-kicker", page.kicker));
  row.append(el("h2", "page-title", page.title || ""));
  return row;
}

function textPage(page, ctx, side) {
  const inner = el("div", "text-inner");
  inner.append(titleRow(page), verse(page.body));
  return shell({ page, ctx, side, content: inner });
}

function chapterPage(page, ctx, side) {
  const vol = VOLUMES[page.volumeKey] || {};
  const inner = el("div", "chapter-head");
  inner.append(
    el("div", "chapter-numeral", page.vol),
    el("div", "chapter-name", `<span>${page.title}</span>`)
  );
  const mottoWrap = el("div", "chapter-motto", vol.motto || "");
  inner.append(mottoWrap);
  const body = el("div", "chapter-body");
  body.append(verse(page.body));
  const seal = el("div", "seal seal--small", page.title);
  body.append(seal);
  inner.append(body);
  inner.append(el("div", "chapter-art", CHAPTER_ART));
  return shell({ page, ctx, side, content: inner });
}

/* ------------------------------------------------------------ 图版 */

function platePage(page, ctx, side) {
  const plate = el("div", "plate");
  const img = el("img");
  img.src = page.image;
  img.alt = page.caption || page.title || "";
  plate.append(img);

  (page.hotspots || []).forEach((spot) => {
    const hot = el("div", "hotspot");
    hot.style.left = `${spot.x}%`;
    hot.style.top = `${spot.y}%`;
    hot.style.width = `${spot.w}%`;
    hot.style.height = `${spot.h}%`;
    hot.tabIndex = 0;
    hot.setAttribute("role", "button");
    hot.setAttribute("aria-label", spot.label);
    hot.innerHTML = `<span class="hotspot-dot"></span><span class="hotspot-tag">${spot.label}</span>`;
    const run = () => {
      if (spot.figure === "dougong") {
        openBracket({ category: spot.category || "all", anchor: hot });
      } else {
        openBracket({ category: "all", anchor: hot });
      }
    };
    hot.addEventListener("click", (e) => {
      e.stopPropagation();
      run();
    });
    hot.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") run();
    });
    plate.append(hot);
  });

  plate.append(el("div", "plate-number", page.caption || ""));
  return shell({ page, ctx, side, content: plate });
}

/* ------------------------------------------------------------ 绘图页 */

function figurePage(page, ctx, side) {
  const plate = el("div", "plate");
  const draw = DRAW[page.drawing];
  const svg = draw ? draw() : "";
  const holder = el("div", "figure-holder", svg);
  plate.append(holder);

  if (page.drawing === "eave") attachEave(plate, holder);
  if (page.drawing === "strip") attachStrip(plate, holder, ctx);

  plate.append(el("div", "plate-number", page.caption || ""));
  return shell({ page, ctx, side, content: plate });
}

/* 出檐：三个位置按钮 */
function attachEave(plate, holder) {
  const tip = holder.querySelector("#fig-eave-tip");
  const moment = holder.querySelector("#fig-eave-moment");
  if (!tip) return;
  const bar = el("div", "figure-controls");
  const steps = [
    { label: "檐近", x: 0, o: 0.5 },
    { label: "檐中", x: -30, o: 1 },
    { label: "檐远", x: -58, o: 1 },
  ];
  steps.forEach((s, i) => {
    const btn = el("button", "ghost-btn", s.label);
    btn.type = "button";
    if (i === 0) btn.setAttribute("aria-pressed", "true");
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      bar.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", "false"));
      btn.setAttribute("aria-pressed", "true");
      tip.style.transform = `translateX(${s.x}px)`;
      if (moment) moment.style.opacity = String(s.o);
    });
    bar.append(btn);
  });
  plate.append(bar);
}

/* 四段线稿：点一段，看说明 */
function attachStrip(plate, holder, ctx) {
  const notes = [
    "西周：青铜器上的大斗形象。图像证据，不是木构实物。",
    "战国：中山国铜方案上出现斗与斜角拱的组合。",
    "汉代：石阙与陶楼上大量出现一斗二升、一斗三升，各朵之间还不相连。",
    "南北朝：人字拱与一斗三升并用，补间斗拱开始萌芽。",
  ];
  const bar = el("div", "figure-controls figure-controls--wrap");
  notes.forEach((text, i) => {
    const btn = el("button", "ghost-btn", ["西周", "战国", "汉代", "南北朝"][i]);
    btn.type = "button";
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const tip = plate.querySelector(".figure-tip");
      if (tip) tip.textContent = text;
    });
    bar.append(btn);
  });
  plate.append(bar, el("div", "figure-tip", notes[0]));
}

/* ------------------------------------------------------------ 表（竖排） */

function tablePage(page, ctx, side) {
  const wrap = el("div", "table-wrap");
  const table = el("table", "verso-table");
  const thead = el("thead");
  const hr = el("tr");
  ["时期", "代表实例", "形态特征"].forEach((h) => hr.append(el("th", "", h)));
  thead.append(hr);
  table.append(thead);
  const tbody = el("tbody");
  page.rows.forEach((row) => {
    const tr = el("tr");
    row.forEach((cell) => tr.append(el("td", "", cell)));
    tbody.append(tr);
  });
  table.append(tbody);
  wrap.append(table);
  wrap.append(el("div", "plate-number", page.caption || ""));
  return shell({ page, ctx, side, content: wrap, extraClass: "page--wide" });
}
/* ------------------------------------------------------------ 目次 */

function contentsPage(page, ctx, side) {
  const inner = el("div", "text-inner");
  inner.append(titleRow(page));
  const list = el("div", "toc-list");
  TOC.forEach((item) => {
    const row = el("button", "toc-row");
    row.type = "button";
    row.innerHTML = `<span class="toc-vol">${item.vol}</span>
      <span class="toc-name">${item.name}</span>
      <span class="toc-leader"></span>
      <span class="toc-page">${String(item.page).padStart(2, "0")}</span>`;
    row.addEventListener("click", (e) => {
      e.stopPropagation();
      ctx.jumpTo(item.page);
    });
    list.append(row);
  });
  inner.append(list);
  return shell({ page, ctx, side, content: inner });
}

/* ------------------------------------------------------------ 四种榫卯 */

function jointGlyph(key) {
  const wood = "#cda878";
  const dark = "#a9814f";
  const ink = "rgba(52,42,30,0.7)";
  const shapes = {
    zhisun: `<rect x="10" y="30" width="34" height="40" fill="${wood}" stroke="${ink}"/>
             <rect x="46" y="42" width="44" height="16" fill="${dark}" stroke="${ink}"/>`,
    yanwei: `<rect x="10" y="26" width="30" height="48" fill="${wood}" stroke="${ink}"/>
             <path d="M40 38 L84 30 L84 70 L40 62 Z" fill="${dark}" stroke="${ink}"/>`,
    qikou: `<rect x="10" y="28" width="38" height="16" fill="${wood}" stroke="${ink}"/>
            <rect x="10" y="56" width="38" height="16" fill="${wood}" stroke="${ink}"/>
            <rect x="48" y="40" width="10" height="20" fill="${dark}" stroke="${ink}"/>
            <rect x="58" y="28" width="32" height="44" fill="${wood}" fill-opacity="0.55" stroke="${ink}"/>`,
    mantou: `<rect x="12" y="52" width="76" height="26" fill="${wood}" stroke="${ink}"/>
             <path d="M36 52 a14 14 0 0 1 28 0 z" fill="${dark}" stroke="${ink}"/>
             <rect x="26" y="26" width="48" height="20" fill="${wood}" stroke="${ink}"/>`,
  };
  return `<svg viewBox="0 0 100 100" aria-hidden="true">${shapes[key] || ""}</svg>`;
}

function modelGridPage(page, ctx, side) {
  const plate = el("div", "model-grid");
  page.items.forEach((item) => {
    const cell = el("button", "model-cell");
    cell.type = "button";
    cell.innerHTML = `
      <span class="model-glyph">${jointGlyph(item.key)}</span>
      <span class="model-text">
        <strong>${item.name}</strong>
        <em>${item.hint}</em>
        <small>${item.use}</small>
      </span>
      <span class="model-open">点开三维</span>`;
    cell.addEventListener("click", (e) => {
      e.stopPropagation();
      openMortise(item.key, { anchor: cell });
    });
    plate.append(cell);
  });
  plate.append(el("div", "plate-number plate-number--bottom", page.caption || ""));
  return shell({ page, ctx, side, content: plate, extraClass: "page--model-grid" });
}

/* ------------------------------------------------------------ 六构件 */

function partsPage(page, ctx, side) {
  const plate = el("div", "parts-grid");
  page.items.forEach((item) => {
    const icon = PART_ICONS[item.key] ? PART_ICONS[item.key]() : "";
    const cell = el("button", "part-cell");
    cell.type = "button";
    cell.innerHTML = `
      <span class="part-figure"><svg viewBox="0 0 100 100" aria-hidden="true">${icon}</svg></span>
      <span class="part-name">${item.name}</span>
      <span class="part-pinyin">${item.pinyin}</span>
      <span class="part-role">${item.role}</span>`;
    cell.addEventListener("click", (e) => {
      e.stopPropagation();
      openBracket({ category: item.key, anchor: cell });
    });
    plate.append(cell);
  });
  plate.append(el("div", "plate-number plate-number--bottom", page.caption || ""));
  return shell({ page, ctx, side, content: plate, extraClass: "page--parts" });
}

/* ------------------------------------------------------------ 数一朵斗拱 */

function quizPage(page, ctx, side) {
  const wrap = el("div", "quiz");
  wrap.innerHTML = `
    <div class="quiz-head">
      <span class="quiz-step">第一问</span>
      <p class="quiz-q">这朵斗拱在什么位置？</p>
      <div class="quiz-opts" data-step="0">
        <button class="ghost-btn" data-ok="1">柱头铺作</button>
        <button class="ghost-btn">补间铺作</button>
        <button class="ghost-btn">转角铺作</button>
      </div>
    </div>
    <div class="quiz-head" hidden>
      <span class="quiz-step">第二问</span>
      <p class="quiz-q">从栌斗起，向外挑了几层？</p>
      <div class="quiz-opts" data-step="1">
        <button class="ghost-btn">1 跳</button>
        <button class="ghost-btn">2 跳</button>
        <button class="ghost-btn">3 跳</button>
        <button class="ghost-btn" data-ok="1">4 跳</button>
      </div>
    </div>
    <div class="quiz-head" hidden>
      <span class="quiz-step">第三问</span>
      <p class="quiz-q">铺作数 = 跳数 + 3 = ？</p>
      <div class="quiz-opts" data-step="2">
        <button class="ghost-btn">五铺作</button>
        <button class="ghost-btn" data-ok="1">七铺作</button>
        <button class="ghost-btn">八铺作</button>
      </div>
    </div>
    <div class="quiz-head" hidden>
      <span class="quiz-step">第四问</span>
      <p class="quiz-q">第一跳的跳头上有横拱吗？</p>
      <div class="quiz-opts" data-step="3">
        <button class="ghost-btn" data-ok="1">没有，偷心造</button>
        <button class="ghost-btn">有，计心造</button>
      </div>
    </div>
    <div class="quiz-answer" hidden>
      <span class="quiz-final">七铺作 双杪双下昂 单偷心造</span>
      <p>四跳：两跳华栱、两跳下昂。加上栌斗层、耍头层、衬枋头层，共七层。</p>
      <button class="ghost-btn quiz-model" type="button">在三维里看这一朵</button>
    </div>`;

  const steps = [...wrap.querySelectorAll(".quiz-head")];
  const answer = wrap.querySelector(".quiz-answer");

  steps.forEach((step, index) => {
    step.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const ok = btn.dataset.ok === "1";
        btn.setAttribute("aria-pressed", String(ok));
        if (!ok) {
          btn.classList.add("is-wrong");
          return;
        }
        step.hidden = true;
        const next = steps[index + 1];
        if (next) next.hidden = false;
        else answer.hidden = false;
      });
    });
  });

  wrap.querySelector(".quiz-model").addEventListener("click", (e) => {
    e.stopPropagation();
    openBracket({ category: "ang", anchor: e.currentTarget, explode: 0.2 });
  });

  wrap.append(el("div", "quiz-art", CHAPTER_ART));
  plateNumber(wrap, page);
  return shell({ page, ctx, side, content: wrap });
}

function plateNumber(host, page) {
  host.append(el("div", "plate-number", page.caption || ""));
}

/* ------------------------------------------------------------ 对照与条形 */

function comparePage(page, ctx, side) {
  const plate = el("div", "plate");
  const holder = el("div", "figure-holder", DRAW.compare());
  plate.append(holder);

  const bar = el("div", "figure-controls");
  const labels = ["唐", "北宋", "明清"];
  const setActive = (i) => {
    [0, 1, 2].forEach((k) => {
      const g = holder.querySelector(`#fig-cmp-${k}`);
      if (g) g.style.opacity = k === i ? "1" : "0";
    });
    bar.querySelectorAll("button").forEach((b, k) => b.setAttribute("aria-pressed", String(k === i)));
  };
  labels.forEach((label, i) => {
    const btn = el("button", "ghost-btn", label);
    btn.type = "button";
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      setActive(i);
    });
    bar.append(btn);
  });
  setActive(0);
  plate.append(bar, el("div", "plate-number", page.caption || ""));
  return shell({ page, ctx, side, content: plate });
}

function barPage(page, ctx, side) {
  const plate = el("div", "plate");
  const holder = el("div", "figure-holder", DRAW.bar());
  plate.append(holder);

  const bar = el("div", "figure-controls");
  const eras = ["汉", "唐", "宋", "元", "明", "清"];
  const setActive = (i) => {
    holder.querySelectorAll(".fig-era").forEach((g) => {
      g.style.opacity = Number(g.dataset.era) === i ? "1" : "0.42";
    });
    bar.querySelectorAll("button").forEach((b, k) => b.setAttribute("aria-pressed", String(k === i)));
  };
  eras.forEach((label, i) => {
    const btn = el("button", "ghost-btn", label);
    btn.type = "button";
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      setActive(i);
    });
    bar.append(btn);
  });
  setActive(1);
  plate.append(bar, el("div", "plate-number", page.caption || ""));
  return shell({ page, ctx, side, content: plate });
}

/* ------------------------------------------------------------ 地图 */

function mapCard(host) {
  const card = el("div", "map-card");
  card.hidden = true;
  card.innerHTML = `
    <button class="close-mini" type="button" aria-label="收起">×</button>
    <h4></h4><div class="meta"></div><p class="body"></p><p class="detail"></p>
    <div class="links"></div>`;
  card.querySelector(".close-mini").addEventListener("click", (e) => {
    e.stopPropagation();
    card.hidden = true;
  });
  host.append(card);
  return card;
}

function fillCard(card, node) {
  card.hidden = false;
  card.classList.remove("is-in");
  void card.offsetWidth;
  card.classList.add("is-in");
  card.querySelector("h4").textContent = node.name;
  card.querySelector(".meta").textContent = node.sub;
  card.querySelector(".body").textContent = node.text;
  card.querySelector(".detail").textContent = node.detail;
  const links = card.querySelector(".links");
  links.innerHTML = "";
  (node.links || []).forEach((link) => {
    const a = document.createElement("a");
    a.href = link.href;
    a.textContent = link.label;
    a.target = link.href.startsWith("http") ? "_blank" : "_self";
    a.addEventListener("click", (e) => e.stopPropagation());
    links.append(a);
  });
}

function mapPage(page, ctx, side, mode) {
  const wrap = el("div", "map-page");
  const holder = el("div", "map-holder");
  wrap.append(holder);
  wrap.append(el("div", "map-hint", mode === "routes"
    ? "四条路线只是方向示意，年代与走向各有争议"
    : "点亮一处地名，看它长成了什么"));
  const card = mapCard(wrap);

  const face = shell({ page, ctx, side, content: wrap, extraClass: "page--map" });
  wrap.append(el("div", "plate-number", page.caption || ""));

  const attach = (geo) => {
    holder.innerHTML = buildMapSvg(geo, mode);
    holder.querySelectorAll(".map-node").forEach((nodeEl) => {
      const id = nodeEl.dataset.node;
      const open = (e) => {
        e.stopPropagation();
        fillCard(card, ctx.nodeById(id));
        wrap.classList.add("has-card");
        holder.querySelectorAll(".map-node").forEach((n) => n.setAttribute("aria-pressed", "false"));
        nodeEl.setAttribute("aria-pressed", "true");
      };
      nodeEl.addEventListener("click", open);
      nodeEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") open(e);
      });
    });
  };

  loadLand()
    .then(attach)
    .catch((err) => {
      holder.innerHTML = `<p class="figure-error">地图素材未载入，请从本地预览地址打开。</p>`;
      console.error(err);
    });

  return face;
}

/* ------------------------------------------------------------ 拆解页 */

function explodePage(page, ctx, side) {
  const plate = el("div", "explode-cue");
  plate.innerHTML = `
    <div class="explode-art">
      <svg viewBox="0 0 200 260" aria-hidden="true">
        <g stroke="rgba(52,42,30,0.6)" fill="#cda878">
          <rect x="60" y="196" width="80" height="14"/>
          <rect x="52" y="170" width="96" height="12" fill="#bc9463"/>
          <rect x="44" y="146" width="112" height="12" fill="#cda878"/>
          <rect x="56" y="122" width="88" height="10" fill="#a9814f"/>
          <rect x="70" y="100" width="60" height="10" fill="#cda878"/>
          <path d="M40 96 L100 60 L160 96" fill="none" stroke-width="1.2"/>
        </g>
        <g stroke="#9e3527" stroke-width="1" stroke-dasharray="3 4" fill="none">
          <path d="M100 210 V246"/>
          <path d="M100 66 V30"/>
        </g>
      </svg>
    </div>
    <p class="explode-copy">拖动滑杆，让构件各自退开半步；<br>再点构件，看它叫什么。</p>
    <button class="big-btn" type="button">把 这 一 朵 拆 开</button>`;

  plate.querySelector(".big-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    openBracket({ category: "all", anchor: e.currentTarget, explode: 0.5 });
  });

  plateNumber(plate, page);
  return shell({ page, ctx, side, content: plate });
}

/* ------------------------------------------------------------ 图版索引 */

function indexPage(page, ctx, side) {
  const plate = el("div", "index-plates");
  const entries = [
    { label: "图一 檐下", page: 4 },
    { label: "图二 河姆渡", page: 6 },
    { label: "图三 三力", page: 10 },
    { label: "图四 三台阶", page: 12 },
    { label: "图五 出檐", page: 14 },
    { label: "图六 四段线稿", page: 16 },
    { label: "图七 一朵斗拱", page: 18 },
    { label: "图八 朝代表", page: 26 },
    { label: "图九 同比例", page: 28 },
    { label: "图十 此消彼长", page: 30 },
    { label: "图十一 东亚地图", page: 32 },
    { label: "图十二 四条路", page: 34 },
    { label: "图十三 当代回声", page: 36 },
    { label: "图十四 抬头", page: 38 },
  ];
  entries.forEach((entry) => {
    const cell = el("button", "index-plate");
    cell.type = "button";
    cell.innerHTML = `<span>${entry.label}</span>`;
    cell.addEventListener("click", (e) => {
      e.stopPropagation();
      ctx.jumpTo(entry.page);
    });
    plate.append(cell);
  });
  plate.append(el("div", "plate-number", page.caption || ""));
  return shell({ page, ctx, side, content: plate, extraClass: "page--index-plates" });
}

/* ------------------------------------------------------------ 分发 */

export function renderPage(page, ctx, side) {
  switch (page.kind) {
    case "cover":
      return coverPage(page);
    case "contents":
      return contentsPage(page, ctx, side);
    case "text":
      return textPage(page, ctx, side);
    case "chapter":
      return chapterPage(page, ctx, side);
    case "plate":
      return platePage(page, ctx, side);
    case "figure":
      return figurePage(page, ctx, side);
    case "model-grid":
      return modelGridPage(page, ctx, side);
    case "parts":
      return partsPage(page, ctx, side);
    case "quiz":
      return quizPage(page, ctx, side);
    case "table":
      return tablePage(page, ctx, side);
    case "compare":
      return comparePage(page, ctx, side);
    case "bar":
      return barPage(page, ctx, side);
    case "map":
      return mapPage(page, ctx, side, "nodes");
    case "routes":
      return mapPage(page, ctx, side, "routes");
    case "explode":
      return explodePage(page, ctx, side);
    case "index":
      return indexPage(page, ctx, side);
    default:
      return textPage(page, ctx, side);
  }
}

/* 竖排版面自适应：若列超出可用宽度，逐级缩小字号，直到整段装进版框。
   竖排里 scrollWidth 就是所有列的总宽，超了就是被裁掉。 */
export function fitText(root) {
  root.querySelectorAll(".verso").forEach((box) => {
    box.style.fontSize = "";
    let size = parseFloat(getComputedStyle(box).fontSize);
    let guard = 0;
    while (box.scrollWidth > box.clientWidth + 1 && size > 9 && guard < 40) {
      size -= 0.3;
      box.style.fontSize = `${size.toFixed(2)}px`;
      guard += 1;
    }
  });
}

/* 书耳「器」按钮要打开什么，由页面类型决定 */
export function modelTargetFor(page) {
  if (page.kind === "model-grid") {
    return {
      label: "看四种榫卯",
      run: (anchor) => openMortise(page.items[0].key, { anchor }),
    };
  }
  if (page.kind === "parts") {
    return {
      label: "看六构件",
      run: (anchor) => openBracket({ category: "dou", anchor }),
    };
  }
  if (page.kind === "plate" && (page.hotspots || []).length) {
    return {
      label: "看三维",
      run: (anchor) => openBracket({ category: page.hotspots[0].category || "all", anchor }),
    };
  }
  if (page.kind === "explode") {
    return {
      label: "拆开这一朵",
      run: (anchor) => openBracket({ category: "all", anchor, explode: 0.5 }),
    };
  }
  if (page.kind === "quiz") {
    return {
      label: "看这一朵",
      run: (anchor) => openBracket({ category: "ang", anchor, explode: 0.15 }),
    };
  }
  return null;
}
