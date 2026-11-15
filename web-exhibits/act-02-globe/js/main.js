import {
  loadBuildings, filterBuildings, featuredPoints, centroid, provinceCounts,
} from './data.js';
import { ERAS, REGIONS, OVERVIEW_FOCUS } from './content.js';
import { createPanel } from './panel.js';
import { createLabels } from './labels.js';
import { createGlobe } from './globe/globe.js';
import { createModelViewer } from './viewer.js';

const $ = (selector) => document.querySelector(selector);
const isNarrow = () => window.matchMedia('(max-width: 1023px)').matches;
const reducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// 模型更新时改这个版本号，避免浏览器读旧缓存
const MODEL_V = '20261115c';

const state = {
  country: null, era: '全部', province: null, selected: null, visible: [], provinces: [],
};

const all = await loadBuildings();

// 四级：建筑三维预览。打开时暂停地球渲染，省一半 GPU
const viewer = createModelViewer({
  onOpen: () => globe?.setPaused(true),
  onClose: () => globe?.setPaused(false),
});

const panel = createPanel({
  contentHost: $('#panel-content'),
  scrollHost: $('.panel-inner'),
  total: all.length,
  actions: {
    pick,
    back: back,
    prev: () => step(-1),
    next: () => step(1),
    province: setProvince,
    openModel: (item) => viewer.open({ url: `${item.model}?v=${MODEL_V}`, name: item.name }),
  },
});

const labels = createLabels({
  layer: $('#map-labels'),
  leaderHost: $('#leaders'),
  onPick: pick,
});

buildEraNav();

const stageHost = $('.earth-stage');
let underlap = false;
let globeSize = 0;

/** 每帧的舞台联动：球压到说明栏时浮出纸面蒙版，并把球的直径交给阴影层 */
function syncStage(view) {
  const stageWidth = view.stageWidth || view.width;
  const bleed = view.bleed || 0;
  const next = view.radius() > stageWidth / 2 - bleed / 2 + 24;
  if (next !== underlap) {
    underlap = next;
    document.body.classList.toggle('is-underlap', underlap);
  }

  const size = Math.round(view.radius() * 2);
  if (Math.abs(size - globeSize) > 1) {
    globeSize = size;
    stageHost.style.setProperty('--globe-size', `${size}px`);
  }
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
  labels.setPoints(state.country ? labelPoints() : [], state.selected);
}

function refresh() {
  state.visible = filterBuildings(all, state);

  // 朝代与省份同时生效时可能一条不剩，此时放掉省份，回到朝代总览
  if (state.province && !state.visible.length) {
    state.province = null;
    state.visible = filterBuildings(all, state);
  }

  if (state.selected && !state.visible.includes(state.selected)) state.selected = null;

  // 省份数量只受地区与朝代影响：选中某省后，仍然看得到其余各省的分布
  state.provinces = state.country === '中国'
    ? provinceCounts(filterBuildings(all, { country: state.country, era: state.era }))
    : [];

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
  globe?.focus(item.lat, item.lon, 'building');
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
  // 退回上一层：单座 → 省份 / 朝代 → 地区 → 全球
  focusScope();
}

/**
 * 按当前层级把镜头落到位：省份 → 朝代 → 地区 → 全球。
 * 省份级与单座级共用最深的镜头距离，只把落点换成该省重心。
 */
function focusScope() {
  if (state.selected) return;
  const center = centroid(state.visible);

  if (state.province && center) {
    globe?.focus(center[0], center[1], 'province');
    return;
  }
  if (state.country && state.era !== '全部' && center) {
    globe?.focus(center[0], center[1], 'era');
    return;
  }
  const focus = state.country ? REGIONS[state.country]?.focus : null;
  if (focus) globe?.focus(focus[0], focus[1], 'region');
  else globe?.focus(OVERVIEW_FOCUS[0], OVERVIEW_FOCUS[1], 'overview');
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
  state.province = null;
  state.selected = null;
  refresh();
  focusScope();
}

function setEra(era) {
  state.era = era;
  state.selected = null;
  refresh();
  // 朝代的落点取本朝代所有条目的重心，即那几处建筑所在的省份
  focusScope();
}

/** 点省份统计格：选中即筛到该省并飞到该省重心，再点一次回到全省 */
function setProvince(province) {
  state.province = province;
  state.selected = null;
  refresh();
  focusScope();
}

function reset() {
  state.country = null;
  state.era = '全部';
  state.province = null;
  state.selected = null;
  refresh();
  focusScope();
}

function buildEraNav() {
  const host = $('#eras');
  host.replaceChildren();
  ERAS.forEach((entry) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.era = entry.key;
    button.textContent = entry.label;
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
  else if (state.province) setProvince(null);
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
      syncStage(view);
      labels.update(view);
    },
  });
  $('#globe').classList.add('is-ready');
  // 首屏直接落在“全球”这一级镜头上，避免初始距离与阶梯对不上
  globe.focus(OVERVIEW_FOCUS[0], OVERVIEW_FOCUS[1], 'overview', { instant: true });
} catch (error) {
  console.error(error);
  $('#globe-error').hidden = false;
  $('#zoom-in').disabled = true;
  $('#zoom-out').disabled = true;
}

refresh();
