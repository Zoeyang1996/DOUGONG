import { ERAS, REGIONS } from '../content.js';
import { shortProvince, eraSpan } from '../data.js';
import { ERA_STATS, formatTotal, provinceMax } from '../era-stats.js';
import { el } from '../dom.js';

/** 地区 / 朝代 / 省份总览：标题、年代、引言、收录数、各省数量与名录 */
export function renderRegion({
  country, era, province, items, provinces, stat, onPick, onProvince,
}) {
  const eraInfo = ERAS.find((entry) => entry.key === era && entry.key !== '全部');
  const region = REGIONS[country];
  const provinceName = province ? shortProvince(province) : '';

  return [
    heading({ region, eraInfo, provinceName }),
    eraInfo ? el('p', { class: 'period', text: eraInfo.period }) : null,
    el('p', {
      class: 'lead',
      text: provinceName
        ? provinceLede(items)
        : (eraInfo ? eraInfo.lede : region.lede),
    }),
    country === '中国' && !provinceName ? statBlock(stat || ERA_STATS[era]) : null,
    el(
      'div',
      { class: 'count' },
      el('strong', { text: String(items.length) }),
      el('span', { text: '处 · 本图册收录' }),
    ),
    provinces.length
      ? provinceBlock({ provinces, province, total: provinces.reduce((sum, p) => sum + p.count, 0), onProvince })
      : null,
    buildList(items, onPick),
  ];
}

function heading({ region, eraInfo, provinceName }) {
  if (provinceName) {
    return el('h2', {}, eraInfo ? [provinceName, el('br'), eraInfo.label] : provinceName);
  }
  const title = eraInfo ? eraInfo.title : region.title;
  return el(
    'h2',
    {},
    title.split('，').map((part, index, all) => [part, index < all.length - 1 ? el('br') : null]),
  );
}

/** 省份说明只用本图册数据，不引入未核的现存总量 */
function provinceLede(items) {
  const eras = eraSpan(items);
  return eras.length
    ? `本图册收录该省 ${items.length} 处，年代跨${eras.join('、')}。`
    : `本图册收录该省 ${items.length} 处。`;
}

/** 各省收录数量：等宽格，便于横向比较；底栏长度即为比例 */
function provinceBlock({ provinces, province, total, onProvince }) {
  const max = Math.max(...provinces.map((entry) => entry.count), 1);
  const sorted = [...provinces].sort((a, b) => b.count - a.count || shortProvince(a.name).localeCompare(shortProvince(b.name), 'zh-Hans-CN'));

  return el(
    'section',
    { class: 'provinces', 'aria-label': '各省收录数量' },
    el(
      'div',
      { class: 'provinces-head' },
      el('span', { class: 'provinces-title', text: '收录分布' }),
      el(
        'button',
        {
          type: 'button',
          class: 'provinces-all' + (province ? '' : ' is-active'),
          'aria-pressed': String(!province),
          onClick: () => onProvince(null),
        },
        `全部 ${total}`,
      ),
    ),
    el('div', { class: 'province-grid' }, sorted.map((entry) => provinceChip(entry, max, entry.name === province, onProvince))),
  );
}

function provinceChip(entry, max, active, onProvince) {
  const chip = el(
    'button',
    {
      type: 'button',
      class: 'province-chip' + (active ? ' is-active' : ''),
      'aria-pressed': String(active),
      'aria-label': `${shortProvince(entry.name)}，收录 ${entry.count} 处`,
      onClick: () => onProvince(active ? null : entry.name),
    },
    el('span', { class: 'chip-name', text: shortProvince(entry.name) }),
    el('span', { class: 'chip-count', text: String(entry.count) }),
    el('span', { class: 'chip-bar', 'aria-hidden': 'true' }),
  );
  // 底栏长度即占最大值的比例，等宽格下可直接横向比较
  chip.style.setProperty('--share', String(entry.count / max));
  return chip;
}

function buildList(items, onPick) {
  const list = el(
    'details',
    { class: 'building-list' },
    el('summary', { text: `建筑名录 · ${items.length}` }),
  );

  items.forEach((item) => {
    list.append(
      el(
        'button',
        { type: 'button', onClick: () => onPick(item) },
        el('span', { class: 'row-name', text: item.name }),
        el('span', { class: 'row-arrow', text: '↗' }),
      ),
    );
  });

  return list;
}

/**
 * 全国现存统计：数字 + 分省条形 + 口径说明。
 * 数字来自独立的数据文件，与「本图册收录」严格分开，避免把收录数当现存数。
 */
function statBlock(stat) {
  if (!stat) return null;
  const max = provinceMax(stat);

  return el(
    'section',
    { class: 'era-stat', 'aria-label': '全国现存统计' },
    el(
      'div',
      { class: 'era-stat-head' },
      el('span', { class: 'era-stat-label', text: '全国现存' }),
      el('span', { class: 'era-stat-scope', text: stat.scope }),
    ),
    el(
      'div',
      { class: 'era-stat-num' },
      el('strong', { text: formatTotal(stat.total) }),
      el('span', { text: stat.unit }),
    ),
    stat.provinces.length
      ? el(
        'div',
        { class: 'era-stat-bars' },
        stat.provinces.map(([name, count]) => {
          const row = el(
            'div',
            { class: 'era-stat-row' },
            el('span', { class: 'era-stat-pname', text: name }),
            el('span', { class: 'era-stat-pbar', 'aria-hidden': 'true' }),
            el('span', { class: 'era-stat-pnum', text: String(count) }),
          );
          row.style.setProperty('--share', String(count / max));
          return row;
        }),
      )
      : null,
    el('p', { class: 'era-stat-note', text: stat.note }),
    el('p', { class: 'era-stat-src', text: `来源 · ${stat.source}` }),
  );
}
