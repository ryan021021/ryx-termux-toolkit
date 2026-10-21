"""Configuração: padrão embutido, `default.toml`, depois o arquivo do usuário. Chave inválida é erro."""

from __future__ import annotations

import copy
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

BUILTIN_DEFAULTS: dict[str, dict[str, Any]] = {
    "core": {"log_level": "info"},
    "backup": {"keep": 10},
    "shell": {"theme": "default", "rc_files": ["~/.bashrc"]},
    "packages": {"recommended": ["git", "openssh", "curl", "python", "jq", "nano"]},
    "server": {"ssh_port": 8022, "services": ["sshd"]},
    "ai": {"providers": ["claude", "gemini", "codex"]},
}
LOG_LEVELS = ("debug", "info", "warning", "error")
LOG_LEVELS_TEXT = ", ".join(LOG_LEVELS)


class ConfigError(ValueError):
    """Configuração inválida; a mensagem diz o arquivo, a chave e o motivo."""


@dataclass(frozen=True)
class Config:
    values: dict[str, dict[str, Any]]

    def get(self, section: str, key: str) -> Any:
        return self.values[section][key]


def _check_value(section: str, key: str, value: Any, example: Any) -> str | None:
    where = f"{section}.{key}"
    if isinstance(example, int) and (isinstance(value, bool) or not isinstance(value, int)):
        return f"{where}: precisa ser inteiro"
    if isinstance(example, str) and not isinstance(value, str):
        return f"{where}: precisa ser texto"
    if isinstance(example, list) and (
        not isinstance(value, list) or not all(isinstance(v, str) for v in value)
    ):
        return f"{where}: precisa ser lista de textos"
    if where == "core.log_level" and value not in LOG_LEVELS:
        return f"{where}: use um de {LOG_LEVELS_TEXT}"
    if where == "backup.keep" and not 1 <= value <= 1000:
        return f"{where}: use de 1 a 1000"
    if where == "server.ssh_port" and not 1 <= value <= 65535:
        return f"{where}: porta de 1 a 65535"
    return None


def validate(data: dict[str, Any]) -> list[str]:
    errors = []
    for section, body in data.items():
        if section not in BUILTIN_DEFAULTS:
            errors.append(f"seção desconhecida: [{section}]")
            continue
        if not isinstance(body, dict):
            errors.append(f"[{section}] precisa ser uma tabela")
            continue
        for key, value in body.items():
            if key not in BUILTIN_DEFAULTS[section]:
                errors.append(f"chave desconhecida: {section}.{key}")
                continue
            problem = _check_value(section, key, value, BUILTIN_DEFAULTS[section][key])
            if problem:
                errors.append(problem)
    return errors


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (ValueError, RecursionError) as exc:  # TOMLDecodeError e UnicodeDecodeError são ValueError
        raise ConfigError(f"{path}: TOML inválido ({exc})") from exc
    except OSError as exc:
        raise ConfigError(f"{path}: não consegui ler ({exc.strerror})") from exc


def load_config(layers: list[Path]) -> Config:
    """Cada camada (arquivo existente) sobrescreve a anterior, chave por chave."""
    merged = copy.deepcopy(BUILTIN_DEFAULTS)
    for path in layers:
        if not path.is_file():
            continue
        data = _read_toml(path)
        problems = validate(data)
        if problems:
            raise ConfigError(f"{path}: " + "; ".join(problems))
        for section, body in data.items():
            merged[section].update(body)
    return Config(merged)


def load_modules_flags(path: Path | None, names: list[str]) -> dict[str, bool]:
    """Todos ligados por padrão; `modules.toml` só desliga/liga os que conhece."""
    flags = dict.fromkeys(names, True)
    if path is None or not path.is_file():
        return flags
    table = _read_toml(path).get("modules", {})
    if not isinstance(table, dict):
        raise ConfigError(f"{path}: modules precisa ser uma tabela ([modules])")
    for name, value in table.items():
        if name not in flags:
            raise ConfigError(f"{path}: módulo desconhecido '{name}'")
        if not isinstance(value, bool):
            raise ConfigError(f"{path}: modules.{name} precisa ser true ou false")
        flags[name] = value
    return flags
