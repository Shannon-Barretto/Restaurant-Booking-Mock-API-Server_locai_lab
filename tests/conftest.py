import sys
from pathlib import Path

# project root is parent of the tests directory
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))