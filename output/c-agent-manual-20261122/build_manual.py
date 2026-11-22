from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT=Path(__file__).parent
doc=Document()
sec=doc.sections[0]
sec.page_width=Inches(8.5); sec.page_height=Inches(11)
sec.top_margin=Inches(.72); sec.bottom_margin=Inches(.68)
sec.left_margin=sec.right_margin=Inches(.78)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3']:
    st=doc.styles[name]; st.font.name='Arial'; st.font.color.rgb=RGBColor(0,0,0)
    st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Source Han Sans CN')
normal=doc.styles['Normal']; normal.font.size=Pt(11)
normal.paragraph_format.line_spacing=Pt(17)
normal.paragraph_format.space_after=Pt(5)
for name,size in [('Title',24),('Heading 1',18),('Heading 2',13),('Heading 3',11.5)]:
    st=doc.styles[name]; st.font.size=Pt(size); st.font.bold=True
    st.paragraph_format.space_before=Pt(8); st.paragraph_format.space_after=Pt(7)
    st.paragraph_format.line_spacing=1.1
    st.paragraph_format.keep_with_next=True
doc.styles['Subtitle'].font.size=Pt(12)
footer=sec.footer.paragraphs[0]; footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
r=footer.add_run('学生排练手册  ·  '); r.font.size=Pt(9)
fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); footer._p.append(fld)
doc.core_properties.title='小拱智能体角色接入与C岗位现场操作手册'
doc.core_properties.subject='A与B交付规范 C角色替换 动作配置 语音问答 排练流程'
doc.core_properties.author='榫卯智言项目组'

def p(text,bold=False):
    x=doc.add_paragraph(); x.add_run(text).bold=bold; return x
def h(text): doc.add_heading(text,2)
def page(title):
    doc.add_page_break(); doc.add_heading(title,1)
def step(title,text):
    x=doc.add_paragraph(); x.paragraph_format.keep_with_next=True; x.add_run(title).bold=True
    p(text)
def code(text):
    lines=text.strip('\n').split('\n')
    for i,line in enumerate(lines):
        x=doc.add_paragraph(); x.paragraph_format.space_after=Pt(1); x.paragraph_format.line_spacing=Pt(12)
        x.paragraph_format.left_indent=Inches(.12); x.paragraph_format.keep_with_next=i<len(lines)-1
        r=x.add_run(line); r.font.name='Menlo'; r.font.size=Pt(9)
def table(headers,rows,widths):
    t=doc.add_table(rows=1, cols=len(headers)); t.alignment=WD_TABLE_ALIGNMENT.CENTER; t.autofit=False
    for c,w in zip(t.columns,widths): c.width=Inches(w)
    for i,v in enumerate(headers): t.rows[0].cells[i].text=v
    for row in rows:
        cells=t.add_row().cells
        for c,v in zip(cells,row): c.text=v
    for ri,row in enumerate(t.rows):
        trPr=row._tr.get_or_add_trPr()
        no=OxmlElement('w:cantSplit');trPr.append(no)
        if ri==0:
            rep=OxmlElement('w:tblHeader');trPr.append(rep)
        for ci,c in enumerate(row.cells):
            c.width=Inches(widths[ci]); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr=c._tc.get_or_add_tcPr()
            borders=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
            pr.append(borders)
            margins=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                e=OxmlElement('w:'+edge);e.set(qn('w:w'),'90');e.set(qn('w:type'),'dxa');margins.append(e)
            pr.append(margins)
            sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'E8EDF1' if ri==0 else ('F7F8FA' if ri%2==0 else 'FFFFFF'));pr.append(sh)
            for para in c.paragraphs:
                para.paragraph_format.space_after=Pt(2);para.paragraph_format.line_spacing=Pt(14)
                for run in para.runs:run.font.size=Pt(10);run.bold=ri==0
    doc.add_paragraph().paragraph_format.space_after=Pt(0)

