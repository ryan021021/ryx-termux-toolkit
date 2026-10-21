"""Bloco gerenciado no .bashrc/.zshrc: instala, atualiza e remove só o que o ryx escreveu."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from pathlib import Path

from ryx.backup import create_backup
from ryx.modules import UserError, add_apply_flags
from ryx.paths import Paths, find_resource
from ryx.permissions import Risk, decide
from ryx.registry import Context, ModuleSpec
from ryx.state import load_state, update_state

SPEC = ModuleSpec("shell", "Bloco gerenciado no .bashrc/.zshrc (prompt e aliases)")
START = "# >>> ryx >>>"
END = "# <<< ryx <<<"
THEME_RE = re.compile(r"^[a-z][a-z0-9-]{0,31}$")
SHELLS = {"bash": ("ryx.sh", ".bashrc"), "zsh": ("ryx.zsh", ".zshrc")}


def render_block(shell: str, theme: str, paths: Paths) -> str:
    if shell not in SHELLS:
        raise UserError(f"shell desconhecido: {shell} (use bash ou zsh)")
    if not THEME_RE.match(theme):
        raise UserError(f"nome de tema inválido: {theme!r}")
    base = find_resource(f"templates/{shell}/{SHELLS[shell][0]}", paths)
    skin = find_resource(f"templates/themes/{theme}.{shell}", paths)
    if base is None or skin is None:
        raise UserError(f"template não encontrado para {shell}/{theme}")
    body = base.read_text(encoding="utf-8").rstrip() + "\n" + skin.read_text(encoding="utf-8")
    return f"{START}\n# Gerenciado pelo ryx; edite fora deste bloco.\n{body.rstrip()}\n{END}\n"


def find_block(text: str) -> tuple[int, int] | None:
    """Posição (início, fim) do bloco; None se não existe. Marcador sem par é erro."""
    starts, ends = text.count(START), text.count(END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1 or text.index(START) > text.index(END):
        raise UserError("marcadores do ryx quebrados no arquivo; corrija à mão antes de continuar")
    begin = text.index(START)
    finish = text.index(END) + len(END)
    if text[finish : finish + 1] == "\n":
        finish += 1
    return begin, finish


def apply_block(text: str, block: str) -> str:
    where = find_block(text)
    if where is None:
        if not text or text.endswith("\n\n"):
            separator = ""
        else:
            separator = "\n" if text.endswith("\n") else "\n\n"
        return text + separator + block
    return text[: where[0]] + block + text[where[1] :]


def remove_block(text: str) -> str:
    where = find_block(text)
    if where is None:
        return text
    before = text[: where[0]].rstrip("\n")
    after = text[where[1] :]
    return before + ("\n" if before else "") + after


def write_atomic(path: Path, text: str) -> None:
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".ryx-rc-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _rc_path(home: Path, raw: str) -> Path:
    """`~/...` ou caminho absoluto, sempre dentro do HOME (sem `..`); o resto é erro."""
    if raw.startswith("~/"):
        candidate = home / raw[2:]
    elif Path(raw).is_absolute():
        candidate = Path(raw)
    else:
        raise UserError(f"rc_files: {raw!r} precisa começar com ~/ (ou ser absoluto dentro do HOME)")
    normal = Path(os.path.normpath(candidate))
    base = Path(os.path.normpath(home))
    if normal == base or base not in normal.parents:
        raise UserError(f"rc_files: {raw!r} fica fora do HOME; o ryx só mexe em arquivos do HOME")
    return normal


def _targets(ctx: Context, only: str | None) -> list[tuple[str, Path]]:
    if only:
        if only not in SHELLS:
            raise UserError(f"shell desconhecido: {only} (use bash ou zsh)")
        return [(only, ctx.paths.home / SHELLS[only][1])]
    found = []
    for raw in ctx.config.get("shell", "rc_files"):
        expanded = _rc_path(ctx.paths.home, raw)
        found.append(("zsh" if expanded.name.endswith("zshrc") else "bash", expanded))
    return found


def _read(path: Path) -> str:
    try:
        if not path.exists():
            return ""
        # Path.read_text(newline=) só existe a partir do Python 3.13; o ryx aceita 3.11
        with path.open(encoding="utf-8", newline="") as handle:
            return handle.read()
    except UnicodeDecodeError as exc:
        raise UserError(f"{path}: não está em UTF-8 ({exc.reason}); não vou mexer nele") from exc
    except OSError as exc:
        raise UserError(f"{path}: não consegui ler ({exc.strerror})") from exc


def _status(ctx: Context, args: argparse.Namespace) -> int:
    theme = args.theme or ctx.config.get("shell", "theme")
    for shell, rc in _targets(ctx, args.shell):
        text = _read(rc)
        if find_block(text) is None:
            ctx.out(f"{rc}: não instalado")
        elif apply_block(text, render_block(shell, theme, ctx.paths)) == text:
            ctx.out(f"{rc}: instalado e em dia ({shell}/{theme})")
        else:
            ctx.out(f"{rc}: instalado, mas diferente do template atual (rode install --apply)")
    return 0


def _record(state: dict, rc: Path, shell: str, theme: str, remove: bool) -> None:
    if remove:
        state["shell"].pop(str(rc), None)
    else:
        state["shell"][str(rc)] = {"shell": shell, "theme": theme}


def _change(ctx: Context, args: argparse.Namespace, remove: bool) -> int:
    theme = args.theme or ctx.config.get("shell", "theme")
    decision = decide(Risk.REVERSIBLE, args.apply, args.yes)
    if decision.execute:
        load_state(ctx.paths.state_file)  # estado ilegível aborta antes de qualquer rc ser gravado
    for shell, rc in _targets(ctx, args.shell):
        real = rc.resolve()  # rc pode ser link (dotfiles): grava no alvo e mantém o link
        text = _read(real)
        if remove:
            new = remove_block(text)
        else:
            new = apply_block(text, render_block(shell, theme, ctx.paths))
        if new == text:
            ctx.out(f"{rc}: nada a fazer")
            continue
        verb = "remover bloco de" if remove else "gravar bloco em"
        if not decision.execute:
            ctx.out(f"[simulação] {verb} {rc} ({decision.reason})")
            continue
        if real.exists():
            result = create_backup(ctx.paths, [real])
            ctx.out(f"backup de {rc}: {result.archive}")
        write_atomic(real, new)
        update_state(
            ctx.paths.state_file,
            lambda s, rc=rc, shell=shell: _record(s, rc, shell, theme, remove),
        )
        ctx.out(f"{rc}: {'bloco removido' if remove else 'bloco gravado'}")
    return 0


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("shell", help=SPEC.summary)
    actions = parser.add_subparsers(dest="action", required=True)
    for name in ("status", "install", "uninstall"):
        sub = actions.add_parser(name)
        sub.add_argument("--shell", choices=sorted(SHELLS), help="só este shell")
        sub.add_argument("--theme", help="nome do tema (padrão: config shell.theme)")
        if name != "status":
            add_apply_flags(sub)


def run(args: argparse.Namespace, ctx: Context) -> int:
    if args.action == "status":
        return _status(ctx, args)
    return _change(ctx, args, remove=args.action == "uninstall")
