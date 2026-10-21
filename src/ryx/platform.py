"""Detecta onde o ryx está rodando. Sem rede, sem root; só ambiente e `getprop` se existir."""

from __future__ import annotations

import os
import platform as _stdlib
import shutil
import subprocess  # noqa: S404
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass

Runner = Callable[[list[str]], str | None]
StatusRunner = Callable[[list[str]], tuple[int, str] | None]


@dataclass(frozen=True)
class PlatformInfo:
    system: str
    machine: str
    python: str
    is_termux: bool
    prefix: str | None
    android_release: str | None
    shell: str | None

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def run_text(command: list[str], timeout: float = 5.0) -> str | None:
    """Roda sem shell, com limite de tempo; qualquer falha vira None."""
    if shutil.which(command[0]) is None:
        return None
    try:
        done = subprocess.run(  # noqa: S603
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def run_status(command: list[str], timeout: float = 5.0) -> tuple[int, str] | None:
    """(código de saída, saída aparada); None só se o comando nem chegou a rodar (ausente, tempo)."""
    if shutil.which(command[0]) is None:
        return None
    try:
        done = subprocess.run(  # noqa: S603
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.returncode, done.stdout.strip()


def detect(
    env: Mapping[str, str] | None = None,
    system: str | None = None,
    machine: str | None = None,
    runner: Runner = run_text,
) -> PlatformInfo:
    env = os.environ if env is None else env
    prefix = env.get("PREFIX")
    is_termux = bool(env.get("TERMUX_VERSION")) or "com.termux" in (prefix or "")
    release = runner(["getprop", "ro.build.version.release"]) if is_termux else None
    shell = env.get("SHELL")
    return PlatformInfo(
        system=system or _stdlib.system(),
        machine=machine or _stdlib.machine(),
        python=_stdlib.python_version(),
        is_termux=is_termux,
        prefix=prefix,
        android_release=release or None,
        shell=os.path.basename(shell) if shell else None,
    )
