"""课后修改 js 后可重新生成双击离线页。现场改 camera-config.js 无需运行此工具。"""
from pathlib import Path
import shutil,tempfile,re,subprocess,os
ROOT=Path(__file__).resolve().parent
subprocess.run([os.sys.executable,str(ROOT/'game/build_template.py')],check=True)
with tempfile.TemporaryDirectory(prefix='atlas-offline-') as work:
    w=Path(work)
    shutil.copytree(ROOT/'game',w/'game');shutil.copytree(ROOT/'js',w/'js');shutil.copytree(ROOT/'vendor',w/'vendor')
    (w/'assets/data').mkdir(parents=True)
    for name in ('china-provinces.json','land.geojson'):shutil.copy2(ROOT/'assets/data'/name,w/'assets/data'/name)
    shutil.copy2(ROOT/'data.json',w/'data.json')
    p=w/'js/data.js';s=p.read_text();start=s.index('let cache = null;');end=s.index('export function filterBuildings')
    s=s[:start]+"import BUILDINGS from '../data.json';\nexport async function loadBuildings(){ return BUILDINGS; }\n\n"+s[end:];p.write_text(s)
    p=w/'js/globe/globe.js';s=p.read_text()
    s=re.sub(r"const landGeoJson = await fetch\('\./assets/data/land\.geojson'\)\.then\(\(res\) => \{.*?\n  \}\);",'const landGeoJson = LAND;',s,flags=re.S)
    start=s.index('  let data = null;')
    end=s.index('  const features =',start)
    s=s[:start]+'  const data = PROVINCES;\n\n'+s[end:]
    s="import LAND from '../../assets/data/land.geojson';\nimport PROVINCES from '../../assets/data/china-provinces.json';\n"+s
    assert 'fetch(' not in s;p.write_text(s)
    exe=os.environ.get('ESBUILD_BIN') or shutil.which('esbuild')
    command=[exe] if exe else ['npx','--no-install','esbuild']
    subprocess.run(command+[str(w/'js/main.js'),'--bundle','--format=esm','--minify','--legal-comments=none','--loader:.geojson=json','--alias:three='+str(w/'vendor/three.module.js'),'--outfile='+str(w/'bundle.js')],check=True)
    html=(ROOT/'开发预览.html').read_text();js=(w/'bundle.js').read_text().replace('</script','<'+chr(92)+'/script')
    html=re.sub(r'<script type="importmap">.*?</script>','',html,flags=re.S)
    html=html.replace('<script type="module" src="js/main.js"></script>','<script type="module">'+js+'</script>')
    (ROOT/'index.html').write_text(html)
print('已更新双击离线页 index.html。保留整个文件夹即可转交使用。')
