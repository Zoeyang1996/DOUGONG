from pathlib import Path
import json,base64,re,struct,hashlib,ast
ROOT=Path(__file__).resolve().parents[1];a=ROOT/'01_镜头未拉近';b=ROOT/'02_镜头穿梭已完善'
models=[]
for p in (a/'assets/models-js').glob('*.js'):
 raw=base64.b64decode(re.search(r']="([A-Za-z0-9+/=]+)";',p.read_text()).group(1));original=Path('/Users/yangzhe/Desktop/浙江工商/DOUGONG/web-exhibits/act-02-globe/assets/models')/(p.stem+'.glb');assert raw==original.read_bytes()
 size,kind=struct.unpack('<I4s',raw[12:20]);doc=json.loads(raw[20:20+size]);external=[v['uri'] for sec in ('images','buffers') for v in doc.get(sec,[]) if v.get('uri') and not v['uri'].startswith('data:')];assert not external
 models.append({'name':p.stem,'bytes':len(raw),'original_sha256':hashlib.sha256(raw).hexdigest(),'external_resources':external})
assert len(models)==12
rows=json.loads((a/'data.json').read_text());assert len(rows)==39
for row in rows:
 assert (a/row['image']).is_file()
 if row.get('model'):assert (a/'assets/models-js'/(Path(row['model']).stem+'.js')).is_file()
checks=[]
for p in sorted(a.rglob('*')):
 if p.is_file():
  rel=p.relative_to(a);checks.append({'file':str(rel),'identical':p.read_bytes()==(b/rel).read_bytes()})
assert [c['file'] for c in checks if not c['identical']]==['camera-config.js']
assert 'DETAIL_ZOOM: 1.05' in (a/'camera-config.js').read_text() and 'FLIGHT_MS: 900' in (a/'camera-config.js').read_text()
assert 'DETAIL_ZOOM: 3.4' in (b/'camera-config.js').read_text() and 'FLIGHT_MS: 2400' in (b/'camera-config.js').read_text()
for p in ROOT.rglob('*.py'):ast.parse(p.read_text())
(ROOT/'验证记录/两版差异与资源核对.json').write_text(json.dumps({'buildings':39,'photos':39,'models':12,'file_count_per_package':len(checks),'different_files':['camera-config.js'],'config_before':{'DETAIL_ZOOM':1.05,'FLIGHT_MS':900},'config_after':{'DETAIL_ZOOM':3.4,'FLIGHT_MS':2400},'checks':checks,'models_byte_identical_to_original':models},ensure_ascii=False,indent=2))
print('检查通过：39资料，39照片，12座模型，两包仅有参数差异。')
