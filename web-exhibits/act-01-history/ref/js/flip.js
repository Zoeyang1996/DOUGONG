/* 木构之间 · 翻页
   叶片绕书脊旋转；翻动时用「分段折弯」的替身，让纸面有受力弯曲与明暗。
   ------------------------------------------------------------------ */

import { PAGES, renderPage } from "./pages.js";

export const PW = 980;
export const PH = 1360;

const LEAVES = Math.ceil(PAGES.length / 2);
const SLABS = 5;
const SLAB_W = PW / SLABS;
const CURL = 24;          // 最大折弯角（度）
const FLIP_MS = 880;
const DRAG_START = 6;     // 起判像素
const COMMIT = 0.3;       // 松手后判定翻过去的比例

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

function el(tag, cls) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  return n;
}

export function createBook({ bookEl, stageEl, leavesEl, castEl, hintEl }) {
  let turned = 0;
  let busy = false;
  let previewP = null;      // 拖动中的进度
  const leaves = [];

  /* ---------------------------------------------------------- 建页 */

  for (let k = 0; k < LEAVES; k += 1) {
    const leaf = el("div", "leaf");
    leaf.dataset.k = String(k);

    const front = el("div", "face face--front");
    front.innerHTML = renderPage(PAGES[k * 2]);
    const back = el("div", "face face--back");
    if (PAGES[k * 2 + 1]) back.innerHTML = renderPage(PAGES[k * 2 + 1]);

    leaf.append(front, back);
    leavesEl.append(leaf);
    leaves.push(leaf);
  }

  /* ---------------------------------------------------------- 静态排布 */

  function layout() {
    leaves.forEach((leaf, k) => {
      leaf.style.transform = k < turned ? "rotateY(-180deg)" : "rotateY(0deg)";
      leaf.style.zIndex = String(k < turned ? 200 + k : 200 + (LEAVES - k));
    });
    stageEl.style.setProperty("--tx", turned === 0 ? `${-PW / 2}px` : "0px");
    castEl.style.opacity = "0";
  }

  /* ---------------------------------------------------------- 折弯替身 */

  function buildGhost(k) {
    const ghost = el("div", "ghost");
    ghost.style.setProperty("--shade", "0.28");

    const makeChain = (mirror) => {
      const chain = el("div", "ghost__chain");
      const page = PAGES[k * 2 + (mirror ? 1 : 0)];
      const html = page ? renderPage(page) : "";
      const slabs = [];
      for (let i = 0; i < SLABS; i += 1) {
        const slab = el("div", "ghost__slab");
        slab.style.width = `${SLAB_W + 0.6}px`;
        const slice = el("div", "ghost__slice");
        slice.style.left = `${-i * SLAB_W}px`;
        if (mirror) slice.style.transform = "scaleX(-1)";
        slice.innerHTML = html;
        slab.append(slice);
        chain.append(slab);
        slabs.push(slab);
      }
      chain.dataset.slabs = "1";
      chain.slabs = slabs;
      return chain;
    };

    const front = makeChain(false);
    const back = makeChain(true);
    back.style.display = "none";
    ghost.append(front, back);
    ghost.chains = { front, back };
    return ghost;
  }

  function paint(ghost, p) {
    const angle = -180 * p;
    const curl = Math.sin(Math.PI * clamp(p, 0, 1)) * CURL;
    const isBack = p > 0.5;
    ghost.chains.front.style.display = isBack ? "none" : "block";
    ghost.chains.back.style.display = isBack ? "block" : "none";

    const chain = isBack ? ghost.chains.back : ghost.chains.front;
    let x = 0;
    let z = 0;
    chain.slabs.forEach((slab, i) => {
      const a = angle + (i / (SLABS - 1)) * curl;
      const rad = (a * Math.PI) / 180;
      slab.style.transform = `translate3d(${x.toFixed(2)}px,0,${z.toFixed(2)}px) rotateY(${a.toFixed(2)}deg)`;
      x += SLAB_W * Math.cos(rad);
      z += -SLAB_W * Math.sin(rad);
    });

    const lit = Math.abs(Math.cos((angle * Math.PI) / 180));
    ghost.style.setProperty("--shade", (0.18 + 0.45 * (1 - lit)).toFixed(3));
    castEl.style.opacity = (Math.sin(Math.PI * clamp(p, 0, 1)) * 0.5).toFixed(3);
    castEl.style.transform = `scaleX(${(0.35 + 0.65 * p).toFixed(3)})`;
  }

  /* ---------------------------------------------------------- 时间轴 */

  function animate(from, to, ghost, done) {
    const dur = Math.max(140, FLIP_MS * Math.abs(to - from));
    const t0 = performance.now();
    const step = (now) => {
      const t = clamp((now - t0) / dur, 0, 1);
      const p = from + (to - from) * easeInOut(t);
      paint(ghost, p);
      if (t < 1) requestAnimationFrame(step);
      else {
        ghost.remove();
        busy = false;
        done();
      }
    };
    requestAnimationFrame(step);
  }

  /* ---------------------------------------------------------- 翻页 */

  function forward(from = 0) {
    if (busy || turned >= LEAVES) return;
    busy = true;
    const k = turned;
    const ghost = buildGhost(k);
    leavesEl.append(ghost);
    leaves[k].style.visibility = "hidden";
    animate(from, 1, ghost, () => {
      leaves[k].style.visibility = "";
      turned = k + 1;
      layout();
    });
  }

  function backward(from = 1) {
    if (busy || turned <= 0) return;
    busy = true;
    const k = turned - 1;
    const ghost = buildGhost(k);
    leavesEl.append(ghost);
    leaves[k].style.visibility = "hidden";
    animate(from, 0, ghost, () => {
      leaves[k].style.visibility = "";
      turned = k;
      layout();
    });
  }

  /* ---------------------------------------------------------- 拖动 */

  let drag = null;

  bookEl.addEventListener("pointerdown", (e) => {
    if (busy) return;
    const rect = bookEl.getBoundingClientRect();
    const mid = rect.left + rect.width / 2;
    drag = {
      x: e.clientX,
      y: e.clientY,
      forward: e.clientX >= mid,
      moved: false,
      ghost: null,
      p: 0,
    };
  });

  window.addEventListener("pointermove", (e) => {
    if (!drag || busy) return;
    const dx = e.clientX - drag.x;
    const dy = e.clientY - drag.y;
    if (!drag.moved) {
      if (Math.abs(dx) < DRAG_START || Math.abs(dx) < Math.abs(dy)) return;
      if (drag.forward && turned >= LEAVES) return;
      if (!drag.forward && turned <= 0) return;
      drag.moved = true;
      drag.ghost = buildGhost(drag.forward ? turned : turned - 1);
      leavesEl.append(drag.ghost);
      const k = drag.forward ? turned : turned - 1;
      leaves[k].style.visibility = "hidden";
      bookEl.setPointerCapture?.(e.pointerId);
      hintEl.dataset.hidden = "1";
    }
    const raw = drag.forward ? -dx / PW : 1 - dx / PW;
    drag.p = clamp(raw, 0, 1);
    previewP = drag.p;
    paint(drag.ghost, drag.p);
  });

  function endDrag(e) {
    if (!drag || busy) return;
    const d = drag;
    drag = null;
    previewP = null;

    if (!d.moved) {
      if (d.forward) forward(0);
      else backward(1);
      return;
    }

    busy = true;
    const k = d.forward ? turned : turned - 1;
    const to = d.p > COMMIT ? 1 : 0;
    const done = () => {
      leaves[k].style.visibility = "";
      turned = d.forward ? (to === 1 ? k + 1 : k) : to === 1 ? k + 1 : k;
      layout();
    };
    animate(d.p, to, d.ghost, done);
  }

  window.addEventListener("pointerup", endDrag);
  window.addEventListener("pointercancel", endDrag);

  /* ---------------------------------------------------------- 键盘 */

  window.addEventListener("keydown", (e) => {
    if (["ArrowLeft", "PageDown", " "].includes(e.key)) {
      e.preventDefault();
      forward(0);
    }
    if (["ArrowRight", "PageUp"].includes(e.key)) {
      e.preventDefault();
      backward(1);
    }
  });

  layout();

  /* 调试：?spread=n 直接翻到第 n 跨页；?p=0.4 定格半程看折弯 */
  const qs = new URLSearchParams(location.search);
  if (qs.has("spread")) {
    turned = clamp(Number(qs.get("spread")) || 0, 0, LEAVES);
    layout();
  }
  if (qs.has("p")) {
    const p = clamp(Number(qs.get("p")) || 0, 0, 1);
    const g = buildGhost(Math.min(turned, LEAVES - 1));
    leavesEl.append(g);
    if (leaves[turned]) leaves[turned].style.visibility = "hidden";
    paint(g, p);
  }

  return {
    next: () => forward(0),
    prev: () => backward(1),
    get turned() { return turned; },
    total: LEAVES,
  };
}
