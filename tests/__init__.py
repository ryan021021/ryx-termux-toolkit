"""Testes do ryx. Importar este pacote põe `src/` no sys.path (unittest e pytest)."""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
