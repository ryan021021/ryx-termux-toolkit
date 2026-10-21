"""doctor e info: olham o ambiente e dizem o que fazer. Nunca alteram nada."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Callable
from pathlib import Path

from ryx import __version__, capabilities
from ryx.modules import FAIL, OK, WARN, Check, report, worst
from ryx.registry import Context, ModuleSpec
from ryx.state import StateError, load_state

SPEC = ModuleSpec("diagnostics", "doctor e info: verifica o ambiente sem alterar nada")
MIN_PYTHON = capabilities.MIN_PYTHON
DISK_FAIL_MB = 100
DISK_WARN_MB = 500
MEM_WARN_MB = 200
COMMANDS = {"git": "pkg install git", "ssh": "pkg install openssh", "curl": "pkg install curl"}


def _existing_ancestor(path: Path) -> Path:
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def read_mem_available_mb(meminfo: Path) -> int | None:
    try:
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def run_checks(
    ctx: Context,
    which: Callable[[str], str | None] = shutil.which,
    disk_usage: Callable[[Path], object] = shutil.disk_usage,
    meminfo: Path = Path("/proc/meminfo"),
    version_info: tuple[int, int] | None = None,
) -> list[Check]:
    checks: list[Check] = []
    py = version_info or sys.version_info[:2]
    ok_py = tuple(py) >= MIN_PYTHON
    checks.append(
        Check(
            "python",
            OK if ok_py else FAIL,
            f"{py[0]}.{py[1]}",
            "" if ok_py else f"instale Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ (pkg install python)",
        )
    )
    info = ctx.platform
    if info.is_termux:
        checks.append(Check("ambiente", OK, f"Termux (Android {info.android_release or '?'})"))
    else:
        checks.append(
            Check("ambiente", WARN, f"{info.system}, fora do Termux", "alguns módulos só rodam no Termux")
        )
    for command, fix in COMMANDS.items():
        found = which(command)
        checks.append(Check(f"comando {command}", OK if found else WARN, found or "não encontrado", fix))
    anchor = _existing_ancestor(ctx.paths.data_dir)
    try:
        free_mb = int(disk_usage(anchor).free // (1024 * 1024))
    except OSError as exc:
        checks.append(Check("disco", WARN, f"não consegui medir ({exc.strerror})"))
    else:
        status = FAIL if free_mb < DISK_FAIL_MB else WARN if free_mb < DISK_WARN_MB else OK
        checks.append(Check("disco", status, f"{free_mb} MB livres", "libere espaço (ex.: pkg clean)"))
    mem = read_mem_available_mb(meminfo)
    if mem is None:
        checks.append(Check("memória", WARN, "MemAvailable indisponível neste sistema"))
    else:
        checks.append(
            Check("memória", WARN if mem < MEM_WARN_MB else OK, f"{mem} MB disponíveis", "feche apps pesados")
        )
    checks.append(
        Check("config", FAIL, ctx.config_error, "corrija o arquivo indicado")
        if ctx.config_error
        else Check("config", OK, "válida")
    )
    try:
        load_state(ctx.paths.state_file)
        checks.append(Check("estado", OK, "legível"))
    except StateError as exc:
        checks.append(Check("estado", FAIL, str(exc), "mova o state.json e rode de novo"))
    return checks


def _doctor(ctx: Context, args: argparse.Namespace) -> int:
    checks = run_checks(ctx)
    result = worst(checks)
    if args.json:
        found = capabilities.collect(ctx.platform.is_termux)
        now = capabilities.utcnow()
        payload = {
            "status": result,
            "checks": [c.__dict__ for c in checks],
            "capabilities": [cap.as_dict(now) for cap in found],
        }
        ctx.out(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        code = report(ctx, checks)
        ctx.out(f"resultado: {result}")
        return code
    return 1 if result == FAIL else 0


def _info(ctx: Context, _args: argparse.Namespace) -> int:
    ctx.out(f"ryx {__version__}")
    for key, value in ctx.platform.as_dict().items():
        ctx.out(f"{key}: {value}")
    for name in ("config_dir", "data_dir", "state_dir", "backup_dir"):
        ctx.out(f"{name}: {getattr(ctx.paths, name)}")
    return 0


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    doctor = subparsers.add_parser("doctor", help="diagnóstico do ambiente")
    doctor.add_argument("--json", action="store_true", help="saída em JSON")
    doctor.set_defaults(handler=_doctor)
    info = subparsers.add_parser("info", help="plataforma e pastas")
    info.set_defaults(handler=_info)


def run(args: argparse.Namespace, ctx: Context) -> int:
    return args.handler(ctx, args)
