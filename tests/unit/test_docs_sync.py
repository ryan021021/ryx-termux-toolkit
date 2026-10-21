"""Teste de sincronização de documentação, CLI e versões (Regra 13 da Carta de Engenharia)."""

from __future__ import annotations

import argparse
import pathlib
import re
import tomllib
import unittest

from ryx import __version__
from ryx.cli import build_parser
from ryx.registry import MODULE_NAMES, build_registry

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent


def get_cli_subcommands() -> set[str]:
    """Extrai todos os comandos e subcomandos do parser da CLI do ryx."""
    registry = build_registry({m: True for m in MODULE_NAMES})
    parser = build_parser(registry)
    commands: set[str] = set()

    top_subparsers = None
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            top_subparsers = action
            break

    if not top_subparsers:
        return commands

    for name, subparser in top_subparsers.choices.items():
        nested = None
        for action in subparser._actions:
            if isinstance(action, argparse._SubParsersAction):
                nested = action
                break
        if nested:
            for sub_name in nested.choices.keys():
                commands.add(f"{name} {sub_name}")
        else:
            commands.add(name)

    return commands


def extract_doc_subcommands(text: str, cli_commands: set[str] | None = None) -> set[str]:
    """Extrai subcomandos documentados em blocos inline no formato `ryx ...`."""
    if cli_commands is None:
        cli_commands = get_cli_subcommands()

    top_levels = {cmd.split()[0] for cmd in cli_commands}
    doc_commands: set[str] = set()

    for match in re.findall(r"`ryx\s+([^`]+)`", text):
        clean = match.strip()
        tokens = clean.split()
        if not tokens:
            continue
        first = tokens[0]
        if first not in top_levels:
            continue

        if first in cli_commands:
            doc_commands.add(first)
            continue

        if len(tokens) > 1:
            second = tokens[1]
            if "|" in second:
                for sub in second.split("|"):
                    candidate = f"{first} {sub}"
                    if candidate in cli_commands:
                        doc_commands.add(candidate)
            else:
                candidate = f"{first} {second}"
                if candidate in cli_commands:
                    doc_commands.add(candidate)

    return doc_commands


def get_versions(root: pathlib.Path = REPO_ROOT) -> dict[str, str]:
    """Obtém as versões declaradas em pyproject.toml, src/ryx/__init__.py e CHANGELOG.md."""
    pyproject_file = root / "pyproject.toml"
    with open(pyproject_file, "rb") as f:
        pyproject_data = tomllib.load(f)
    pyproject_version = str(pyproject_data.get("project", {}).get("version", ""))

    init_file = root / "src" / "ryx" / "__init__.py"
    init_text = init_file.read_text(encoding="utf-8")
    init_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_text)
    init_version = init_match.group(1) if init_match else ""

    changelog_file = root / "CHANGELOG.md"
    changelog_text = changelog_file.read_text(encoding="utf-8")
    changelog_match = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", changelog_text, re.MULTILINE)
    changelog_version = changelog_match.group(1) if changelog_match else ""

    return {
        "pyproject.toml": pyproject_version,
        "src/ryx/__init__.py": init_version,
        "CHANGELOG.md": changelog_version,
    }


def check_versions_match(versions: dict[str, str]) -> None:
    """Valida se todas as versões declaradas existem e são idênticas."""
    for source in ("pyproject.toml", "src/ryx/__init__.py", "CHANGELOG.md"):
        if not versions.get(source):
            raise ValueError(f"Versão ausente em {source}")

    v_pyproject = versions["pyproject.toml"]
    v_init = versions["src/ryx/__init__.py"]
    v_changelog = versions["CHANGELOG.md"]

    if v_pyproject != v_init:
        raise ValueError(f"Versão difere: pyproject.toml ({v_pyproject}) != src/ryx/__init__.py ({v_init})")
    if v_pyproject != v_changelog:
        raise ValueError(f"Versão difere: pyproject.toml ({v_pyproject}) != CHANGELOG.md ({v_changelog})")


def check_commands_match(cli_cmds: set[str], doc_cmds: set[str]) -> None:
    """Valida se o conjunto de subcomandos da CLI bate exatamente com a documentação."""
    faltando = sorted(cli_cmds - doc_cmds)
    if faltando:
        raise ValueError(f"Subcomando(s) da CLI ausentes em docs/COMMANDS.md: {faltando}")
    sobrando = sorted(doc_cmds - cli_cmds)
    if sobrando:
        raise ValueError(f"Subcomando(s) documentados que não existem na CLI: {sobrando}")


class DocsSyncTest(unittest.TestCase):
    """Garante que a documentação, CLI e versões estejam sincronizadas (Regra 13)."""

    def test_versoes_sincronizadas(self):
        """Versão em pyproject.toml, src/ryx/__init__.py e CHANGELOG.md devem ser idênticas."""
        versions = get_versions()
        check_versions_match(versions)

    def test_todos_subcomandos_cli_documentados_e_vice_versa(self):
        """Todo subcomando na CLI deve estar em docs/COMMANDS.md e vice-versa."""
        cli_cmds = get_cli_subcommands()
        self.assertTrue(cli_cmds, "Nenhum comando encontrado na CLI")

        doc_file = REPO_ROOT / "docs" / "COMMANDS.md"
        self.assertTrue(doc_file.is_file(), f"Arquivo não encontrado: {doc_file}")
        doc_cmds = extract_doc_subcommands(doc_file.read_text(encoding="utf-8"), cli_cmds)

        check_commands_match(cli_cmds, doc_cmds)

    def test_mutante_versao_divergente_falha(self):
        """Mutante: se qualquer versão divergir ou faltar, a validação deve falhar."""
        valid = {"pyproject.toml": "0.1.0", "src/ryx/__init__.py": "0.1.0", "CHANGELOG.md": "0.1.0"}
        check_versions_match(valid)

        mutante_init = {**valid, "src/ryx/__init__.py": "0.2.0"}
        with self.assertRaisesRegex(ValueError, "pyproject.toml.*!=.*src/ryx/__init__.py"):
            check_versions_match(mutante_init)

        mutante_changelog = {**valid, "CHANGELOG.md": "0.9.9"}
        with self.assertRaisesRegex(ValueError, "pyproject.toml.*!=.*CHANGELOG.md"):
            check_versions_match(mutante_changelog)

        mutante_vazio = {**valid, "pyproject.toml": ""}
        with self.assertRaisesRegex(ValueError, "Versão ausente"):
            check_versions_match(mutante_vazio)

    def test_mutante_subcomando_apagado_falha(self):
        """Mutante: se um subcomando for removido da documentação, a validação deve acusar."""
        cli_cmds = {"modules", "server status", "doctor"}
        doc_cmds_incompleto = {"modules", "doctor"}  # falta "server status"

        with self.assertRaisesRegex(ValueError, "ausentes em docs/COMMANDS.md:.*server status"):
            check_commands_match(cli_cmds, doc_cmds_incompleto)

    def test_mutante_subcomando_inexistente_falha(self):
        """Mutante: se um subcomando inexistente for documentado, a validação deve acusar."""
        cli_cmds = {"modules", "doctor"}
        doc_cmds_extra = {"modules", "doctor", "fantasma executar"}

        with self.assertRaisesRegex(ValueError, "não existem na CLI:.*fantasma executar"):
            check_commands_match(cli_cmds, doc_cmds_extra)


if __name__ == "__main__":
    unittest.main()

