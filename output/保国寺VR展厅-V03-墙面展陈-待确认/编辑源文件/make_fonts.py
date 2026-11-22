"""Embed just the glyphs used by this review version instead of full CJK collections."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools import subset
root=Path(__file__).resolve().parents[1]
charset=''.join((root/'编辑源文件'/name).read_text() for name in ['curation.py','build_curation.py'])
charset+=''.join(chr(i) for i in range(32,127))
out=root/'素材/字体';out.mkdir(exist_ok=True)
for source,name,index in [('/System/Library/Fonts/Supplemental/Songti.ttc','展陈标题.ttf',0),('/System/Library/Fonts/Supplemental/Songti.ttc','展陈标题补字.ttf',1),('/System/Library/Fonts/STHeiti Medium.ttc','展陈正文.ttf',0)]:
 font=TTFont(source,fontNumber=index)
 options=subset.Options();options.hinting=False;options.layout_features=['*']
 worker=subset.Subsetter(options=options);worker.populate(text=charset);worker.subset(font)
 font.save(out/name)
 print(name,(out/name).stat().st_size)
