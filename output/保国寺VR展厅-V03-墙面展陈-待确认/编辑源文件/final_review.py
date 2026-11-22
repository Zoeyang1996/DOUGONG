import runpy,sys
from pathlib import Path
directory=Path(__file__).parent
runpy.run_path(str(directory/'build_curation.py'))
runpy.run_path(str(directory/'validate_curation.py'))
sys.argv.append('--refined')
runpy.run_path(str(directory/'render_curation.py'))
