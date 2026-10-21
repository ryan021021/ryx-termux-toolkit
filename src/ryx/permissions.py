"""Quanto cuidado cada ação pede. Leitura passa; escrita reversível pede --apply; sensível, --apply --yes."""

from __future__ import annotations

import enum
import hashlib
import json
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


class Level(enum.Enum):
    """ADR-0002: L0 leitura · L1 sem política (nega) · L2 reversível · L3 sensível."""

    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3


_LEVEL_OF_RISK = {Risk.READ: Level.L0, Risk.REVERSIBLE: Level.L2, Risk.SENSITIVE: Level.L3}


def level_of(risk: object) -> Level:
    """Classe ausente ou desconhecida é L3 (nega por padrão)."""
    if isinstance(risk, Level):
        return risk
    try:
        return _LEVEL_OF_RISK.get(risk, Level.L3)  # type: ignore[call-overload]
    except TypeError:
        return Level.L3


@dataclass(frozen=True)
class Plan:
    """A operação exata: o que roda, com quais argumentos, em qual alvo, em qual versão."""

    operation: str
    args: tuple[str, ...]
    target: str
    version: str

    def digest(self) -> str:
        blob = json.dumps([self.operation, list(self.args), self.target, self.version], ensure_ascii=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Approval:
    """Aprovação presa ao hash de um plano; `by` é "human" ou "agent"."""

    plan_hash: str
    by: str


def decide_plan(
    plan: Plan,
    level: object,
    apply: bool = False,
    yes: bool = False,
    approval: Approval | None = None,
) -> Decision:
    """Nega por padrão: sem classe vira L3, L1 não existe e L2/L3 só rodam com aprovação do mesmo plano."""
    if not isinstance(level, (Level, Risk)):
        return Decision(False, "operação sem classe de risco: negada")
    lvl = level_of(level)
    if lvl is Level.L1:
        return Decision(False, "L1 não existe sem política escrita: negada")
    if lvl is Level.L0:
        return Decision(True, "leitura")
    if not apply:
        return Decision(False, "simulação: acrescente --apply para gravar")
    if approval is None or approval.by not in ("human", "agent"):
        return Decision(False, "sem aprovação válida do plano")
    if approval.plan_hash != plan.digest():
        return Decision(False, "plano mudou depois da aprovação: negado")
    if lvl is Level.L3:
        if approval.by != "human":
            return Decision(False, "L3 nunca é aprovado por agente")
        if not yes:
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
