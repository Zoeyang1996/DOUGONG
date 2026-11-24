import { createCharacter } from './character.js';
import { createAnswers } from './answers.js';
import { el } from '../dom.js';

export function createGuide() {
  const answer = createAnswers();
  const root = el('section', { class: 'wood-guide', 'aria-label': '小拱木构向导' });
  const trigger = el('button', { class: 'guide-avatar', type: 'button', 'aria-label': '与小拱对话，可拖拽移动', 'aria-expanded': 'false', title: '点我聊聊 · 按住可拖动' });
  const name = el('span', { class: 'guide-name', text: '小拱' });
  const characterHost = el('span', { class: 'guide-character' }); trigger.append(characterHost, name);
  const log = el('div', { class: 'guide-log', role: 'log', 'aria-live': 'polite' });
  const input = el('input', { type: 'text', placeholder: '问我一个木构问题…', 'aria-label': '向小拱提问', maxLength: 200, autocomplete: 'off' });
  const submit = el('button', { type: 'submit', text: '发送' });
  const form = el('form', { class: 'guide-form' }, input, submit);
  const suggestions = el('div', { class: 'guide-suggestions' });
  const close = el('button', { type: 'button', class: 'guide-close', text: '×', 'aria-label': '收起小拱对话' });
  const panel = el('section', { class: 'guide-chat', hidden: true, 'aria-label': '与小拱对话' },
    el('header', {}, el('div', {}, el('strong', { text: '小拱' }), el('span', { text: '木构小向导 · 离线知识问答' })), close), log, suggestions, form);
  root.append(panel, trigger); document.body.append(root);
  let character;
  try { character = createCharacter(characterHost); } catch (error) {
    characterHost.textContent = '拱'; characterHost.classList.add('guide-fallback');
    console.error('小拱三维显示未能启动', error);
  }
  let x = Math.max(12, innerWidth - (innerWidth < 680 ? 220 : 370)), y = 8, drag = null, ignoreClick = false, lastAnswer = '';
  try { const saved = JSON.parse(localStorage.getItem('wood-guide-position')); if (saved && Number.isFinite(saved.x) && Number.isFinite(saved.y)) { x = saved.x; y = saved.y; } } catch {}
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  function position() {
    x = clamp(x, 4, innerWidth - 116); y = clamp(y, 4, innerHeight - 160);
    root.style.left = `${x}px`; root.style.top = `${y}px`;
    if (panel.hidden) return;
    const width = Math.min(360, innerWidth - 24);
    let height = Math.min(490, innerHeight - 24);
    let px = x + 108, py = y + 22;
    if (px + width > innerWidth - 12) px = x - width + 4;
    // 窄屏把对话放到角色下方或上方，避免对话窗遮住小拱本身。
    if (px < 12) {
      px = 12;
      const below = innerHeight - y - 168, above = y - 12;
      const placeBelow = below >= above;
      height = Math.min(height, Math.max(220, placeBelow ? below : above));
      py = placeBelow ? y + 164 : y - height - 8;
    }
    panel.style.width = `${width}px`; panel.style.height = `${height}px`;
    panel.style.left = `${clamp(px, 12, innerWidth - width - 12)}px`;
    panel.style.top = `${clamp(py, 12, innerHeight - height - 12)}px`;
  }
  function stopSpeech() { window.speechSynthesis?.cancel(); }
  function closeChat() { panel.hidden = true; trigger.setAttribute('aria-expanded', 'false'); character?.setActive(false); stopSpeech(); }
  function openChat() { panel.hidden = false; trigger.setAttribute('aria-expanded', 'true'); character?.setActive(true); position(); }
  function bubble(text, user = false) {
    const item = el('div', { class: `guide-bubble${user ? ' is-user' : ''}`, text });
    if (!user && window.speechSynthesis) {
      const speak = el('button', { type: 'button', class: 'guide-speak', text: '朗读', 'aria-label': '朗读这条回答' });
      speak.onclick = () => { stopSpeech(); const voice = new SpeechSynthesisUtterance(text); voice.lang = 'zh-CN'; voice.rate = 1; speechSynthesis.speak(voice); };
      item.append(speak);
    }
    log.append(item); while (log.children.length > 24) log.firstChild.remove();
    log.scrollTop = log.scrollHeight;
  }
  function ask(question) {
    if (!question.trim()) return;
    stopSpeech(); bubble(question, true); const result = answer(question); lastAnswer = result.answer;
    bubble(lastAnswer); input.value = '';
  }
  for (const text of ['保国寺为什么珍贵？', '斗拱有什么作用？', '120秒游戏怎么玩？']) {
    const button = el('button', { type: 'button', text }); button.onclick = () => ask(text); suggestions.append(button);
  }
  bubble('你好，我是小拱。保国寺的千年木构，或亲手拼搭的窍门，都可以问我。');
  form.onsubmit = event => { event.preventDefault(); ask(input.value); };
  close.onclick = closeChat;
  trigger.addEventListener('click', () => { if (ignoreClick) { ignoreClick = false; return; } panel.hidden ? openChat() : closeChat(); });
  trigger.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    drag = { id: event.pointerId, startX: event.clientX, startY: event.clientY, x, y, moved: false };
    trigger.setPointerCapture(event.pointerId);
  });
  trigger.addEventListener('pointermove', event => {
    if (!drag || drag.id !== event.pointerId) return;
    const dx = event.clientX - drag.startX, dy = event.clientY - drag.startY;
    drag.moved ||= Math.hypot(dx, dy) > 7;
    if (drag.moved) { event.preventDefault(); x = drag.x + dx; y = drag.y + dy; root.classList.add('is-dragging'); position(); }
  });
  function finishDrag(event) {
    if (!drag || drag.id !== event.pointerId) return;
    ignoreClick = drag.moved; root.classList.remove('is-dragging');
    if (trigger.hasPointerCapture(event.pointerId)) trigger.releasePointerCapture(event.pointerId);
    drag = null;
    try { localStorage.setItem('wood-guide-position', JSON.stringify({ x, y })); } catch {}
    // Some touch browsers don't emit click after a drag: never swallow the next intentional tap.
    if (ignoreClick) setTimeout(() => { ignoreClick = false; }, 350);
  }
  trigger.addEventListener('pointerup', finishDrag); trigger.addEventListener('pointercancel', finishDrag);
  trigger.addEventListener('lostpointercapture', () => { drag = null; root.classList.remove('is-dragging'); });
  document.addEventListener('pointerdown', event => { if (!root.contains(event.target)) closeChat(); }, true);
  window.addEventListener('resize', position); position();
  return { close: closeChat, isOpen: () => !panel.hidden, setContext() {} };
}
