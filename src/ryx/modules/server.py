"""Estado do servidor no Termux (sshd, serviços runit, wake-lock). Só leitura."""

from __future__ import annotations

import argparse
import re
import shutil
import socket
from collections.abc import Callable
from pathlib import Path

from ryx.modules import FAIL, OK, WARN, Check, UserError, report
from ryx.platform import run_text
from ryx.registry import Context, ModuleSpec

SPEC = ModuleSpec("server", "Estado do servidor no Termux: sshd, serviços, wake-lock (só leitura)")
SERVICE_RE = re.compile(r"^[a-z0-9_-]{1,32}$")
CONNECT_TIMEOUT_S = 1.0


def port_open(port: int, connect: Callable[..., object] = socket.create_connection) -> bool:
    try:
        conn = connect(("127.0.0.1", port), timeout=CONNECT_TIMEOUT_S)
    except OSError:
        return False
    close = getattr(conn, "close", None)
    if close:
        close()
    return True


def service_check(
    name: str,
    prefix: Path | None,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[[list[str]], str | None] = run_text,
) -> Check:
    if not SERVICE_RE.match(name):
        raise UserError(f"nome de serviço inválido: {name!r}")
    label = f"serviço {name}"
    if which("sv") is None:
        return Check(label, WARN, "sv (runit) não encontrado", "pkg install termux-services")
    out = runner(["sv", "status", name])
    if out is None:
        known = prefix is not None and (prefix / "var" / "service" / name).exists()
        detail = "sv não respondeu" if known else "serviço não cadastrado"
        return Check(label, WARN, detail, f"sv-enable {name}")
    if out.startswith("run:"):
        return Check(label, OK, out)
    return Check(label, WARN, out, f"sv up {name}")


def run_checks(
    ctx: Context,
    connect: Callable[..., object] = socket.create_connection,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[[list[str]], str | None] = run_text,
) -> list[Check]:
    if not ctx.platform.is_termux:
        return [Check("ambiente", WARN, "fora do Termux; nada para checar", "rode no aparelho")]
    port = ctx.config.get("server", "ssh_port")
    checks = [
        Check("sshd", OK, f"escutando na porta {port}")
        if port_open(port, connect)
        else Check("sshd", FAIL, f"nada escutando na porta {port}", "inicie com: sshd")
    ]
    prefix = Path(ctx.platform.prefix) if ctx.platform.prefix else None
    for name in ctx.config.get("server", "services"):
        checks.append(service_check(name, prefix, which, runner))
    lock = which("termux-wake-lock")
    checks.append(
        Check("wake-lock", OK, "comando disponível")
        if lock
        else Check("wake-lock", WARN, "termux-wake-lock ausente", "pkg install termux-api")
    )
    return checks


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("server", help=SPEC.summary)
    parser.add_subparsers(dest="action", required=True).add_parser("status")


def run(args: argparse.Namespace, ctx: Context) -> int:
    return report(ctx, run_checks(ctx))
