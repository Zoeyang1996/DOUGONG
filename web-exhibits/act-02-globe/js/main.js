import { loadBuildings, filterBuildings, featuredPoints, centroid } from './data.js';
import { ERAS, REGIONS, OVERVIEW_FOCUS } from './content.js';
import { createPanel } from './panel.js';
import { createLabels } from './labels.js';
import { buildDial } from './dial.js';
import { createGlobe } from './globe/globe.js';

const $ = (selector) => document.querySelector(selector);
const isNarrow = () => window.matchMedia('(max-width: 760px)').matches;
const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const state = { country: null, era: '全部', selected: null, visible: [] };

const all = await loadBuildings();

const panel = createPanel({
  contentHost: $('#panel-content'),
  scrollHost: $('.panel-inner'),
  total: all.length,
  actions: {
    pick,
    back: back,
    prev: () => step(-1),
    next: () => step(1),
  },
});

const labels = createLabels({
  layer: $('#map-labels'),
  leaderHost: $('#leaders'),
  onPick: pick,
});

buildDial($('#dial'));
buildEraNav();

const dialHost = $('#dial');
let dialSize = 0;

function syncDial(view) {
  const size = Math.round(view.radius() * 2 + 30);
  if (Math.abs(size - dialSize) < 1) return;
  dialSize = size;
  dialHost.style.width = `${size}px`;
}

let globe = null;

function labelPoints() {
  const limit = isNarrow() ? 4 : 6;
  const points = featuredPoints(state.visible, limit);
  if (state.selected && !points.includes(state.selected)) {
    points[points.length - 1] = state.selected;
  }
  return points;
}

function syncLabels() {
  const order = new Map(state.visible.map((item, index) => [item.id, index + 1]));
  labels.setPoints(state.country ? labelPoints() : [], state.selected, order);
}

function refresh() {
  state.visible = filterBuildings(all, state);
  if (state.selected && !state.visible.includes(state.selected)) state.selected = null;

  syncNav();
  panel.render(state);
  syncLabels();
  globe?.setVisible(state.visible);
  globe?.setActive(state.selected);
  globe?.setIdleSpin(!state.country);
}

function pick(item) {
  state.selected = item;
  refresh();
  globe?.focus(item.lat, item.lon, 5.2);
  if (isNarrow()) {
    $('#panel').scrollIntoView({
      behavior: reducedMotion() ? 'auto' : 'smooth',
      block: 'start',
    });
  }
}

function back() {
  state.selected = null;
  refresh();
}

function step(direction) {
  if (!state.visible.length) return;
  const index = state.visible.indexOf(state.selected);
  const next = state.visible[(index + direction + state.visible.length) % state.visible.length];
  pick(next);
}

function setCountry(country) {
  state.country = country;
  state.era = '全部';
  state.selected = null;
  refresh();
  const focus = REGIONS[country]?.focus;
  if (focus) globe?.focus(focus[0], focus[1], focus[2]);
}

function setEra(era) {
  state.era = era;
  state.selected = null;
  refresh();
  const center = centroid(state.visible);
  if (center) globe?.focus(center[0], center[1], 5.3);
}

function reset() {
  state.country = null;
  state.era = '全部';
  state.selected = null;
  refresh();
  globe?.focus(OVERVIEW_FOCUS[0], OVERVIEW_FOCUS[1], OVERVIEW_FOCUS[2]);
}

function buildEraNav() {
  const host = $('#eras');
  host.replaceChildren();
  ERAS.forEach((entry) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.era = entry.key;
    button.innerHTML = '';
    const index = document.createElement('span');
    index.className = 'era-num';
    index.textContent = String(ERAS.indexOf(entry)).padStart(2, '0');
    button.append(index, document.createTextNode(entry.label));
    button.addEventListener('click', () => setEra(entry.key));
    host.append(button);
  });
}

function syncNav() {
  document.querySelectorAll('[data-country]').forEach((button) => {
    const active = button.dataset.country === state.country;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });

  const erasHost = $('#eras');
  erasHost.hidden = state.country !== '中国';

  document.querySelectorAll('[data-era]').forEach((button) => {
    const active = button.dataset.era === state.era;
    button.classList.toggle('active', active);
    button.setAttribute('aria-pressed', String(active));
  });
}

document.querySelectorAll('[data-country]').forEach((button) => {
  button.addEventListener('click', () => setCountry(button.dataset.country));
});

$('#reset').addEventListener('click', reset);
$('#zoom-in').addEventListener('click', () => globe?.zoom(0.85));
$('#zoom-out').addEventListener('click', () => globe?.zoom(1.18));

$('#about').addEventListener('click', () => $('#about-dialog').showModal());
$('#close-about').addEventListener('click', () => $('#about-dialog').close());

$('#fullscreen').addEventListener('click', async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch {
    $('#fullscreen').textContent = '请用浏览器全屏';
  }
});

document.addEventListener('fullscreenchange', () => {
  $('#fullscreen').innerHTML = document.fullscreenElement
    ? '退出全屏<span class="glyph" aria-hidden="true">⛶</span>'
    : '全屏<span class="glyph" aria-hidden="true">⛶</span>';
});

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape' || $('#about-dialog').open) return;
  if (state.selected) back();
  else if (state.country && state.era !== '全部') setEra('全部');
  else if (state.country) reset();
});

window.addEventListener('resize', syncLabels);

refresh();

try {
  globe = await createGlobe({
    host: $('#globe'),
    items: all,
    onPick: pick,
    onFrame: (view) => {
      syncDial(view);
      labels.update(view);
    },
  });
  $('#globe').classList.add('is-ready');
} catch (error) {
  console.error(error);
  $('#globe-error').hidden = false;
  $('#zoom-in').disabled = true;
  $('#zoom-out').disabled = true;
}

refresh();
