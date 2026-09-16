from pathlib import Path
import sys
from firmware import build, pack

import hashlib
output = Path(sys.argv[1] if len(sys.argv) > 1 else 'build/bh_hcq_v2.bin')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_bytes(blob:=pack(build()))
print(f'{hashlib.sha256(blob).hexdigest()}  {output} ({len(blob)} bytes)')
