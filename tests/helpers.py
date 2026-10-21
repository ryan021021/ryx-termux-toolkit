"""Montagem de um Context isolado para os testes (nada fora da pasta temporária)."""

from __future__ import annotations

import copy
import logging
import os
from pathlib import Path

from ryx.config import BUILTIN_DEFAULTS, Config
from ryx.paths import resolve_paths
from ryx.platform import detect
from ryx.registry import Context

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
IS_WINDOWS = os.name == "nt"


def make_ctx(
    root: Path,
    termux: bool = False,
    overrides: dict[str, dict] | None = None,
    config_error: str | None = None,
) -> tuple[Context, list[str]]:
    """Contexto com HOME e RYX_HOME dentro de `root`; devolve também as linhas impressas."""
    home = root / "home"
    home.mkdir(parents=True, exist_ok=True)
    env = {"HOME": str(home), "RYX_HOME": str(root / "ryx"), "RYX_RESOURCES": str(REPO)}
    paths = resolve_paths(env)
    values = copy.deepcopy(BUILTIN_DEFAULTS)
    for section, body in (overrides or {}).items():
        values[section].update(body)
    platform_env = {"TERMUX_VERSION": "0.118", "PREFIX": "/data/data/com.termux/files/usr"}
    info = detect(platform_env if termux else {}, "Linux", "aarch64", lambda _c: "14")
    lines: list[str] = []
    logger = logging.getLogger("ryx-test")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return Context(paths, Config(values), logger, info, lines.append, config_error), lines


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")
    return path
