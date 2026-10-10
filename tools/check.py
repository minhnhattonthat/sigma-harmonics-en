"""One-command check (pre-commit runs this): tests + text lint."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
steps = [[sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', 'tests']]
lint = ROOT / 'tools' / 'lint.py'
if lint.exists():
    steps.append([sys.executable, '-X', 'utf8', str(lint)])
for cmd in steps:
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode:
        sys.exit(r.returncode)
