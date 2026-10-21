"""Log com máscara de segredos: o que sai na tela ou no arquivo nunca leva token."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

REDACTED = "[REDACTED]"
PRIVATE_FILE = 0o600
_NAMES = r"(?:token|secret|password|passwd|senha|api[_-]?key|access[_-]?key|private[_-]?key|authorization)"
# Valor: entre aspas (aceita espaço) ou, se não houver aspas fechando, até o próximo espaço.
_VALUE = r"""(?P<q>["'])(?:(?!(?P=q)).)*(?P=q)|\S+"""
_PATTERNS = [
    # chave=valor, "chave": "valor", GITHUB_TOKEN=..., AWS_SECRET_ACCESS_KEY=..., --token=...
    re.compile(
        r"(?i)(?P<head>[\w.-]{0,64}" + _NAMES + r"[\w.-]{0,64}[\"']?\s*[=:]\s*(?:(?:bearer|basic)\s+)?)(?:"
        + _VALUE
        + ")"
    ),
    # opção de linha de comando com o valor separado por espaço: --token abc
    re.compile(r"(?i)(?P<head>(?<!\S)--[\w-]{0,64}" + _NAMES + r"[\w-]{0,64}\s+)(?!-)(?:" + _VALUE + ")"),
    # usuário:senha@host dentro de URL
    re.compile(r"(?P<head>\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s:/@]+:)[^\s@/]+(?=@)"),
    re.compile(r"(?i)(?P<head>\bbearer\s+)[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{20,}"
        r"|AKIA[0-9A-Z]{16}|xox[abprs]-[A-Za-z0-9-]{10,})\b"
    ),
]


def _mask(match: re.Match[str]) -> str:
    groups = match.groupdict()
    quote = groups.get("q") or ""
    return (groups.get("head") or "") + quote + REDACTED + quote


def redact(text: str) -> str:
    out = text
    for pattern in _PATTERNS:
        out = pattern.sub(_mask, out)
    return out


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


def _open_private_log(log_file: Path) -> logging.FileHandler:
    """Abre o log com modo 0600 (cria assim e fecha um log antigo aberto demais)."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    os.close(os.open(log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, PRIVATE_FILE))
    os.chmod(log_file, PRIVATE_FILE)
    return logging.FileHandler(log_file, encoding="utf-8")


def get_logger(level: str = "info", log_file: Path | None = None) -> logging.Logger:
    logger = logging.getLogger("ryx")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    for old in list(logger.handlers):
        logger.removeHandler(old)
        old.close()
    logger.propagate = False
    formatter = RedactingFormatter("%(asctime)s %(levelname)s %(message)s")
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    if log_file is not None:
        try:
            handler = _open_private_log(log_file)
        except OSError:
            logger.warning("não consegui abrir o log em %s; sigo só na tela", log_file)
        else:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger
