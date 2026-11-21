from pathlib import Path
from html.parser import HTMLParser
import re,shutil,json,hashlib,zipfile
root=Path(__file__).resolve().parents[1]
source=Path('/Users/yangzhe/Downloads/榫卯智言-三幕小拱离线网页包-20261118/web-exhibits')
name='保国寺宋大殿-120秒拼搭游戏-学生离线版-20261119'
out=root/'output'/name
out.mkdir(parents=True,exist_ok=True);(out/'资源').mkdir(exist_ok=True)
s=(source/'act-03.html').read_text()
s=re.sub(r'<!-- Shared wooden AI guide -->.*?(?=</body>)','',s,flags=re.S)
s=s.replace('assets/保国寺整殿模型.js','资源/保国寺整殿模型.js').replace('<a href="index.html">木构之间</a>','<a href="#" aria-label="保国寺木构拼搭游戏">木构之间</a>')
(out/'双击打开-保国寺宋大殿拼搭.html').write_text(s)
shutil.copy2(source/'assets/保国寺整殿模型.js',out/'资源/保国寺整殿模型.js')
shutil.copy2(root/'web-exhibits/shared/vendor/THREE-LICENSE.txt',out/'资源/Three.js许可.txt')
(out/'先读我-学生使用说明.txt').write_text('''保国寺宋大殿 · 120秒拼搭游戏 · 学生离线版

【怎么打开】
1. 将压缩包完整解压到电脑或希沃屏幕的本地文件夹。
2. 双击“ 双击打开-保国寺宋大殿拼搭.html ”，使用较新版本的 Microsoft Edge 或 Google Chrome 打开。
3. 等待木构准备完成，再点击“开始120秒挑战”。
4. 可以全屏演示。不需要联网、Python、Node.js或Unity。

【怎么玩】
右边是打乱顺序的20组备料，按住木件拖到左边相应提示区域，松手拼合。
同一个结构阶段允许自由排序，底部的各组柱子不用按固定先后顺序。
落入合理提示区域会自动吸附；错误放置退回备料区，不增加进度。
完成当前阶段后进入下一阶段；全部完成获胜，超过120秒则挑战结束。
拼接、倒计时、成功和失败配有音效。先点击开始，再按需要开启声音并调整电脑音量。
按住左边空白区域可旋转查看，使用界面上的放大、缩小和复位按钮调整视角。
点击“完成效果”可以查看整殿参考。挑战结束后可以重新开始。

【发给同学或拷到学校】
必须发送整个ZIP，或整个解压后的文件夹，不要只发送HTML文件。
“资源”文件夹中的模型不能删除或改名，否则会无法备料。
不要直接在压缩包预览窗口里运行HTML，先解压。
本包只包含整殿拼搭游戏，不含另两幕网页、AI联网服务及密钥，也不是VR安装包。

【遇到问题】
画面空白：确认完整解压、资源文件夹齐全，换较新版本的Edge或Chrome；学校电脑的显卡与浏览器设置可能影响三维显示。
一直准备木构：检查是否漏拷了“资源/保国寺整殿模型.js”，关闭其他大型三维程序后重开。
没有声音：点击开始、检查游戏声音开关、浏览器标签页是否静音以及电脑音量。
拖拽不顺：先使用鼠标测试，再在希沃屏上确认触摸驱动和浏览器；实际学校设备仍需要现场验证。

【文件组成】
双击打开-保国寺宋大殿拼搭.html：界面、游戏程序、装配清单与音效。
资源/保国寺整殿模型.js：本地木构模型。
资源/Three.js许可.txt：三维运行库许可。
文件校验清单.json：拷贝完整性核对信息，无需打开也能玩。

此版本是可直接运行的离线成品，程序与运行库已合并。需要练习修改模块源码时，应使用对应源码工程，不必在此合并成品中直接修改运行库。
模型为参考现场资料整理的教学模型，不作为文物测绘或构件加工依据。
''')
class Check(HTMLParser):
 def handle_starttag(self,t,attrs):
  a=dict(attrs)
  for k in ('src','href'):
   v=a.get(k,'')
   if v and not v.startswith(('#','data:','blob:')):
    assert not v.startswith(('http:','https:')),v
    assert (out/v).is_file(),v
Check().feed(s)
assert 'wood-guide/' not in s
assert 'new StageChallenge(20)' in s
assert 'duration=120000' in s
items=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.rglob('*') if p.is_file() and p.name!='文件校验清单.json']
(out/'文件校验清单.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
zp=out.with_suffix('.zip')
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in out.rglob('*'):
  if p.is_file():z.write(p,name+'/'+p.relative_to(out).as_posix())
with zipfile.ZipFile(zp) as z:assert z.testzip() is None
print(json.dumps({'folder':str(out),'zip':str(zp),'zipMiB':round(zp.stat().st_size/1024**2,1),'files':len(items)+1},ensure_ascii=False))
