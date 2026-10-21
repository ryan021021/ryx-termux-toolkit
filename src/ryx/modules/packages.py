"""Pacotes recomendados do Termux: confere o que falta e instala só com --apply."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess  # noqa: S404
from collections.abc import Callable

from ryx.modules import UserError, add_apply_flags
from ryx.permissions import Risk, decide
from ryx.platform import StatusRunner, run_status
from ryx.registry import Context, ModuleSpec

SPEC = ModuleSpec("packages", "Confere e instala os pacotes recomendados (pkg)")
PACKAGE_RE = re.compile(r"^[a-z0-9][a-z0-9+.-]{0,63}$")
INSTALL_TIMEOUT_S = 1800
DPKG_NOT_FOUND = 1  # dpkg-query -W sai com 1 quando nenhum pacote casa com o nome


def validate_names(names: list[str]) -> list[str]:
    bad = [n for n in names if not PACKAGE_RE.match(n)]
    if bad:
        raise UserError("nome de pacote inválido: " + ", ".join(repr(b) for b in bad))
    return names


def package_status(
    names: list[str],
    which: Callable[[str], str | None] = shutil.which,
    runner: StatusRunner = run_status,
) -> dict[str, bool | None]:
    """True instalado, False ausente, None se não consegui consultar (sem dpkg-query, erro ou tempo)."""
    if which("dpkg-query") is None:
        return dict.fromkeys(names)
    return {name: _query(name, runner) for name in names}


def _query(name: str, runner: StatusRunner) -> bool | None:
    answer = runner(["dpkg-query", "-W", "-f=${Status}", name])
    if answer is None:
        return None
    code, out = answer
    if code == DPKG_NOT_FOUND:
        return False
    return "install ok installed" in out if code == 0 else None


def _wanted(ctx: Context, extra: list[str]) -> list[str]:
    names = list(dict.fromkeys([*ctx.config.get("packages", "recommended"), *extra]))
    return validate_names(names)


def _check(ctx: Context, args: argparse.Namespace) -> int:
    status = package_status(_wanted(ctx, args.add))
    for name, state in status.items():
        label = "instalado" if state else "FALTA" if state is False else "desconhecido"
        ctx.out(f"{name}: {label}")
    if all(v is None for v in status.values()):
        ctx.out("dpkg-query não encontrado ou sem resposta: não dá para conferir os pacotes")
    return 0


def _install(ctx: Context, args: argparse.Namespace) -> int:
    status = package_status(_wanted(ctx, args.add))
    unknown = [n for n, s in status.items() if s is None]
    if unknown:
        raise UserError(
            "não consegui consultar o dpkg-query para: " + ", ".join(unknown)
            + " (fora do Termux ou dpkg-query sem resposta); nada foi instalado"
        )
    missing = [n for n, s in status.items() if s is False]
    if not missing:
        ctx.out("nada a instalar")
        return 0
    command = ["pkg", "install", "-y", *missing]
    decision = decide(Risk.REVERSIBLE, args.apply, args.yes)
    if not decision.execute:
        ctx.out(f"[simulação] {' '.join(command)} ({decision.reason})")
        return 0
    if not ctx.platform.is_termux or shutil.which("pkg") is None:
        raise UserError("instalar pacotes só funciona no Termux (comando pkg não encontrado)")
    ctx.logger.info("instalando: %s", ", ".join(missing))
    try:
        done = subprocess.run(command, timeout=INSTALL_TIMEOUT_S, check=False)  # noqa: S603
    except subprocess.TimeoutExpired as exc:
        raise UserError(f"pkg passou de {INSTALL_TIMEOUT_S}s e foi interrompido") from exc
    return done.returncode


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("packages", help=SPEC.summary)
    actions = parser.add_subparsers(dest="action", required=True)
    for name in ("check", "install"):
        sub = actions.add_parser(name)
        sub.add_argument("--add", action="append", default=[], metavar="PACOTE", help="pacote extra")
        if name == "install":
            add_apply_flags(sub)


def run(args: argparse.Namespace, ctx: Context) -> int:
    return _check(ctx, args) if args.action == "check" else _install(ctx, args)
