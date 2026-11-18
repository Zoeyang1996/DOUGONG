from pathlib import Path
import subprocess,shutil,json,hashlib
base=Path(r'C:\Users\Administrator\Downloads')
for role in ['C','D']:
 p=base/f'{role}同学-比赛独立训练包-11-19';node=p/'runtime/node.exe'
 # Validate the actual reset and solve sequence without leaving an incomplete exercise on delivery.
 subprocess.run([str(node),str(p/'prepare.cjs')],check=True,capture_output=True)
 if role=='C':
  assert len(json.loads((p/'knowledge/cards.json').read_text(encoding='utf-8')))==1
  assert '练习：在此接通问答' in (p/'web/guide/app.js').read_text(encoding='utf-8')
  assert 'TWEEN_MS = 50' in (p/'web/act-02-globe/js/globe/globe.js').read_text(encoding='utf-8')
  paths=['web/guide/app.js','knowledge/cards.json','web/act-02-globe/js/globe/globe.js']
  (p/'web/guide/assets').mkdir(exist_ok=True)
  shutil.copy2(p/'web/shared/wood-guide/assets/xiaogong-turnaround-v01.png',p/'web/guide/assets/小拱原始三视图.png')
  (p/'原始备份/web/guide/assets').mkdir(exist_ok=True)
  shutil.copy2(p/'web/guide/assets/小拱原始三视图.png',p/'原始备份/web/guide/assets/小拱原始三视图.png')
 else:
  assert (p/'web/act-03-assembly/app.js').read_text(encoding='utf-8').count('<8 /* 练习预设')==2
  paths=['web/act-03-assembly/app.js']
 for rel in paths:shutil.copy2(p/'原始备份'/rel,p/rel)
 run=subprocess.run([str(node),'--test',str(p/'tests/*.test.cjs')],capture_output=True,text=True,encoding='utf-8');assert run.returncode==0,run.stdout+run.stderr
 for f in list((p/'web/guide').glob('*.js'))+[p/'server.cjs',p/'prepare.cjs']:
  assert subprocess.run([str(node),'--check',str(f)],capture_output=True).returncode==0
 
 for dll in Path(r'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin').glob('*.dll'):shutil.copy2(dll,p/'runtime'/dll.name)
 (p/'runtime/运行程序来源.txt').write_text('Node.js '+subprocess.check_output([str(node),'-p','process.version']).decode().strip()+'；来自当前Codex运行环境。官方许可：https://github.com/nodejs/node/blob/main/LICENSE',encoding='utf-8')
 for cmd in p.glob('*.cmd'):
  text=cmd.read_text(encoding='utf-8');cmd.write_bytes(text.replace('\r\n','\n').replace('\r','').replace('\n','\r\n').encode('utf-8'))
 hashes={str(f.relative_to(p)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest() for f in (p/'web').rglob('*') if f.is_file()}
 (p/'原始文件校验.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf-8')
 report=f'''# 打包验证记录\n\n2026-11-19\n\n- 从下载目录内自带Node启动独立服务：通过。\n- 本地首页、模块依赖、数据与模型HTTP加载：通过。\n- 活跃页面静态依赖无缺失；C典藏12个模型路径存在。\n- 比赛起点准备脚本及定向恢复：通过；交付时已恢复完整基准。\n- 代码/服务检查：{'4' if role=='C' else '3'}项通过。\n- 新增JavaScript语法检查：通过。\n- 不包含原项目私有.env；不依赖DOUGONG绝对路径。\n- 浏览器自动化连接不可用，本次未完成页面截图与视觉操作复核。\n- 麦克风识别、真实API调用、真实触摸屏需按手册在比赛设备上验收。\n\n''' + run.stdout
 (p/'验证记录.md').write_text(report,encoding='utf-8')
 print(role,'reset, source restore, tests and syntax PASS; MB',round(sum(f.stat().st_size for f in p.rglob('*') if f.is_file())/1048576,1))

