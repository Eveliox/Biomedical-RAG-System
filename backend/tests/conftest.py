"""Shared pytest config: put backend/ on sys.path so `import app...` works."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # .../backend
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
