"""doctor e info: olham o ambiente e dizem o que fazer. Nunca alteram nada."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import textwrap
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from ryx import __version__, capabilities
from ryx.modules import FAIL, OK, WARN, Check, report, worst
from ryx.registry import Context, ModuleSpec
from ryx.state import StateError, load_state

# Severidades (§22)
SEV_INFO = "INFO"
SEV_NOTICE = "NOTICE"
SEV_WARNING = "WARNING"
SEV_ERROR = "ERROR"
SEV_CRITICAL = "CRITICAL"
SEVERITIES = (SEV_INFO, SEV_NOTICE, SEV_WARNING, SEV_ERROR, SEV_CRITICAL)

# Estados de Nó (§22)
NODE_HEALTHY = "HEALTHY"
NODE_DEGRADED = "DEGRADED"
NODE_OFFLINE = "OFFLINE"
NODE_BLOCKED = "BLOCKED"
NODE_UNKNOWN = "UNKNOWN"
NODE_STATES = (NODE_HEALTHY, NODE_DEGRADED, NODE_OFFLINE, NODE_BLOCKED, NODE_UNKNOWN)

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


def determine_node_state(
    checks: list[Check],
    capabilities_list: list[capabilities.Capability] | None = None,
    heartbeat_at: datetime | None = None,
    heartbeat_ttl_s: int = 120,
    offline: bool = False,
    now: datetime | None = None,
) -> tuple[str, str]:
    """Determina (node_state, severity) conforme v2.1 §22.

    Regra estrita: medida vencida (ttl_s) ou heartbeat vencido NUNCA vira HEALTHY; vira UNKNOWN.
    """
    if now is None:
        now = capabilities.utcnow()

    if offline:
        return NODE_OFFLINE, SEV_ERROR

    if heartbeat_at is not None:
        if (now - heartbeat_at).total_seconds() > heartbeat_ttl_s:
            return NODE_UNKNOWN, SEV_WARNING

    caps = capabilities_list or []
    if any(cap.is_stale(now) for cap in caps):
        return NODE_UNKNOWN, SEV_WARNING

    statuses = {c.status for c in checks}
    if FAIL in statuses:
        return NODE_BLOCKED, SEV_CRITICAL

    cap_states = {cap.state for cap in caps}
    if (
        capabilities.UNSUPPORTED in cap_states
        or capabilities.NEEDS_CONFIGURATION in cap_states
        or capabilities.TEMPORARILY_UNAVAILABLE in cap_states
        or WARN in statuses
    ):
        return NODE_DEGRADED, SEV_WARNING if WARN in statuses else SEV_NOTICE

    return NODE_HEALTHY, SEV_INFO


def format_narrow(text: str, width: int = 40) -> list[str]:
    """Quebra linhas preservando indentação e garantindo limite de largura de tela."""
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph:
            lines.append("")
            continue
        if len(paragraph) <= width:
            lines.append(paragraph)
        else:
            sublines = textwrap.wrap(paragraph, width=width, break_long_words=True, break_on_hyphens=True)
            lines.extend(sublines if sublines else [""])
    return lines


def _doctor(ctx: Context, args: argparse.Namespace) -> int:
    checks = run_checks(ctx)
    result = worst(checks)
    found = capabilities.collect(ctx.platform.is_termux)
    now = capabilities.utcnow()
    node_state, severity = determine_node_state(checks, found, now=now)

    if args.json:
        payload = {
            "status": result,
            "node_state": node_state,
            "severity": severity,
            "checks": [c.__dict__ for c in checks],
            "capabilities": [cap.as_dict(now) for cap in found],
        }
        ctx.out(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        code = report(ctx, checks)
        state_msg = f"nó: {node_state} (severidade: {severity})"
        for line in format_narrow(state_msg, width=40):
            ctx.out(line)
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