doc.add_heading('小拱智能体角色接入\n与C岗位现场操作手册',0)
doc.add_paragraph('人工智能赛道四人协作环节  学生练习与现场讲解用',style='Subtitle')
p('版本日期  2026年11月22日')
p('目标是让C接收A与B临场生成的新角色，完成三维显示、动画状态连接和真实语音问答。提前准备知识库与应用框架，现场使用新资产进行接入和验证；角色外观改变时，无须重建知识库或重新接入大模型。')
h('先确认工程目前能做什么')
table(['现有能力','赛前需要补齐或验证'],[
('GLB加载与动作名称配置','新模型尺寸、朝向、材质及动作兼容性'),
('待机 聆听 思考 朗读四种状态','导入面板、自动居中落地、动作列表与预览'),
('文字问答 语音识别 回答朗读','比赛电脑的麦克风、中文语音和现场网络'),
('知识卡依据与本地检索模式','多动作文件合并、点击欢迎动作等新增功能')],[2.5,4.4])
p('本手册以现有C岗位精简工程为操作基线。第3至7页给出可按文件练习的接入路线；第10页列出增强工具的开发验收项。增强界面尚不能当作已完成的软件使用。',True)
h('C应展示的核心技能')
p('检查数字资产 → 配置模型与动作 → 修改交互状态连接 → 在浏览器验证 → 用资料依据解释回答。导入成功只是第一步，必须证明“朗读时讲解、结束后待机、停止后复位”确实联动。')
p('建议C用时8分钟；这是角色智能体环节的排练建议，最终并入四人总计50分钟的流程。云端生成等待须按排练实测预留。')

page('01 A与B向C交付什么')
h('A 创意策划师')
p('软件：你们选定的LibTV工作流及AIGC图像工具。A现场说明木构文化提取、造型约束与提示词迭代，生成供三维制作使用的统一三视图。具体按钮以实际账号界面为准。')
p('形象允许变化，但结构限定为双臂双腿类人形；T字站姿、双臂水平展开，手臂与身体分离；三视图同一比例、同一高度、全身完整。避免斗拱冠遮挡肩部、复杂道具和额外肢体。')
p('旧版小拱三视图双臂自然下垂，本次应重新生成符合绑定要求的T字站姿。三视图还要人工核对正侧背面是否一致，不能仅凭“生成成功”通过。')
h('B 三维建模师')
p('软件：Tripo Studio；Blender仅作为赛前整理与必要修复工具。B导入图片生成模型，检查手臂、冠部、材质，再对同一个角色绑定骨骼、生成动作。每个动作不得分别重新生成一个角色。')
table(['交付项','统一要求','C如何验收'],[
('角色文件','优先GLB 含材质 骨骼 动画','加载后有模型且材质正常'),
('待机动作','原地 轻微 可循环','连续播放不漂移'),
('讲解动作','原地手势 可循环','朗读期间保持在显示区域'),
('欢迎动作','挥手或致意 播放一次','增强版接入 点击触发'),
('交付记录','文件名 实际动作名 正面朝向','C据此填写配置并核对')],[1.1,2.75,3.05])
p('建议交付名称：xiaogong-live.glb。命名只为方便传递，不能靠改文件后缀转换格式。另存FBX可供后续编辑，网页练习先使用已验证的GLB。')
p('优先交付一个含多个动作的GLB。若Tripo分别导出多个动作文件，须先走已排练的合并流程或增强导入器；当前基础加载器只读取一个GLB中的动作，不会自动合并。')
p('B交接台词：“这是本次新生成的角色，已完成骨骼绑定。待机和讲解动作来自同一套骨架，请C接入应用并验证状态联动。”')

