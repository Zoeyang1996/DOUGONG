import { INTRO } from '../content.js';
import { el } from '../dom.js';

/** 首页：以木为骨，与时间相逢 */
export function renderIntro(total) {
  return [
    el('p', { class: 'overline', text: INTRO.overline }),
    el('h2', { class: 'intro-title' }, INTRO.title.map((line) => el('span', { text: line }))),
    el(
      'p',
      { class: 'lead' },
      INTRO.lede.split('<br>').map((line, i, all) => [line, i < all.length - 1 ? el('br') : null]),
    ),
    el(
      'div',
      { class: 'count' },
      el('strong', { text: String(total) }),
      el('span', { text: '条 · 图册收录' }),
    ),
  ];
}
