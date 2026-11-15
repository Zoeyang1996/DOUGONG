"""One-time, lossless archive of known backups; archive entries retain original paths."""
from pathlib import Path
import os,zipfile,hashlib,json,shutil,subprocess
root=Path(__file__).resolve().parents[1]
archive=root/'archive'/'2026-11-15-整理前备份'
archive.mkdir(parents=True,exist_ok=True)
before=subprocess.check_output(['du','-sk',str(root)],text=True).split()[0]
candidates=[]
for base in ['models','web-exhibits']:
 for p in (root/base).rglob('*'):
  if 'node_modules' in p.parts or not p.is_file():continue
  if '.blend' in p.name and p.name.rsplit('.blend',1)[-1].isdigit():candidates.append(p)
for name in ['.demo-build','.chart-data-LCLx3M','.chart-data-iOqV1S']:
 for folder,dirs,files in os.walk(root/name,followlinks=False):
  dirs[:]=[d for d in dirs if not (Path(folder)/d).is_symlink()]
  candidates.extend(Path(folder)/f for f in files if not (Path(folder)/f).is_symlink())
if (root/'web').is_file():candidates.append(root/'web')
zip_path=archive/'旧备份与临时成果.zip'
assert not zip_path.exists(),'Archive already exists; do not rerun.'
manifest=[]
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in candidates:
  rel=p.relative_to(root).as_posix();blob=p.read_bytes()
  manifest.append({'path':rel,'size':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
  z.writestr(rel,blob)
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 for record in manifest:assert hashlib.sha256(z.read(record['path'])).hexdigest()==record['sha256']
for p in candidates:p.unlink()
# Empty temporary directories and the obsolete runtime symlink only.
for name in ['.demo-build','.chart-data-LCLx3M','.chart-data-iOqV1S']:
 for folder,dirs,files in os.walk(root/name,topdown=False,followlinks=False):
  for d in dirs:
   p=Path(folder)/d
   if p.is_symlink():p.unlink()
  p=Path(folder)
  if p.exists() and not any(p.iterdir()):p.rmdir()
original=root/'docs/01-依据/原始文档';original.mkdir(exist_ok=True)
moves=[]
for name in ['人工智能赛道+数字媒体技术.docx','保国寺资料调查.docx','基础斗拱资料调查.docx','网站的创意想法.docx']:
 p=root/name
 if p.exists():
  target=original/name;assert not target.exists();shutil.move(p,target);moves.append({'from':name,'to':target.relative_to(root).as_posix()})
report={'before_KiB':int(before),'archived_files':manifest,'moves':moves,'original_bytes':sum(x['size'] for x in manifest),'archive_bytes':zip_path.stat().st_size}
(archive/'整理清单.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['archived_files','moves']},ensure_ascii=False));print('Archived files:',len(manifest),'moved originals:',len(moves))
