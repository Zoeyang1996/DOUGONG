import runpy,sys
from pathlib import Path
p=Path(__file__).parent
sys.argv.append('--main')
runpy.run_path(str(p/'render_previews.py'))
runpy.run_path(str(p/'bake_export.py'))