page('02 C上场前准备软件和文件')
h('软件与启动方式')
p('准备VS Code、Node.js 20或更新版本、已验证的Chrome或Edge，以及可用的麦克风和扬声器。浏览器语音能力受系统、浏览器和网络影响，必须在比赛电脑上实测。')
p('工程位置：下载 → 榫卯修改 → C同学-精简项目备份。练习时先复制整个文件夹作为个人练习副本，不在唯一原件上试改。')
table(['文件或目录','用途','现场是否修改'],[
('server.cjs','启动本地网页与问答接口','通常不改'),
('web/guide/character-config.json','模型地址 动作名称 显示比例','主要修改'),
('web/guide/character.js','GLB显示与动画切换','必要时调显示或过渡'),
('web/guide/app.js','录音 问答 朗读状态连接','演示少量行为修改'),
('web/guide/assets/','存放B交付的新GLB','复制新文件'),
('knowledge/ 与 docs/','知识卡与参考原文','赛前核验内容'),
('config/','服务模式与本机私密配置','赛前配置 不投屏密钥')],[2.55,2.6,1.75])
step('步骤1 打开完整工程','在VS Code中选择“文件 → 打开文件夹”，打开个人练习副本。不要只打开一个HTML文件。')
step('步骤2 启动本地服务','在工程根目录打开终端，输入下方命令并保持窗口运行。Windows也可使用包内“启动训练.cmd”。')
code('node server.cjs')
step('步骤3 打开智能体页面','浏览器访问 http://localhost:8781/guide/ 。出现角色区、问题输入、录音按钮和资料依据区后再继续。不要通过双击HTML来验证需要接口的智能体。')
p('开场前先试一次文字提问，再试录音和朗读；确认页面显示的是DeepSeek模式还是本地检索模式。密钥保存在本机服务配置，不写入GLB、网页或投屏代码。')

page('03 C接收并导入现场新角色')
step('步骤1 留存交付文件','将B交付的GLB复制到 web/guide/assets/，命名为 xiaogong-live.glb。保留B原始导出文件，另记实际动作名称和朝向。通过U盘或共享目录交付时先确认文件复制完整。')
step('步骤2 配置模型路径','打开 web/guide/character-config.json，将modelUrl设置为 assets/xiaogong-live.glb。该地址相对于智能体页面，不能填写B电脑上的磁盘路径。保存文件后回到浏览器刷新。')
step('步骤3 先确认确实加载了新模型','核对角色外观是否与B的交付一致；检查页面提示“已载入角色GLB”。如果提示“真实模型加载失败，当前为模拟角色”，说明没有成功，不能以备用几何角色显示为验收通过。')
step('步骤4 检查大小与朝向','先用scale调整比例并刷新。scale是统一缩放系数，0.8表示缩小到80%，1.2表示放大到120%；应根据现场资产调整，不预设每个角色都适用同一数值。')
p('当前基础版相机和模型摆放是固定的，单改scale不能解决所有原点或朝向问题。若模型背对游客、悬空或完全不在画面内，应由B按统一规范重新导出，或使用赛前完成的居中、落地、朝向适配功能。')
h('C现场检查顺序')
p('先看模型是否出现，再看材质，再看正面朝向，再看完整身高，最后才检查动作。一次只改一个参数并验证，避免同时改多个文件后无法判断错误来源。')
h('成功标准')
p('新角色的头冠和双脚均在画面内，材质无明显缺失，默认站姿稳定。记录这一状态后再进入动作配置。现阶段不要求自动口型同步，也不要求现场处理任意非人形骨架。')
h('本步骤讲解台词')
p('“我接收的是刚生成的新角色。先将它作为独立资产接入，再校准显示比例。智能体知识库与角色模型分开管理，因此更换外观不会改变它对保国寺的知识。”')

page('04 C把真实动作连接到对话状态')
p('先从B的交付记录获得动作名称，再与文件实际内容核对。动作名必须逐字匹配，包含大小写、空格和标点。不能把下方示例名称当作Tripo必定生成的名称。')
table(['应用状态','推荐分配的动作','触发时机'],[
('idle 待机','待机动作','页面空闲或朗读结束'),
('listening 聆听','复用待机动作','录音开始'),
('thinking 思考','复用待机动作','已提交问题 等待回答'),
('speaking 朗读','讲解动作','实际开始播放回答语音')],[1.55,2.3,3.05])
h('配置示例')
p('仅当文件真实动作名分别为Idle与Talk时，才使用下列写法。现场把它们换成B本次交付的实际名称。JSON不支持注释，最后一项后不能多写逗号。')
code('''{
  "modelUrl": "assets/xiaogong-live.glb",
  "scale": 1,
  "animations": {
    "idle": "Idle",
    "listening": "Idle",
    "thinking": "Idle",
    "speaking": "Talk"
  }
}''')
step('步骤1 保存并刷新','先保存配置，再刷新智能体页面。当前基础版没有“保存并应用”的面板按钮，配置文件保存后仍需刷新。')
step('步骤2 验证讲解动作','勾选“回答后朗读”，发送文字问题。听到朗读时观察讲解动作；朗读结束后应切回待机。')
step('步骤3 验证停止行为','朗读中点击“停止朗读”，确认声音停止且角色返回待机。动作不切换时优先核对名称、导出动画选项和文件中是否实际包含该动作。')
p('欢迎动作先由B生成并交付。当前基础版没有欢迎状态和角色点击事件，不能只在配置里添加一个hello字段就认为能触发；增强版须同时接入事件、单次播放及结束复位。')

