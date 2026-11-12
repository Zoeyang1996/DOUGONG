import * as THREE from 'three';
import { OrbitControls } from '../shared/vendor/OrbitControls.js';
import { GLTFLoader } from '../shared/vendor/GLTFLoader.js';
import { Challenge } from './game-state.mjs';

const $ = q => document.querySelector(q);
const host = $('#assembly');
const game = new Challenge();
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
const definitions = [
  ['栌斗', n => n === 'dou_ludou_01'],
  ['泥道栱', n => n === 'gong_nidaogong_01'],
  ['第一杪华栱', n => n === 'gong_huagong_tiao1_01'],
  ['第一层承斗', n => n.startsWith('dou_jiaohu_t1_') || n.startsWith('dou_sandou_nidao_')],
  ['第二杪华栱', n => n === 'gong_huagong_tiao2_01'],
  ['柱心慢栱', n => n === 'gong_mangong_center_01'],
  ['第二层承斗', n => n.startsWith('dou_jiaohu_t2_') || n.startsWith('dou_sandou_center2_')],
  ['第一下昂', n => n === 'ang_xiaang_01'],
  ['瓜子栱', n => n.startsWith('gong_guazigong_l3_')],
  ['第三层承斗', n => n.startsWith('dou_sandou_l3_') || n === 'dou_ang_head_01'],
  ['第二下昂', n => n === 'ang_xiaang_02'],
  ['横向慢栱', n => n.startsWith('gong_mangong_l4_')],
  ['第四层承斗', n => n.startsWith('dou_sandou_l4_') || n === 'dou_ang_head_02'],
  ['耍头', n => n === 'timber_shuatou_01'],
  ['令栱', n => n.startsWith('gong_linggong_')],
  ['上层承斗', n => n.startsWith('dou_sandou_top_')],
  ['承托枋', n => n.startsWith('fang_context_')],
  ['槫', n => n.startsWith('tuan_context_')],
];
let renderer, scene, camera, controls, groups = [], base = [], selected = null;
let drag = null, loaded = false, doneShown = false, width = 0, height = 0;
let flyIns = [], pointerIds = new Set();
$('#progress-track').innerHTML = '<i></i>'.repeat(game.total);

