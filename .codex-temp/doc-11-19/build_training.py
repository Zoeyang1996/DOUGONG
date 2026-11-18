from pathlib import Path
import json
root=Path.cwd(); base=root/'竞赛演示/03-岗位讲解与实操/版本11-19'
train=base/'01-C与D分步训练'; outlines=base/'02-四岗台词大纲'
train.mkdir(exist_ok=True);outlines.mkdir(exist_ok=True)
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.strip()+'\n',encoding='utf-8')
lab=train/'C-智能体基础练习';lab.mkdir(exist_ok=True)
write(lab/'cards.json',json.dumps([{'id':'BG001','question':'保国寺现存大殿建于哪一年？','keywords':['大殿','建于','哪一年','年代'],'answer':'依据项目现有资料，保国寺大殿建于北宋大中祥符六年，即公元1013年。','source':'docs/02-内容/01-保国寺-历史沿革与价值.md','locator':'基础档案 大殿建造年代'}],ensure_ascii=False,indent=2))
write(lab/'config.json',json.dumps({'mode':'local','base_url':'https://api.deepseek.com','model':'','voiceEnabled':False},ensure_ascii=False,indent=2))
write(lab/'server.py',r'''
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, os, urllib.request
ROOT=Path(__file__).resolve().parent

def cards():
    data=json.loads((ROOT/'cards.json').read_text(encoding='utf-8-sig'))
    ids=set()
    for c in data:
        for key in ('id','question','keywords','answer','source','locator'):
            if not c.get(key):raise ValueError('知识卡缺少 '+key)
        if c['id'] in ids:raise ValueError('重复ID '+c['id'])
        if not isinstance(c['keywords'],list):raise ValueError('keywords必须为列表')
        ids.add(c['id'])
    return data

def retrieve(question):
    ranked=sorted([(sum(k in question for k in c['keywords']),c) for c in cards()],key=lambda x:x[0],reverse=True)
    return [c for score,c in ranked if score>0][:3]

def answer(question):
    refs=retrieve(question)
    cfg=json.loads((ROOT/'config.json').read_text(encoding='utf-8-sig'))
    if not refs:return {'answer':'现有训练资料没有依据，暂时无法确认。','refs':[],'mode':'未调用模型'}
    if cfg['mode']=='local':return {'answer':refs[0]['answer'],'refs':refs,'mode':'本地检索练习，不是大模型回答'}
    if cfg['mode']!='deepseek':raise ValueError('mode必须为local或deepseek')
    key=os.environ.get('DEEPSEEK_API_KEY','');model=cfg.get('model','')
    if not key or not model:raise ValueError('请配置后端环境变量DEEPSEEK_API_KEY及实际model ID')
    # Training deliberately restricts destination to the documented official endpoint.
    if cfg['base_url'].rstrip('/')!='https://api.deepseek.com':raise ValueError('此练习仅使用官方API地址')
    body={'model':model,'messages':[{'role':'system','content':'仅依据给定资料回答；资料不足说明无法确认。资料：'+json.dumps(refs,ensure_ascii=False)},{'role':'user','content':question}]}
    req=urllib.request.Request(cfg['base_url'].rstrip('/')+'/chat/completions',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    with urllib.request.urlopen(req,timeout=30) as res:data=json.load(res)
    return {'answer':data['choices'][0]['message']['content'],'refs':refs,'mode':'真实API '+data.get('model',model)}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
    def send_json(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.end_headers();self.wfile.write(raw)
    def do_POST(self):
        if self.path!='/ask':self.send_json({'error':'Not found'},404);return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>16000:raise ValueError('请求大小不合法')
            q=json.loads(self.rfile.read(size)).get('question','').strip()
            if not q:raise ValueError('请输入问题')
            self.send_json(answer(q))
        except Exception as e:
            # Do not return provider response bodies or secrets.
            self.send_json({'error':str(e) if isinstance(e,ValueError) else '请求失败：'+type(e).__name__},400)
if __name__=='__main__':
    cards();print('打开 http://localhost:8031；Ctrl+C停止。')
    ThreadingHTTPServer(('127.0.0.1',8031),Handler).serve_forever()
''')
write(lab/'index.html',r'''
<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>C智能体流程训练</title>
<style>body{max-width:850px;margin:40px auto;font:18px/1.8 sans-serif;padding:20px;background:#f5f1e9;color:#30291f}button,input{font:inherit;padding:12px;margin:5px}input{width:75%}pre{white-space:pre-wrap;background:white;padding:20px}#state{font-weight:bold}</style>
<h1>C同学：知识与语音流程训练</h1><p>独立练习样例。此页用文字表示角色状态，不是正式三维小拱。默认本地检索，切换API后才调用大模型。</p>
<p id="state">待机</p><input id="question" value="保国寺现存大殿建于哪一年？"><button id="ask">提问</button><br>
<button id="record" disabled>开始录音</button><button id="stop">停止录音</button><button id="speak">朗读回答</button><button id="cancel">停止朗读</button>
<p id="mode"></p><pre id="answer"></pre><h2>本轮资料</h2><pre id="refs"></pre>
<script>
const $=s=>document.querySelector(s);let latest='',recognition,busy=false;
function state(s){$('#state').textContent=s}
async function ask(){if(busy)return;busy=true;state('思考');$('#answer').textContent='';
 try{const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:$('#question').value})});const d=await r.json();if(!r.ok)throw Error(d.error);latest=d.answer;$('#answer').textContent=latest;$('#refs').textContent=JSON.stringify(d.refs,null,2);$('#mode').textContent=d.mode}
 catch(e){latest='';$('#answer').textContent=e.message;$('#refs').textContent='';$('#mode').textContent='请求未完成'}finally{busy=false;state('待机')}}
$('#ask').onclick=ask;
$('#speak').onclick=()=>{if(!latest)return;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(latest);u.lang='zh-CN';u.onstart=()=>state('朗读');u.onend=u.onerror=()=>state('待机');speechSynthesis.speak(u)};
$('#cancel').onclick=()=>{speechSynthesis.cancel();state('待机')};
async function initVoice(){const cfg=await fetch('config.json').then(r=>r.json());if(!cfg.voiceEnabled){$('#mode').textContent='录音未接通：完成训练步骤后启用';return}
 const R=window.SpeechRecognition||window.webkitSpeechRecognition;
 if(!R){$('#mode').textContent='此浏览器无可用语音识别接口；请改用文字测试，并记录语音未通过';return}
 recognition=new R();recognition.lang='zh-CN';recognition.interimResults=false;
 recognition.onstart=()=>state('聆听');recognition.onerror=e=>{$('#mode').textContent='识别失败：'+e.error;state('待机')};recognition.onend=()=>{if(!busy)state('待机')};
 recognition.onresult=e=>{$('#question').value=e.results[0][0].transcript; /* TRAIN_C: 在这里调用问答函数 */};
 $('#record').disabled=false;$('#record').onclick=()=>{if(!busy)try{recognition.start()}catch(e){$('#mode').textContent=e.message}};
 $('#stop').onclick=()=>recognition.stop();}
initVoice().catch(e=>$('#mode').textContent=e.message);
</script></html>
''')
write(lab/'test_lab.py',r'''
import unittest
from server import cards,retrieve,answer
class LabTests(unittest.TestCase):
 def test_cards(self):self.assertTrue(cards())
 def test_known(self):self.assertTrue(retrieve('大殿建于哪一年'))
 def test_unknown(self):self.assertEqual(retrieve('火星人口多少'),[])
 def test_boundary(self):self.assertEqual(answer('火星人口多少')['refs'],[])
if __name__=='__main__':unittest.main()
''')
write(train/'00-从这里开始.md',r'''
# C与D分步训练入口
基准：版本11-19 v1.2；D本包只含120秒触屏斗拱拼接，不含Unity、VR或PICO训练。台词大纲在同级“02-四岗台词大纲”。

1. 安装并打开VS Code、Chrome或Edge、Python 3、Node.js。终端分别运行 `python --version` 与 `node --version`，均显示版本后继续。若Windows只有 `py`，后文python命令改用py。
2. C从《C-分步训练手册.md》开始，使用本包内独立练习，不需要恢复旧工程。真实模型调用需要教师提供可用账号、模型ID与密钥；无账号时可完成本地检索训练，但不能记为API通过。
3. D从《D-120秒触屏斗拱训练手册.md》开始，按手册复制独立训练目录，正式工程保持原样。
4. 每次练习后填写《训练记录模板.md》，记录实际结果、截图位置和下一次要修正的内容。

建议进度：第一轮理解与打开工程；第二轮逐项修改；第三轮反例测试；第四轮按C 6分钟与4分钟、D 5分钟计时讲解。学习阶段不限于赛场时间，不要在尚未熟练时同时赶时间。

文件状态：C样例是真实可运行的独立基础练习，默认本地关键词检索；语音使用浏览器提供的识别与合成，支持和联网情况需实机验证；三维小拱尚需接回正式工程。D和C典藏训练直接依据现有源码入口。正式设备触控、麦克风与外部API不因文件生成就视为验收通过。
''')
write(train/'C-分步训练手册.md',r'''
# C同学分步训练手册
目标：掌握知识卡制作、检索、DeepSeek调用、语音与状态，再掌握木构典藏的AI辅助修改与人工镜头调整。先独立练熟，再压缩为第三段6分钟、第十段4分钟。

## 第一课 打开可运行的训练起点
1. 用文件资源管理器进入本包的“C-智能体基础练习”，复制整个文件夹为“C-我的练习”。前者保留作重练起点。
2. VS Code选择“文件 → 打开文件夹”，打开“C-我的练习”。左侧应看到server.py、cards.json、config.json、index.html、test_lab.py。
3. 选择“终端 → 新建终端”，输入 `python server.py`，看到localhost:8031后不要关闭终端。
4. Chrome/Edge访问 `http://localhost:8031`，点击提问。应看到1013年、资料卡及“本地检索练习，不是大模型回答”。
5. 新建第二个终端，运行 `python -m unittest -v test_lab.py`。四项通过后截图。端口占用时关闭之前的训练服务再重试，不要结束不认识的进程。

验收：能独立启动页面、回答已知问题；输入“火星人口多少”显示无依据。页面是文字状态训练器，不冒充三维小拱。

## 第二课 从资料到知识卡
1. 在原DOUGONG工程打开 `docs/02-内容/04-斗拱-读法与铺作.md`，查找铺作解释；与教师核对“七铺作是不是七个斗”的资料依据。
2. 回练习窗口打开cards.json，复制第一条对象，在数组中加逗号后粘贴。把id改为BG002，question改成上述问题，keywords填为 `["七铺作","七个斗","铺作"]`。
3. answer由自己依据核对后的资料概括，source写实际文件名或原始出处，locator写章节/页码；不要留空或复制未经核对的模型输出。
4. 保存；第二终端运行单元测试。若提示JSON错误，检查逗号、英文双引号与数组括号；若重复ID则改为唯一编号。
5. 刷新网页，分别输入“七铺作是不是七个斗”“如何理解七铺作”。两次都应显示BG002资料。服务每次读取知识卡，修改后无需重启。
6. 打开server.py的retrieve，解释关键词计分和最多三条结果；删去一个关键词比较命中变化，再恢复。

验收：提交新增知识卡、原文依据和两种问法的截图。此练习采用关键词检索，没有建立向量数据库。

## 第三课 接通真实模型
前提：教师提供官方API可用模型ID和密钥；一次提交会向该API发送问题与命中的训练资料。仅使用公开教学资料。不开通账号也可先完成前两课。
1. 在运行服务的终端按Ctrl+C停止；config.json将mode由local改为deepseek，model填写账号实际可用的完整模型ID。不要把口头的“4.1”直接当接口ID。
2. 在PowerShell以隐藏输入方式设置本次终端环境：
```powershell
$secret = Read-Host '输入训练API密钥' -AsSecureString
$env:DEEPSEEK_API_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
python server.py
```
3. 打开server.py，依次定位读取配置、retrieve、messages、urllib.request.Request和模型返回字段；指出检索资料如何进入system消息，游客问题如何进入user消息。
4. 网页问同一问题，检查模式显示“真实API”及返回的模型标识。F12 → Network查看/ask的响应，应含answer、refs和mode；截图不要包含密钥。
5. 将model暂时设成空值，保存后再问一次，观察缺配置提示；恢复正确ID。输入无关问题，确认先提示无资料，不编造答案。
6. 练习结束Ctrl+C停止服务，运行 `Remove-Item Env:DEEPSEEK_API_KEY` 清掉本终端变量；恢复mode为local便于离线练习。

错误处理：连接失败先检查网络、模型ID和账号权限；本样例返回错误类型，不把真实失败改成假答案。官方配置说明：https://api-docs.deepseek.com/en/ ，模型列表：https://api-docs.deepseek.com/api/list-models/ 。
验收：一轮真实响应和一次错误处理。云端调用不能讲成本地部署。

## 第四课 现场接通语音
1. 起点：网页录音按钮不可用。config.json把voiceEnabled改成true，保存刷新。若显示浏览器不支持，换到教师已验证的Chrome/Edge；仍不支持则记录未通过，不能用文字输入冒充识别。
2. 点击开始录音，允许本页麦克风，问“大殿建于哪一年”，点击停止。识别文字进入输入框；此时不会自动提交，这是本课留出的连接点。
3. VS Code打开index.html，搜索 `TRAIN_C`，把该注释替换为 `ask();`，保存刷新。重新录音后应自动检索并显示回答。
4. 点击朗读回答，观察“朗读 → 待机”；再朗读并点击停止，确认恢复。浏览器需有可用中文语音；听不到声音检查音量与声音输出。
5. 打开index.html搜索onstart、onresult、onend、onerror，逐一指出聆听、思考、朗读、待机状态在哪里改变。浏览器语音识别可能依赖联网服务；未许可或网络错误有提示，不能保证离线识别。
6. 如需自动朗读，把朗读处理抽成speakAnswer函数，在回答成功后调用；保留按钮作为自动播放受限时的入口。先保证手动朗读通过再做扩展。

验收：录屏一轮“开始 → 停止 → 识别 → 回答 → 朗读 → 待机”；另录一次识别失败或取消。三维接回时，将文字状态映射到B交付的真实动画片段；本包没有虚构现成骨骼与动画。无角色GLB时先完成文字链路并记录该项待接入。

## 第五课 木构典藏的实际文件与运行
1. 在DOUGONG的web-exhibits下新建“training-C-atlas”，复制整个act-02-globe中的内容到这里，保持与shared同级。VS Code打开DOUGONG，不修改原act-02-globe。
2. 根目录终端运行 `python -m http.server 8032 --bind 127.0.0.1`；浏览器打开 `http://localhost:8032/web-exhibits/training-C-atlas/`。
3. 打开复制目录index.html，确认末尾加载js/main.js。不要修改旧app.js：当前网页入口采用模块目录。
4. 打开js/views/detail.js搜索 `if (item.model)`，定位有模型才显示入口的条件；打开js/viewer.js定位模型加载和关闭；在data.json中查找已有model字段，选择一个真实有模型条目和一个无模型条目。
5. 点击两个样本，记录实际入口区别；打开有模型预览、旋转、关闭、再次打开。若模型404，F12网络面板查看实际请求路径，再核对文件，不随便改URL前缀。

## 第六课 AI局部修改与人工镜头训练
1. 先复制待修改的detail.js和globe/globe.js为.bak留在练习目录。使用团队确定的AI编程工具；本稿不把Harness当成某个固定产品名。
2. 提交任务：“只在training-C-atlas中修改详情页，使有模型入口的提示更清楚，保留item.model判断；不修改原项目，不新增无效模型路径；给出文件差异与测试步骤。”
3. 逐行查看差异后再接受。检查无模型条目仍只显示图文，有模型条目仍能打开三维；若AI删掉条件，拒绝该改动并让其修正。
4. 打开js/globe/globe.js，搜索TWEEN_MS，记录原值1100；改成1600，保存刷新，比较聚焦时长。再还原1100。这是参数训练，不宣称修复了原本不存在的缺陷。
5. 搜索focus和tween，阅读起点、目标、开始时间以及每帧progress；边看代码边在浏览器连续点击建筑A、B，核对最终停在B。现有代码已具备过渡，不为舞台效果破坏原工程。
6. 练习说明相机平滑与实际三维入口如何验证；提交修改差异和“有模型、无模型、连点、返回、开关预览”五项结果。

## 压缩为比赛操作
第三段6分钟：35秒接资产说明；70秒新增知识卡；50秒模型配置与真实请求；40秒检索验证；65秒语音事件连接；60秒状态与朗读；40秒完整验证和交接。先练会再计时，等待计入机动。
第十段4分钟：40秒定位设计与代码；40秒限定AI任务；40秒审查差异；60秒人工镜头操作；60秒五项验证与返回入口。
重练：关闭服务，用保留的C-智能体基础练习另复制一个新练习目录；典藏只在training-C-atlas内恢复自己的.bak。不要覆盖原工程、密钥或同学文件。
''')
write(train/'D-120秒触屏斗拱训练手册.md',r'''
# D同学 120秒触屏斗拱拼接训练
本文件只练触屏网页，不含Unity、VR、PICO。基准是现有“小小营造师”：57个构件，柱头预置，其余构件合为18组，120秒内依次拼接。它是单组铺作挑战，不把它讲成整殿搭建。

## 第一课 建立独立训练副本
1. VS Code打开DOUGONG根目录；在资源管理器展开web-exhibits。
2. 在文件资源管理器复制act-03-assembly为training-D-assembly，仍放在web-exhibits下；两个目录与shared同级，依赖相对路径才成立。
3. VS Code终端运行 `python -m http.server 8032 --bind 127.0.0.1`。C已经开启此端口时共用同一服务，不重复启动。
4. 浏览器打开 `http://localhost:8032/web-exhibits/training-D-assembly/`。应显示完整模型、开始入口、120秒挑战。无法加载先F12查看网络错误，不双击HTML。
5. 新开终端运行 `node --test web-exhibits/training-D-assembly/game-state.test.mjs`。应通过三项测试。

## 第二课 完整体验并认识代码
1. 点击开始：从完整模型变为逐步搭建，倒计时开始；右侧先选栌斗并拖到标记处松手。
2. 另开一局先选择非当前步骤，观察提示，进度不能增加。再选择正确构件，先点选后点击落点，比较替代操作。
3. 拖到标记以外松开，应该不安装；材料仍可再选。这里的退回主要是取消拖拽缩略图和保留备料，不是三维木件沿路径飞回。
4. 打开app.js：definitions定义18组名称与模型对象筛选；start开局；select选件；beginDrag/moveDrag/endDrag处理拖拽；clearDrag清理；place触发安装；finish显示结果。
5. 打开game-state.mjs：Challenge记录status、placed、deadline、remaining；默认120000毫秒。现版按组顺序判断index等于placed；同层构件已合并成组，不是任意单件都能换序。

## 第三课 倒计时和重开训练
1. 复制game-state.mjs为game-state.mjs.bak，再把默认duration的120000临时改成10000，保存刷新。开始游戏，等10秒，验证时间到后不能继续安装。
2. 切到另一个标签页超过10秒后返回，仍应超时。解释deadline与当前时间的差值，不能靠每帧减1来计时。
3. 点击重开：进度0，模型与结果面板恢复，重新倒计时。
4. 恢复120000，重新运行三项测试并再开一局观察显示120。不要把练习用10秒版交付。

## 第四课 触控容差的手动修改
1. 在app.js搜索 `<66`，找到moveDrag里的near提示和endDrag里的near放置判定，当前均为66像素。
2. 在顶部常量区增加 `const DROP_RADIUS = 76;`，将这两处比较改为 `< DROP_RADIUS`，保存刷新。两处必须一致，避免亮了却放不下。
3. 触摸屏分别测试距落点较近与明显较远的放手；记录76相较66是否更易操作、是否误吸附。数值是训练试验，不是文物尺寸或通用最佳值。
4. 保留宿主范围inside判断、ensurePlaying检查和game.place顺序检查；不能为了提高成功率删除规则。
5. 在VS Code展示自己的差异：只有一个新增常量和两处引用。最终选择有测试依据的阈值并记录。

## 第五课 输入取消与防重复
1. 阅读beginDrag中的setPointerCapture：拖出原按钮仍能接收事件；moveDrag只处理当前pointerId。
2. 阅读clearDrag中的releasePointerCapture、移除拖拽缩略图、恢复controls.enabled；找到pointercancel、blur与visibilitychange绑定。
3. 开始拖动后切换窗口，回来不应留悬浮缩略图；再次拖动应可用。鼠标模拟不能替代真实触屏的pointercancel验证。
4. 正确安装一组后尝试再点该组，进度不能重复增加；全部18组完成后不能再次计分。
5. 在game-state.test.mjs阅读超时边界、18组完成与延迟计时三个测试；解释为什么截止时刻再放件应该失败。

## 第六课 接收B资产 先核对再替换
1. 备份练习目录assets/baoguosi-zhutou-v02.glb，打开app.js搜索该文件名，找到加载位置。
2. 向B索取新GLB与对象命名清单。在Blender导入GLB，展开对象名称，对照definitions中的dou_ludou_01等筛选条件。随意改名会导致分组缺件。
3. 把新模型另存新文件名到练习assets，修改加载路径；必要时只调整对应筛选条件，并逐组检查有对象、归属唯一、柱头单独保留。
4. 页面刷新检查初始完整外观、18组缩略图、每组归位后的目标姿态。不是只看文件能打开。
5. 如果新资产采用另一套命名或组数，先做映射表再改代码；同步修改总组数、进度条及固定18组文案，不能把任意整殿GLB直接塞进此挑战。没有新资产时用当前模型完成训练，交付记录写“现有模型验证”。

## 第七课 触摸屏验收
接上目标屏幕，在该电脑启动本地服务并打开localhost；进入全屏。按下列顺序测试并记录通过/失败：
1. 开始显示120秒，计时连续。
2. 正确组拖至落点，进度仅加1。
3. 错误组与远离落点分别不计分。
4. 已安装组不能重复计分。
5. 先选件、再点落点可完成安装。
6. 拖拽取消后能继续；空白区域旋转与材料拖动不冲突。
7. 超时后安装无效；后台等待不能延长时间。
8. 完成18组显示成功；重开清零并恢复120。
9. 横屏布局、按钮尺寸、双指缩放在实际屏幕可用。

## 第八课 五分钟比赛练习
35:00—36:00：打开工程与模型路径，说明120秒18组规则及接收B资产的检查结果。
36:00—38:00：展示一次操作难点，现场完成容差常量修改，说明提示与判定同步。
38:00—40:00：验证正确、错误、重复、取消和重开，显示测试结果；无需等完整120秒耗尽，超时边界由测试和另一次完整实机录屏支撑。
最终交付：练习目录、修改前后差异、三项测试输出、真实触控录屏、训练记录。不修改正式工程，不涉及Unity内容。
重练：关闭浏览器练习页，将训练目录另命名为一次练习记录，再从正式act-03-assembly复制一份新的training-D-assembly；不删除已有记录。
''')
write(train/'训练记录模板.md','''
# 每次训练记录
姓名：　日期：　练习目录：　开始与结束时间：

| 项目 | 实际填写 |
|---|---|
| 本次目标 | |
| 打开的软件及版本 | |
| 修改的文件与位置 | |
| 修改前表现 | |
| 具体修改 | |
| 正例测试结果 | |
| 反例或失败恢复结果 | |
| 截图/录屏保存位置 | |
| 是否恢复练习起点 | |
| 下一次待处理内容 | |

C另填：本地检索还是实际API；模型ID；语音浏览器及是否联网；角色动画是否已接入；典藏有无模型与连点测试。
D另填：实际屏幕型号；倒计时是否恢复120；18组是否齐全；鼠标测试与真实触摸测试分别记录。
未做项目填写“未测”，失败填写现象与原因，不统一打勾。
''')
# Role outlines: prompts rather than spoken lines.
common='''\n## 自己改写时的要求\n每个操作点围绕“收到什么、要解决什么、具体操作、如何验证、交给谁”组织自己的表达。不照读软件菜单，不夸大AI能力，不把准备好的结果当作现场新生成。占位结果填入真实文件、截图与测试，不编造数据。\n'''
roles={
'A':('创意策划', '''
## 第一段 00:00—03:00 调研与方案
- 开场要点：项目主题、游客理解斗拱的困难、四项成果与四岗职责。
- 资料要点：现场照片、原始出处与一项设计依据。
- 操作提示：演示页 → Lovart或libtv设计记录 → 三视图；区分前期生成记录与现场操作。
- 设计说明：参考元素、角色比例、正侧背一致性。
- 交接：把三视图及形象约束交B，引出角色制作。
## 第四段 13:00—14:00 双端体验策划
- 说明触屏与VR的体验差别、成功/失败反馈和容错边界。
- 本轮D训练采用120秒单组铺作18组拼接；与整殿展示明确区分。
- 操作：设计方案页指认备料、目标、反馈，再交B制作资产。
## 第九段 40:00—41:00 木构典藏设计交付
- 操作：XD关键页与原型预览。
- 要点：地区与建筑选择、镜头聚焦、有模型与无模型两种呈现。
- 交接：把页面行为与资源清单交C，指出验收方法。
## 第十一段 45:00—47:00 总结主持
- 串联四项成果，邀请B/C/D说明贡献。
- 以实际成果和测试记录总结，不使用未经测试的提升比例。
- 结束与致谢，由自己写成自然表达。
'''),
'B':('三维资产制作', '''
## 第二段 03:00—07:00 角色制作与动作
- 接收A三视图；说明生成约束、比例与冠部要求。
- 操作：Tripo输入与任务记录 → 旋转检查 → 绑定与动作预览 → GLB导出。
- 验证：冠部变形、袖子穿插、材质、骨骼、实际动作名称。
- 交接C：GLB与动作清单；等待未完成时说明实际状态。
## 第五段 14:00—20:00 铺作交付与连续建模
- 操作：Blender打开代表性铺作，定位真实问题、调整连接、检查对象与原点。
- 解释：正常榫卯咬合与错误穿模；游戏草模与测绘复原区别。
- 第一次交D：VR用途FBX及贴图、清单；本大纲保留原总流程交接。
- 随后立即打开宋大殿斗拱工程，从已有零件手动组合、命名、归入集合。
## 第六段 20:00—33:00 并行操作
- D主讲期间继续搭建，不安排另一段长台词。
- 操作：组合、对齐、命名、分组、保存，保持同一工程连续性。
## 第七段 33:00—35:00 收尾与第二次交付
- 展示基本完成工程和集合树，完成一至两项实际收尾。
- 导出GLB并核对命名与装配清单，交D。
- 提醒交接检查：120秒挑战要求对象命名和18组映射兼容；整殿GLB不能不经映射直接替换。
## 第十一段 总结
- 自己的手工技能、资产检查方法、两次交付与验证结果。
'''),
'C':('智能体与木构典藏开发', '''
## 第三段 07:00—13:00 小拱智能体
- 接收B角色与动作清单；区分角色资产、知识、模型、语音各自作用。
- 软件切换：VS Code资源树 → 终端服务 → 浏览器测试 → 网络响应。
- 知识卡要点：原文出处、ID、问题、关键词、回答、定位；新增一条而非只展示成品。
- 检索要点：保存与加载、两种问法、命中依据、无依据时的边界。
- 模型要点：服务地址与实际模型ID、后端配置、资料与问题进入请求、真实响应；区分本地检索、云API和本地部署。
- 语音操作：未接通起点 → 录音权限 → 停止提交 → 识别文字 → 问答 → 朗读 → 待机。
- 状态说明：聆听、思考、朗读、待机由真实事件驱动；没有三维角色时说明练习只验证文字状态。
- 结果验证：一个正确问题、一个无依据问题、一次失败恢复。
- 交接A：返回统一入口，说明实际通过内容。
## 第十段 41:00—45:00 木构典藏
- 接收XD行为要求；打开现有js/main.js对应的模块工程。
- AI任务要点：指定文件和目标、约束范围、检查差异与资源映射。
- 人工操作要点：镜头时长、当前起点与新目标、连续点击过渡；明确参数练习与真实缺陷修复的区别。
- 验证要点：有模型能开、无模型不显示无效入口、连点最终到正确建筑、关闭可继续操作。
- 交接：回统一入口准备总结。
## 第十一段 总结
- 贡献：知识整理、真实模型调用、语音链路、AI代码审查与人工修正。
- 证据：知识卡、请求结果、录屏、文件差异和五项测试。
'''),
'D':('120秒触屏斗拱拼接', '''
## 本大纲范围
只列120秒触屏拼接内容，不列Unity、VR、PICO台词。原总流程第六段20:00—33:00不在本包重排；若后续取消该段，应另行调整50分钟总表。
## 第七段末 接收B资产
- 核对GLB版本、对象命名、分组清单和目标姿态。
- 说明当前网页是单组铺作18组挑战，接入新模型需要映射，不把整殿直接等同此关卡。
## 第八段 35:00—40:00 游戏搭建与验证
- 规则要点：120秒，柱头预置，18组依次安装；成功、超时、重开。
- 打开软件：VS Code → 本地服务终端 → 浏览器 → 触摸屏。
- 资产要点：加载文件、definitions映射、组数与显示结果。
- 操作要点：选件、拖动、松手判定、近处吸附、错处不计分；也支持选件后点落点。
- 修改要点：DROP_RADIUS统一提示和落点容差；保留宿主范围、当前状态及顺序限制。
- 解释输入：pointerId、指针捕获、取消清理，材料拖动与场景旋转不冲突。
- 计时要点：deadline，后台等待不延时，截止不再计分。
- 验证顺序：正确、错误、重复、取消、重开；测试与实机记录分别说明。
- 交接A：展示当前实际成果，引出木构典藏。
## 第十一段 总结
- 贡献：模型映射、触屏输入、判定与状态管理、真实设备测试。
- 证据：修改差异、三项测试、120秒实机录屏及训练记录。
''')}
write(outlines/'00-使用说明.md','''# 四岗台词大纲\n基于版本11-19 v1.2，每人独立一份。只提供讲解要点、软件操作、证据和交接，不提供可照读的完整台词。\n\nD按本次要求仅列120秒触屏部分；原第六段VR时间未在本包擅自分配给其他同学。A/B大纲仍保留总流程必要的交接提示。训练时以当前18组单组铺作玩法为准，整殿展示与此挑战分开说明。\n\n建议每人先用自己的话改写，操作熟练后再计时；最终由A把各自开头和交接连起来核对。''')
for role,(name,body) in roles.items():write(outlines/f'{role}-台词文档大纲.md',f'# {role}同学台词大纲 {name}\n'+body+common)
print('Created training guides, working C lab and four outlines')
