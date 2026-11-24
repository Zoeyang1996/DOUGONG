import { renderIntro } from './views/intro.js';
import { renderRegion } from './views/region.js';
import { renderDetail } from './views/detail.js';
import { shortProvince } from './data.js';

/**
 * 左栏控制器：按状态选择版面，并把交互交回主控。
 */
export function createPanel({ contentHost, scrollHost, total, actions }) {
  function render(state) {
    const { country, era, province, selected, visible, provinces } = state;
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
        onOpenModel: actions.openModel,
        onChallenge: actions.challenge,
      });
    } else if (!country) {
      nodes = renderIntro(total);
    } else {
      nodes = renderRegion({
        country,
        era,
        province,
        stat: state.stat,
        items: visible,
        provinces,
        onPick: actions.pick,
        onProvince: actions.province,
      });
    }

    contentHost.replaceChildren(...nodes.filter(Boolean));
    scrollHost.scrollTop = 0;

    // 换页时轻微浮现一次，读起来像“弹出”，不打断阅读
    contentHost.classList.remove('is-entering');
    void contentHost.offsetWidth;
    contentHost.classList.add('is-entering');
  }

  return { render };
}

function backLabel({ country, era, province }) {
  if (!country) return '图册总览';
  const parts = [country];
  if (country === '中国' && era && era !== '全部') parts.push(era);
  if (province) parts.push(shortProvince(province));
  return parts.length > 1 ? parts.slice(1).join(' · ') : country;
}
