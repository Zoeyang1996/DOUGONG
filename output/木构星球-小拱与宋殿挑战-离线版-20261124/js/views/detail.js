import { el } from '../dom.js';

/** 单条建筑详情：标题、年代、地点、正文、形制。 */
export function renderDetail({ item, backLabel, onBack, onPrev, onNext, onOpenModel, onChallenge }) {
  return [
    el(
      'button',
      { class: 'back', type: 'button', onClick: onBack },
      el('span', { class: 'arrow', 'aria-hidden': 'true', text: '←' }),
      backLabel,
    ),
    photoFrame(item, onOpenModel),
    el('h2', { class: 'detail-title', text: item.name }),
    el('p', { class: 'detail-year', text: item.year }),
    el('p', { class: 'detail-meta', text: item.place }),
    needsNote(item.status) ? el('p', { class: 'status', text: item.status }) : null,
    el('p', { class: 'detail-body', text: item.text }),
    item.quote ? el('blockquote', { class: 'detail-quote', text: item.quote }) : null,
    specList(item),
    item.id === 'song-01-baoguosi-dadian' ? el('button', { class: 'detail-challenge', type: 'button', text: '120 秒 · 亲手营造宋殿 →', onClick: onChallenge }) : null,
    el(
      'div',
      { class: 'detail-next' },
      el(
        'button',
        { type: 'button', id: 'prev', onClick: onPrev },
        el('span', { class: 'arrow', 'aria-hidden': 'true', text: '←' }),
        '上一处',
      ),
      el(
        'button',
        { type: 'button', id: 'next', onClick: onNext },
        '下一处',
        el('span', { class: 'arrow', 'aria-hidden': 'true', text: '→' }),
      ),
    ),
  ];
}

function needsNote(status = '') {
  return status.includes('待核') || status.includes('争议');
}

function photoFrame(item, onOpenModel) {
  const image = el('img', {
    class: 'photo',
    alt: `${item.name}外观`,
    loading: 'lazy',
    src: item.image,
  });

  image.addEventListener('error', () => {
    image.replaceWith(el('div', { class: 'photo-fallback', text: '此建筑照片暂缺' }));
  });

  // 有三维模型的建筑，图变成入口：点一下进入四级预览
  if (item.model) {
    return el(
      'button',
      {
        class: 'photo-frame has-model',
        type: 'button',
        'aria-label': `打开${item.name}的三维模型`,
        onClick: () => onOpenModel?.(item),
      },
      image,
      el('span', { class: 'photo-badge', text: '三维' }),
    );
  }

  // 图下不放说明文字：图版信息已在标题与形制栏中
  return el('figure', { class: 'photo-frame' }, image);
}

function specList(item) {
  const rows = [
    ['形制', item.type],
    ['构造', item.structure],
    ['坐标', item.coordNote],
  ].filter(([, value]) => value);

  return el(
    'dl',
    { class: 'detail-spec' },
    rows.map(([label, value]) => [el('dt', { text: label }), el('dd', { text: value })]),
  );
}
