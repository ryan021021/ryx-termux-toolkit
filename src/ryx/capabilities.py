"""Capacidades medidas com estado, evidência e frescor (ADR-0003). Só observa; nunca altera nada.

Regra: o que não deu para medir nunca vira SUPPORTED nem zero. Leitura negada é UNSUPPORTED com a
evidência dizendo por quê; comando que não respondeu é TEMPORARILY_UNAVAILABLE.
"""

from __future__ import annotations

import json
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ryx.platform import run_status

SUPPORTED = "SUPPORTED"
UNSUPPORTED = "UNSUPPORTED"
UNKNOWN = "UNKNOWN"
TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
NEEDS_CONFIGURATION = "NEEDS_CONFIGURATION"
STATES = (SUPPORTED, UNSUPPORTED, UNKNOWN, TEMPORARILY_UNAVAILABLE, NEEDS_CONFIGURATION)

TTL_STATIC_S = 3600  # comando instalado e arquivo do kernel mudam pouco
TTL_BATTERY_S = 60  # bateria muda a cada minuto
MIN_PYTHON = (3, 11)
# python fica fora: no Windows, `python3 --version` pode acionar o instalador e baixar um Python inteiro
COMMANDS = ("git", "ssh", "curl")
VERSION_FLAG = {"ssh": "-V"}  # o ssh não aceita --version
READABLE = {"proc.loadavg": Path("/proc/loadavg"), "proc.meminfo": Path("/proc/meminfo")}
BATTERY_COMMAND = "termux-battery-status"

Clock = Callable[[], datetime]
Which = Callable[[str], "str | None"]
Status = Callable[[list[str]], "tuple[int, str] | None"]
Reader = Callable[[Path], str]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class Capability:
    id: str
    state: str
    evidence: str
    measured_at: datetime
    ttl_s: int

    def __post_init__(self) -> None:
        if self.state not in STATES:
            raise ValueError(f"estado de capacidade inválido: {self.state}")
        if self.measured_at.tzinfo is None:
            raise ValueError("measured_at precisa de fuso (use UTC)")

    def is_stale(self, now: datetime) -> bool:
        return now - self.measured_at > timedelta(seconds=self.ttl_s)

    def as_dict(self, now: datetime) -> dict:
        return {
            "id": self.id,
            "state": self.state,
            "evidence": self.evidence,
            "measured_at": self.measured_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ttl_s": self.ttl_s,
            "stale": self.is_stale(now),
        }


def probe_command(
    command: str, which: Which = shutil.which, status: Status = run_status, now: Clock = utcnow
) -> Capability:
    def cap(state: str, evidence: str) -> Capability:
        return Capability(f"command.{command}", state, evidence, now(), TTL_STATIC_S)

    path = which(command)
    if path is None:
        return cap(UNSUPPORTED, "não está no PATH")
    result = status([command, VERSION_FLAG.get(command, "--version")])
    if result is None:
        return cap(TEMPORARILY_UNAVAILABLE, "não respondeu (tempo esgotado ou erro ao abrir)")
    code, out = result
    if code != 0:
        return cap(UNKNOWN, f"está no PATH, mas a checagem de versão saiu com {code}")
    return cap(SUPPORTED, out.splitlines()[0] if out else path)


def probe_python(version_info: tuple[int, ...] | None = None, now: Clock = utcnow) -> Capability:
    """O interpretador que roda o ryx é a evidência; nenhum processo é aberto."""
    version = tuple(version_info or sys.version_info[:3])
    text = ".".join(str(part) for part in version)
    if version[:2] >= MIN_PYTHON:
        return Capability("runtime.python", SUPPORTED, text, now(), TTL_STATIC_S)
    wanted = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}+"
    return Capability("runtime.python", NEEDS_CONFIGURATION, f"{text}; precisa de {wanted}", now(), TTL_STATIC_S)


def probe_readable(cid: str, path: Path, reader: Reader = _read_text, now: Clock = utcnow) -> Capability:
    def cap(state: str, evidence: str) -> Capability:
        return Capability(cid, state, evidence, now(), TTL_STATIC_S)

    try:
        reader(path)
    except PermissionError:
        return cap(UNSUPPORTED, f"leitura negada em {path}")
    except FileNotFoundError:
        return cap(UNSUPPORTED, f"{path} não existe")
    except OSError as exc:
        return cap(UNKNOWN, f"erro ao ler {path}: {exc.strerror or exc}")
    except ValueError:
        return cap(UNKNOWN, f"{path} não é texto legível")
    return cap(SUPPORTED, f"{path} legível")


def probe_battery(
    is_termux: bool, which: Which = shutil.which, status: Status = run_status, now: Clock = utcnow
) -> Capability:
    def cap(state: str, evidence: str) -> Capability:
        return Capability("battery.read", state, evidence, now(), TTL_BATTERY_S)

    if not is_termux:
        return cap(UNSUPPORTED, "só no Termux, pelo termux-api")
    if which(BATTERY_COMMAND) is None:
        return cap(NEEDS_CONFIGURATION, "instale o pacote termux-api e o app Termux:API")
    result = status([BATTERY_COMMAND])
    if result is None:
        return cap(TEMPORARILY_UNAVAILABLE, f"{BATTERY_COMMAND} não respondeu (o app Termux:API está instalado?)")
    code, out = result
    try:
        data = json.loads(out) if code == 0 else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        return cap(UNKNOWN, f"{BATTERY_COMMAND} não devolveu JSON (código {code})")
    level = data.get("percentage")
    if not isinstance(level, (int, float)) or isinstance(level, bool):
        return cap(UNKNOWN, f"{BATTERY_COMMAND} respondeu sem o nível da bateria")
    return cap(SUPPORTED, f"{level}%")


def collect(
    is_termux: bool,
    which: Which = shutil.which,
    status: Status = run_status,
    reader: Reader = _read_text,
    now: Clock = utcnow,
) -> list[Capability]:
    found = [probe_python(now=now)]
    found += [probe_command(c, which, status, now) for c in COMMANDS]
    found += [probe_readable(cid, path, reader, now) for cid, path in READABLE.items()]
    found.append(probe_battery(is_termux, which, status, now))
    return found
