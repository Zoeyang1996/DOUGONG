import { ERAS, REGIONS } from '../content.js';
import { el, pad } from '../dom.js';

/** 地区 / 朝代总览：标题、引言、收录数与名录 */
export function renderRegion({ country, era, items, onPick }) {
  const eraInfo = ERAS.find((entry) => entry.key === era && entry.key !== '全部');
  const region = REGIONS[country];
  const title = eraInfo ? eraInfo.title : region.title;
  const lede = eraInfo ? eraInfo.lede : region.lede;
  const overline = `${country} / ${eraInfo ? `${eraInfo.title}木构` : region.era}`;

  return [
    el('p', { class: 'overline', text: overline }),
    el(
      'h2',
      {},
      title.split('，').map((part, index, all) => [part, index < all.length - 1 ? el('br') : null]),
    ),
    eraInfo ? el('p', { class: 'period', text: eraInfo.period }) : null,
    el('p', { class: 'lead', text: lede }),
    el(
      'div',
      { class: 'count' },
      el('strong', { text: pad(items.length) }),
      el('span', { text: '条 · 图册收录' }),
    ),
    buildList(items, onPick),
  ];
}

function buildList(items, onPick) {
  const list = el(
    'details',
    { class: 'building-list' },
    el('summary', { text: `建筑名录 · ${items.length}` }),
  );

  items.forEach((item, index) => {
    list.append(
      el(
        'button',
        { type: 'button', onClick: () => onPick(item) },
        el('span', { class: 'num', text: pad(index + 1) }),
        el('span', { class: 'row-name', text: item.name }),
        el('span', { class: 'row-arrow', text: '↗' }),
      ),
    );
  });

  return list;
}
