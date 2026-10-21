"""Onde o ryx lê e grava. Tudo sai de variáveis de ambiente, nada fixo no código."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

APP = "ryx"
SOURCE_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    home: Path
    config_dir: Path
    data_dir: Path
    state_dir: Path
    backup_dir: Path

    @property
    def user_config(self) -> Path:
        return self.config_dir / "config.toml"

    @property
    def state_file(self) -> Path:
        return self.state_dir / "state.json"

    @property
    def log_file(self) -> Path:
        return self.state_dir / "ryx.log"


def _home(env: Mapping[str, str]) -> Path:
    value = env.get("HOME") or env.get("USERPROFILE")
    return Path(value) if value else Path.home()


def resolve_paths(env: Mapping[str, str] | None = None) -> Paths:
    """`RYX_HOME` isola tudo numa pasta (testes e instalação sem tocar o HOME)."""
    env = os.environ if env is None else env
    home = _home(env)
    root = env.get("RYX_HOME")
    if root:
        base = Path(root)
        return Paths(home, base / "config", base / "data", base / "state", base / "backups")
    config = Path(env.get("XDG_CONFIG_HOME") or home / ".config") / APP
    data = Path(env.get("XDG_DATA_HOME") or home / ".local" / "share") / APP
    state = Path(env.get("XDG_STATE_HOME") or home / ".local" / "state") / APP
    return Paths(home, config, data, state, data / "backups")


def resource_dirs(paths: Paths, env: Mapping[str, str] | None = None) -> list[Path]:
    """Onde procurar `config/` e `templates/`: variável, pasta de dados, árvore do código."""
    env = os.environ if env is None else env
    found = []
    if env.get("RYX_RESOURCES"):
        found.append(Path(env["RYX_RESOURCES"]))
    found.extend([paths.data_dir, SOURCE_ROOT])
    return found


def find_resource(relative: str, paths: Paths, env: Mapping[str, str] | None = None) -> Path | None:
    for base in resource_dirs(paths, env):
        candidate = base / relative
        if candidate.exists():
            return candidate
    return None
