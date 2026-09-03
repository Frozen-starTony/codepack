"""
Entry point for running codepack as a module: `python -m codepack`.
"""

import sys
from codepack.cli import main

if __name__ == "__main__":
    sys.exit(main())
