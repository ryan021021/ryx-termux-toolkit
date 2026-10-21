"""Rotinas embutidas e fechadas: o ryx não executa comando arbitrário vindo de config."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass

from ryx.backup import BackupError, create_backup, prune_backups
from ryx.modules import UserError, add_apply_flags, report
from ryx.modules.diagnostics import run_checks as doctor_checks
from ryx.permissions import Risk, decide
from ryx.registry import Context, ModuleSpec

SPEC = ModuleSpec("automation", "Rotinas embutidas (doctor, backup-config, prune-backups)")


@dataclass(frozen=True)
class Routine:
    name: str
    summary: str
    risk: Risk
    run: Callable[[Context], int]


def _doctor(ctx: Context) -> int:
    return report(ctx, doctor_checks(ctx))


def _backup_config(ctx: Context) -> int:
    try:
        result = create_backup(ctx.paths, [ctx.paths.config_dir, ctx.paths.state_file])
    except BackupError as exc:
        raise UserError(str(exc)) from exc
    ctx.out(f"backup criado: {result.archive} ({result.files} arquivo(s))")
    return 0


def _prune(ctx: Context) -> int:
    removed = prune_backups(ctx.paths, ctx.config.get("backup", "keep"))
    ctx.out(f"{len(removed)} backup(s) antigo(s) removido(s)")
    return 0


ROUTINES = {
    r.name: r
    for r in (
        Routine("doctor", "diagnóstico do ambiente", Risk.READ, _doctor),
        Routine("backup-config", "backup da config e do estado do ryx", Risk.REVERSIBLE, _backup_config),
        Routine("prune-backups", "apaga backups além de backup.keep", Risk.SENSITIVE, _prune),
    )
}


def _list(ctx: Context) -> int:
    for routine in ROUTINES.values():
        ctx.out(f"{routine.name} [{routine.risk.value}]: {routine.summary}")
    return 0


def _run(ctx: Context, args: argparse.Namespace) -> int:
    routine = ROUTINES.get(args.name)
    if routine is None:
        raise UserError(f"rotina desconhecida: {args.name} (veja: ryx automation list)")
    decision = decide(routine.risk, args.apply, args.yes)
    if not decision.execute:
        ctx.out(f"[simulação] {routine.name}: {routine.summary} ({decision.reason})")
        return 0
    return routine.run(ctx)


def _crontab(ctx: Context) -> int:
    ctx.out("# Sugestão (o ryx não instala cron sozinho). Cole com: crontab -e")
    ctx.out("0 3 * * * ryx automation run backup-config --apply")
    ctx.out("30 3 * * 0 ryx automation run prune-backups --apply --yes")
    return 0


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("automation", help=SPEC.summary)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("list")
    actions.add_parser("crontab")
    run_parser = actions.add_parser("run")
    run_parser.add_argument("name")
    add_apply_flags(run_parser)


def run(args: argparse.Namespace, ctx: Context) -> int:
    if args.action == "list":
        return _list(ctx)
    if args.action == "crontab":
        return _crontab(ctx)
    return _run(ctx, args)
