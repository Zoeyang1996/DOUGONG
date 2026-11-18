from pathlib import Path
import json, shutil, hashlib, datetime
ROOT=Path.cwd(); DEST=Path(r'C:\Users\Administrator\Downloads')
NODE=Path(r'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe')
def put(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n',encoding='utf-8')
def cp(src,dst):shutil.copytree(src,dst,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.env','node_modules'))
PACKS={}
for role,act in [('C','act-02-globe'),('D','act-03-assembly')]:
 p=DEST/f'{role}同学-比赛独立训练包-11-19'
 if p.exists():raise RuntimeError('目标已存在，停止以避免覆盖：'+str(p))
 p.mkdir();PACKS[role]=p
 cp(ROOT/'web-exhibits'/act,p/'web'/act)
 cp(ROOT/'web-exhibits/shared',p/'web/shared')
 cp(ROOT/'docs/02-内容',p/'docs')
 (p/'runtime').mkdir();shutil.copy2(NODE,p/'runtime/node.exe')
 # Original sources stay byte-identical; shared relative imports stay inside this package.
 port=8781 if role=='C' else 8782
 put(p/'package.json',json.dumps({'name':'baoguosi-'+role.lower()+'-rehearsal','private':True,'scripts':{'start':'node server.cjs','test':'node --test tests/*.test.cjs'}},indent=2))
 put(p/'训练工程.code-workspace',json.dumps({'folders':[{'path':'.'}],'settings':{'files.exclude':{'原始备份':True,'runtime':True}},'tasks':{'version':'2.0.0','tasks':[{'label':'启动比赛工程','type':'process','command':'${workspaceFolder}/runtime/node.exe','args':['${workspaceFolder}/server.cjs'],'options':{'cwd':'${workspaceFolder}'},'problemMatcher':[]}] }},ensure_ascii=False,indent=2))
 put(p/'启动训练.cmd',f'''@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 请保留此窗口。关闭服务按 Ctrl+C。
start "" "http://localhost:{port}"
"%~dp0runtime\node.exe" "%~dp0server.cjs"
pause''')
 put(p/'运行检查.cmd','''@echo off
chcp 65001 >nul
cd /d "%~dp0"
"%~dp0runtime\node.exe" --test tests\*.test.cjs
pause''')
 put(p/'server.cjs',r'''
const http=require('node:http'),fs=require('node:fs'),path=require('node:path');
const ROOT=__dirname, PORT=Number(process.env.TRAINING_PORT||PORT_NUMBER);
const mime={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.css':'text/css; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.glb':'model/gltf-binary','.wasm':'application/wasm','.md':'text/plain; charset=utf-8'};
const send=(res,n,data)=>{res.writeHead(n,{'Content-Type':'application/json; charset=utf-8'});res.end(JSON.stringify(data))};
async function route(req,res){try{
 if(req.method==='GET'&&req.url==='/api/config'&&fs.existsSync(path.join(ROOT,'config/model.json'))){const c=JSON.parse(fs.readFileSync(path.join(ROOT,'config/model.json')));send(res,200,{mode:c.mode,model:c.model,configured:!!process.env.DEEPSEEK_API_KEY});return}
 if(req.method==='POST'&&req.url==='/api/chat'){
  let raw='';for await(const chunk of req){raw+=chunk;if(raw.length>16000){send(res,413,{error:'问题过长'});return}}
  const question=JSON.parse(raw).question;if(typeof question!=='string'||!question.trim()){send(res,400,{error:'请输入问题'});return}
  const {answer}=require('./services/guide.cjs');send(res,200,await answer(question));return;
 }
 if(req.method!=='GET'&&req.method!=='HEAD'){send(res,405,{error:'Method not allowed'});return}
 let pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
 let rel=pathname.startsWith('/docs/')?pathname.slice(1):'web'+pathname;
 let file=path.resolve(ROOT,rel);const web=path.join(ROOT,'web'),docs=path.join(ROOT,'docs');
 if(!(file.startsWith(web+path.sep)||file===web||file.startsWith(docs+path.sep))){send(res,403,{error:'Forbidden'});return}
 if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
 if(!fs.existsSync(file)||!fs.statSync(file).isFile()){send(res,404,{error:'文件不存在'});return}
 res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});
 if(req.method==='HEAD')res.end();else fs.createReadStream(file).pipe(res);
 }catch(e){send(res,400,{error:e.message?.slice(0,220)||'请求失败'})}}
const server=http.createServer(route);
if(require.main===module){
 const env=path.join(ROOT,'config/private.env');if(fs.existsSync(env))for(const line of fs.readFileSync(env,'utf8').split(/\r?\n/)){const m=line.match(/^DEEPSEEK_API_KEY=(.*)$/);if(m)process.env.DEEPSEEK_API_KEY=m[1].trim()}
 server.on('error',e=>{console.error(e.code==='EADDRINUSE'?'端口已占用，请关闭本包此前的启动窗口。':e.message);process.exitCode=1});server.listen(PORT,'127.0.0.1',()=>console.log('本机比赛工程：http://localhost:'+PORT+'；按Ctrl+C停止'));
}
module.exports={server};
'''.replace('PORT_NUMBER',str(port)))
 title='C同学 · 小拱与木构典藏' if role=='C' else 'D同学 · 120秒触屏斗拱拼接'
 links='<a href="guide/">打开小拱智能体</a>' if role=='C' else ''
 put(p/'web/index.html',f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{title}</title><style>body{{font:20px/1.8 sans-serif;max-width:900px;margin:80px auto;background:#f4efe5;color:#30271f}}a{{display:block;margin:20px 0;padding:25px;background:white;color:inherit}}small{{color:#665}}</style><h1>{title}</h1><p>比赛与训练使用同一工程 · 版本11-19</p>{links}<a href="{act}/">打开{'木构典藏' if role=='C' else '120秒触屏挑战'}</a><small>启动和操作说明见文件夹中的《从这里开始》与《逐步排练》。使用完毕关闭本包启动窗口。</small></html>''')
 # No private existing environment files are copied.
 put(p/'.gitignore','config/private.env\n练习留档/\n')
 put(p/'tests/package.test.cjs',r'''
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
test('local package has entry, runtime and engine',()=>{for(const f of ['web/index.html','runtime/node.exe','web/shared/vendor/three.module.js','server.cjs'])assert.ok(fs.existsSync(path.join(root,f)),f)});
test('HTTP serves only package public files',async()=>{const {server}=require('../server.cjs');await new Promise(r=>server.listen(0,'127.0.0.1',r));try{const u='http://127.0.0.1:'+server.address().port;assert.equal((await fetch(u)).status,200);assert.equal((await fetch(u+'/config/private.env')).status,404)}finally{await new Promise(r=>server.close(r))}});
''')
C=PACKS['C'];D=PACKS['D']
put(C/'config/model.json',json.dumps({'mode':'local','baseUrl':'https://api.deepseek.com','model':''},ensure_ascii=False,indent=2))
put(C/'config/private.env.example','DEEPSEEK_API_KEY=在本机填入自己的密钥')
put(C/'knowledge/cards.json',json.dumps([
{'id':'BG001','question':'保国寺大殿建于哪一年','keywords':['大殿','建于','哪一年','年代'],'answer':'保国寺现存大殿建于北宋大中祥符六年，即1013年。','source':'/docs/01-保国寺-历史沿革与价值.md','locator':'基础档案'},
{'id':'BG002','question':'七铺作是不是七个斗','keywords':['七铺作','七个斗','铺作'],'answer':'不是。铺作等级不能按斗的个数理解，应结合出跳和铺作层次辨认。','source':'/docs/04-斗拱-读法与铺作.md','locator':'出跳与铺作等级'}],ensure_ascii=False,indent=2))
put(C/'services/guide.cjs',r'''
const fs=require('node:fs'),path=require('node:path');const ROOT=path.resolve(__dirname,'..');
function cards(){const cs=JSON.parse(fs.readFileSync(path.join(ROOT,'knowledge/cards.json'),'utf8').replace(/^\uFEFF/,''));const ids=new Set();for(const c of cs){for(const k of ['id','question','keywords','answer','source','locator'])if(!c[k])throw Error('知识卡缺少字段 '+k);if(ids.has(c.id))throw Error('知识卡ID重复');if(!Array.isArray(c.keywords)||!c.keywords.length)throw Error('keywords必须为非空数组');ids.add(c.id)}return cs}
function retrieve(q){return cards().map(c=>({c,s:c.keywords.filter(k=>q.includes(k)).length})).filter(x=>x.s>0).sort((a,b)=>b.s-a.s).slice(0,3).map(x=>x.c)}
async function answer(q){const refs=retrieve(q);if(!refs.length)return {answer:'当前资料不足，无法确认。请换个木构相关问题或查阅原始资料。',refs:[],mode:'无依据，未调用模型'};
 const cfg=JSON.parse(fs.readFileSync(path.join(ROOT,'config/model.json'),'utf8').replace(/^\uFEFF/,''));
 if(cfg.mode==='local')return {answer:refs[0].answer,refs,mode:'本地资料检索 · 未调用大模型'};
 if(cfg.mode!=='deepseek')throw Error('mode仅支持local或deepseek');
 if(!cfg.model||!process.env.DEEPSEEK_API_KEY)throw Error('请填写实际model ID和后端密钥，再重启服务');
 if(cfg.baseUrl!=='https://api.deepseek.com')throw Error('此版本仅连接DeepSeek官方API');
 const response=await fetch(cfg.baseUrl+'/chat/completions',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+process.env.DEEPSEEK_API_KEY},body:JSON.stringify({model:cfg.model,messages:[{role:'system',content:'你是木构科普助手小拱。仅依据以下资料，用简洁中文回答，资料不足应说明。资料：'+JSON.stringify(refs)},{role:'user',content:q}]}),signal:AbortSignal.timeout(30000)});
 if(!response.ok)throw Error('模型服务返回HTTP '+response.status+'，检查网络、账号和模型ID');
 const data=await response.json();return {answer:data.choices[0].message.content,refs,mode:'真实模型调用 · '+data.model};}
module.exports={cards,retrieve,answer};
''')
put(C/'web/guide/character-config.json',json.dumps({'modelUrl':'','scale':1,'animations':{'idle':'','listening':'','thinking':'','speaking':''}},indent=2))
put(C/'web/guide/index.html',r'''
<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>小拱 · 木构问答</title><link rel="stylesheet" href="style.css"><script type="importmap">{"imports":{"three":"../shared/vendor/three.module.js"}}</script>
<header><a href="../">← 比赛入口</a><span>榫卯智言 / 小拱智能体</span><a href="../act-02-globe/">木构典藏 →</a></header>
<main><section class="character"><div id="stage"></div><p id="model-note">模拟角色 · 后续替换真实带骨骼GLB</p><div class="identity"><h1>和小拱聊一聊</h1><p>从一座宋代大殿，认识中国木构。</p><strong id="state">待机</strong></div></section>
<section class="conversation"><p class="eyebrow">有依据的木构讲解</p><h2>你想了解什么？</h2><div class="quick"><button data-q="保国寺大殿建于哪一年？">大殿的年代</button><button data-q="七铺作是不是七个斗？">认识七铺作</button></div><label for="question">输入问题，或用语音提问</label><textarea id="question" rows="3">保国寺大殿建于哪一年？</textarea><div class="actions"><button id="ask">发送问题</button><button id="record">开始录音</button><button id="stop">停止录音</button><button id="cancel">停止朗读</button></div><label><input type="checkbox" id="auto" checked> 回答后朗读</label><button id="speak">重新朗读</button><p id="mode">正在读取服务配置</p><p id="notice" role="status"></p><article id="answer" aria-live="polite">你好，我是小拱。我们从保国寺开始吧。</article><details open><summary>本轮资料依据</summary><div id="refs">提交问题后显示命中的知识卡。</div></details></section></main><script type="module" src="app.js"></script></html>
''')
put(C/'web/guide/style.css',r'''
*{box-sizing:border-box}body{margin:0;background:#f3eee4;color:#302a21;font:16px/1.7 "Microsoft YaHei",sans-serif}header{height:76px;padding:0 4%;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #d8cbb7}a{color:#66543d}main{display:grid;grid-template-columns:45% 55%;min-height:calc(100vh - 76px)}.character{position:relative;background:radial-gradient(ellipse,#e6d6b9,#eae3d6);min-height:680px}#stage{height:460px;width:100%}#stage canvas{display:block}#model-note{text-align:center;font-size:13px;color:#685d4b}.identity{text-align:center}h1{font-size:32px;margin:12px}#state{display:inline-block;background:#e0d7c5;padding:7px 30px;border-radius:40px}.conversation{padding:36px 8% 40px}.eyebrow{font-size:13px;letter-spacing:.2em;color:#836849}h2{font-size:30px;margin:6px 0 22px}button{min-height:44px;border:1px solid #cbbda6;border-radius:6px;background:#fffaf0;color:#443a2a;padding:8px 15px;font:inherit;cursor:pointer;margin:4px}button:disabled{opacity:.5}#ask{background:#665136;color:white}.quick{margin-bottom:20px}textarea{display:block;width:100%;font:inherit;padding:14px;margin:8px 0;background:#fffcf6;border:1px solid #cbbda6;border-radius:8px;resize:vertical}#answer{padding:20px;background:#fffcf6;border-left:3px solid #94764d;min-height:110px;margin:16px 0;white-space:pre-wrap}#mode,#notice{font-size:13px;color:#745c40}#refs p{border-bottom:1px solid #d9ccba;padding:8px 0}details{font-size:14px}@media(max-width:850px){main{grid-template-columns:1fr}.character{min-height:470px}#stage{height:300px}.conversation{padding:24px}header{font-size:12px;padding:10px}}
''')
put(C/'web/guide/character.js',r'''
import * as THREE from 'three';import {GLTFLoader} from '../shared/vendor/GLTFLoader.js';
export async function createCharacter(host){
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(34,1,.1,100);camera.position.set(0,1.7,6);camera.lookAt(0,1.3,0);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
scene.add(new THREE.HemisphereLight(0xffffff,0x73634e,2));const light=new THREE.DirectionalLight(0xffe8c4,3);light.position.set(3,5,4);scene.add(light);
const root=new THREE.Group();scene.add(root);let mode='idle',mixer=null,actions={},current=null,simulation=true;
const wood=new THREE.MeshStandardMaterial({color:0xaa7644,roughness:.65}),robe=new THREE.MeshStandardMaterial({color:0x6f7965,roughness:.85}),dark=new THREE.MeshStandardMaterial({color:0x34291f});
function box(w,h,d,mat,x,y,z,parent=root){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.position.set(x,y,z);parent.add(m);return m}
const head=new THREE.Group();head.position.y=2;root.add(head);box(.75,.65,.62,wood,0,0,0,head);box(.09,.11,.05,dark,-.18,.03,.33,head);box(.09,.11,.05,dark,.18,.03,.33,head);
const mouth=box(.22,.04,.05,dark,0,-.18,.33,head);box(1.1,.14,.45,wood,0,.4,0,head);box(.75,.15,.5,wood,0,.55,0,head);box(.45,.15,.6,wood,0,.7,0,head);
box(.85,1.05,.55,robe,0,1.15,0);box(.25,.35,.4,dark,-.22,.45,0);box(.25,.35,.4,dark,.22,.45,0);
const arm=new THREE.Group();arm.position.set(.55,1.65,0);root.add(arm);box(.2,.7,.24,wood,0,-.3,0,arm);box(.2,.7,.24,wood,-.55,1.3,0);
try{const cfg=await fetch('character-config.json').then(r=>r.json());if(cfg.modelUrl){const gltf=await new GLTFLoader().loadAsync(cfg.modelUrl);root.clear();root.add(gltf.scene);gltf.scene.scale.setScalar(cfg.scale||1);mixer=new THREE.AnimationMixer(gltf.scene);for(const [state,name] of Object.entries(cfg.animations)){const clip=gltf.animations.find(a=>a.name===name);if(clip)actions[state]=mixer.clipAction(clip)}simulation=false;document.querySelector('#model-note').textContent='已载入角色GLB · 动作按配置映射';}}
catch(e){document.querySelector('#model-note').textContent='真实模型加载失败，当前为模拟角色：'+e.message}
const clock=new THREE.Clock();new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix()}).observe(host);
renderer.setAnimationLoop(t=>{const dt=clock.getDelta();if(mixer)mixer.update(dt);if(simulation){root.position.y=Math.sin(t*.002)*.025;head.rotation.z=mode==='thinking'?.12:mode==='listening'?-.09:0;arm.rotation.z=mode==='speaking'?Math.sin(t*.007)*.25-.35:0;mouth.scale.y=mode==='speaking'?1+Math.abs(Math.sin(t*.015))*3:1}renderer.render(scene,camera)});
return state=>{mode=state;const next=actions[state];if(next&&next!==current){current?.fadeOut(.2);next.reset().fadeIn(.2).play();current=next}else if(!next&&current){current.fadeOut(.2);current=null}};
}
''')
put(C/'web/guide/app.js',r'''
import {createCharacter} from './character.js';
const $=s=>document.querySelector(s);const names={idle:'待机',listening:'聆听',thinking:'思考',speaking:'朗读'};let animate=()=>{},busy=false,latest='',rec=null,recording=false,epoch=0;
createCharacter($('#stage')).then(fn=>animate=fn).catch(e=>$('#model-note').textContent='三维显示不可用：'+e.message);
function setState(s){$('#state').textContent=names[s];animate(s)}
function stopSpeech(){epoch++;speechSynthesis.cancel();setState('idle')}
function speak(){if(!latest)return;stopSpeech();const token=epoch;const u=new SpeechSynthesisUtterance(latest);u.lang='zh-CN';u.onstart=()=>{if(token===epoch)setState('speaking')};u.onend=()=>{if(token===epoch)setState('idle')};u.onerror=()=>{if(token===epoch){setState('idle');$('#notice').textContent='朗读未完成，可点击重新朗读'}};speechSynthesis.speak(u)}
async function ask(){if(busy)return;if(recording)rec.stop();stopSpeech();busy=true;$('#ask').disabled=true;setState('thinking');$('#notice').textContent='';$('#refs').replaceChildren();
try{const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:$('#question').value}),signal:AbortSignal.timeout(35000)});const d=await response.json();if(!response.ok)throw Error(d.error);latest=d.answer;$('#answer').textContent=latest;$('#mode').textContent=d.mode;
for(const c of d.refs){const p=document.createElement('p');p.textContent=c.id+' · '+c.locator+' ';const a=document.createElement('a');a.href=c.source;a.target='_blank';a.rel='noopener';a.textContent='查看原文';p.append(a);$('#refs').append(p)}if(!d.refs.length)$('#refs').textContent='本轮无匹配资料。';setState('idle');if($('#auto').checked)speak();}
catch(e){latest='';$('#answer').textContent='本次请求未完成';$('#notice').textContent=e.message;setState('idle')}finally{busy=false;$('#ask').disabled=false}}
$('#ask').onclick=ask;$('#speak').onclick=speak;$('#cancel').onclick=stopSpeech;document.querySelectorAll('[data-q]').forEach(b=>b.onclick=()=>{$('#question').value=b.dataset.q;ask()});
const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
if(Recognition){rec=new Recognition();rec.lang='zh-CN';rec.interimResults=false;rec.onstart=()=>{recording=true;setState('listening');$('#notice').textContent='正在聆听，说完后点击停止录音'};rec.onresult=e=>{$('#question').value=e.results[0][0].transcript;ask()};rec.onerror=e=>{$('#notice').textContent='语音识别未完成：'+e.error;setState('idle')};rec.onend=()=>{recording=false;if(!busy&&$('#state').textContent==='聆听')setState('idle')};$('#record').onclick=()=>{if(busy||recording)return;stopSpeech();try{rec.start()}catch(e){$('#notice').textContent=e.message}};$('#stop').onclick=()=>rec.stop();}
else{$('#record').disabled=true;$('#notice').textContent='此浏览器不支持当前语音识别接口，请使用已验证的Edge/Chrome；文字输入仍可使用。'}
fetch('/api/config').then(r=>r.json()).then(c=>$('#mode').textContent=c.mode==='local'?'当前：本地检索模式，未调用大模型':'当前：DeepSeek模式 · '+(c.model||'模型ID待配置')).catch(e=>$('#notice').textContent=e.message);
''')
put(C/'tests/guide.test.cjs',r'''
const test=require('node:test'),assert=require('node:assert/strict');const {cards,retrieve,answer}=require('../services/guide.cjs');
test('cards and sources',()=>{assert.equal(cards().length,2);assert.equal(retrieve('七铺作是不是七个斗')[0].id,'BG002')});
test('known fact and boundary',async()=>{assert.match((await answer('大殿哪一年')).answer,/1013/);assert.deepEqual((await answer('火星人口')).refs,[])});
''')
put(D/'tests/game.test.cjs',r'''
const test=require('node:test'),assert=require('node:assert/strict');
test('120 seconds, ordered assembly, duplicate rejection and restart',async()=>{const {Challenge}=await import('../web/act-03-assembly/game-state.mjs');const g=new Challenge();g.start(0);assert.equal(g.duration,120000);assert.equal(g.place(1,1),false);assert.equal(g.place(0,1),true);assert.equal(g.place(0,2),false);assert.equal(g.place(1,120000),false);g.start(200000);for(let i=0;i<18;i++)assert.equal(g.place(i,200001+i),true);assert.equal(g.status,'won');g.start(300000);assert.equal(g.placed,0)});
''')
# Original editable source + classroom operation notes; include distribution exports without relying on their old build tool path.
cp(ROOT/'output/小小营造师-西沃离线版',D/'离线成品参考')
for p in PACKS.values():
 for part in ['web','docs','services','knowledge','config','tests']:
  if (p/part).exists():cp(p/part,p/'原始备份'/part)
 shutil.copy2(p/'server.cjs',p/'原始备份/server.cjs')
 put(p/'还原练习.ps1',r'''
$ErrorActionPreference='Stop'
$base=[IO.Path]::GetFullPath($PSScriptRoot)
$archive=Join-Path $base ('练习留档\'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $archive -Force | Out-Null
foreach($part in @('web','docs','services','knowledge','config','tests','server.cjs')) {
 $source=Join-Path (Join-Path $base '原始备份') $part
 $target=Join-Path $base $part
 if(Test-Path -LiteralPath $source) {
  if(Test-Path -LiteralPath $target){Copy-Item -LiteralPath $target -Destination $archive -Recurse -Force}
  # Copy contents into the existing directory, no recursive deletion.
  if((Get-Item -LiteralPath $source).PSIsContainer){New-Item -ItemType Directory -Path $target -Force|Out-Null;Get-ChildItem -LiteralPath $source -Force|ForEach-Object{Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force}}
  else{Copy-Item -LiteralPath $source -Destination $target -Force}
 }
}
Write-Host '基准文件已恢复；额外新增文件保留；旧练习已复制留档。请重启服务。'
''')
 hashes={str(f.relative_to(p)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'web').rglob('*') if f.is_file()}
 put(p/'原始文件校验.json',json.dumps(hashes,ensure_ascii=False,indent=2))
print(json.dumps({r:str(p) for r,p in PACKS.items()},ensure_ascii=False))
