/* 木构之间 · 入口 */

import { initBook } from "./book.js";

const stage = document.getElementById("stage");
const fill = document.querySelector(".progress-fill");
const text = document.querySelector(".progress-text");

const book = initBook(stage, {
  onChange({ pageIndex, step, totalSpread, rightPage }) {
    if (fill) fill.style.width = `${Math.round((step / totalSpread) * 100)}%`;
    if (!text) return;
    if (pageIndex === 0) {
      text.textContent = "封面 · 轻触翻开";
      return;
    }
    const folio = rightPage?.folio || "";
    text.textContent = `${folio} — ${step} / ${totalSpread}`;
  },
});

/* 供本地检查脚本调用 */
window.__book = book;

window.setTimeout(() => {
  document.body.classList.add("is-ready");
}, 600);