page('05 C在VS Code展示少量行为修改')
p('现场代码展示选一个经过排练的改动即可。导入、配置、验证仍应真实完成；不要为了增加操作数量同时改动服务、知识库与三维渲染。')
h('演示一 调整动作切换的柔和程度')
p('文件：web/guide/character.js。使用搜索找到 current?.fadeOut(.2) 和 next.reset().fadeIn(.2).play()，将两处 .2 同时改为 .35。含义是把淡出、淡入从0.2秒调整为0.35秒，减少突然切换的感觉。')
code('''current?.fadeOut(.35);
next.reset().fadeIn(.35).play();''')
p('这两行是现有代码对应片段，不应单独粘贴到文件末尾。只修改原位置的数值；保存、刷新后重新发起问答，比较动作衔接。效果还受导出姿态与动画质量影响。')
h('演示二 连接朗读结束后的待机状态')
p('文件：web/guide/app.js。现有代码已经在语音播放开始与结束时调用setState。下面展示的是它的核心关系，不是需要整段覆盖原文件的替换代码。')
code('''u.onstart = () => setState('speaking');
u.onend = () => setState('idle');''')
p('现有工程还用token与epoch判断旧语音回调，防止“停止后又被旧事件改状态”。练习时保留这些保护。若将“修复结束不复位”作为现场任务，教师需提前制作独立练习副本，仅移除onend中的待机调用，再由C现场补回；正式成品不预先破坏。')
h('现场说清楚修改为什么有效')
p('“我把动画播放连接到语音的真实开始和结束事件。声音还没有开始时不提前做讲解动作；朗读结束或停止后回到待机。这里调整过渡时间，让状态切换更自然。”')
h('验收证据')
p('保存后浏览器刷新；讲解动作启动、自然结束复位、停止朗读复位三项都通过。若动作本身没有变化，不能只凭改过代码宣称完成，需要检查动作映射和实际导出。')

page('06 C完成真实语音问答验证')
step('步骤1 先验证文字通路','在问题框输入“保国寺大殿建于哪一年？”，点击“发送问题”。确认服务返回文字、模式标识及本轮资料依据。若文字通路失败，先处理本地服务或接口问题，不先排查麦克风。')
step('步骤2 检查录音设备','用比赛电脑系统确认麦克风可用。浏览器首次请求麦克风时，由操作学生允许本次演示使用。对着麦克风正常讲话，避免扬声器回声影响识别。')
step('步骤3 发起语音提问','点击“开始录音”，清晰说出“七铺作是不是七个斗？”。当前浏览器识别接口可能在判断一句话结束后自动提交；可用“停止录音”结束采集，不把它理解为必定发送完整结果的按钮。')
step('步骤4 观察完整状态链','录音开始显示聆听；识别后提交显示思考；返回回答后，实际开始朗读才进入朗读状态；声音结束后返回待机。指向资料依据区解释本轮命中的原文。')
step('步骤5 做一次游客式追问','例如“请用适合小学生的话解释斗拱有什么作用”。如果系统当前只发送单轮问题，不宣称已具备连续上下文记忆。要展示“它是什么”这类依赖前文的追问，须赛前补做会话历史并测试。')
h('不能混淆的三件事')
p('模型能离线显示，不代表大模型可离线回答；本地知识检索模式不等于已经调用DeepSeek；播放身体讲解动画也不等于逐字口型同步。按页面实际模式和已完成能力讲解。')
h('问答验收要点')
p('年代类问题应能对应已审核知识卡；关于七铺作的回答不能简单解释为“七个斗”。对照片无法判断的暗榫、尺寸等问题，应说明资料不足，不编造测绘数据。验证至少两个事实问题和一个通俗解释问题。')
h('语音失败时仍可继续展示')
p('告知评委当前语音识别受设备或网络影响，改为键入同一个问题，继续展示知识回答、资料依据与角色动作联动。若使用预录音频或备用成果，应明确说明，不能将其当作实时生成。')

