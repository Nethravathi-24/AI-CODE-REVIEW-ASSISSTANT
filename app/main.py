"""Streamlit launcher entry point forwarding to app.py main()."""

from pathlib import Path
import sys

# Ensure repository root is in sys.path for absolute package imports
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from app.app import main
except ImportError:
    from app import main

if __name__ == "__main__":
    main()
