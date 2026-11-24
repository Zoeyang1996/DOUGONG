"""将可编辑的游戏界面、引擎与规则生成离线游戏页。只用Python标准库。"""
from pathlib import Path
p=Path(__file__).resolve().parent
html=(p/'hall-template.html').read_text().replace('__HALL_GAME_SOURCE__',(p/'engine.js').read_text()+'\n'+(p/'game-source.js').read_text()).replace('__HALL_BASE__','../')
(p/'index.html').write_text(html)
