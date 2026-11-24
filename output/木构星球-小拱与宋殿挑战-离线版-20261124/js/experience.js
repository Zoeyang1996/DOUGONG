import { createGuide } from './guide/widget.js';
import { el } from './dom.js';

const BAOGUOSI = 'song-01-baoguosi-dadian';

export function createExperience({ pauseAtlas }) {
  const guide = createGuide();
  let frame = null, previousFocus = null, selected = null;
  const dismiss = el('button', { type: 'button', class: 'challenge-close', text: '×', 'aria-label': '关闭挑战邀请' });
  const accept = el('button', { type: 'button', class: 'challenge-accept', text: '接受游戏挑战 →' });
  const later = el('button', { type: 'button', class: 'challenge-later', text: '先看看这座殿' });
  const invitation = el('section', { class: 'challenge-invitation', hidden: true, role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'challenge-title' });
  const artwork = el('div', { class: 'challenge-art', 'aria-hidden': 'true' });
  artwork.innerHTML = '<svg viewBox="0 0 420 390" fill="none" xmlns="http://www.w3.org/2000/svg"><g stroke="currentColor" stroke-linejoin="round"><path d="M42 335H378V349H42zM79 325V207m262 118V207M159 325V207m102 118V207" stroke-width="8"/><path d="M67 212H353M67 200H353M84 325h-10m94 0h-18m120 0h-18m94 0h-10M39 182H381M54 169H366M77 150H343M95 126H325M113 98H307M130 72H290" stroke-width="5"/><path d="M27 184Q68 165 104 123L151 73m242 111q-41-19-77-61l-47-50M82 146Q118 129 151 73m187 73Q302 129 269 73" stroke-width="4"/><path d="M69 198v-14h25v14m11 0v-14h25v14m11 0v-14h25v14m11 0v-14h25v14m11 0v-14h25v14m11 0v-14h25v14m11 0v-14h25v14m11 0v-14h25v14M107 165v-14h27v14m28 0v-14h27v14m42 0v-14h27v14m28 0v-14h27v14M141 122v-16h30v16m78 0v-16h30v16M156 95V76m108 19V76M168 69V49h84v20M149 49h122M84 256h74m104 0h74M84 244h74m104 0h74M192 323V244h36v79" stroke-width="3"/><path d="M65 355h290" stroke-width="1"/></g></svg>';
  invitation.append(el('div', { class: 'challenge-card' }, dismiss, artwork,
    el('div', { class: 'challenge-copy' }, el('p', { class: 'challenge-eyebrow', text: '保国寺 · 亲手营造' }),
      el('h2', { id: 'challenge-title' }, '一殿千年，', el('br'), '由你筑起。'),
      el('p', { class: 'challenge-description', text: '从立柱到屋架，将二十组木构落榫归位。给自己 120 秒，赴一场宋构营造之约。' }),
      el('p', { class: 'challenge-rule', text: '按住木件拖入左侧 · 同层可自由拼搭' }), accept, later)));

  const exit = el('button', { type: 'button', class: 'hall-exit', text: '← 退出挑战 · 返回保国寺' });
  const soundButton = el('button', { type: 'button', class: 'hall-sound', text: '音效 开', 'aria-pressed': 'true' });
  const fullscreen = el('button', { type: 'button', class: 'hall-fullscreen', text: '全屏' });
  const gameOverlay = el('section', { class: 'hall-overlay', hidden: true, role: 'dialog', 'aria-modal': 'true', 'aria-label': '保国寺宋大殿120秒拼搭挑战' },
    el('header', { class: 'hall-bar' }, exit, el('span', { text: '保国寺 · 宋殿营造' }), el('nav', { class: 'hall-actions' }, soundButton, fullscreen)));
  const loading = el('p', { class: 'hall-preparing', role: 'status', text: '正在备料，准备完成后开始计时…' });
  document.body.append(invitation, gameOverlay);
  const atlasElements = () => document.querySelectorAll('.masthead,.atlas,.colophon');
  function lock(value) {
    atlasElements().forEach(element => element.inert = value);
    document.body.classList.toggle('experience-open', value);
  }
  function hideInvitation(restore = true) {
    invitation.hidden = true;
    if (gameOverlay.hidden) { lock(false); if (restore) previousFocus?.focus({ preventScroll: true }); }
  }
  function showInvitation() {
    if (selected?.id !== BAOGUOSI || !gameOverlay.hidden) return;
    previousFocus = document.activeElement;
    guide.close(); invitation.hidden = false; lock(true); accept.focus({ preventScroll: true });
  }
  function startGame() {
    if (frame) return;
    hideInvitation(false); guide.close(); lock(true); pauseAtlas(true);
    gameOverlay.hidden = false; gameOverlay.append(loading); loading.hidden = false;
    document.body.dataset.experience = 'preparing';
    soundButton.textContent='音效 开';soundButton.setAttribute('aria-pressed','true');
    frame = el('iframe', { class: 'hall-frame', title: '120秒保国寺宋大殿拼搭游戏', allow: 'autoplay; fullscreen' });
    frame.src = new URL('game/index.html', location.href).href;
    gameOverlay.append(frame); exit.focus({ preventScroll: true });
  }
  function exitGame() {
    if (!frame) return;
    frame.contentWindow?.postMessage({ channel: 'wood-hall-v1', action: 'mute' }, '*');
    // Removing the child releases its timer, audio context, and WebGL scene.
    frame.remove(); frame = null; gameOverlay.hidden = true; loading.hidden = true;
    guide.close(); lock(false); pauseAtlas(false); document.body.dataset.experience = 'atlas';
    const reentry = document.querySelector('.detail-challenge');
    (reentry || previousFocus)?.focus({ preventScroll: true });
  }
  dismiss.onclick = later.onclick = () => hideInvitation(); accept.onclick = startGame; exit.onclick = exitGame;
  invitation.addEventListener('click', event => { if (event.target === invitation) hideInvitation(); });
  soundButton.onclick = () => frame?.contentWindow?.postMessage({ channel:'wood-hall-v1',action:'toggle-sound' },'*');
  fullscreen.onclick = async () => {
    try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.documentElement.requestFullscreen(); }
    catch { fullscreen.textContent = '请用浏览器全屏'; }
  };
  window.addEventListener('message', event => {
    if (!frame || event.source !== frame.contentWindow || event.data?.channel !== 'wood-hall-v1') return;
    const action = event.data.action;
    if (action === 'sound') { soundButton.textContent=event.data.muted?'音效 关':'音效 开';soundButton.setAttribute('aria-pressed',String(!event.data.muted)); }
    if (action === 'outside-pointer') guide.close();
    if (action === 'exit') exitGame();
    if (action === 'ready') { loading.hidden = true; document.body.dataset.experience = 'game'; }
    if (action === 'error') loading.textContent = '木构暂时未能准备好，请退出后重新接受挑战。';
    if (action === 'progress') { gameOverlay.dataset.placed = String(event.data.placed); gameOverlay.dataset.status = event.data.status; }
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      if (guide.isOpen()) guide.close();
      else if (frame) exitGame();
      else if (!invitation.hidden) hideInvitation();
      else return;
      event.preventDefault(); event.stopImmediatePropagation(); return;
    }
    if (event.key !== 'Tab' || invitation.hidden) return;
    const nodes = [dismiss, accept, later], first = nodes[0], last = nodes.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }, true);
  document.body.dataset.experience = 'atlas';
  return {
    openChallenge: showInvitation,
    onBuilding(item) {
      selected = item;
      if (item.id === BAOGUOSI) showInvitation();
    },
  };
}
