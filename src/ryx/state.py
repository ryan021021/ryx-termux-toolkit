"""Estado do ryx em JSON: escrita atômica, permissão 0600, versão checada."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

STATE_VERSION = 1


class StateError(RuntimeError):
    """Estado ilegível ou de uma versão que este ryx não entende."""


def empty_state() -> dict[str, Any]:
    return {"version": STATE_VERSION, "shell": {}, "backups": []}


def _check_shapes(path: Path, data: dict[str, Any]) -> None:
    shell, backups = data["shell"], data["backups"]
    if not isinstance(shell, dict) or not all(isinstance(v, dict) for v in shell.values()):
        raise StateError(f"{path}: formato inválido em 'shell' (esperado um objeto de objetos)")
    if not isinstance(backups, list):
        raise StateError(f"{path}: formato inválido em 'backups' (esperada uma lista)")


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as exc:  # ValueError cobre JSON e UTF-8 inválidos
        raise StateError(f"{path}: ilegível ({exc}). Mova o arquivo e rode de novo.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("version"), int):
        raise StateError(f"{path}: formato desconhecido")
    if data["version"] > STATE_VERSION:
        raise StateError(f"{path}: versão {data['version']} é mais nova que este ryx")
    merged = {**empty_state(), **data}
    _check_shapes(path, merged)
    return merged


def save_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def update_state(path: Path, change: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    data = load_state(path)
    change(data)
    save_state(path, data)
    return data
