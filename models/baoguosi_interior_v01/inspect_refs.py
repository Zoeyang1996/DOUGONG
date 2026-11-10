from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,json
from PIL import Image,ImageOps,ImageDraw
O=Path(__file__).resolve().parent;R=O.parent.parent/'research'/'baoguosi_ model';D=O/'references';D.mkdir(exist_ok=True)
z=zipfile.ZipFile(R/'保国寺资料调查.docx');root=ET.fromstring(z.read('word/document.xml'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
txt=[''.join(p.itertext()) for p in []]
paras=[''.join(p.itertext()) for p in root.findall('.//w:p',ns)]
(D/'document_text.txt').write_text('\n'.join(paras),encoding='utf-8')
files=[]
for f in sorted(R.glob('*.jpg')):files.append(('PHOTO_'+f.name.split('_')[1],f))
for f in z.namelist():
 if f.startswith('word/media/'):
  p=D/Path(f).name;p.write_bytes(z.read(f));files.append((p.stem,p))
valid=[]
for name,p in files:
 try:
  im=Image.open(p);valid.append((name,p,im.copy().convert('RGB')))
 except:pass
for start in range(0,len(valid),12):
 batch=valid[start:start+12];sheet=Image.new('RGB',(1600,400*((len(batch)+3)//4)),(238,236,231));dr=ImageDraw.Draw(sheet)
 for i,(name,p,im) in enumerate(batch):
  im.thumbnail((390,365));x=i%4*400;y=i//4*400;sheet.paste(im,(x+(400-im.width)//2,y+25));dr.text((x+10,y+5),name,fill='black')
 sheet.save(D/f'sheet_{start//12:02}.jpg')
(D/'index.json').write_text(json.dumps([{'id':n,'path':str(p),'size':im.size} for n,p,im in valid],ensure_ascii=False,indent=2),encoding='utf-8')
print('Images',len(valid))
