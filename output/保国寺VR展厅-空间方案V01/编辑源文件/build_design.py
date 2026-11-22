from pathlib import Path
import math, json, html, io
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
REF=Path('/Users/yangzhe/Downloads/榫卯修改/国风室内场景')
W,H=1190.551,841.89 # A3 landscape, pt
M=72/25.4
S=1000/125*M
PX,PY=57,170
C={'ink':'#303832','muted':'#7d8178','paper':'#fcfbf7','wood':'#b28a61','wood2':'#d7bea1','stone':'#d5d3c8','green':'#527361','red':'#aa6650','line':'#b9bcaf','gold':'#9c8055'}
pdfmetrics.registerFont(TTFont('CN','/System/Library/Fonts/STHeiti Light.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('SONG','/System/Library/Fonts/Supplemental/Songti.ttc',subfontIndex=0))
CV=canvas.Canvas(str(ROOT/'保国寺VR数字斗拱展厅-空间设计方案V01.pdf'),pagesize=(W,H),pageCompression=1)
CV.setTitle('保国寺 VR 数字斗拱展厅｜空间设计方案 V01')
CV.setAuthor('榫卯智言 · 空间方案')

class Page:
 def __init__(self,num,title,sub,scale='概念方案'):
  self.num=num; self.svg=[]; self.name=f'{num:02d}-{title}'
  self.rect(0,0,W,H,C['paper'],None)
  self.text(40,35,'榫卯智言 / BAOGUOSI DIGITAL TIMBER GALLERY',9,C['muted'])
  self.text(40,71,title,26,font='SONG')
  self.text(40,95,sub,10,C['muted'])
  self.line(40,111,W-40,111,C['line'],.6)
  self.line(40,H-43,W-40,H-43,C['line'],.6)
  self.text(40,H-26,'V01  ·  2026.11.22  ·  纯虚拟空间设计；尺寸为本次提案值，非保国寺实测复原或施工图。',8,C['muted'])
  self.text(W-40,H-26,f'{scale}  /  A3  /  {num:02d}',8,C['muted'],anchor='end')
 def rect(self,x,y,w,h,fill=None,stroke=None,lw=1,dash=None):
  CV.setLineWidth(lw); CV.setDash(dash or [])
  if fill: CV.setFillColor(HexColor(fill))
  if stroke: CV.setStrokeColor(HexColor(stroke))
  CV.rect(x,H-y-h,w,h,fill=int(bool(fill)),stroke=int(bool(stroke)))
  d=f' stroke-dasharray="{",".join(map(str,dash))}"' if dash else ''
  self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{lw}"{d}/>')
 def line(self,x1,y1,x2,y2,color=None,lw=1,dash=None):
  color=color or C['ink']; CV.setStrokeColor(HexColor(color));CV.setLineWidth(lw);CV.setDash(dash or [])
  CV.line(x1,H-y1,x2,H-y2)
  d=f' stroke-dasharray="{",".join(map(str,dash))}"' if dash else ''
  self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{lw}"{d}/>')
 def text(self,x,y,t,size=10,color=None,font='CN',anchor='start'):
  color=color or C['ink'];CV.setFillColor(HexColor(color));CV.setFont(font,size)
  {'start':CV.drawString,'middle':CV.drawCentredString,'end':CV.drawRightString}[anchor](x,H-y,t)
  self.svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="{anchor}" font-family="{("Songti SC,SimSun,serif" if font=="SONG" else "PingFang SC,Microsoft YaHei,Noto Sans CJK SC,sans-serif")}">{html.escape(t)}</text>')
 def para(self,x,y,t,width,size=10,leading=17,color=None):
  line='';cur=y
  for ch in t:
   if ch=='\n' or pdfmetrics.stringWidth(line+ch,'CN',size)>width:
    self.text(x,cur,line,size,color);cur+=leading;line='' if ch=='\n' else ch
   else: line+=ch
  if line:self.text(x,cur,line,size,color);cur+=leading
  return cur
 def circle(self,x,y,r,fill=None,stroke=None,lw=1):
  if fill:CV.setFillColor(HexColor(fill))
  if stroke:CV.setStrokeColor(HexColor(stroke))
  CV.setLineWidth(lw);CV.setDash([]);CV.circle(x,H-y,r,fill=int(bool(fill)),stroke=int(bool(stroke)))
  self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{lw}"/>')
 def poly(self,pts,color=None,lw=1,dash=None,fill=None,closed=False):
  color=color or C['ink'];CV.setStrokeColor(HexColor(color));CV.setLineWidth(lw);CV.setDash(dash or [])
  if fill:CV.setFillColor(HexColor(fill))
  p=CV.beginPath();p.moveTo(pts[0][0],H-pts[0][1])
  for x,y in pts[1:]:p.lineTo(x,H-y)
  if closed:p.close()
  CV.drawPath(p,fill=int(bool(fill)),stroke=1)
  d=f' stroke-dasharray="{",".join(map(str,dash))}"' if dash else ''
  self.svg.append(f'<{("polygon" if closed else "polyline")} points="'+ ' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{fill or "none"}" stroke="{color}" stroke-width="{lw}"{d}/>')
 def arrow(self,a,b,color=None,lw=2):
  color=color or C['green'];self.line(*a,*b,color,lw)
  ang=math.atan2(b[1]-a[1],b[0]-a[0]);sz=7
  self.poly([b,(b[0]-sz*math.cos(ang-.45),b[1]-sz*math.sin(ang-.45)),(b[0]-sz*math.cos(ang+.45),b[1]-sz*math.sin(ang+.45))],color,.6,fill=color,closed=True)
 def img(self,path,x,y,w,h):
  buf=io.BytesIO()
  Image.open(path).convert('RGB').save(buf,format='JPEG',quality=92,optimize=True)
  buf.seek(0)
  CV.drawImage(ImageReader(buf),x,H-y-h,w,h,preserveAspectRatio=True,anchor='c',mask='auto')
 def finish(self,svg=False):
  if svg:
   p=ROOT/'图纸'/f'{self.name}.svg'
   p.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 {W} {H}">'+''.join(self.svg)+'</svg>',encoding='utf-8')
  CV.showPage()

zones=[
 ('01','入木 · 序厅',(0,0,12,7),'#ece6db',(8.5,5.2),'84㎡'),
 ('02','寻源 · 营造图谱',(0,7,12,10),'#eceee4',(7.5,14.8),'120㎡'),
 ('03','识材 · 构件展廊',(0,17,12,7),'#f0e5d5',(5.6,23),'84㎡'),
 ('04','解构 · 铺作工坊',(12,17,12,7),'#e7e5dc',(18,23),'84㎡'),
 ('05','观殿 · 主展厅',(12,7,12,10),'#e8ede6',(16,16),'120㎡'),
 ('06','成殿 · 整殿挑战',(24,10,12,14),'#ede4d5',(30,23),'168㎡'),
 ('07','传承 · 成果尾厅',(24,0,12,10),'#eee8e1',(33,8.8),'120㎡'),
 ('08','留白 · 静廊',(12,0,12,7),'#f0efe9',(18,5.5),'84㎡')]
stands=[('P01',15,10,6,4,.3,'大殿主展台'),('P02',1.8,20.2,1.2,1.2,.9,'构件台'),('P03',7.7,20.2,1.2,1.2,.9,'构件台'),('P04',9.5,18,1.2,1.2,.9,'构件台'),('P05',14,21.4,2.4,1.2,.8,'铺作工作台'),('P06',20,21.4,2.4,1.2,.8,'铺作工作台'),('P07',28,17,6,4,.3,'整殿挑战台'),('P08',32,4.5,2.4,1.2,.8,'尾厅机动展台')]

def pt(x,y):return PX+x*S,PY+(24-y)*S
def box(p,x,y,w,h,fill,stroke=None,lw=1):
 a,b=pt(x,y+h);p.rect(a,b,w*S,h*S,fill,stroke,lw)
def seg(p,x1,y1,x2,y2,color=None,lw=1,dash=None):p.line(*pt(x1,y1),*pt(x2,y2),color,lw,dash)
def label(p,x,y,t,size=10,color=None):p.text(*pt(x,y),t,size,color,anchor='middle')
def wall(p,x1,y1,x2,y2):seg(p,x1,y1,x2,y2,C['ink'],4.5)
def dim(p,x1,y1,x2,y2,t):
 p.line(x1,y1,x2,y2,C['muted'],.6)
 for x,y in [(x1,y1),(x2,y2)]:p.line(x-3,y+3,x+3,y-3,C['muted'],.7)
 if y1==y2:p.text((x1+x2)/2,y1-4,t,8,C['muted'],anchor='middle')
 else:p.text(x1-5,(y1+y2)/2,t,8,C['muted'],anchor='end')
def sidebar(p,items):
 y=151
 for head,body in items:
  p.text(916,y,head,12,C['green'],font='SONG');y+=23
  y=p.para(916,y,body,225,9.5,16,C['muted'])+21
def scale_bar(p):
 x,y=PX,734
 for i in range(5):p.rect(x+i*S,y,S,5,C['ink'] if i%2==0 else '#ffffff',C['ink'],.5)
 for i in [0,1,5]:p.text(x+i*S,y+18,str(i),8,C['muted'],anchor='middle')
 p.text(x+6*S,y+17,'m',8,C['muted'])
 p.text(x,y+39,'按 A3 原尺寸打印为 1:125；缩印或屏幕查看请使用图示比例尺。',8,C['muted'])
def plan(p,mode='base'):
 for no,name,(x,y,w,h),fill,pos,area in zones:
  box(p,x,y,w,h,fill)
 # floor panel grid
 for x in range(0,37,3):seg(p,x,0,x,24,'#d4d5ca',.3)
 for y in range(0,25,3):seg(p,0,y,36,y,'#d4d5ca',.3)
 for no,name,bounds,fill,(x,y),area in zones:
  tx,ty=pt(x,y);tw=pdfmetrics.stringWidth(f'{no}  {name}','CN',10)
  p.rect(tx-tw/2-3,ty-10,tw+6,14,fill)
  label(p,x,y,f'{no}  {name}',10)
 # perimeter and actual openings
 wall(p,0,0,4.5,0);wall(p,7.5,0,28.5,0);wall(p,31.5,0,36,0)
 wall(p,0,0,0,24);wall(p,0,24,36,24);wall(p,36,24,36,0)
 for y1,y2 in [(0,2),(5,18.5),(21.5,24)]:wall(p,12,y1,12,y2)
 for y1,y2 in [(0,3),(6,10),(13,24)]:wall(p,24,y1,24,y2)
 for y in [7,17]:
  for x1,x2 in [(0,3.5),(6.5,12)]:wall(p,x1,y,x2,y)
 for x1,x2 in [(12,17),(20,24)]:wall(p,x1,7,x2,7);wall(p,x1,17,x2,17)
 for x1,x2 in [(24,29),(32,36)]:wall(p,x1,10,x2,10)
 # 3-metre-long offset entrance screen, 2.5m inside foyer
 box(p,5,2.5,3,.15,C['wood']);label(p,6.5,2,'木格影壁',8,C['muted'])
 # peripheral interpretation walls, display niches, seating
 for y in [9,12,15]:box(p,.4,y,1,.9,C['wood2'])
 for x in [1.8,5,8.2]:box(p,x,23.3,2.3,.4,C['wood2'])
 box(p,14,1.3,8,.65,C['wood2']);label(p,18,1,'坐凳 / 灯带',7.5,C['muted'])
 box(p,35.3,12,.35,7,C['wood']);box(p,35.3,2,.35,5,C['wood'])
 # white empty plinths, muted wood edges
 for no,x,y,w,h,z,name in stands:
  box(p,x,y,w,h,'#fcfbf7',C['gold'],1)
  label(p,x+w/2,y+h/2+.1,no,9,C['gold'])
 # safe composition areas; not physical playspace requirements
 if mode!='ceiling':
  for x in [15,20.8]:
   box(p,x-1.15,18.15,2.3,2.3,None,C['green'],.65)
  label(p,18,17.6,'虚拟交互站位',7.5,C['green'])
 # dimensions / doors
 xx,yy=pt(0,24);dim(p,xx,yy-15,xx+36*S,yy-15,'36000')
 for i in range(3):dim(p,PX+i*12*S,PY-32,PX+(i+1)*12*S,PY-32,'12000')
 dim(p,PX-15,PY,PX-15,PY+24*S,'24000')
 p.text(PX+3,PY-48,'尺寸单位 mm / 区域尺寸按轴线概念划分',8,C['muted'])
 label(p,6,-.9,'入口 3000',8,C['green']);label(p,30,-.9,'出口 3000',8,C['green'])
 label(p,12,20,'3000',7.5,C['muted']);label(p,24,11.5,'3000',7.5,C['muted'])
 scale_bar(p)

# 01 / intentions and local references
p=Page(1,'入木见构 · 展厅设计意向','从单间书房，转为有层次、有回游、有停留的数字木构展馆。')
p.img(REF/'场景预览.png',40,139,510,288)
p.text(40,448,'原场景 / 保留木构秩序，重做空间关系',15,font='SONG')
p.para(40,471,'原模型呈现的是单间禅意室内。本案延续木色、格栅、灰石与柔光，取消书房式满墙装饰和房间中心毯面，改为连续展廊、错位洞口与独立主展厅。',506,11,19)
p.img(REF/'展厅1.jpg',590,139,173,245)
p.img(REF/'展厅2.jpg',783,139,173,245)
p.img(REF/'展厅3.jpg',976,139,173,245)
p.text(590,411,'取其空间语言，形成统一的中式当代展陈',17,font='SONG')
p.para(590,438,'参考图用于提炼：屏风叠景、木框节奏、暖灰矿物肌理、低眩光展台。避免直接复制图中商标、日式榻榻米或特定历史构造。保国寺内容由后续审核过的展品与图文承载。',560,11,19)
for i,(name,col,note) in enumerate([('暖灰米墙','#e1d6c2','主背景 60%'),('烟熏木色','#8b6848','木框 / 展台 25%'),('哑光灰石','#b4b5ab','地面 12%'),('暗古铜','#8b7751','收口 3%')]):
 x=42+i*280;p.rect(x,586,249,62,col);p.text(x,675,name,15,font='SONG');p.text(x,699,note,10,C['muted'])
p.text(42,752,'空间建议：36×24m / 外轮廓约864㎡ / 8个功能区域 / 普通展廊净高5.4m / 主厅净高7.2m',12,C['green'])
p.finish()

# 02 / master plan
p=Page(2,'总平面与展台布置','平面先行：固定边界、开口、尺度及展台，再进入后续三维设计。','平面 1:125')
plan(p)
sidebar(p,[('空间总量','外轮廓36×24m，约864㎡。图示区域面积为含分隔墙及过渡的概念毛面积，并非净使用面积。'),('展厅层次','由低照度序厅进入图谱展廊，经过构件展廊和工坊，再进入抬高的主厅，最后进入整殿挑战与成果尾厅。'),('开口与通行','主要门洞建议宽3m；展台外侧原则保留2.4m及以上通路。入口影壁促成转折，静廊提供捷径与停留。'),('展台预留','P01、P07为空的核心大型展台；P02-P04为单件台，P05-P06为铺作台，P08为机动台。图中未放置预设展品。'),('建模依据','本图确定拓扑与家具位置。图上方为参照方向，不代表现实地理北向。材质/灯光/效果图不得改变本图开口位置。')])
p.finish(True)

# 03 / circulation
p=Page(3,'参观动线与VR交互站位','主线迂回、支线可回游；场景行进采用虚拟移动，避免把展厅尺寸理解为现实活动范围。','平面 1:125')
plan(p)
route=[(6,-.2),(6,1.2),(3.4,1.2),(3.4,5.5),(5,6),(5,11),(6,13),(5,16),(5,18.2),(4.5,19),(6,19),(10.7,20),(12.5,20),(17.7,19.6),(18.5,17.8),(18.5,15.5),(13.7,15.2),(13.7,8.5),(22,8.5),(22,11.5),(25.5,11.5),(26.7,14.7),(30.5,14.7),(30.5,11),(30.5,9),(28.5,7),(28.5,4.2),(30,2),(30,-.2)]
for a,b in zip(route,route[1:]):seg(p,*a,*b,C['green'],2)
for idx in [3,6,11,16,20,25,27]:p.arrow(pt(*route[idx]),pt(*route[idx+1]),C['green'],2)
# quiet shortcut passes through actual openings
quiet=[(8.8,3.5),(12,3.5),(18.5,3.5),(22.5,4.5),(24,4.5),(27,4.5)]
p.poly([pt(*q) for q in quiet],C['gold'],1.4,[4,4])
p.poly([pt(18.5,3.5),pt(18.5,7.8)],C['gold'],1.4,[4,4])
for tag,x,y,tx,ty in [('V1',3.4,5,8,5.8),('V2',13.7,9,19,13),('V3',17.7,19.6,20.9,22.1)]:
 a=pt(x,y);p.circle(*a,9,'#ffffff',C['red'],1);p.text(a[0],a[1]+3,tag,8,C['red'],anchor='middle');p.arrow(a,pt(tx,ty),C['red'],1)
sidebar(p,[('主线叙事','01 入木 → 02 寻源 → 03 识材 → 04 解构 → 05 观殿 → 06 成殿 → 07 传承 → 出口。绿色为推荐参观方向，不强制单向。'),('回游与捷径','08 静廊连接入口、主厅与尾厅，支持返回看展、休息及快速结束。金色虚线为回游支线。'),('视点确认','V1：入口转折与影壁。V2：主厅模型台与抬高屋架。V3：铺作工坊与交互工作台。效果图为风格意向，图纸控制实际位置。'),('头显操作逻辑','远距离采用瞬移点或手柄移动，转角设可见落点。抓取/拼搭限于站位附近。现实空间边界由头显现场标定，不能照搬本图的大尺度。'),('体验细节','预留引导、复位、重新开始、声音与字幕的后续接口。本站位只是空间预留，游戏与AI逻辑将在确认建模后另行接入。')])
p.finish(True)

# 04 / ceiling
p=Page(4,'顶面、木构节奏与灯光意向','保持统一模块；以主厅抬高和照度层次区分空间，控制小木条和透明叠层数量。','顶面 1:125')
plan(p,'ceiling')
for x in [3,9,15,21,27,33]:
 seg(p,x,.5,x,23.5,C['wood'],2)
for y in [3,9,15,21]:seg(p,.5,y,35.5,y,C['wood'],1.4)
# uplight clerestory perimeter for central hall
box(p,12.5,7.5,11,9,None,C['gold'],1.4)
label(p,18,8.1,'H=7.2m / 柔光天窗',9,C['green'])
for x,y in [(2,4),(10,4),(2,10),(10,10),(2,15),(10,15),(2,22),(10,22),(15,22),(21,22),(27,22),(33,22),(27,13),(33,13),(27,5),(33,5)]:
 a=pt(x,y);p.circle(*a,3,C['ink']);seg(p,x-.45,y,x+.45,y,C['gold'],.7)
for x,y in [(13,8),(23,8),(13,16),(23,16)]:p.circle(*pt(x,y),3,C['gold'])
sidebar(p,[('净高提案','普通展廊/工坊：5.4m。主展厅：7.2m。此为虚拟展厅造型尺度，并非宋大殿柱高或梁架测绘数据。'),('L1 环境照明','建议中性偏暖的整体光感；连续侧向洗墙配合顶面漫射。避免只有明暗强烈的射灯，确保头显内转角可辨。'),('L2 展品重点','每个预留展台配置重点灯位，方向向内收束，后续根据展品高度调整。展台先为空，不设置悬空亮光占位模型。'),('L3 引导与天窗','主厅顶面局部漫射天窗形成重点；木框后方暗藏灯带，弱化光源直视。材料以哑光为主，避免大面积镜面反光。'),('性能设计','重复木框用可复用模块；半透屏风集中于序厅及工坊边界。优先烘焙环境光，少量动态光留给交互展品；实际性能由设备测试决定。')])
p.finish(True)

# 05 / sections and elevation
p=Page(5,'剖面与立面控制','确定空间高差、开口、展墙与空展台关系。图示为展馆新设计，不模拟保国寺原殿的真实营造尺寸。','A-A 1:125 / B-B 1:125')
p.text(60,151,'A-A / 主厅横剖 · 位于平面 y=12m',15,font='SONG')
x0,y0=60,368
def section(xbase,ybase,width,height,central=False):
 p.line(xbase,ybase,xbase+width*S,ybase,C['ink'],2)
 if central:
  coords=[(0,0),(0,5.4),(12,5.4),(12,7.2),(24,7.2),(24,5.4),(36,5.4),(36,0)]
 else:coords=[(0,0),(0,height),(width,height),(width,0)]
 p.poly([(xbase+x*S,ybase-y*S) for x,y in coords],C['ink'],1.5)
 for x in [0,width]:p.line(xbase+x*S,ybase-4.8*S,xbase+x*S,ybase,C['wood'],3)
 if central:
  p.line(xbase+12*S,ybase-5.4*S,xbase+12*S,ybase,C['wood'],3)
  p.line(xbase+24*S,ybase-5.4*S,xbase+24*S,ybase-3*S,C['wood'],3)
 for x,y,w,h,z,_ in [(15,0,6,0,.3,'')]:
  if central:p.rect(xbase+x*S,ybase-z*S,w*S,z*S,'#e6dacc',C['gold'])
 if central:
  p.text(xbase+18*S,ybase-7.2*S-12,'主厅 7200',10,C['green'],anchor='middle')
  p.text(xbase+6*S,ybase-5.4*S-12,'展廊 5400',10,C['muted'],anchor='middle')
  p.text(xbase+30*S,ybase-5.4*S-12,'挑战厅 5400',10,C['muted'],anchor='middle')
  p.text(xbase+18*S,ybase-22,'P01 空展台 6000×4000×300',9,C['gold'],anchor='middle')
 dim(p,xbase,ybase+24,xbase+width*S,ybase+24,f'{int(width*1000)}')
section(x0,y0,36,5.4,True)
p.text(60,451,'B-B / 西侧展廊内立面 · 位于平面 x=0.25m',15,font='SONG')
xb,yb=60,648
section(xb,yb,24,5.4)
for xx in [2,7,12,17,22]:
 p.rect(xb+(xx-.7)*S,yb-3.4*S,1.4*S,2.4*S,'#e9deca',C['wood'],1)
for xx in [4,10,16]:p.rect(xb+xx*S,yb-.8*S,1.2*S,.8*S,'#e0cfb8',C['wood'],1)
p.text(60,710,'展墙原则：木框 + 暖灰墙 + 克制留白；图文与展品审核后再填入，避免把装饰当作营造史料。',10,C['muted'])
sidebar(p,[('顶面层次','展廊延续横向木框秩序，主厅局部抬升至7.2m并引入漫射顶光。木框为展馆设计语汇，不标注未经考据的宋式构造名称。'),('立面构成','底部石材踢脚；中部米灰展墙与木框；上部格栅/洗墙带。必要的门框、收口、凹槽与灯位在建模中完整表达。'),('展品尺度','P01与P07承载缩尺数字展品；完整大殿不以真实建筑体积硬塞进主厅。若后续需要1:1大殿体验，将单独作为传送场景。'),('地面原则','全馆标高保持一致，不设台阶、地坑或必须跨越的门槛。各区域通过铺装方向和光感切换，不靠高差引导。')])
p.finish(True)

# 06 / fixtures
p=Page(6,'空展台、展墙与细部清单','先做可持续填充的展馆壳体；展品、AI角色与游戏模块随后独立接入。','展台概念详图 / 标注尺寸优先')
cards=[(40,'A / 核心空展台','6000×4000×300 mm','P01 主厅 / P07 整殿挑战'),(425,'B / 铺作工作台','2400×1200×800 mm','P05 / P06 工坊'),(810,'C / 构件独立台','1200×1200×900 mm','P02 / P03 / P04')]
for x,title,dimt,where in cards:
 p.text(x,151,title,17,font='SONG');p.text(x,177,dimt,12,C['gold']);p.text(x,200,where,10,C['muted'])
 # axon schematic, dimension authority in caption
 xx,yy=x+30,326;w=210;d=65;h=18 if x==40 else 80
 p.poly([(xx,yy),(xx+d,yy-d*.55),(xx+w+d,yy-d*.55),(xx+w,yy)],C['gold'],1,fill='#e9dece',closed=True)
 p.poly([(xx,yy),(xx+w,yy),(xx+w,yy+h),(xx,yy+h)],C['gold'],1,fill='#cfb79a',closed=True)
 p.poly([(xx+w,yy),(xx+w+d,yy-d*.55),(xx+w+d,yy-d*.55+h),(xx+w,yy+h)],C['gold'],1,fill='#bda17e',closed=True)
 p.text(x,yy+h+30,'台面留空；图中为展台本体',10,C['muted'])
for x,title,body in [(40,'统一构造语言','哑光木饰面侧板、细石或浅色矿物台面、内缩暗色踢脚。轮廓清楚，边缘微倒角，避免漂浮感。'),(425,'交互工作台','桌前保留交互站位，构件托盘作为后续可切换模块。拼搭目标、操作范围和复位入口在软件阶段接入。'),(810,'单件展示','重点灯从内侧上方照射，背后保留暖灰留白展墙。展台编号仅用于本方案与建模管理，不必显示给游客。')]:
 p.text(x,479,title,16,font='SONG');p.para(x,507,body,330,11,20,C['muted'])
p.line(40,595,W-40,595,C['line'],.8)
p.text(40,627,'建模细节范围',17,font='SONG')
rows=[('空间壳体','墙、顶、地、门洞、转折、主厅抬高、连续地面'),('展陈固定件','8组空展台、壁龛展架、坐凳、格栅、展板背衬'),('材质与收口','木纹方向、板缝、踢脚、墙角、门套、台面倒角'),('灯光与交互预留','漫射天窗、洗墙灯槽、重点灯位、虚拟落点、游戏站位')]
for i,(a,b) in enumerate(rows):
 y=655+i*28;p.text(42,y,a,10,C['green']);p.text(190,y,b,11)
p.finish(True)

# 07 and 08 generated visual concepts, only included once they exist
for num,name,file,caption in [(7,'主展厅效果意向','01-主展厅效果意向.png','V2 / 从主厅西南侧望向中央空展台。以暖灰矿物墙、烟熏木框、哑光石地面和漫射顶光统一空间。'),(8,'展廊与工坊效果意向','02-展廊工坊效果意向.png','V3 / 从构件展廊转入铺作工坊。屏风形成遮挡与借景，空工作台为后续拼搭展品留位。')]:
 file=ROOT/'效果意向'/file
 if file.exists():
  p=Page(num,name,'风格与氛围审核图；非精确模型渲染，尺度、洞口与展台数量以平面和剖面为准。')
  p.img(file,40,131,W-80,560)
  p.para(42,724,caption,W-90,12,21)
  p.text(42,775,'视觉图为AI生成的概念设计意向；展台中的展品与历史形制均需另行审核。',9,C['muted'])
  p.finish()

p=Page(9,'方案确认与后续建模边界','本轮提交的是可修改的空间提案；等待确认后再修改 Blender，并输出新的 FBX。')
items=[('01 / 空间规模','是否接受36×24m、约864㎡的纯虚拟展厅规模，以及主厅7.2m、周边5.4m的净高关系。'),('02 / 动线与功能','是否接受由西侧展廊、北侧工坊、中部主厅、东侧整殿挑战形成的迂回主线，以及南侧静廊的回游捷径。'),('03 / 材质与光感','是否接受暖灰米墙、烟熏木色、灰石地面和少量暗古铜；整体明亮可辨、有柔和阴影，不做暗黑书房。'),('04 / 展台与留白','是否接受8组固定空展台，以及可放缩尺大殿的P01/P07。现阶段只完成展馆与展陈基础，不把全部展台塞满。'),('05 / VR使用方式','以手柄移动/瞬移为主要跨区方式，站位附近进行抓取拼搭；若后续改为自由手势，另行校核交互范围。')]
y=155
for title,body in items:
 p.rect(42,y-12,13,13,None,C['line'],1);p.text(73,y,title,17,font='SONG');p.para(73,y+27,body,1000,12,21,C['muted']);y+=110
p.text(42,734,'确认后交付：新展馆 .blend + FBX + 材质贴图 + 分组清单；原始房间模型单独保留。',12,C['green'])
p.text(42,762,'本轮未启动 Blender、未修改原 .blend / .fbx，也未实现新的Unity游戏逻辑。',10,C['muted'])
p.finish()
CV.save()
(ROOT/'编辑源文件'/'空间参数.json').write_text(json.dumps({'version':'V01','status':'待用户确认，未建模','units':'m','footprint':[36,24],'normal_clear_height':5.4,'main_hall_clear_height':7.2,'plan_print_scale':'A3 1:125','zones':[{'id':z[0],'name':z[1],'bounds_xywh':z[2],'gross_area':z[5]} for z in zones],'empty_plinths':[{'id':a,'x':x,'y':y,'size':[w,h,z],'name':n} for a,x,y,w,h,z,n in stands]},ensure_ascii=False,indent=2),encoding='utf-8')
print(ROOT/'保国寺VR数字斗拱展厅-空间设计方案V01.pdf')
