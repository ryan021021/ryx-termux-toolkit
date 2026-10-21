"""Registro de módulos: cada módulo se descreve (SPEC), cria seus subcomandos e roda."""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from types import ModuleType

from ryx.config import Config
from ryx.paths import Paths
from ryx.platform import PlatformInfo

MODULE_NAMES = ["shell", "diagnostics", "packages", "server", "automation", "ai"]


@dataclass(frozen=True)
class ModuleSpec:
    name: str
    summary: str
    stability: str = "experimental"


@dataclass
class Context:
    """O que todo comando recebe. `out` é a saída padrão, trocável nos testes."""

    paths: Paths
    config: Config
    logger: logging.Logger
    platform: PlatformInfo
    out: Callable[[str], None]
    config_error: str | None = None


class Registry:
    def __init__(self) -> None:
        self._modules: dict[str, ModuleType] = {}
        self._enabled: dict[str, bool] = {}

    def add(self, module: ModuleType, enabled: bool = True) -> None:
        spec: ModuleSpec = module.SPEC
        if spec.name in self._modules:
            raise ValueError(f"módulo duplicado: {spec.name}")
        self._modules[spec.name] = module
        self._enabled[spec.name] = enabled

    def specs(self) -> list[tuple[ModuleSpec, bool]]:
        return [(m.SPEC, self._enabled[n]) for n, m in self._modules.items()]

    def enabled_modules(self) -> list[ModuleType]:
        return [m for n, m in self._modules.items() if self._enabled[n]]


def build_registry(flags: dict[str, bool]) -> Registry:
    registry = Registry()
    for name in MODULE_NAMES:
        registry.add(importlib.import_module(f"ryx.modules.{name}"), flags.get(name, True))
    return registry
