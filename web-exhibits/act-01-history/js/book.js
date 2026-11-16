/* 木构之间 · 翻页引擎
   中式直排书：书页从左边掀起，越过书脊落到右半边
   叶片 k：正面 = 第 2k 页（左槽），背面 = 第 2k+1 页（翻过去后落在右槽）

   宽屏：一次摊开两页（右页先读，左页后读）
   窄屏：一次只摊开一页，书整体左右平移，把当前页挪到中间
   ------------------------------------------------------------------ */

import { PAGES } from "./content.js";
import { renderPage, modelTargetFor, fitText, el } from "./pages.js";
import { nodeById } from "./map.js";

const FLIP_MS = 980;
const DRAG_THRESHOLD = 0.32;
const SOLO_QUERY = "(max-width: 900px)";

export function initBook(root, { onChange } = {}) {
  const totalLeaves = Math.ceil(PAGES.length / 2);
  let spread = 0;          // 已翻过的叶片数
  let slot = "left";       // 单页模式：当前看的是左槽还是右槽
  let animating = false;
  let solo = window.matchMedia(SOLO_QUERY).matches;

  const book = el("div");
  book.id = "book";
  book.append(el("div", "crease"));

  const ctx = {
    currentIndex: 0,
    jumpTo: (pageIndex) => goToPage(pageIndex),
    modelTargetFor,
    nodeById,
  };

  const leaves = [];
  for (let k = 0; k < totalLeaves; k += 1) {
    const leaf = el("div", "leaf");
    leaf.dataset.leaf = String(k);

    const front = el("div", "face face--front");
    if (PAGES[k * 2]) front.append(renderPage(PAGES[k * 2], ctx, "left"));
    const back = el("div", "face face--back");
    if (PAGES[k * 2 + 1]) back.append(renderPage(PAGES[k * 2 + 1], ctx, "right"));

    front.append(el("div", "turn-shade"));
    back.append(el("div", "turn-shade"));
    leaf.append(front, back);
    book.append(leaf);
    leaves.push(leaf);
  }

  root.append(book);
  fitText(book);

  /* 视口变化：版面字级跟着开本走，重新拟合一次 */
  let refitTimer = 0;
  window.addEventListener("resize", () => {
    window.clearTimeout(refitTimer);
    refitTimer = window.setTimeout(() => fitText(book), 180);
  });

  /* ---------------------------------------------------------- 页面索引 */

  function pageIndex() {
    if (spread === 0) return 0;
    if (!solo) return spread * 2;                 // 宽屏：右页为当前页
    return slot === "right" ? spread * 2 - 1 : spread * 2;
  }

  /* ---------------------------------------------------------- 状态 */

  function setZ() {
    leaves.forEach((leaf, k) => {
      if (k < spread) leaf.style.zIndex = String(100 + k);
      else leaf.style.zIndex = String(100 + (totalLeaves - k));
    });
  }

  function applyLeaf(k, turned, animate) {
    const leaf = leaves[k];
    leaf.style.transitionDuration = animate ? `${FLIP_MS}ms` : "0ms";
    leaf.style.transform = turned ? "rotateY(180deg)" : "rotateY(0deg)";
    leaf.dataset.turned = turned ? "1" : "0";
  }

  function sync(animate = true) {
    leaves.forEach((leaf, k) => applyLeaf(k, k < spread, animate));
    setZ();
    const closed = spread === 0 && (!solo || slot === "left");
    document.body.dataset.state = closed ? "closed" : "open";
    document.body.dataset.slot = solo ? slot : "spread";

    const idx = pageIndex();
    ctx.currentIndex = idx;
    if (onChange) {
      onChange({
        spread,
        pageIndex: idx,
        totalSpread: solo ? PAGES.length - 1 : totalLeaves,
        step: solo ? idx : spread,
        rightPage: PAGES[idx] || null,
        leftPage: solo ? null : PAGES[spread * 2] || null,
        solo,
      });
    }
  }

  function settle() {
    window.setTimeout(() => {
      animating = false;
      sync(false);
    }, FLIP_MS);
  }

  /* ---------------------------------------------------------- 翻页 */

  function next() {
    if (animating) return;

    if (solo) {
      if (slot === "right") {
        slot = "left";
        sync(true);
        return;
      }
      if (spread >= totalLeaves) return;
      animating = true;
      const leaf = leaves[spread];
      leaf.style.zIndex = "1500";
      applyLeaf(spread, true, true);
      spread += 1;
      slot = "right";
      sync(true);
      settle();
      return;
    }

    if (spread >= totalLeaves) return;
    animating = true;
    const leaf = leaves[spread];
    leaf.style.zIndex = "1500";
    applyLeaf(spread, true, true);
    spread += 1;
    sync(true);
    settle();
  }

  function prev() {
    if (animating) return;

    if (solo) {
      if (slot === "left") {
        if (spread <= 0) return;
        slot = "right";
        sync(true);
        return;
      }
      if (spread <= 0) return;
      animating = true;
      spread -= 1;
      const leaf = leaves[spread];
      leaf.style.zIndex = "1500";
      applyLeaf(spread, false, true);
      slot = "left";
      sync(true);
      settle();
      return;
    }

    if (spread <= 0) return;
    animating = true;
    spread -= 1;
    const leaf = leaves[spread];
    leaf.style.zIndex = "1500";
    applyLeaf(spread, false, true);
    sync(true);
    settle();
  }

  function goToPage(pageIndexTarget) {
    const p = Math.max(0, Math.min(pageIndexTarget, PAGES.length - 1));
    animating = true;
    if (p === 0) {
      spread = 0;
      slot = "left";
    } else if (solo) {
      spread = Math.ceil(p / 2);
      slot = p % 2 === 1 ? "right" : "left";
    } else {
      spread = Math.ceil(p / 2);
      slot = "left";
    }
    leaves.forEach((leaf, k) => applyLeaf(k, k < spread, false));
    setZ();
    window.setTimeout(() => {
      animating = false;
      sync(false);
    }, 60);
  }

  /* ---------------------------------------------------------- 拖页（宽屏） */

  const stage = document.getElementById("stage");
  let drag = null;

  stage.addEventListener("pointerdown", (e) => {
    if (solo || animating || document.body.dataset.overlay === "open") return;
    const rect = book.getBoundingClientRect();
    const pageW = rect.width / 2;
    const leftPage = rect.left;
    // 只从「左页的外口」起手，避免与页内交互抢手势
    if (e.clientX > leftPage + pageW * 0.93 && e.clientX < leftPage + pageW) {
      drag = { x: e.clientX };
    }
  });

  stage.addEventListener("pointermove", (e) => {
    if (!drag) return;
    if (spread >= totalLeaves) return;
    const rect = book.getBoundingClientRect();
    const pageW = rect.width / 2;
    const dx = e.clientX - drag.x;
    if (dx <= 2) return;
    const leaf = leaves[spread];
    const progress = Math.min(1, dx / pageW);
    leaf.style.transitionDuration = "0ms";
    leaf.style.transform = `rotateY(${progress * 180}deg)`;
    leaf.style.zIndex = "1500";
    drag.leaf = leaf;
    drag.progress = progress;
  });

  stage.addEventListener("pointerup", () => {
    if (!drag) return;
    const { leaf, progress } = drag;
    drag = null;
    if (!leaf) return;
    animating = true;
    if ((progress || 0) > DRAG_THRESHOLD) {
      applyLeaf(spread, true, true);
      spread += 1;
    } else {
      applyLeaf(spread, false, true);
    }
    sync(true);
    settle();
  });

  stage.addEventListener("wheel", (e) => {
    if (document.body.dataset.overlay === "open") return;
    if (Math.abs(e.deltaY) < 12) return;
    if (e.deltaY > 0) next();
    else prev();
  }, { passive: true });

  window.addEventListener("keydown", (e) => {
    if (document.body.dataset.overlay === "open") return;
    if (["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) return;
    if (e.key === "ArrowLeft" || e.key === "PageDown" || e.key === " ") {
      e.preventDefault();
      next();
    }
    if (e.key === "ArrowRight" || e.key === "PageUp") {
      e.preventDefault();
      prev();
    }
    if (e.key === "Home") goToPage(1);
    if (e.key === "End") goToPage(PAGES.length - 2);
  });

  /* 封面上点一下即翻开 */
  book.addEventListener("click", (e) => {
    if (spread !== 0 || slot !== "left") return;
    if (e.target.closest(".cover")) next();
  });

  document.querySelector(".turn-zone--next")?.addEventListener("click", next);
  document.querySelector(".turn-zone--prev")?.addEventListener("click", prev);

  /* 跨过断点时切换模式：重排到同一页 */
  const mq = window.matchMedia(SOLO_QUERY);
  mq.addEventListener("change", (ev) => {
    const here = pageIndex();
    solo = ev.matches;
    goToPage(here);
  });

  sync(false);

  return { next, prev, goToPage, getSpread: () => spread, getPage: pageIndex, totalLeaves };
}
