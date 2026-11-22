import runpy
from pathlib import Path
directory=Path(__file__).parent
runpy.run_path(str(directory/'finalize_delivery.py'))
runpy.run_path(str(directory/'validate_v02.py'))
