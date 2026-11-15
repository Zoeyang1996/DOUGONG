import { el } from './dom.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

/**
 * 地名签：由细引线连到朱点，纵向自动避让，并尽量对齐成一列，
 * 像旧地图边缘的图版注记。只留建筑名，不再挂编号。
 */
export function createLabels({ layer, leaderHost, onPick }) {
  let entries = [];
  let widths = [];

  function setPoints(points, selected) {
    layer.replaceChildren();
    leaderHost.replaceChildren();
    entries = [];
    widths = [];

    points.forEach((item) => {
      const button = el(
        'button',
        {
          class: 'map-label' + (selected && selected.id === item.id ? ' selected' : ''),
          type: 'button',
          'aria-label': '查看' + item.name,
          onClick: () => onPick(item),
        },
        el('span', { text: item.name }),
      );

      const line = document.createElementNS(SVG_NS, 'line');
      const dot = document.createElementNS(SVG_NS, 'circle');
      dot.setAttribute('r', '1.6');

      layer.append(button);
      leaderHost.append(line, dot);
      entries.push({ item, button, line, dot, x: 0, y: 0 });
    });

    requestAnimationFrame(measure);
  }

  function measure() {
    widths = entries.map((entry) => entry.button.offsetWidth);
  }

  function update(view) {
    if (!view.width || !entries.length) return;

    const narrow = view.width < 540;
    const spacing = narrow ? 46 : 50;
    const stageRight = view.stageRight || view.width;
    const stageTop = view.stageTop || 0;
    const stageBottom = stageTop + (view.stageHeight || view.height);
    const topPad = stageTop + 24;
    // 右下角是缩放工具栏（窄屏 36px 高 + 44px 热区），标签列止于其上
    const bottomPad = stageBottom - (narrow ? 120 : 56);
    const placed = [];

    entries.forEach((entry, index) => {
      const projection = view.project(entry.item.lat, entry.item.lon);
      entry.x = projection.x;
      entry.y = projection.y;
      if (projection.front && projection.y > stageTop - 16 && projection.y < stageBottom + 16) {
        placed.push({ index, anchorX: projection.x, anchorY: projection.y, y: projection.y });
      }
    });

    placed.sort((a, b) => a.anchorY - b.anchorY);

    // 可用高度不够时压缩间距，保证整列仍在 topPad—bottomPad 之间
    const available = Math.max(0, bottomPad - topPad);
    const gap = placed.length > 1
      ? Math.min(spacing, available / (placed.length - 1))
      : spacing;

    // 每张签尽量贴住自己的锚点高度，再自上而下避让，引线就不会拉成斜长线
    placed.forEach((slot, index) => {
      const target = Math.min(Math.max(slot.anchorY, topPad), bottomPad);
      slot.y = index === 0 ? target : Math.max(target, placed[index - 1].y + gap);
    });

    // 整列平移一次：先按触底量上推，再按越顶量下压。
    // 只平移不求值，避免同一段偏移被重复叠加到同一张签上。
    const lastSlot = placed[placed.length - 1];
    const pushUp = lastSlot ? Math.max(0, lastSlot.y - bottomPad) : 0;
    if (pushUp) placed.forEach((slot) => { slot.y -= pushUp; });

    const topOverflow = placed.length ? Math.max(0, topPad - placed[0].y) : 0;
    if (topOverflow) placed.forEach((slot) => { slot.y += topOverflow; });

    // 栏位贴住舞台右缘：引线自球面引出，不压住大陆
    const maxWidth = Math.max(...widths, 88);
    const columnX = Math.max(8, stageRight - maxWidth - 12);

    const placedMap = new Map(placed.map((slot) => [slot.index, slot]));

    entries.forEach((entry, index) => {
      const slot = placedMap.get(index);
      if (!slot) {
        if (!entry.button.hidden) {
          entry.button.hidden = true;
          entry.line.style.display = 'none';
          entry.dot.style.display = 'none';
        }
        return;
      }

      const width = widths[index] || 96;
      const toRight = entry.x < columnX - 8;
      const left = toRight ? columnX : Math.max(6, entry.x - width - 26);

      entry.button.hidden = false;
      entry.button.style.left = Math.round(left) + 'px';
      entry.button.style.top = Math.round(slot.y) + 'px';

      entry.line.style.display = '';
      entry.dot.style.display = '';
      entry.line.setAttribute('x1', entry.x.toFixed(1));
      entry.line.setAttribute('y1', entry.y.toFixed(1));
      entry.line.setAttribute('x2', (toRight ? left : left + width).toFixed(1));
      entry.line.setAttribute('y2', slot.y.toFixed(1));
      entry.dot.setAttribute('cx', entry.x.toFixed(1));
      entry.dot.setAttribute('cy', entry.y.toFixed(1));
    });
  }

  return { setPoints, update };
}
