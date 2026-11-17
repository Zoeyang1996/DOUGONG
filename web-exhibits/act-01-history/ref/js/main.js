import { createBook, PW, PH } from "./flip.js";

const bookEl = document.getElementById("book");
const stageEl = bookEl.querySelector(".book__stage");
const leavesEl = bookEl.querySelector(".book__leaves");
const castEl = bookEl.querySelector(".book__cast");
const hintEl = document.getElementById("hint");

createBook({ bookEl, stageEl, leavesEl, castEl, hintEl });

/* 开本按视口缩放；留一点呼吸，别顶到屏幕边 */
function fit() {
  const s = Math.min(
    (window.innerWidth - 72) / (PW * 2),
    (window.innerHeight - 64) / PH
  );
  bookEl.style.setProperty("--s", Math.max(0.2, s).toFixed(4));
}

fit();
window.addEventListener("resize", fit);

/* 首次交互后提示淡出 */
bookEl.addEventListener("pointerdown", () => {
  hintEl.dataset.hidden = "1";
}, { once: true });

/* 调试：?p=0.42 定格半程，方便看折弯与明暗 */
const debugP = new URLSearchParams(location.search).get("p");
if (debugP) {
  window.__freeze = Number(debugP);
}

if (location.search.includes("debug")) {
  setTimeout(() => {
    const r = bookEl.getBoundingClientRect();
    const body = document.querySelector(".body");
    const cs = body ? getComputedStyle(body) : null;
    const br = body ? body.getBoundingClientRect() : null;
    const plate = document.querySelector(".plate");
    const pr = plate ? plate.getBoundingClientRect() : null;
    document.title = `vp ${innerWidth}x${innerHeight} book ${Math.round(r.width)} left ${Math.round(r.left)} | body fs ${cs && cs.fontSize} lh ${cs && cs.lineHeight} w ${br && Math.round(br.width)} h ${br && Math.round(br.height)} | plate ${pr && Math.round(pr.width)}x${pr && Math.round(pr.height)}`;
  }, 900);
}