function status(message) { $('#feedback').textContent = message; }
function setTimer() {
  $('#seconds').textContent = String(Math.ceil(game.remaining / 1000)).padStart(3, '0');
  $('.timer').classList.toggle('urgent', game.remaining <= 15000 && game.status === 'playing');
}
function select(index) {
  if (!ensurePlaying() || index < game.placed) return;
  selected = index;
  groups.forEach((g, i) => {
    g.button.classList.toggle('selected', i === index);
    g.button.setAttribute('aria-pressed', String(i === index));
    g.ghosts.forEach(mesh => {
      mesh.material.opacity = i === index ? .32 : .07;
      mesh.material.color.set(i === index ? 0x52725b : 0x86907d);
    });
  });
  $('#selection-label').textContent = groups[index].name + (groups[index].meshes.length > 1 ? ` · ${groups[index].meshes.length} 件一组` : '');
  $('#target').hidden = false;
  status(index === game.placed ? '拖到标记处，或点击标记完成拼装。' : `先安放${groups[game.placed].name}，再接着往上搭。`);
}
function clearSelection() {
  selected = null; $('#target').hidden = true;
  groups.forEach(g => {
    g.button.classList.remove('selected'); g.button.setAttribute('aria-pressed', 'false');
    g.ghosts.forEach(m => { m.material.opacity = .07; m.material.color.set(0x86907d); });
  });
}
function progress() {
  $('#placed').textContent = String(game.placed).padStart(2, '0');
  $('#remaining').textContent = `${game.total - game.placed} 组待归位`;
  $('#progress-track').setAttribute('aria-valuenow', game.placed);
  [...$('#progress-track').children].forEach((el, i) => el.classList.toggle('done', i < game.placed));
  groups.forEach((g, i) => { g.button.classList.toggle('placed', i < game.placed); g.button.disabled = game.status !== 'playing' || i < game.placed; });
  $('#step-label').textContent = game.placed < game.total ? `第 ${String(game.placed + 1).padStart(2, '0')} 步 · 安放${groups[game.placed].name}` : '一朵斗拱，已然成形。';
}
function start() {
  if (!loaded) return;
  clearDrag(); clearSelection(); flyIns = []; doneShown = false;
  groups.forEach(g => {
    g.meshes.forEach(m => { m.visible = false; m.position.set(0,0,0); });
    g.ghosts.forEach(m => m.visible = true);
  });
  game.start(performance.now()); $('#result').hidden = true; $('#start').hidden = true; $('#restart').hidden = false;
  $('#stage-label').textContent = '营造中'; $('#selection-label').textContent = '选一组木件，放入左侧轮廓。';
  progress(); setTimer(); resetView(); status('从右侧找到栌斗，放到柱头上。');
}
function ensurePlaying() {
  game.tick(performance.now());
  if (game.status === 'lost' && !doneShown) finish();
  return game.status === 'playing';
}
function place(index) {
  if (!ensurePlaying()) return;
  if (!game.place(index, performance.now())) {
    status(`顺序还差一步：先安放${groups[game.placed].name}。`); return;
  }
  const g = groups[index];
  g.meshes.forEach(m => { m.visible = true; if (!reduced) m.position.y = .18; });
  g.ghosts.forEach(m => m.visible = false);
  if (!reduced) flyIns.push({ meshes:g.meshes, start:performance.now() });
  clearSelection(); progress(); setTimer();
  $('#selection-label').textContent = `${g.name}，已归位。`;
  status(game.placed < game.total ? `${g.name}已就位，接下来是${groups[game.placed].name}。` : '挑战完成。');
  if (game.status === 'won') finish();
}
function finish() {
  doneShown = true; clearDrag(); clearSelection(); progress(); setTimer();
  const won = game.status === 'won';
  $('#stage-label').textContent = won ? '已成形' : '时间到';
  $('#result-overline').textContent = won ? '营造完成' : '本次挑战结束';
  $('#result-title').textContent = won ? '一木相接，一朵成形。' : '时间到，手艺再练。';
  const seconds = Math.ceil((game.duration - game.remaining) / 1000);
  $('#result-copy').textContent = won ? `用时 ${seconds} 秒，18 组木件全部归位。` : `已完成 ${game.placed} / 18 组。再试一次，接住下一层。`;
  $('#result').hidden = false;
  $('#again').focus({preventScroll:true});
}
function targetScreen(index) {
  const rect = host.getBoundingClientRect();
  const v = groups[index].center.clone().project(camera);
  // Keep the touch target inside the workshop even at unusual zoom/rotation.
  const x = Math.max(36, Math.min(rect.width - 36, (v.x + 1) * rect.width / 2));
  const y = Math.max(36, Math.min(rect.height - 100, (1 - v.y) * rect.height / 2));
  return { x: rect.left + x, y: rect.top + y, localX:x, localY:y };
}
function beginDrag(e,index) {
  if (e.button !== 0 || !ensurePlaying() || index < game.placed || drag) return;
  e.preventDefault(); select(index);
  drag = {index, pointer:e.pointerId, x:e.clientX, y:e.clientY, moved:false, image:null};
  groups[index].button.setPointerCapture(e.pointerId);
  controls.enabled = false;
}
function moveDrag(e) {
  if (!drag || e.pointerId !== drag.pointer) return;
  if (!ensurePlaying()) return;
  if (Math.hypot(e.clientX-drag.x,e.clientY-drag.y)>7) drag.moved = true;
  if (drag.moved && !drag.image) {
    drag.image = new Image(); drag.image.src=groups[drag.index].thumbnail; drag.image.className='drag-preview';
    document.body.append(drag.image); groups[drag.index].button.classList.add('picked');
  }
  if(drag.image){drag.image.style.left=e.clientX+'px';drag.image.style.top=e.clientY+'px';}
  const point=targetScreen(drag.index);
  $('#target').classList.toggle('near',Math.hypot(e.clientX-point.x,e.clientY-point.y)<66);
}
function clearDrag() {
  if (!drag) return;
  const b=groups[drag.index].button;
  if(b.hasPointerCapture(drag.pointer))b.releasePointerCapture(drag.pointer);
  drag.image?.remove(); b.classList.remove('picked'); drag=null;
  if(controls)controls.enabled=true; $('#target').classList.remove('near');
}
function endDrag(e) {
  if (!drag || e.pointerId!==drag.pointer) return;
  const {index,moved}=drag, p=targetScreen(index), rect=host.getBoundingClientRect();
  const inside=e.clientX>=rect.left&&e.clientX<=rect.right&&e.clientY>=rect.top&&e.clientY<=rect.bottom;
  const near=Math.hypot(e.clientX-p.x,e.clientY-p.y)<66;
  clearDrag();
  if(!ensurePlaying())return;
  if(moved){if(inside&&near)place(index);else status('靠近左侧标记再松手；也可以直接点击标记。');}
}
addEventListener('pointermove',moveDrag);
addEventListener('pointerup',endDrag);
addEventListener('pointercancel',clearDrag);
addEventListener('blur',clearDrag);
document.addEventListener('visibilitychange',()=>{if(document.hidden)clearDrag();if(game.status==='playing')ensurePlaying();});
$('#target').onclick=()=>{if(selected!==null)place(selected)};
$('#start').onclick=start; $('#restart').onclick=start; $('#again').onclick=start;
$('#help').onclick=()=>$('#help-dialog').showModal(); $('#reference-open').onclick=()=>$('#reference-dialog').showModal();
document.querySelectorAll('dialog').forEach(dialog=>dialog.querySelectorAll('.dialog-close,.dialog-done').forEach(button=>button.onclick=()=>dialog.close()));
$('#fullscreen').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{status('可使用浏览器菜单进入全屏。')}};
document.addEventListener('fullscreenchange',()=>$('#fullscreen').textContent=document.fullscreenElement?'退出全屏':'全屏 ⛶');
function resetView() {
  if(!camera)return;
  camera.position.set(5.5,3.8,7); controls.target.set(0,.7,-.22); controls.update();
}
$('#reset-view').onclick=resetView;
function zoom(factor){const delta=camera.position.clone().sub(controls.target);delta.setLength(THREE.MathUtils.clamp(delta.length()*factor,4.5,14));camera.position.copy(controls.target).add(delta);controls.update();}
$('#zoom-in').onclick=()=>zoom(.85);$('#zoom-out').onclick=()=>zoom(1.18);

