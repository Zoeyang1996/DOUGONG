import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { build } from '../../act-01-history/node_modules/esbuild/lib/main.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.resolve(root,'../..','output','小小营造师-西沃离线版');
await fs.mkdir(output,{recursive:true});
const model=await fs.readFile(path.join(root,'assets/baoguosi-zhutou-v02.glb'));
const jsonLength=model.readUInt32LE(12), modelInfo=JSON.parse(model.subarray(20,20+jsonLength).toString());
if((modelInfo.buffers||[]).some(b=>b.uri)||(modelInfo.images||[]).some(i=>i.uri))throw Error('模型仍含外部依赖');
let source=await fs.readFile(path.join(root,'app.js'),'utf8');
const loader="new GLTFLoader().loadAsync('./assets/baoguosi-zhutou-v02.glb')";
if(!source.includes(loader))throw Error('模型载入代码已变更，请更新导出器');
source=source.replace(loader,`new GLTFLoader().parseAsync(Uint8Array.from(atob(document.getElementById('embedded-model').textContent.trim()),c=>c.charCodeAt(0)).buffer,'')`);
source=source.replace("document.querySelectorAll('img[src=\"assets/assembled-reference.png\"]')","document.querySelectorAll('[data-reference-image]')");
source=source.replace('请通过本地预览地址打开网页。','请使用支持 WebGL 2 的 Edge 或 Chrome 浏览器打开本文件。');
const result=await build({stdin:{contents:source,resolveDir:root,sourcefile:'offline-entry.js',loader:'js'},bundle:true,format:'iife',target:['chrome100','edge100'],write:false,minify:true,legalComments:'inline',alias:{three:path.resolve(root,'../shared/vendor/three.module.js')}});
const script=result.outputFiles[0].text;
let html=await fs.readFile(path.join(root,'index.html'),'utf8');
const css=await fs.readFile(path.join(root,'style.css'),'utf8');
const image=await fs.readFile(path.join(root,'assets/assembled-reference.png'));
html=html.replace('<link rel="stylesheet" href="style.css">',()=>`<style>${css}</style>`)
 .replace(/<script type="importmap">[\s\S]*?<\/script>/,'')
 .replaceAll('href="../index.html"','href="#workbench"')
 .replaceAll('src="assets/assembled-reference.png"',`data-reference-image src="data:image/png;base64,${image.toString('base64')}"`)
 .replace('<script type="module" src="app.js"></script>',()=>`<script id="embedded-model" type="application/octet-stream">${model.toString('base64')}</script>\n<script>${script.replace(/<\/script/gi,'<\\/script')}</script>`)
 .replace('<head>','<head><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; img-src data: blob:; connect-src \'none\'; font-src data:">');
await fs.writeFile(path.join(output,'双击打开-斗拱挑战.html'),html);
await fs.writeFile(path.join(output,'使用说明.txt'),`小小营造师 · 西沃离线版\n\n1. 把本文件夹拷贝到西沃电脑的桌面。\n2. 双击“ 双击打开-斗拱挑战.html ”即可开始，不需要联网、不需要安装 Blender、不需要服务器。\n3. 如果系统没有用浏览器打开：右键 HTML 文件 → 打开方式 → Microsoft Edge 或 Google Chrome。\n4. 点击网页右上角“全屏”，或按键盘 F11。\n5. 点击“开始挑战”，在120秒内完成18组拼装。可拖放，也可先点右侧构件，再点左侧落点。\n\n所有模型、Three.js、木材贴图生成代码、样式、效果图均已内嵌在 HTML 内。仅复制这个 HTML 文件也可以运行。ZIP文件请先完整解压，再打开其中的HTML，不要直接从压缩包预览。\n\n运行环境：支持 WebGL 2 的现代 Edge / Chrome。网页使用系统中文字体，不同电脑字形可能略有差异。西沃的具体设备性能及真实多点触摸仍需现场确认。若显示三维载入失败，请先用 Edge 打开并检查浏览器硬件加速；无需降低浏览器安全设置。\n\n模型为现有形制草模的游戏搭接修正版，非施工或加工依据。\n`);
await fs.copyFile(path.resolve(root,'../act-01-history/node_modules/three/LICENSE'),path.join(output,'Three.js开源许可.txt'));
const markup=html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi,'');
const tags=[...markup.matchAll(/<(?:script|img|link)\b[^>]*\b(?:src|href)="([^"]*)"/g)].map(m=>m[1]);
if(tags.some(url=>!url.startsWith('data:')))throw Error('HTML仍引用外部资源');
if(/type="module"|type="importmap"/.test(html))throw Error('模块未合并');
console.log(JSON.stringify({output,htmlBytes:Buffer.byteLength(html),modelNodes:modelInfo.nodes.length,externalResourceTags:0,networkBlockedByCSP:true},null,2));
