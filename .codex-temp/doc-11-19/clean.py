from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E
from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.table import Table
import json
folder=Path('竞赛演示/03-岗位讲解与实操/版本11-19')
src=next(folder.glob('*.docx'))
out=folder/'榫卯智言-50分钟流程与四岗台词-版本11-19-v1.1清稿.docx'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
counts={}
def remove(el):
 p=el.getparent()
 if p is not None:p.remove(el)
def unwrap(el):
 p=el.getparent()
 if p is not None:
  i=p.index(el)
  for child in list(el):p.insert(i,child);i+=1
  p.remove(el)
with ZipFile(src) as zin,ZipFile(out,'w',ZIP_DEFLATED) as zout:
 for item in zin.infolist():
  name=item.filename
  if 'comment' in name.lower() and name.startswith('word/'):continue
  data=zin.read(name)
  if name.endswith('.xml') or name.endswith('.rels'):
   root=E.fromstring(data)
   if name.startswith('word/') and name.endswith('.xml'):
    # Accept final text: remove deleted/moved-from content, retain insertions/moved-to text.
    for tag in ['del','moveFrom']:
     for el in list(root.iter('{'+W+'}'+tag)):counts[tag]=counts.get(tag,0)+1;remove(el)
    for tag in ['ins','moveTo']:
     for el in list(root.iter('{'+W+'}'+tag)):counts[tag]=counts.get(tag,0)+1;unwrap(el)
    for el in list(root.iter()):
     local=E.QName(el).localname
     if E.QName(el).namespace==W and (local.endswith('PrChange') or local in ['tblGridChange','cellIns','cellDel','cellMerge','numberingChange','trackRevisions','revisionView','commentRangeStart','commentRangeEnd','commentReference','moveFromRangeStart','moveFromRangeEnd','moveToRangeStart','moveToRangeEnd','highlight']):remove(el)
   if name.endswith('.rels'):
    for el in list(root):
     if 'comment' in el.get('Type','').lower() or 'comment' in el.get('Target','').lower():remove(el)
   if name=='[Content_Types].xml':
    for el in list(root):
     if 'comment' in el.get('PartName','').lower():remove(el)
   data=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
  zout.writestr(item,data)
d=Document(out)
for p in d.paragraphs:
 if p.text.startswith('本版基准：'):
  p.text='版本：11-19 v1.1。本文为50分钟流程与四岗台词清稿，后续排练与修订以本版为准。'
d.save(out)
lines=[]
for el in d.element.body:
 if el.tag==qn('w:p'):
  p=Paragraph(el,d)
  if p.text:lines.extend([('# ' if p.style.name=='Title' else '## ' if p.style.name=='Heading 1' else '### ' if p.style.name=='Heading 2' else '')+p.text,''])
 elif el.tag==qn('w:tbl'):
  for i,row in enumerate(Table(el,d).rows):
   lines.append('| '+' | '.join(c.text.replace('\n','<br>') for c in row.cells)+' |')
   if i==0:lines.append('| '+' | '.join('---' for c in row.cells)+' |')
  lines.append('')
out.with_suffix('.md').write_text('\n'.join(lines),encoding='utf-8')
with ZipFile(out) as z:
 assert z.testzip() is None
 for n in z.namelist():
  assert not ('comment' in n.lower() and n.startswith('word/'))
  if n.startswith('word/') and n.endswith('.xml'):
   r=E.fromstring(z.read(n))
   for el in r.iter():
    local=E.QName(el).localname
    assert not (E.QName(el).namespace==W and (local.endswith('PrChange') or local in ['ins','del','commentReference','trackRevisions']))
p=folder/'版本说明.md'
s=p.read_text(encoding='utf-8').replace('当前排练文档：榫卯智言-50分钟流程与四岗台词-版本11-19-v1.0.docx。','当前排练文档：榫卯智言-50分钟流程与四岗台词-版本11-19-v1.1清稿.docx。')
s+='\n## v1.1 清稿\n\n接受已有文字与格式修订，删除批注、修订记录和高亮批阅标记，保留最终内容。v1.0与输入基准留档。\n'
p.write_text(s,encoding='utf-8')
print(json.dumps(counts));print(out.resolve())
