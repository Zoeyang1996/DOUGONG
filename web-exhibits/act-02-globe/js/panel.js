import { renderIntro } from './views/intro.js';
import { renderRegion } from './views/region.js';
import { renderDetail } from './views/detail.js';

/**
 * 左栏控制器：按状态选择版面，并把交互交回主控。
 */
export function createPanel({ contentHost, scrollHost, total, actions }) {
  function render(state) {
    const { country, era, selected, visible } = state;
    let nodes;

    if (selected) {
      nodes = renderDetail({
        item: selected,
        index: Math.max(0, visible.indexOf(selected)),
        total: visible.length,
        backLabel: backLabel(state),
        onBack: actions.back,
        onPrev: actions.prev,
        onNext: actions.next,
      });
    } else if (!country) {
      nodes = renderIntro(total);
    } else {
      nodes = renderRegion({ country, era, items: visible, onPick: actions.pick });
    }

    contentHost.replaceChildren(...nodes.filter(Boolean));
    scrollHost.scrollTop = 0;
  }

  return { render };
}

function backLabel({ country, era }) {
  if (!country) return '图册总览';
  if (country === '中国' && era && era !== '全部') return `${country} · ${era}`;
  return country;
}
