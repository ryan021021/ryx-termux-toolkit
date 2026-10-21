"""Estado do servidor no Termux (sshd, serviços runit, wake-lock). Só leitura."""

from __future__ import annotations

import argparse
import glob
import os
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
    command = ["sv", "status", name]
    if prefix is not None and not os.environ.get("SVDIR"):
        # sessão SSH sem login não traz o SVDIR; sem ele o sv não acha nenhum serviço
        command = ["env", f"SVDIR={prefix / 'var' / 'service'}", *command]
    out = runner(command)
    if out is None:
        known = prefix is not None and (prefix / "var" / "service" / name).exists()
        if known:
            return Check(label, WARN, "sv não respondeu", "confira com: export SVDIR=$PREFIX/var/service; sv status " + name)
        return Check(label, WARN, "serviço não cadastrado", f"sv-enable {name}")
    if out.startswith("run:"):
        return Check(label, OK, out)
    return Check(label, WARN, out, f"sv up {name}")


def _first_wins(lines: list[str], settings: dict[str, str]) -> bool:
    """A primeira ocorrência vale, menos ListenAddress (junta todas). Para no `Match`: devolve False."""
    for raw in lines:
        parts = raw.split(None, 1)
        if len(parts) != 2 or parts[0].startswith("#"):
            continue
        key = parts[0].lower()
        if key == "match":
            return False
        if key == "listenaddress":
            settings["listenaddress"] = f"{settings.get('listenaddress', '')} {parts[1].strip()}".strip()
        else:
            settings.setdefault(key, parts[1].strip())
    return True


def _include_files(main: Path, patterns: str) -> list[Path]:
    found: list[Path] = []
    for pattern in patterns.split():
        pattern = pattern.strip("\"")
        base = Path(pattern) if Path(pattern).is_absolute() else main.parent / pattern
        try:
            found.extend(sorted(Path(m) for m in glob.glob(str(base))))
        except (OSError, ValueError):
            continue
    return found


def read_sshd_settings(
    prefix: Path | None, runner: Callable[[list[str]], str | None] = run_text
) -> dict[str, str] | None:
    """Config efetiva do sshd: `sshd -T` e, se não der, os arquivos (a primeira ocorrência vale, `Match` ignorado). Só leitura."""
    settings: dict[str, str] = {}
    _first_wins((runner(["sshd", "-T"]) or "").splitlines(), settings)
    if "passwordauthentication" in settings:
        return settings
    settings = {}
    if prefix is None:
        return None
    main = prefix / "etc" / "ssh" / "sshd_config"
    try:
        lines = main.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in lines:
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "include":
            for inc in _include_files(main, parts[1]):
                try:
                    if not _first_wins(inc.read_text(encoding="utf-8").splitlines(), settings):
                        break
                except OSError:
                    continue
        elif not _first_wins([line], settings):
            break
    return settings or None


def _listens_everywhere(addresses: str | None) -> bool:
    """Qualquer ListenAddress amplo (ou nenhum) conta como escuta em todas as interfaces."""
    if not addresses:
        return True
    for address in addresses.split():
        host = address.split("]")[0] + "]" if address.startswith("[") else address.rsplit(":", 1)[0] if address.count(":") == 1 else address
        if host in ("0.0.0.0", "[::]", "::", "*", ""):
            return True
    return False


def sshd_config_checks(settings: dict[str, str] | None, home: Path) -> list[Check]:
    """Avisa (nunca muda) sobre senha, interfaces e chaves do sshd (ameaça M8, achado F7)."""
    if settings is None:
        return [Check("sshd config", WARN, "NÃO VERIFICADO: não consegui ler a config do sshd", "rode: sshd -T")]
    keys_file = home / ".ssh" / "authorized_keys"
    try:
        keys = [ln for ln in keys_file.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    except OSError:
        keys = []
    checks = []
    if settings.get("passwordauthentication", "yes").lower() == "yes":
        checks.append(Check("sshd senha", WARN, "login por senha ligado", "depois de testar a chave, ponha PasswordAuthentication no na config do sshd"))
    else:
        checks.append(Check("sshd senha", OK, "login por senha desligado"))
    if _listens_everywhere(settings.get("listenaddress")):
        checks.append(Check("sshd escuta", WARN, "escuta em todas as interfaces", "em rede de terceiros, prefira um túnel; ListenAddress limita"))
    else:
        checks.append(Check("sshd escuta", OK, f"escuta em {settings['listenaddress']}"))
    if keys:
        checks.append(Check("sshd chaves", OK, f"{len(keys)} chave(s) autorizada(s)"))
    else:
        checks.append(Check("sshd chaves", WARN, "nenhuma chave em ~/.ssh/authorized_keys", "copie a chave pública antes de desligar a senha"))
    return checks


def run_checks(
    ctx: Context,
    connect: Callable[..., object] = socket.create_connection,
    which: Callable[[str], str | None] = shutil.which,
    runner: Callable[[list[str]], str | None] = run_text,
    sshd_settings: Callable[[], dict[str, str] | None] | None = None,
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
    settings = sshd_settings() if sshd_settings else read_sshd_settings(prefix, runner)
    checks.extend(sshd_config_checks(settings, ctx.paths.home))
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
