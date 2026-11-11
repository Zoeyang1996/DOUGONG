from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
p=Path(__file__).resolve().parent.parent/'previews'
items=[('01-第一幕-开场.png','01  榫卯与斗拱 · 滚动叙事'),('02-第二幕-木构星图.png','02  木构建筑 · 三维地球'),('03-第三幕-拼装进行中.png','03  斗拱拼装 · 限时挑战')]
sheet=Image.new('RGB',(1920,468),'#e8e1d3');draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
for i,(file,label) in enumerate(items):
 im=Image.open(p/file).convert('RGB');im.thumbnail((620,388))
 sheet.paste(im,(i*640+10,10));draw.text((i*640+22,420),label,font=font,fill='#4b493e')
sheet.save(p/'三幕视觉总览.jpg',quality=94)