page('07 C的八分钟现场流程与台词')
table(['用时','操作','观众看到的结果'],[
('00:00至01:00','接收B文件 核对交付记录','确认使用本次新角色'),
('01:00至02:30','复制GLB 修改路径与比例','新角色正确显示'),
('02:30至04:00','填写动作映射 预览与验证','待机与讲解可切换'),
('04:00至05:00','VS Code修改过渡或复位逻辑','修改短小且能说明原因'),
('05:00至07:00','语音提问 查看依据 测试停止','完整对话与动作联动'),
('07:00至08:00','验收并向下一岗位交接','交付配置和测试结论')],[1.25,2.65,3])
h('接收成果时')
p('“B已经完成新角色的三维生成与骨骼绑定。我负责把这份资产接入应用，连接知识服务、语音交互与角色动作。角色外观可以改变，但接入规范保持一致。”')
h('配置角色与动作时')
p('“我先确认模型和材质加载成功，再调整显示比例。接下来根据这个文件实际包含的动画，把待机动作分配给空闲和聆听状态，把讲解动作分配给语音回答状态。”')
h('修改代码时')
p('“这里控制两个动作之间的过渡。我把淡入淡出时间统一调整为0.35秒，并保留停止语音后的复位逻辑。保存后回到页面测试，确认修改确实生效。”')
h('进行问答时')
p('“现在用游客的问题验证。请问，七铺作是不是七个斗？我们同时看三个结果：识别的问题是否正确、回答是否有资料依据、角色动作是否跟随语音开始和结束。”')
h('交接时')
p('“新角色已经完成接入，待机、讲解和停止复位测试通过。这里交付角色文件、动作配置与测试记录，后续可接入三幕网页或其他展示终端。”')
p('D可接收角色及检验结果，再进入其Unity环节；本环节不要求D参与网页代码修改。云端生成若尚未完成，C可先介绍知识卡与接口准备，等B完成后再做真实导入。')

page('08 C常见故障与排查顺序')
table(['现象','优先检查','处理与演示口径'],[
('新模型没有出现','路径 文件名 本地服务是否运行','核对assets路径；失败提示为模拟角色时不能算成功'),
('模型过大或不在画面','scale 原点 朝向 真实尺寸','先调比例；仍异常则重导出或用适配工具'),
('模型全白或材质丢失','导出是否包含贴图 资源是否完整','B重新导出含材质GLB；不能只复制外置贴图中的一张'),
('模型能看但不动','动画是否导出 名称是否完全匹配','核对实际clip名；重新导出包含动画'),
('只播放一个动作','单文件是否真的包含多个动作','基础版不自动合并；转赛前验证的整理流程'),
('动作播放后跑出画面','动作根节点位移','B改用原地动作；不能只靠拖回角色遮盖问题'),
('手臂或斗拱冠变形','骨骼定位 权重 肩部结构','B检查绑定；采用已验证动作 说明修复范围'),
('文字也无法回答','服务启动 配置 模式 网络','先通文字接口 再检查语音；别把本地模式当大模型'),
('识别失败或按钮不可用','浏览器支持 麦克风权限 网络','改用文字提问继续验证 明确说明'),
('回答有字但没声音','回答后朗读 系统中文语音 音量','点击重新朗读；声音失败不能宣称语音验收通过'),
('停止后动作又被触发','旧回调保护是否保留','检查token与epoch逻辑；恢复已验证文件')],[1.45,2.25,3.2])
h('统一处理原则')
p('先定位“资产、显示、动画、问答、语音”哪一层失败，再处理对应文件。一次只改一个原因；超过排练设定的排查时限，切换已说明的备用路径，把未通过项记录下来。')
p('不得隐瞒替换为旧角色、播放预录语音或切换本地检索。现场真实性来自真实操作和清楚的结果说明，不来自保证每次生成都完全一样。')

