import { el, pad } from './dom.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

/**
 * 地名签：由细引线连到朱点，纵向自动避让，并尽量对齐成一列，
 * 像旧地图边缘的图版注记。
 */
export function createLabels({ layer, leaderHost, onPick }) {
  let entries = [];
  let widths = [];

  function setPoints(points, selected, order) {
    layer.replaceChildren();
    leaderHost.replaceChildren();
    entries = [];
    widths = [];

    points.forEach((item) => {
      const number = order && order.has(item.id) ? order.get(item.id) : 0;
      const button = el(
        'button',
        {
          class: 'map-label' + (selected && selected.id === item.id ? ' selected' : ''),
          type: 'button',
          'aria-label': '查看' + item.name,
          onClick: () => onPick(item),
        },
        el('span', { class: 'idx', text: pad(number) }),
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

    const spacing = view.width < 540 ? 32 : 36;
    const stageWidth = view.width;
    const stageHeight = view.height;
    const topPad = 74;
    const placed = [];

    entries.forEach((entry, index) => {
      const projection = view.project(entry.item.lat, entry.item.lon);
      entry.x = projection.x;
      entry.y = projection.y;
      if (projection.front && projection.y > -24 && projection.y < stageHeight + 24) {
        placed.push({ index, anchorX: projection.x, anchorY: projection.y, y: projection.y });
      }
    });

    placed.sort((a, b) => a.anchorY - b.anchorY);

    // 注记自上而下排成一列，像图版侧栏的注记
    placed.forEach((slot, index) => {
      slot.y = topPad + index * spacing;
    });

    // 栏位贴住舞台右缘：引线自海面引出，不压住大陆
    const maxWidth = Math.max(...widths, 90);
    const columnX = Math.max(8, stageWidth - maxWidth - 12);

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