function thumbnail(meshes,thumbRenderer) {
  const sc=new THREE.Scene(),root=new THREE.Group();
  meshes.forEach(m=>{const c=m.clone();c.visible=true;root.add(c)});
  const box=new THREE.Box3().setFromObject(root),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());
  root.position.sub(center);sc.add(root,new THREE.HemisphereLight(0xfff5df,0x647260,2.8));
  const light=new THREE.DirectionalLight(0xffeed7,3);light.position.set(3,5,4);sc.add(light);
  const extent=Math.max(size.x,size.y,size.z),cam=new THREE.PerspectiveCamera(30,1.7,.01,100);
  cam.position.set(extent*1.5,extent*1.2,extent*2.2);cam.lookAt(0,0,0);
  thumbRenderer.render(sc,cam);return thumbRenderer.domElement.toDataURL('image/png');
}
async function init() {
  scene=new THREE.Scene();camera=new THREE.PerspectiveCamera(33,1,.01,100);
  renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;host.append(renderer.domElement);
  controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.enablePan=false;
  controls.minDistance=4.5;controls.maxDistance=14;controls.maxPolarAngle=Math.PI*.79;controls.rotateSpeed=.7;
  resetView();
  scene.add(new THREE.HemisphereLight(0xfff3df,0x65705c,2.5));
  const sun=new THREE.DirectionalLight(0xffe9c8,3.3);sun.position.set(3,7,5);sun.castShadow=true;
  sun.shadow.mapSize.set(1024,1024);sun.shadow.camera.left=-4;sun.shadow.camera.right=4;sun.shadow.camera.top=4;sun.shadow.camera.bottom=-4;sun.shadow.normalBias=.025;scene.add(sun);
  const rim=new THREE.DirectionalLight(0xffffff,1.8);rim.position.set(-4,3,-4);scene.add(rim);
  const disk=new THREE.Mesh(new THREE.CylinderGeometry(1.65,1.7,.07,96),new THREE.MeshStandardMaterial({color:0xc8c9b8,roughness:.9}));
  disk.position.set(0,-1.095,-.1);disk.receiveShadow=true;scene.add(disk);
  const ring=new THREE.Mesh(new THREE.TorusGeometry(1.85,.006,6,120),new THREE.MeshBasicMaterial({color:0xbac0ad}));ring.rotation.x=-Math.PI/2;ring.position.set(0,-1.13,-.1);scene.add(ring);
  const source=(await new GLTFLoader().loadAsync('./assets/baoguosi-zhutou-v02.glb')).scene;
  source.updateMatrixWorld(true);
  const meshes=[];
  source.traverse(o=>{
    if(!o.isMesh)return;
    const geometry=o.geometry.clone().applyMatrix4(o.matrixWorld);
    const mesh=new THREE.Mesh(geometry,o.material.clone());mesh.name=o.name;mesh.userData={...o.userData};mesh.castShadow=true;mesh.receiveShadow=true;
    meshes.push(mesh);scene.add(mesh);
  });
  const matches=(m,fn)=>fn(m.userData.originalName||m.name);
  // GLTF object names retain dots; mapping uses the user's original identifiers.
  groups=definitions.map(([name,test])=>({name,meshes:meshes.filter(m=>matches(m,test)),ghosts:[]}));
  base=meshes.filter(m=>m.name==='context_gualeng_column');
  if(groups.some(g=>g.meshes.length===0)||groups.reduce((s,g)=>s+g.meshes.length,0)+base.length!==meshes.length)throw Error('构件清单与模型不一致');
  const thumbRenderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true});thumbRenderer.setSize(340,200);thumbRenderer.outputColorSpace=THREE.SRGBColorSpace;thumbRenderer.toneMapping=THREE.ACESFilmicToneMapping;
  groups.forEach((g,index)=>{
    const box=new THREE.Box3();g.meshes.forEach(m=>box.expandByObject(m));g.center=box.getCenter(new THREE.Vector3());
    g.thumbnail=thumbnail(g.meshes,thumbRenderer);
    g.meshes.forEach(mesh=>{
      mesh.visible=false;
      const ghost=new THREE.Mesh(mesh.geometry,new THREE.MeshStandardMaterial({color:0x86907d,transparent:true,opacity:.07,depthWrite:false,roughness:1}));
      scene.add(ghost);g.ghosts.push(ghost);
    });
    const b=document.createElement('button');g.button=b;b.className='piece';b.dataset.index=index;b.style.setProperty('--tilt',[-10,8,-4,5,-7,11][index%6]+'deg');
    b.setAttribute('aria-label',`选择${g.name}`);b.setAttribute('aria-pressed','false');b.disabled=true;
    b.innerHTML=`<img src="${g.thumbnail}" alt="" draggable="false"><span class="piece-name">${g.name}</span>${g.meshes.length>1?`<span class="piece-count">×${g.meshes.length}</span>`:''}`;
    b.addEventListener('pointerdown',e=>beginDrag(e,index));
    b.addEventListener('click',e=>{if(e.detail===0)select(index)});
  });
  // Spread pieces in a deterministic mixed order, with large touch regions.
  const scatter=[7,0,14,3,10,5,16,8,1,12,4,17,2,15,11,6,13,9];
  $('#parts').replaceChildren(...scatter.map(i=>groups[i].button));
  thumbRenderer.dispose();thumbRenderer.forceContextLoss();
  $('#piece-total').textContent=meshes.length-base.length;
  $('#load-state').hidden=true;loaded=true;$('#start').disabled=false;progress();
  $('#step-label').textContent='从栌斗开始，逐层拼起。';
  new ResizeObserver(()=>{
    width=host.clientWidth;height=host.clientHeight;if(!width||!height)return;
    renderer.setSize(width,height);camera.aspect=width/height;
    // Narrow screens retain the full height of the assembly, while allowing a generous width.
    camera.fov=THREE.MathUtils.radToDeg(2*Math.atan(Math.tan(THREE.MathUtils.degToRad(33)/2)/Math.min(1,camera.aspect/0.85)));
    camera.updateProjectionMatrix();
  }).observe(host);
  renderer.domElement.addEventListener('webglcontextlost',e=>{e.preventDefault();clearDrag();game.reset();$('#load-state').hidden=false;$('#load-state').textContent='三维显示已中断，请刷新后重试。';$('#start').disabled=true;loaded=false;});
  renderer.setAnimationLoop(t=>{
    controls.update();
    if(game.status==='playing'){game.tick(performance.now());setTimer();if(game.status==='lost')finish();}
    flyIns=flyIns.filter(f=>{const p=Math.min(1,(t-f.start)/330),offset=.18*Math.pow(1-p,3);f.meshes.forEach(m=>m.position.y=offset);return p<1});
    if(selected!==null&&game.status==='playing'){
      const p=targetScreen(selected);$('#target').style.left=p.localX+'px';$('#target').style.top=p.localY+'px';
    }
    renderer.render(scene,camera);
  });
}
init().catch(error=>{
  console.error(error);$('#load-state').textContent='模型暂未载入，请刷新页面重试。';status('请通过本地预览地址打开网页。');
  $('#start').disabled=true;$('#zoom-in').disabled=true;$('#zoom-out').disabled=true;
});
