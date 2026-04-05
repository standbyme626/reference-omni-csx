"""Domain-service application package."""
import sys
from pathlib import Path

# Ensure the project root is on sys.path so providers/ and models/ are importable.
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
