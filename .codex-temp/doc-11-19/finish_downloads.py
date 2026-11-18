from pathlib import Path
import json
base=Path(r'C:\Users\Administrator\Downloads')
def put(p,s):p.write_text(s.strip()+'\n',encoding='utf-8')
for role in ['C','D']:
 p=base/f'{role}同学-比赛独立训练包-11-19';port=8781 if role=='C' else 8782
 for name,cmd in [('启动训练.cmd',f'start "" "http://localhost:{port}"\n"%~dp0runtime\\node.exe" "%~dp0server.cjs"'),('运行检查.cmd','"%~dp0runtime\\node.exe" --test "%~dp0tests\\*.test.cjs"'),('准备比赛练习起点.cmd','"%~dp0runtime\\node.exe" "%~dp0prepare.cjs"')]:
  (p/name).write_text('@echo off\r\nchcp 65001 >nul\r\ncd /d "%~dp0"\r\n'+cmd.replace('\n','\r\n')+'\r\npause\r\n',encoding='utf-8')
 changes= """
edit('web/guide/app.js',s=>s.replace("$('#question').value=e.results[0][0].transcript;ask()","$('#question').value=e.results[0][0].transcript;/* 练习：在此接通问答 */"));
edit('knowledge/cards.json',s=>JSON.stringify(JSON.parse(s).filter(c=>c.id!=='BG002'),null,2));
edit('web/act-02-globe/js/globe/globe.js',s=>s.replace('const TWEEN_MS = 1100;','const TWEEN_MS = 50; // 练习预设：镜头太快'));
""" if role=='C' else """
edit('web/act-03-assembly/app.js',s=>s.replaceAll('<66','<8 /* 练习预设：落点范围过小 */'));
"""
 put(p/'prepare.cjs',r'''
const fs=require('node:fs'),path=require('node:path');const base=__dirname;
const backup=path.join(base,'练习留档','准备起点-'+Date.now());
function edit(rel,fn){const target=path.join(base,rel),original=path.join(base,'原始备份',rel),saved=path.join(backup,rel);fs.mkdirSync(path.dirname(saved),{recursive:true});fs.copyFileSync(target,saved);const s=fs.readFileSync(original,'utf8');fs.writeFileSync(target,fn(s));}
'''+changes+"\nconsole.log('比赛练习起点已准备；旧编辑已保存至 '+backup+'。请刷新页面。此为有意设置的练习任务，非原始工程缺陷。');")
 put(p/'从这里开始.txt',f'''{role}同学比赛独立训练包 · 版本11-19

1. 本文件夹可以整体移动、复制到另一台Windows x64电脑。文件夹内自带Node运行程序，不需要安装Python或下载npm依赖。VS Code及Edge/Chrome需电脑已有。
2. 双击“启动训练.cmd”，保留启动窗口。浏览器打开 http://localhost:{port} 。若首次打开太早显示无法连接，刷新一次。
3. 用VS Code打开“训练工程.code-workspace”。只改本包内的文件。
4. 第一次先体验完整基准版，再双击“准备比赛练习起点.cmd”。按《逐步排练.md》修复任务，操作结果就在同一网页里显示。
5. 双击“运行检查.cmd”看代码与服务测试。真实触屏、语音权限、外部API另需现场验证。
6. 重练会自动保存所改文件到“练习留档”。要恢复全部基准，在文件夹空白处右键打开终端，运行 powershell -NoProfile -File .\\还原练习.ps1 。若系统策略阻止，请手动把原始备份的对应文件复制覆盖，不调整系统安全策略。
7. 关闭服务：启动窗口按Ctrl+C。两个包端口不同，可同时运行。不要只拿走单个HTML；整体复制本文件夹。

正式来源：D的触屏工程、C的木构典藏直接复制当前工程源码及完整资源。C的小拱模块按最新流程补建，先使用明确标注的模拟动画角色，后续替换带动画GLB。原始备份保存打包时全部代码；训练与演示共用web下的同一份代码。

旧目录中scripts/build-offline.mjs是原项目离线打包历史工具，其原有外部构建环境不随本包提供。日常开发、比赛运行和测试均无需运行此历史脚本；D另附已生成的离线成品参考。''')
C=base/'C同学-比赛独立训练包-11-19';D=base/'D同学-比赛独立训练包-11-19'
put(C/'逐步排练.md',r'''
# C比赛操作全流程
本包有完整木构典藏和新补建的小拱工程。训练、现场操作、结果展示都使用web中的同一份文件，原始备份仅用于恢复。角色目前是有分层肢体运动的模拟模型，不声称已有骨骼GLB。

## 第一次 打开全部比赛窗口
1. 双击启动训练.cmd，访问localhost:8781；双击训练工程.code-workspace，VS Code选择信任自己确认的这个本地工程。
2. 浏览器入口打开“小拱智能体”；另一标签打开“木构典藏”。小拱应出现模拟木色角色、输入框、语音按钮和资料区；典藏应能选择地区、建筑并打开已有三维模型。
3. VS Code打开knowledge/cards.json、services/guide.cjs、config/model.json、web/guide/app.js、web/guide/character.js。第二环节再打开web/act-02-globe/js/views/detail.js和js/globe/globe.js。
4. 点两个示例问题、观察资料、听朗读、进入典藏查看模型。双击运行检查.cmd，打包基准应通过4项检查。外部API和麦克风状态不会被本地测试替代。

## 准备比赛练习起点
双击准备比赛练习起点.cmd，再刷新两页。程序基于完整基准设置三项明确练习任务：删去BG002知识卡；断开识别文字后的自动问答；把典藏过渡从1100ms设成50ms。原文件已经留档，工程仍完整可运行。这些是训练预设，不说成原工程真实缺陷。

## 第三段 07:00—13:00
### 07:00—07:35 角色与工程确认
浏览器展示当前角色。VS Code打开web/guide/character-config.json，说明当前modelUrl为空，所以使用模拟角色；展示四个动作状态配置位置。比赛前有真实GLB时按后面的替换步骤操作。
### 07:35—08:45 制作并加载知识卡
1. VS Code打开docs/04-斗拱-读法与铺作.md，定位铺作与出跳；并排打开knowledge/cards.json。
2. 在数组最后一个对象后加逗号，新增以下对象（正式内容以教师审校为准）：
```json
{"id":"BG002","question":"七铺作是不是七个斗","keywords":["七铺作","七个斗","铺作"],"answer":"不是。铺作等级不能按斗的个数理解，应结合出跳和铺作层次辨认。","source":"/docs/04-斗拱-读法与铺作.md","locator":"出跳与铺作等级"}
```
3. 保存后浏览器提问“七铺作是不是七个斗”，应由无依据变成有BG002卡片。再换一种包含“七铺作”的问法；点击“查看原文”。后端每次读取卡片，保存即生效。
### 08:45—09:35 接入DeepSeek
赛前先完成账号配置，现场展示配置与请求链路，不现场注册账号。config/model.json：mode设为deepseek，model填实际可用的完整模型ID，baseUrl保留官方地址。复制config/private.env.example为private.env并填本人的密钥，重启启动训练.cmd。密钥只由后端读取、不随网页返回；演示时只打开model.json，不打开private.env。
打开services/guide.cjs，定位retrieve、messages与fetch。浏览器再次问同一问题，页面模式应显示“真实模型调用”及服务返回的ID。没有密钥时保持local，仅完成本地检索，不能说已经接入大模型。配置错误会提示原因，不返回假回答。
### 09:35—10:15 检索验证
F12打开网络面板，检查/api/chat响应的refs、answer、mode；问未知问题，确认显示无依据。用真正返回的结果讲解，保留本轮来源。
### 10:15—11:20 语音连接
先点开始录音并允许麦克风，问“大殿建于哪一年”，点停止。练习起点会把识别结果写进输入框但不提交。
VS Code在web/guide/app.js搜索“练习：在此接通问答”，把整段注释替换为 `ask()`，注意保留函数闭合括号与分号。保存刷新，重复录音；应自动请求并回答。
语音识别采用浏览器SpeechRecognition，可能依赖浏览器的联网服务；不支持或网络失败时会提示。仅在同一比赛电脑的Edge/Chrome验证通过后使用；按实际支持状态讲解，文字入口始终保留。
### 11:20—12:20 朗读与角色状态
勾选回答后朗读，重新提问。观察聆听→思考→朗读→待机；搜索app.js的setState、onstart、onend、onerror，指出真实事件如何驱动状态。点击停止朗读，验证停止后回到待机。浏览器自动播放受限时点重新朗读。
### 12:20—13:00 完整验证与交接
录完一轮问答，检查文字、资料、音频、角色反馈；返回比赛入口，交A引出下一环节。

## 第十段 41:00—45:00 木构典藏
1. 41:00—41:40：打开典藏页面及VS Code的web/act-02-globe/js/views/detail.js；找到if(item.model)，确认有模型与无模型两类数据。
2. 41:40—42:20：在团队的AI编程工具中打开本包目录。任务写明：“仅修改web/act-02-globe/js/views/detail.js中已有三维入口的提示文字，使其说明可旋转观察；保留item.model判断，不改布局，不新增模型路径；列出修改差异。”这需要电脑已有AI编程工具及账号，本包不附第三方账号。
3. 42:20—43:00：检查AI差异并应用，测试有模型可开，无模型仍保留图文。既有功能不声称从零生成。
4. 43:00—44:00：打开js/globe/globe.js，搜索TWEEN_MS。练习起点为50，把它恢复为1100；解释过渡时间、当前相机方向与新目标，搜索focus和tween定位实现。此项是预设训练问题的修正。
5. 44:00—45:00：连续选建筑A、B，观察最终到B；打开、关闭模型，再返回地区。检查没有新增资源错误，回总入口。
6. 双击运行检查.cmd，确认知识卡和网页服务检查通过；记录实际麦克风、模型API和三维操作结果。检查通过不代表外部服务已验证。

## 替换B后续交付的真实角色
1. 将含骨骼、材质和动画的GLB复制至web/guide/assets/xiaogong.glb，不覆盖原三视图。
2. Blender导入该GLB，查看实际动作片段名称。记录待机、聆听、思考、朗读四种状态对应的真实名称，不凭空填名称。
3. 编辑character-config.json：modelUrl填 `assets/xiaogong.glb`；animations每项填真实动作名；scale按实际尺度调整。
4. 刷新页面，提示应变为已载入角色GLB。分别触发四种状态，检查动画过渡、材质、冠部和袖子；名称不匹配时没有对应动作，需修正配置。模型应以脚底为原点、Y轴向上，导出前在Blender整理。
5. 加载失败会明确显示并使用模拟形象，不假装已换成正式角色。

## 重练与课堂记录
重练前先关闭服务。准备起点会另存对应改动到练习留档，并再次设置三项练习任务。完整恢复见从这里开始.txt；不要给private.env截图或发送给其他同学。比赛当天须固定本包、浏览器、API模型与AI编程工具版本，按同一流程彩排。
''')
put(D/'逐步排练.md',r'''
# D比赛操作全流程 仅120秒触屏挑战
本包完整复制现有单组铺作挑战：57个模型构件，柱头预置，其他构件合为18组。比赛与练习使用同一网页、同一模型和同一代码。没有Unity、VR或PICO步骤。

## 第一次打开
1. 双击启动训练.cmd，访问localhost:8782，点120秒触屏挑战。
2. 双击训练工程.code-workspace；VS Code打开web/act-03-assembly/app.js、game-state.mjs、index.html、style.css；展开assets，看GLB与完成参考图。
3. 先完整体验一局。开始后120秒计时，正确组才能归位；支持拖到落点松手和先选件再点落点。点击重开恢复0进度和120秒。
4. 双击运行检查.cmd，基准应通过3项检查；鼠标通过后仍要在实际触屏上测试。

## 准备比赛练习起点
双击准备比赛练习起点.cmd。它会把app.js两处落点范围从66px改成8px，原改动留档。刷新网页，体验落点变难。此为明确设置的训练问题，正式演示时说明练习起点，不把它说成原工程缺陷。

## 第七段末 接收B资产
1. 打开assets与app.js中loadAsync位置。当前使用baoguosi-zhutou-v02.glb。
2. 接收B的GLB与对象清单，先另存，不覆盖现有基准文件。对照app.js的definitions逐组检查名称匹配。
3. 网页是18组单组铺作，整殿GLB不能不经映射直接替换。若B的文件仍在制作，可先用本包现有同一模型进行接入演练；说明资产版本。

## 第八段 35:00—40:00
### 35:00—36:00 打开与定位
浏览器介绍120秒与18组规则；VS Code打开模型加载路径、definitions和game-state.mjs。
说明ready、playing、won、lost，placed、deadline与remaining分别记录什么。展示备料、目标轮廓和进度。
### 36:00—38:00 手动修改
1. 开始游戏，演示范围太小的训练问题。
2. app.js顶部常量区加入 `const DROP_RADIUS = 76;`。
3. 搜索 `8 /* 练习预设：落点范围过小 */` ，把两处比较右侧都替换成DROP_RADIUS：moveDrag控制靠近高亮，endDrag控制能否安装。
4. 两处最后都应形如 `Math.hypot(...) < DROP_RADIUS`。保存并刷新，不修改顺序、宿主范围inside和ensurePlaying判定。
5. 解释“靠近提示”和“松手判定”为什么必须用同一值。76px是本次训练值，正式采用需真实屏幕测定。
### 38:00—40:00 验证与交接
1. 正确组近处松手，进度只增加1。
2. 错误组和明显偏离落点均不能安装；备料保留，拖拽缩略图消失。
3. 已安装组不能重复计分。
4. 拖动时切换窗口再回来，无悬浮图残留，仍可继续拖动；阅读clearDrag与pointercancel/blur绑定。
5. 点击重开，结果面板、模型、进度和120秒全部恢复。
6. 双击运行检查.cmd，说明测试覆盖超时边界、18组完成和重新开始；现场不必等待120秒全部结束。课前另录真实完整超时验证。
7. 结束交A，进入木构典藏；不安排Unity相关讲解。

## 课后必须做的完整验证
- 触屏单指材料拖动、空白旋转、双指缩放，不互相冲突。
- 先选件再点落点可用；拖到范围外松手无计分。
- 后台等待超过120秒，回来已经超时；截止后不再安装。
- 18组全部完成显示成功，重开再次从120秒开始。
- 检查真实屏幕比例、全屏、字号和按钮，不用桌面鼠标结果代替。

## 定位表
- index.html：布局与按钮；style.css：触控区域和视觉。
- app.js：definitions、start、beginDrag、moveDrag、endDrag、clearDrag、place、finish。
- game-state.mjs：时间与安装状态；game-state.test.mjs：原工程三项测试。
- assets/baoguosi-zhutou-v02.glb：真实练习模型；wood-material.js：木材材质。
- ../shared/vendor：本地Three.js、控件和GLB加载器，无需联网下载。

## 重练
双击准备比赛练习起点.cmd重新设置故障；它会从基准取app.js，因此上一轮修改先自动留档。若需全部恢复见从这里开始.txt。离线成品参考只用于观察，不在其内改代码；所有比赛手动修改均在web/act-03-assembly内。
''')
for p in [C,D]:
 put(p/'练习记录.md','''# 本次排练记录\n姓名： 日期： 浏览器版本： 屏幕/麦克风：\n\n开始时间： 结束时间： 修改文件：\n\n修改前现象： 实际修改： 正例结果： 反例结果：\n\n录屏位置： 尚未通过项： 下次要调整：\n\nC填写实际API模型与调用结果、语音识别和角色类型；D填写120秒实测与18组完成情况。不写未实际验证的“全部通过”。''')
print('Launchers fixed; complete rehearsal instructions and resettable starting points saved.')
