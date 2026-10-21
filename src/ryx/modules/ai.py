"""CLIs de IA instaladas e se a chave está no ambiente. Nunca imprime o valor da chave."""

from __future__ import annotations

import argparse
import os
import re
import shutil
from collections.abc import Callable, Mapping

from ryx.modules import OK, WARN, Check, UserError, render_checks
from ryx.platform import run_text
from ryx.registry import Context, ModuleSpec

SPEC = ModuleSpec("ai", "Detecta CLIs de IA (claude, gemini, codex) e chaves no ambiente")
NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
KEY_VARS = {
    "claude": ("ANTHROPIC_API_KEY",),
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "codex": ("OPENAI_API_KEY",),
}
VERSION_MAX = 80


def check_provider(
    name: str,
    env: Mapping[str, str],
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[[list[str]], str | None] = run_text,
) -> Check:
    if not NAME_RE.match(name):
        raise UserError(f"nome de provider inválido: {name!r}")
    path = which(name)
    if path is None:
        return Check(name, WARN, "não instalado", "instale o CLI do provider (veja docs/MODULES.md)")
    version = (runner([path, "--version"]) or "versão desconhecida").splitlines()[0][:VERSION_MAX]
    names = KEY_VARS.get(name, ())
    has_key = any(env.get(var) for var in names)
    key_note = (
        "chave no ambiente: sim" if has_key else "chave no ambiente: não" if names else "sem chave conhecida"
    )
    return Check(name, OK, f"{version}; {key_note}")


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("ai", help=SPEC.summary)
    parser.add_subparsers(dest="action", required=True).add_parser("check")


def run(args: argparse.Namespace, ctx: Context, env: Mapping[str, str] | None = None) -> int:
    environment = os.environ if env is None else env
    checks = [check_provider(n, environment) for n in ctx.config.get("ai", "providers")]
    for line in render_checks(checks):
        ctx.out(line)
    return 0
