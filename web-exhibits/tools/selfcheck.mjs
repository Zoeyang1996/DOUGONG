#!/usr/bin/env node
/**
 * 第二幕交付自检。
 *
 * 现场验收用：一条命令把「数据——资产——引用」三层跑一遍，
 * 逐项打勾或报错。改完内容、换完模型，跑这个比人眼翻页面快。
 *
 *   node web-exhibits/tools/selfcheck.mjs
 */

import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const ACT = resolve(HERE, '..', 'act-02-globe');

const C = {
  ok: '\x1b[32m', bad: '\x1b[31m', dim: '\x1b[2m', bold: '\x1b[1m', off: '\x1b[0m',
};

// era 只对中国条目必填：日本、欧洲没有朝代词表，留空是有意的
const REQUIRED = ['id', 'name', 'region', 'lat', 'lon', 'image', 'text', 'year', 'place'];
const MIN_MODEL_BYTES = 50 * 1024;

let failures = 0;

function line(ok, label, detail = '') {
  const tag = ok ? `${C.ok}通过${C.off}` : `${C.bad}失败${C.off}`;
  if (!ok) failures += 1;
  console.log(`  ${tag}  ${label}${detail ? `  ${C.dim}${detail}${C.off}` : ''}`);
}

function section(title) {
  console.log(`\n${C.bold}${title}${C.off}`);
}

const raw = readFileSync(join(ACT, 'data.json'), 'utf8');
const items = JSON.parse(raw);

/* ── 1. 数据 ───────────────────────────────────────────── */
section('一、数据');
line(Array.isArray(items) && items.length > 0, 'data.json 可解析', `${items.length} 条`);

const missingField = [];
const dupId = new Map();
const badCoord = [];
for (const it of items) {
  const lack = REQUIRED.filter((k) => it[k] === undefined || it[k] === '' || it[k] === null);
  if (it.region === '中国' && !it.era) lack.push('era');
  if (lack.length) missingField.push(`${it.id || '?'} 缺 ${lack.join('/')}`);
  dupId.set(it.id, (dupId.get(it.id) || 0) + 1);
  if (!Number.isFinite(+it.lat) || !Number.isFinite(+it.lon)
      || Math.abs(+it.lat) > 90 || Math.abs(+it.lon) > 180) {
    badCoord.push(it.id || '?');
  }
}
line(missingField.length === 0, '必备字段齐全', missingField.slice(0, 3).join('；'));
line([...dupId.values()].every((n) => n === 1), 'id 无重复',
  [...dupId].filter(([, n]) => n > 1).map(([k]) => k).join(', '));
line(badCoord.length === 0, '经纬度合法', badCoord.join(', '));

const byRegion = items.reduce((acc, it) => {
  acc[it.region] = (acc[it.region] || 0) + 1;
  return acc;
}, {});
console.log(`       ${C.dim}${Object.entries(byRegion).map(([k, v]) => `${k} ${v}`).join(' · ')}${C.off}`);

/* ── 2. 图片 ───────────────────────────────────────────── */
section('二、图片');

const noImage = [];
for (const it of items) {
  const p = join(ACT, it.image);
  if (!existsSync(p) || statSync(p).size < 8 * 1024) noImage.push(it.id);
}
line(noImage.length === 0, `${items.length} 条记录的主图都在`, noImage.slice(0, 4).join(', '));

const photoDir = join(ACT, 'assets', 'buildings');
let photos = 0;
const walk = (dir) => {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) walk(p);
    else if (/^0[12]\.jpg$/i.test(entry.name)) photos += 1;
  }
};
walk(photoDir);
line(photos >= items.length * 2, '建筑照片成对', `${photos} 张 / 需 ${items.length * 2} 张`);

/* ── 3. 三维模型 ───────────────────────────────────────── */
section('三、三维模型');

const withModel = items.filter((it) => it.model);
line(withModel.length > 0, '有模型引用', `${withModel.length} 座`);

const broken = [];
let totalBytes = 0;
for (const it of withModel) {
  const p = join(ACT, it.model);
  if (!existsSync(p) || statSync(p).size < MIN_MODEL_BYTES) {
    broken.push(`${it.id}(${it.model})`);
    continue;
  }
  totalBytes += statSync(p).size;
  const head = readFileSync(p).subarray(0, 4).toString('binary');
  if (head !== 'glTF') broken.push(`${it.id}(文件头不是 glTF)`);
}
line(broken.length === 0, `${withModel.length} 个引用均可打开`, broken.slice(0, 3).join('；'));
console.log(`       ${C.dim}合计 ${(totalBytes / 1048576).toFixed(1)} MB，平均 ${(totalBytes / withModel.length / 1048576).toFixed(2)} MB${C.off}`);

const modelDir = join(ACT, 'assets', 'models');
const onDisk = existsSync(modelDir)
  ? readdirSync(modelDir).filter((f) => f.toLowerCase().endsWith('.glb'))
  : [];
const orphan = onDisk.filter(
  (f) => !withModel.some((it) => it.model.endsWith(f)),
);
line(orphan.length === 0, '没有孤立模型文件', orphan.join(', '));

/* ── 4. 缺口（不是错误，是待办） ───────────────────────── */
const noModel = items.filter((it) => !it.model);
section('四、待接入三维的记录（不算失败）');
console.log(`       ${C.dim}${noModel.length} 座暂无模型：${noModel.slice(0, 6).map((it) => it.name).join('、')}${noModel.length > 6 ? ' 等' : ''}${C.off}`);

/* ── 5. 结论 ───────────────────────────────────────────── */
console.log();
if (failures === 0) {
  console.log(`${C.ok}${C.bold}全部通过${C.off}  ${C.dim}${items.length} 条数据 · ${photos} 张照片 · ${withModel.length} 个模型${C.off}`);
  process.exit(0);
}
console.log(`${C.bad}${C.bold}${failures} 项未通过${C.off}`);
process.exit(1);
