/* 木构之间 · 从书页里跳出来的三维浮层
   卡片、展台、滑杆、构件分类条、目录与夹注面板
   ------------------------------------------------------------------ */

import * as THREE from "three";
import { createStage, frameObject, woodMaterial } from "./gl.js";
import { buildMortise, MORTISE_META } from "./mortise.js";
import { createBracket, CATEGORIES } from "./dougong.js";

let shell = null;
let activeStage = null;
let activeModel = null;

function el(tag, className, html) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (html != null) node.innerHTML = html;
  return node;
}

function buildShell() {
  const overlay = el("div", "overlay");
  overlay.id = "overlay";
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.innerHTML = `
    <div class="card">
      <div class="card-head">
        <div class="card-title"><h2></h2><p></p></div>
        <button class="card-close" type="button" aria-label="合上">×</button>
      </div>
      <div class="card-body"></div>
    </div>`;
  document.body.append(overlay);

  const api = {
    overlay,
    card: overlay.querySelector(".card"),
    head: overlay.querySelector(".card-title h2"),
    sub: overlay.querySelector(".card-title p"),
    body: overlay.querySelector(".card-body"),
    close() {
      overlay.classList.remove("is-open");
      window.setTimeout(() => {
        if (activeStage) {
          activeStage.dispose();
          activeStage = null;
          activeModel = null;
        }
        api.body.innerHTML = "";
      }, 240);
      document.body.dataset.overlay = "closed";
    },
    open() {
      overlay.classList.add("is-open");
      document.body.dataset.overlay = "open";
    },
  };

  overlay.querySelector(".card-close").addEventListener("click", () => api.close());
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) api.close();
  });
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && overlay.classList.contains("is-open")) api.close();
  });

  return api;
}

function getShell() {
  if (!shell) shell = buildShell();
  return shell;
}

function placeOrigin(anchor) {
  const s = getShell();
  if (!anchor) {
    s.card.style.setProperty("--ox", "50%");
    s.card.style.setProperty("--oy", "50%");
    return;
  }
  const r = anchor.getBoundingClientRect();
  const c = s.card.getBoundingClientRect();
  const ox = ((r.left + r.width / 2 - c.left) / c.width) * 100;
  const oy = ((r.top + r.height / 2 - c.top) / c.height) * 100;
  s.card.style.setProperty("--ox", `${Math.max(-20, Math.min(120, ox))}%`);
  s.card.style.setProperty("--oy", `${Math.max(-20, Math.min(120, oy))}%`);
}

/* 展台骨架：左三维，右说明（两块直接挂在 card-body 上，才能进两列栅格） */
function stageBody({ badge, hint, side, actions }) {
  const wrap = el("div", "stage-host");
  wrap.innerHTML = `
    <div class="stage-badge">${badge}</div>
    <div class="stage-hint">${hint}</div>
    <div class="stage-loading">模 型 载 入 中</div>`;
  const sideBox = el("div", "card-side", side);
  if (actions) sideBox.append(actions);
  return { wrap, sideBox };
}

function makeStage(wrap) {
  if (activeStage) {
    activeStage.dispose();
    activeStage = null;
  }
  activeStage = createStage(wrap, { distance: 4.6 });
  const loading = wrap.querySelector(".stage-loading");
  if (loading) loading.hidden = true;
  return activeStage;
}

function slider(label, min, max, value, step, onInput) {
  const row = el("div", "slider-row");
  const lo = el("span", "", label[0]);
  const hi = el("span", "", label[1]);
  const input = document.createElement("input");
  input.type = "range";
  input.min = String(min);
  input.max = String(max);
  input.step = String(step);
  input.value = String(value);
  input.addEventListener("input", () => onInput(Number(input.value)));
  row.append(lo, input, hi);
  return { row, input };
}

/* ------------------------------------------------------------ 榫卯 */