page('09 练习安排与增强工具验收')
h('学生分四轮练习')
p('第一轮用已验证的角色完成启动、配置、问答与停止复位。第二轮换一个外观不同但结构合规的角色，完成相同操作。第三轮由教师设置一个缺少动画或路径错误，C定位并说明原因。第四轮四人联排计时，记录生成等待与交接耗时。')
p('至少使用三种外观差异明显的角色验证替换能力。每轮记录模型文件、动作名、接入耗时、三个问答结果及失败原因；不要只在固定小拱上排练。')
h('教师赛前需要准备的文件')
p('一份不改动的完整成品备份；一份供C修改的练习副本；三个通过显示和动画测试的角色；B的交付记录表；C的验收记录；一份故障练习副本。私密配置单独留在本机，不打进给学生公开传递的资产包。')
h('增强版导入工具的开发验收项')
p('导入GLB后自动居中、落地和按高度缩放，并允许校正朝向；列出真实动作及预览；配置待机、聆听、思考、讲解；支持欢迎动作单次播放与结束复位；缺少动作明确提示；检查通过后再替换当前角色。')
p('若要接收多个动作文件，还需验证骨骼层级、名称与轨道目标是否兼容，导入后逐个预览；不兼容就提示B重新整理。模型来源相同也不能免检。配置导出与刷新后恢复同样需要验收。')
h('现有基础版使用边界')
p('基础版当前只按动作名称加载单个GLB，不提供图形化导入面板、自动落地、多文件动作合并或角色点击欢迎。新模型载入后也应补做初始待机启动，不能只看到“待机”文字就判断动画正在播放。')
h('最后一次上场检查')
p('工程服务已启动；新模型文件可读取；动作名称已核对；麦克风与中文朗读已测试；当前问答模式已确认；密钥不在投屏范围；备用路径已准备；8分钟流程已计时。')

page('10 操作文件索引与技术参考')
h('现有工程的可核对位置')
p('下载/榫卯修改/C同学-精简项目备份/。下面的文件名用于在VS Code中查找，建议使用“打开文件夹”保留目录关系。')
table(['要做的事','对应文件'],[
('改变角色路径和动作名称','web/guide/character-config.json'),
('检查GLB加载与动画过渡','web/guide/character.js'),
('检查录音 朗读和状态事件','web/guide/app.js'),
('确认真实按钮和页面内容','web/guide/index.html'),
('确认本地服务与端口','server.cjs'),
('检查问答服务与知识资料','services/guide.cjs 与 knowledge/ 和 docs/')],[2.8,4.1])
h('教师应先完成的三项确认')
p('第一，使用实际Tripo账号导出一次，确认是一个多动作GLB还是多个单动作文件，并确定统一交付路线。第二，让三种合规角色经过同一接入流程，确定显示适配需要补哪些功能。第三，在比赛电脑测试中文语音识别、朗读与大模型网络。')
p('本手册的代码片段是操作说明，没有自动修改现有工程。学生开始练习前，教师应先确认所用副本与本手册路径、页面按钮一致；对增强工具，按第10页逐项开发验收后再切换练习路线。')
h('官方参考')
p('Tripo Rigging & Animation\nhttps://www.tripo3d.ai/product-doc/module-post-processing/rigging-animation')
p('Tripo Export & DCC\nhttps://www.tripo3d.ai/product-doc/export-and-integration/export-dcc')
p('Tripo Animation 开发文档\nhttps://developers.tripo3d.com/en/models/animation')
p('参考核对日期为2026年11月22日。Tripo界面、账号权限和导出选项可能变化，现场操作以本队账号排练结果为准。GLB支持骨骼动画不代表任意资产都能免检接入。')

for st in doc.styles:
    for node in list(st.element.iter(qn('w:pBdr'))): node.getparent().remove(node)
    if st.type==1:
        pp=st.element.get_or_add_pPr();snap=OxmlElement('w:snapToGrid');snap.set(qn('w:val'),'0');pp.append(snap)
for para in doc.paragraphs:
    for node in list(para._p.iter(qn('w:pBdr'))): node.getparent().remove(node)
    for run in para.runs:
        run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'Source Han Sans CN')
file=OUT/'小拱智能体角色接入与C岗位现场操作手册.docx'
doc.save(file)
print(file)
