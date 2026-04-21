import sys
from pathlib import Path

# Add blackhole-py/extra/ so 'emu' is importable as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