export function openMortise(key, { anchor, onSwitch } = {}) {
  const s = getShell();
  const meta = MORTISE_META[key] || { name: "榫卯", pinyin: "", use: "" };

  s.head.textContent = meta.name;
  s.sub.textContent = `${meta.pinyin} · ${meta.use}`;

  const actions = el("div", "card-actions");
  const resetBtn = el("button", "ghost-btn", "复位视角");
  resetBtn.type = "button";
  actions.append(resetBtn);

  const { wrap, sideBox } = stageBody({
    badge: meta.name,
    hint: "拖动旋转 · 双指缩放",
    side: `
      <div class="side-verse">${sideTextFor(key)}</div>
      <dl class="side-notes">
        <dt>怎么读它</dt>
        <dd>${hintFor(key)}</dd>
        <dt>口径</dt>
        <dd>模型据形制示意建模，尺寸与出土原件不同；只用于说明原理。</dd>
      </dl>`,
    actions,
  });
  s.body.innerHTML = "";
  s.body.append(wrap, sideBox);

  placeOrigin(anchor);
  s.open();

  const stage = makeStage(wrap);
  const model = buildMortise(key);
  activeModel = model;
  stage.scene.add(model.group);
  frameObject(stage.camera, stage.controls, model.group, 1.45);

  const slide = slider(["拉开", "合拢"], 0, 1, 0.55, 0.01, (v) => {
    model.setOpenAmount(v);
  });
  model.setOpenAmount(0.55);
  sideBox.insertBefore(slide.row, actions);

  resetBtn.addEventListener("click", () => frameObject(stage.camera, stage.controls, model.group, 1.35));

  if (model.allowRock) {
    const rock = el("button", "ghost-btn", "试转一下柱头");
    rock.type = "button";
    let on = false;
    rock.addEventListener("click", () => {
      on = !on;
      rock.setAttribute("aria-pressed", String(on));
      model.moving.rotation.y = on ? 0.18 : 0;
      model.group.rotation.y = on ? 0.12 : 0;
    });
    actions.append(rock);
  }

  if (onSwitch) {
    const next = el("button", "ghost-btn", "换一种榫卯");
    next.type = "button";
    next.addEventListener("click", () => {
      onSwitch();
    });
    actions.append(next);
  }

  /* 一进来先缓缓合上，让人看见榫头是怎么进去的 */
  window.setTimeout(() => {
    slide.input.value = "1";
    slide.input.dispatchEvent(new Event("input"));
  }, 900);
}

function sideTextFor(key) {
  const map = {
    zhisun:
      "最基础的一种。<strong>榫头</strong>方直，插入<strong>卯口</strong>，靠两侧壁面抵抗错动。做法简单，但抗拔能力一般，所以常配销钉。",
    yanwei:
      "端部做成梯形，<strong>越拉越紧</strong>。拔出的力越大，斜面把力转成挤压，反而锁得更死。多见于抽屉、箱柜与梁枋接头。",
    qikou:
      "板边一凸一凹，互相嵌合。它限制的是<strong>板与板之间的错动和翘曲</strong>，同时把缝隙拉长，减少漏风漏雨。",
    mantou:
      "柱头的圆形榫头落入梁底的圆卯。<strong>只限位，不锁死</strong>，柱与梁可以轻微转动——这正是木构能卸掉一部分地震能量的原因之一。",
  };
  return map[key] || "";
}

function hintFor(key) {
  const map = {
    zhisun: "拖动滑杆看榫头推入；注意侧面贴合的那一条线，那是承担剪力的地方。",
    yanwei: "拖动滑杆上下移动；试着从斜角观察两块斜颊如何卡住梯形端头。",
    qikou: "拖动滑杆让两板靠近；拼缝处的凸舌比板面略薄，是为了留出胀缩余地。",
    mantou: "拖动滑杆让梁落下；再点「试转一下柱头」，看圆榫允许的那一点转动。",
  };
  return map[key] || "";
}
/* ------------------------------------------------------------ 斗拱 */

