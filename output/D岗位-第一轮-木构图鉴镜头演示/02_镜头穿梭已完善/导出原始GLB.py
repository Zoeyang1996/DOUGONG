from pathlib import Path
import base64,re,json
root=Path(__file__).resolve().parent;out=root/'导出的原始GLB';out.mkdir(exist_ok=True)
for p in (root/'assets/models-js').glob('*.js'):
    encoded=re.search(r']="([A-Za-z0-9+/=]+)";',p.read_text()).group(1)
    (out/(p.stem+'.glb')).write_bytes(base64.b64decode(encoded))
print('12座模型已导出：'+str(out))
