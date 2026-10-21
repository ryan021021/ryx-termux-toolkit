"""Módulos do ryx. Cada um define SPEC, add_parser(subparsers) e run(args, ctx) -> int."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ryx.registry import Context

OK, WARN, FAIL = "ok", "warn", "fail"


class UserError(RuntimeError):
    """Erro que o usuário resolve (argumento, arquivo, ambiente); vira `erro: ...` e exit 1."""


def add_apply_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--apply", action="store_true", help="grava de verdade (padrão: simulação)")
    parser.add_argument("--yes", action="store_true", help="confirma ação sensível (com --apply)")


_MARK = {OK: "[ok]   ", WARN: "[aviso]", FAIL: "[FALHA]"}


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str
    fix: str = ""


def render_checks(checks: list[Check]) -> list[str]:
    lines = []
    for check in checks:
        lines.append(f"{_MARK[check.status]} {check.name}: {check.detail}")
        if check.fix and check.status != OK:
            lines.append(f"         como resolver: {check.fix}")
    return lines


def report(ctx: Context, checks: list[Check]) -> int:
    """Imprime os checks e devolve o código de saída (1 se algum falhou, senão 0)."""
    for line in render_checks(checks):
        ctx.out(line)
    return 1 if worst(checks) == FAIL else 0


def worst(checks: list[Check]) -> str:
    statuses = {c.status for c in checks}
    return FAIL if FAIL in statuses else WARN if WARN in statuses else OK
