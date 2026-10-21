"""Quanto cuidado cada ação pede. Leitura passa; escrita reversível pede --apply; sensível, --apply --yes."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


class Risk(enum.Enum):
    READ = "read"
    REVERSIBLE = "reversible"
    SENSITIVE = "sensitive"


@dataclass(frozen=True)
class Decision:
    execute: bool
    reason: str


def decide(risk: Risk, apply: bool = False, yes: bool = False) -> Decision:
    """`execute=False` significa simulação: mostrar o plano e não gravar nada."""
    if risk is Risk.READ:
        return Decision(True, "leitura")
    if not apply:
        return Decision(False, "simulação: acrescente --apply para gravar")
    if risk is Risk.SENSITIVE and not yes:
        return Decision(False, "ação sensível: acrescente também --yes")
    return Decision(True, "autorizado")


def safe_relative(raw: str) -> PurePosixPath:
    """Caminho relativo sem `..`, sem raiz e sem `:` (unidade ou fluxo); levanta ValueError se não for."""
    if not raw or "\\" in raw or "\x00" in raw:
        raise ValueError(f"caminho recusado: {raw!r}")
    rel = PurePosixPath(raw)
    if rel.is_absolute() or not rel.parts or ".." in rel.parts or any(":" in part for part in rel.parts):
        raise ValueError(f"caminho recusado: {raw!r}")
    return rel


def inside(base: Path, target: Path) -> bool:
    """True se `target` está dentro de `base` depois de resolver links e `..`."""
    try:
        target.resolve().relative_to(base.resolve())
    except ValueError:
        return False
    return True
