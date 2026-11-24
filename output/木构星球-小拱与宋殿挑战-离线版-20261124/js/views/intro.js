import { INTRO } from '../content.js';
import { el } from '../dom.js';

/** 首页：以木为骨，与时间相逢 */
export function renderIntro(total) {
  return [
    el('h2', { class: 'intro-title' }, INTRO.title.map((line) => el('span', { text: line }))),
    el('p', { class: 'lead', text: INTRO.lede }),
    el(
      'div',
      { class: 'count' },
      el('strong', { text: String(total) }),
      el('span', { text: '处木构' }),
    ),
  ];
}
