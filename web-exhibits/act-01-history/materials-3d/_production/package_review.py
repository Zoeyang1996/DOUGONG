from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,re
B=Path(__file__).resolve().parents[1];T=B.parent/'materials-text-image'
font='/System/Library/Fonts/STHeiti Medium.ttc'
f=lambda n:ImageFont.truetype(font,n)
rows=json.loads((B/'asset-index.json').read_text())
# Read-only review sheets assembled from the actual Blender output.
def sheet(items,cols,cellw,cellh,path,title,sub):
 W=cols*cellw+80;H=((len(items)+cols-1)//cols)*cellh+200
 im=Image.new('RGB',(W,H),'#f1ede3');d=ImageDraw.Draw(im);d.text((40,35),title,font=f(40),fill='#292d27');d.text((40,94),sub,font=f(21),fill='#6f6b60')
 for i,row in enumerate(items):
  x=40+(i%cols)*cellw;y=150+(i//cols)*cellh
  image=Image.open(B/row['folder']/'render.png').convert('RGB');image.thumbnail((cellw-20,cellh-96))
  im.paste(image,(x+(cellw-20-image.width)//2,y))
  meta=json.loads((B/row['folder']/'assembly.json').read_text())
  d.text((x,y+cellh-85),row['id']+'  '+meta['title'],font=f(27),fill='#292d27')
  d.text((x,y+cellh-46),meta['asset_type']+'  /  '+str(row['mesh_count'])+' 个独立木件',font=f(18),fill='#9a4c2e')
 d.text((40,H-34),'统一材质与机位 · 轮廓归一，非同比例 · 2026.11.11 素材审核稿',font=f(17),fill='#6f6b60');im.save(path)
sheet(rows[:6],3,600,600,B/'六阶段模型总览.png','从相接到层叠：六个中心模型','G1 榫卯 → G2 柱梁 → G3 柱头承托 → G4 唐 → G5 保国寺宋构 → G6 清式')
sheet(rows[6:],3,600,560,B/'五种部件识名总览.png','先认五个名字，再看复杂铺作','G3之后的识名插页 · 斗 / 拱（栱）/ 升 / 昂 / 翘 · 具体朝代需切换术语')
(T/'K_部件识名/renders').mkdir(exist_ok=True)
import shutil
shutil.copy2(B/'五种部件识名总览.png',T/'K_部件识名/renders/五种部件总览.png')
lines=['# 第一幕三维素材包','', '2026-11-11 · 素材审核版。六段历史中心模型＋五个术语独立模型；现有网页未接入。','', '![六阶段总览](六阶段模型总览.png)','', '![五部件总览](五种部件识名总览.png)','', '| ID | 模型 | 木件数 | 装配事件数 | GLB大小 | 工程 | 渲染 |','|---|---|---:|---:|---:|---|---|']
for r in rows:
 meta=json.loads((B/r['folder']/'assembly.json').read_text());p=r['folder'];k=r['id']
 lines.append(f'| {k} | {meta["title"]} | {r["mesh_count"]} | {meta["assembly_events"]} | {r["glb_bytes"]/1e6:.2f} MB | [{k}.blend]({p}/{k}.blend) | [查看]({p}/render.png) |')
lines += ['', '## 每组交付','', '- `.blend`：可编辑原生模型，构件独立，帧1组合、80分离观察、140回到组合。分离图不是历史施工顺序。','- `.glb`：导出当前组合状态，含独立对象、材质、构件标识。已使用Draco，后续网页需加载本地解码器。','- `render.png`：固定同一机位的组合渲染；六个G组另有`exploded.png`，拆解观察图保持方向、单独调整取景以避免裁切。','- `assembly.json`：中文名称、稳定ID、教学落位顺序、依赖、起始偏移、最终位姿、类型、来源和待核项。','- `validation.json`：几何检查。总体验证见`verification-report.json`。','', '## 统一规范','', '1. 全套共用 `WOOD_SHARED_v1`，原创1024木纹在 `shared/wood_basecolor_1024.png`，材质库为`shared/WoodMaterial.blend`。纹理已嵌入各GLB和工程。','2. Blender Z向上；GLB与JSON为Y向上，换算[x,z,-y]。模型归一后围绕同一原点，根节点用于整组进退场。','3. 固定正交机位；每组单独做轮廓归一，不是实测同比例比较。GLB里的米仅为工作单位。','4. 画面审核采用统一中性背景；网页纸色由后续页面设置。保持素木是视觉比较策略，不还原各建筑历史彩画。','5. G4/G5/G6分别构建，有不同构件排布、出跳与昂形。G4非佛光寺测绘复原，G6非太和殿特定檐层复原；G5是保国寺实例目标、待核形制。','', '## 对04数量预算的调整','', '全套保留125个独立木件，其中六个历史模型120件、识名5件。没有为凑18—24件而把多个木件合并。装配事件把可同步落位的关联件分组，木件数与事件数分别登记。各组GLB均小于3 MB；这不代表已验证网页帧率。','', '## 审核重点','', 'G1/G2可见卯槽已切出，按元数据轴向插入。G3是承托原理。唐宋清的精确尺寸、局部接合、横栱层位和史料仍待核；隐藏榫卯未制作，不据此生产实物或演示真实结构受力。','', '[对应图文资料](../materials-text-image/README.md) · [修订与审核清单](../planning/05-素材准备-修订与审核清单.md)']
(B/'README.md').write_text('\n'.join(lines))
# Image provenance now includes newly obtained Commons thumbnails.
for path in T.glob('*/image-register.json'):
 data=json.loads(path.read_text())
 for r in data:
  if r['file'].endswith('Wutai_2009_492_960px.jpg') or '故宫内檐' in r['file']:r['image_type']='来源站提供的960px缩略图，原样下载、未裁切'
  if '现状外观' in r['file']:r['source_page_url']='local:research/保国寺实地调研照片/516b4f325h43760af614fa3534c93205.jpg'
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2))
# Keep failed attempts as log history, not failed deliverables in the root.
for p in B.glob('*_ERROR.txt'):shutil.move(str(p),str(B/'_production'/('resolved_'+p.name)))
# Report text lengths and broken local Markdown links.
check=[]
for p in T.glob('*/content.json'):
 d=json.loads(p.read_text());check.append({'id':d['id'],'body_chars':len(d.get('body',''))})
broken=[]
for p in list(T.rglob('*.md'))+[B/'README.md']:
 for u in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if not u.startswith(('http','local:','#')) and not (p.parent/u).exists():broken.append([str(p),u])
(B/'package-check.json').write_text(json.dumps({'text_lengths':check,'broken_links':broken},ensure_ascii=False,indent=2));print('BROKEN',broken)
