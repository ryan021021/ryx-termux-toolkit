"""Linha de comando do ryx: monta os subcomandos dos módulos ligados e despacha."""

from __future__ import annotations

import argparse
import os
import sys
import tarfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from ryx import __version__
from ryx.backup import (
    BackupError,
    create_backup,
    list_backups,
    prune_backups,
    restore_backup,
    verify_backup,
)
from ryx.config import Config, ConfigError, load_config, load_modules_flags
from ryx.logger import get_logger
from ryx.modules import UserError, add_apply_flags
from ryx.paths import Paths, find_resource, resolve_paths
from ryx.permissions import Risk, decide
from ryx.platform import detect
from ryx.registry import MODULE_NAMES, Context, Registry, build_registry
from ryx.state import StateError

EXIT_OK, EXIT_FAIL = 0, 1


def _backup_sources(ctx: Context, extra: list[str]) -> list[Path]:
    """Fontes padrão (podem não existir ainda) mais as pedidas com --path (essas têm de existir)."""
    explicit = [Path(p) for p in extra]
    missing = [str(p) for p in explicit if not os.path.lexists(p)]
    if missing:
        raise UserError("--path não existe: " + ", ".join(missing))
    return [ctx.paths.config_dir, ctx.paths.state_file, *explicit]


def _backup_list(_args: argparse.Namespace, ctx: Context) -> int:
    for archive in list_backups(ctx.paths):
        ctx.out(archive.name)
    return EXIT_OK


def _backup_verify(args: argparse.Namespace, ctx: Context) -> int:
    problems = verify_backup(Path(args.archive))
    for problem in problems:
        ctx.out(f"problema: {problem}")
    ctx.out("íntegro" if not problems else f"{len(problems)} problema(s)")
    return EXIT_FAIL if problems else EXIT_OK


def _backup_create(args: argparse.Namespace, ctx: Context) -> int:
    decision = decide(Risk.REVERSIBLE, args.apply, args.yes)
    sources = _backup_sources(ctx, args.path)
    if not decision.execute:
        ctx.out(f"[simulação] backup de: {', '.join(str(s) for s in sources)} ({decision.reason})")
        return EXIT_OK
    result = create_backup(ctx.paths, sources)
    ctx.out(f"backup criado: {result.archive} ({result.files} arquivo(s))")
    for note in result.skipped:
        ctx.out(f"ignorado: {note}")
    return EXIT_OK


def _backup_restore(args: argparse.Namespace, ctx: Context) -> int:
    risk = Risk.SENSITIVE if args.overwrite else Risk.REVERSIBLE
    decision = decide(risk, args.apply, args.yes)
    if not decision.execute:
        ctx.out(f"[simulação] restaurar {args.archive} em {args.to} ({decision.reason})")
        return EXIT_OK
    written = restore_backup(Path(args.archive), Path(args.to), overwrite=args.overwrite)
    ctx.out(f"{len(written)} arquivo(s) restaurado(s) em {args.to}")
    return EXIT_OK


def _backup_prune(args: argparse.Namespace, ctx: Context) -> int:
    decision = decide(Risk.SENSITIVE, args.apply, args.yes)
    keep = ctx.config.get("backup", "keep")
    if not decision.execute:
        ctx.out(f"[simulação] manter só os {keep} backups mais novos ({decision.reason})")
        return EXIT_OK
    ctx.out(f"{len(prune_backups(ctx.paths, keep))} backup(s) removido(s)")
    return EXIT_OK


BACKUP_ACTIONS: dict[str, Callable[[argparse.Namespace, Context], int]] = {
    "list": _backup_list,
    "verify": _backup_verify,
    "create": _backup_create,
    "restore": _backup_restore,
    "prune": _backup_prune,
}


def _backup(args: argparse.Namespace, ctx: Context) -> int:
    handler = BACKUP_ACTIONS.get(args.action)
    if handler is None:
        raise UserError(f"ação de backup desconhecida: {args.action}")
    return handler(args, ctx)


def _modules(registry: Registry) -> Callable[[argparse.Namespace, Context], int]:
    def run(_args: argparse.Namespace, ctx: Context) -> int:
        for spec, enabled in registry.specs():
            state = "ligado" if enabled else "desligado"
            ctx.out(f"{spec.name} [{spec.stability}, {state}]: {spec.summary}")
        return EXIT_OK

    return run


def build_parser(registry: Registry) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ryx", description="Toolkit modular para Termux.")
    parser.add_argument("--version", action="version", version=f"ryx {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMANDO")
    sub.add_parser("modules", help="lista os módulos").set_defaults(run=_modules(registry))
    backup = sub.add_parser("backup", help="backup da config e do estado")
    backup.set_defaults(run=_backup)
    actions = backup.add_subparsers(dest="action", required=True)
    create = actions.add_parser("create")
    create.add_argument("--path", action="append", default=[], help="arquivo ou pasta extra")
    add_apply_flags(create)
    actions.add_parser("list")
    verify = actions.add_parser("verify")
    verify.add_argument("archive")
    restore = actions.add_parser("restore")
    restore.add_argument("archive")
    restore.add_argument("--to", required=True, help="pasta de destino (nunca grava fora dela)")
    restore.add_argument("--overwrite", action="store_true", help="sobrescreve (exige --apply --yes)")
    add_apply_flags(restore)
    add_apply_flags(actions.add_parser("prune"))
    for module in registry.enabled_modules():
        before = set(sub.choices)
        module.add_parser(sub)
        for command in set(sub.choices) - before:
            sub.choices[command].set_defaults(run=module.run)
    return parser


def _load(paths: Paths, env: Mapping[str, str]) -> tuple[Config, dict[str, bool], str | None]:
    """Config e módulos; config inválida não impede o `doctor` de explicar o problema."""
    default = find_resource("config/default.toml", paths, env)
    modules = paths.config_dir / "modules.toml"
    if not modules.is_file():
        modules = find_resource("config/modules.toml", paths, env) or modules
    layers = [p for p in (default, paths.user_config) if p is not None]
    try:
        config, error = load_config(layers), None
    except ConfigError as exc:
        config, error = load_config([]), str(exc)
    return config, load_modules_flags(modules, MODULE_NAMES), error


def main(
    argv: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
    out: Callable[[str], None] = print,
) -> int:
    env = os.environ if env is None else env
    paths = resolve_paths(env)
    try:
        config, flags, config_error = _load(paths, env)
        registry = build_registry(flags)
        args = build_parser(registry).parse_args(argv)
        if config_error and args.command not in ("doctor", "info", "modules"):
            raise ConfigError(config_error)
        log_file = paths.log_file if env.get("RYX_LOG_FILE") == "1" else None
        logger = get_logger(config.get("core", "log_level"), log_file)
        ctx = Context(paths, config, logger, detect(env), out, config_error)
        return args.run(args, ctx)
    except (UserError, ConfigError, StateError, BackupError, OSError, tarfile.TarError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return EXIT_FAIL
    except SystemExit as exc:  # argparse: --help, --version e erro de uso
        return exc.code if isinstance(exc.code, int) else 2
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