export async function openBracket({ category = "all", anchor, explode = 0, onNote } = {}) {
  const s = getShell();
  s.card.className = "card";
  s.head.textContent = "一朵斗拱";
  s.sub.textContent = "保国寺柱头铺作形制草模 · 点构件看名字";

  const actions = el("div", "card-actions");
  const resetBtn = el("button", "ghost-btn", "复位视角");
  resetBtn.type = "button";
  actions.append(resetBtn);

  const { wrap, sideBox } = stageBody({
    badge: "斗 · 拱 · 昂",
    hint: "拖动旋转 · 双指缩放 · 点构件识别",
    side: `
      <div class="side-verse">
        一朵斗拱，可以拆成许多名字。<strong>斗</strong>是垫块，<strong>拱</strong>是弓形短木，
        <strong>昂</strong>斜伸出去像杠杆。<strong>翘</strong>沿进深出跳（宋式称华栱），
        <strong>耍头</strong>在最上层收住整朵，<strong>枋</strong>把一朵朵连成圈。
      </div>
      <dl class="side-notes">
        <dt>操作</dt>
        <dd>点下面的构件名，只看那一类；再点一次「整朵」复原。拖滑杆可以拆解。</dd>
        <dt>口径</dt>
        <dd>模型为形制草模，榫卯细部与尺寸待核；命名依宋《营造法式》。</dd>
      </dl>`,
    actions,
  });
  s.body.innerHTML = "";
  s.body.append(wrap, sideBox);

  const partsBar = el("div", "parts-bar");
  CATEGORIES.forEach((cat) => {
    const chip = el("button", "part-chip", cat.label);
    chip.type = "button";
    chip.dataset.cat = cat.key;
    chip.setAttribute("aria-pressed", String(cat.key === category));
    chip.addEventListener("click", () => {
      partsBar.querySelectorAll(".part-chip").forEach((b) => b.setAttribute("aria-pressed", "false"));
      chip.setAttribute("aria-pressed", "true");
      if (bracket) {
        bracket.setCategory(cat.key);
        s.sub.textContent = bracket.categoryNote(cat.key) || "保国寺柱头铺作形制草模 · 点构件看名字";
      }
    });
    partsBar.append(chip);
  });
  wrap.append(partsBar);

  placeOrigin(anchor);
  s.open();
  s.sub.textContent = "模型载入中…";

  const stage = makeStage(wrap);
  let bracket = null;

  try {
    bracket = await createBracket();
    activeModel = bracket;
    stage.scene.add(bracket.group);
    frameObject(stage.camera, stage.controls, bracket.group, 1.08);
    bracket.setCategory(category);
    bracket.setExplode(explode);
    s.sub.textContent = "点一件构件，看它叫什么";
    if (onNote) onNote(bracket);
  } catch (err) {
    s.sub.textContent = "三维素材未能载入，请从本地预览地址打开";
    console.error(err);
    return;
  }

  const slide = slider(["合拢", "拆开"], 0, 1, explode, 0.01, (v) => {
    bracket.setExplode(v);
  });
  sideBox.insertBefore(slide.row, actions);

  resetBtn.addEventListener("click", () => {
    frameObject(stage.camera, stage.controls, bracket.group, 1.08);
    bracket.highlightMesh(null);
  });

  /* 点选识别：拖动不算点击 */
  const dom = stage.renderer.domElement;
  let downAt = null;
  dom.addEventListener("pointerdown", (e) => {
    downAt = { x: e.clientX, y: e.clientY };
  });
  dom.addEventListener("pointerup", (e) => {
    if (!downAt) return;
    const moved = Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y);
    downAt = null;
    if (moved > 8) return;

    const rect = dom.getBoundingClientRect();
    const pointer = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );
    const ray = new THREE.Raycaster();
    ray.setFromCamera(pointer, stage.camera);
    const hit = ray.intersectObjects(bracket.meshes, false)[0];
    if (!hit) {
      bracket.highlightMesh(null);
      s.sub.textContent = "点一件构件，看它叫什么";
      return;
    }
    bracket.highlightMesh(hit.object);
    const cn = hit.object.userData.cn || "构件";
    s.sub.textContent = `${cn} · 再点空白处取消`;
  });

  dom.style.touchAction = "none";
}

/* ------------------------------------------------------------ 文字面板 */

function openPanel({ title, subtitle, className, inner, anchor }) {
  const s = getShell();
  s.card.className = `card ${className || ""}`.trim();
  s.head.textContent = title;
  s.sub.textContent = subtitle || "";
  s.body.innerHTML = "";
  const box = el("div", className === "index-card" ? "index-list" : "notes-verse", inner);
  s.body.append(box);
  placeOrigin(anchor);
  s.open();
  return box;
}

export function openNotes({ title, notes, sources, anchor }) {
  const notesHtml = (notes || []).map((n) => `<p>${n}</p>`).join("");
  const sourcesHtml = (sources || []).length
    ? `<h3>依据</h3>${sources.map((n) => `<p>${n}</p>`).join("")}`
    : "";
  return openPanel({
    title: title || "夹注",
    subtitle: "页边小字：辨误、出处与待核",
    className: "notes-card",
    inner: `${notesHtml}${sourcesHtml}`,
    anchor,
  });
}

export function openIndex({ items, current, onJump, anchor }) {
  const box = openPanel({
    title: "目次",
    subtitle: "点一条，翻到那一页",
    className: "index-card",
    inner: "",
    anchor,
  });
  items.forEach((item) => {
    const btn = el("button", "index-item");
    btn.type = "button";
    btn.innerHTML = `<span class="num">${String(item.page).padStart(2, "0")}</span>
      <span class="vol">${item.vol}</span><span class="name">${item.name}</span>`;
    if (current != null && item.page === current) btn.classList.add("is-current");
    btn.addEventListener("click", () => {
      const s = getShell();
      s.close();
      onJump(item.page);
    });
    box.append(btn);
  });
  return box;
}

export function closePopup() {
  if (shell) shell.close();
}
