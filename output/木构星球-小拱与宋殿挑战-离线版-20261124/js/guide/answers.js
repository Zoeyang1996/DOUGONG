import { KNOWLEDGE } from './knowledge.js';

const normalize = value => String(value).toLowerCase().replace(/斗栱/g, '斗拱').replace(/双杪/g, '双抄').replace(/[^\w\u4e00-\u9fff]/g, '');
const bigrams = value => { const s = normalize(value); return new Set(Array.from({ length: Math.max(0, s.length - 1) }, (_, i) => s.slice(i, i + 2))); };
const interactionCards = [
  { id:'local-value',title:'保国寺的历史价值',tags:['保国寺为什么珍贵','保国寺的价值','保国寺的特色','保国寺有什么特别'],answer:'保国寺现存大殿核心建于1013年，是保存至今的重要北宋木构遗存。大殿的柱网、拼合瓜棱柱、七铺作双抄双下昂，以及梁架和藻井，让我们能够从真实构件认识早期木构的营造智慧。图册中的历史沿革与游戏中的分组搭建，分别帮助你读懂它和亲手体验它。' },
  { id: 'local-challenge', title: '如何接受与退出挑战', tags: ['开始游戏','接受挑战','退出游戏','返回保国寺','怎么挑战'], answer: '在图册中依次选择“中国”“宋”，打开“保国寺大殿”，就能接受 120 秒挑战。模型备料完成后开始计时。点击游戏顶栏的“退出挑战 · 返回保国寺”可随时回到刚才的建筑详情。' },
  { id: 'local-ip', title: '拖动小拱', tags: ['移动小拱','拖动小拱','关闭对话'], answer: '按住我并拖动，就能换个位置。轻点我会打开对话，再点一次或点击页面其他位置即可收起。游戏里也可以随时找我。' },
  { id: 'local-offline', title: '离线小向导', tags: ['联网','大模型','人工智能','deepseek','离线','你能做什么'], answer: '这份离线演示使用本机保存的项目知识卡，能够回答保国寺、榫卯、斗拱和图册建筑的问题，也能提示游戏玩法。当前没有连接云端大模型；未收录的问题我会说明，不会编造答案。' },
];
const cards = [...interactionCards, ...KNOWLEDGE];
export function createAnswers() {
  let lastCard = null;
  return function answer(question) {
    const query = normalize(question);
    if (!query) return { answer: '想了解保国寺，还是想试一试斗拱拼搭？' };
    if (/^(谢谢|好的|明白了|知道了|多谢|再见|拜拜)/.test(query)) return { answer: /再见|拜拜/.test(query) ? '下次见！随时点我，一起继续读懂木构。' : '不客气！还可以问我斗拱的构造，或去保国寺试一试亲手营造。' };
    if (/^(你好|您好|嗨|hello|小拱你好|你是谁)$/.test(query)) return KNOWLEDGE[0];
    if (/简单|再说一次|详细一点|继续讲|什么意思/.test(query) && lastCard && query.length < 10) return { ...lastCard, answer: `我们刚才聊的是“${lastCard.title}”。${lastCard.answer}` };
    const tokens = bigrams(query);
    const ranked = cards.map(card => {
      const title = normalize(card.title), tags = card.tags || [], tagText = normalize(tags.join(' '));
      const heading = bigrams(title + tagText), body = bigrams(card.answer);
      let score = 0, matches = 0;
      for (const token of tokens) { if (heading.has(token)) { score += 1.8; matches++; } else if (body.has(token)) score += .12; }
      for (const tag of tags) { const t = normalize(tag); if (t.length > 1 && query.includes(t)) score += 3 + Math.min(t.length, 6); }
      if (query.includes(title) && title.length > 1) score += 8;
      // Current game should outrank old generic interface cards for explicit drag/column questions.
      if (card.id === 'K051' && /游戏|120|拼搭|拼接|柱子|拖拽|拖动|搭建|顺序|放置/.test(query)) score += 8;
      return { card, score, matches };
    }).sort((a, b) => b.score - a.score);
    const best = ranked[0];
    if (best.score < 4 || (best.matches === 0 && best.score < 8)) return { answer: '这个问题我暂时没有可靠的本地资料。可以换个问法，或问我“保国寺大殿建于哪一年”“斗拱有什么作用”“120秒游戏怎么玩”。' };
    lastCard = best.card;
    return best.card;
  };
}
