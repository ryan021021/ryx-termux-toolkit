"""Varredura do código e do repositório: chamadas perigosas, dependências, segredos, dados pessoais."""

import ast
import getpass
import re
import sys
import unittest
from pathlib import Path

from tests.helpers import REPO

SRC = REPO / "src" / "ryx"
SCRIPTS = sorted((REPO / "scripts").glob("*.py"))
BANNED_CALLS = {"eval", "exec", "compile", "__import__", "input"}
BANNED_ATTRS = {("os", "system"), ("os", "popen"), ("pickle", "loads"), ("pickle", "load")}
SKIP_DIRS = {".git", "__pycache__", ".ruff_cache", ".pytest_cache", "dist", "build", ".venv"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"AIza[A-Za-z0-9_-]{30,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]
PERSONAL = [
    re.compile(r"[A-Za-z]:\\Users\\", re.I),
    re.compile(r"/home/[a-z0-9_]+/", re.I),
]
# o login de quem roda os testes também não pode aparecer (lido na hora, para não gravar o nome aqui)
_LOGIN = getpass.getuser()
if len(_LOGIN) >= 4 and _LOGIN.lower() not in {"runner", "root", "user", "admin"}:
    PERSONAL.append(re.compile(rf"\b{re.escape(_LOGIN)}\b"))
TEXT_SUFFIXES = {".py", ".md", ".toml", ".sh", ".yml", ".yaml", ".txt", ".svg", ".json", ".zsh", ".bash", ""}
THIS_FILE = Path(__file__).resolve()


def python_files():
    return sorted(SRC.rglob("*.py"))


def parsed():
    for file in python_files():
        yield file, ast.parse(file.read_text(encoding="utf-8"))


def repo_text_files():
    for path in REPO.rglob("*"):
        if not path.is_file() or SKIP_DIRS & set(path.relative_to(REPO).parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size < 1_000_000:
            yield path


class DangerousCallsTest(unittest.TestCase):
    def test_nada_de_eval_exec_os_system_ou_shell_true(self):
        offenders = []
        for file, tree in parsed():
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if isinstance(func, ast.Name) and func.id in BANNED_CALLS:
                    offenders.append(f"{file.name}:{node.lineno} {func.id}()")
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if (func.value.id, func.attr) in BANNED_ATTRS:
                        offenders.append(f"{file.name}:{node.lineno} {func.value.id}.{func.attr}()")
                spawns = (isinstance(func, ast.Attribute) and getattr(func.value, "id", "") == "subprocess") or (
                    isinstance(func, ast.Name) and func.id in {"run", "Popen", "call", "check_call", "check_output"}
                )
                for kw in node.keywords:
                    safe = isinstance(kw.value, ast.Constant) and kw.value.value is False
                    if spawns and kw.arg == "shell" and not safe:
                        offenders.append(f"{file.name}:{node.lineno} shell=")
        self.assertEqual(offenders, [])

    def test_so_biblioteca_padrao(self):
        stdlib = set(sys.stdlib_module_names)
        outside = []
        for file, tree in parsed():
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    names = [node.module]
                for name in names:
                    top = name.split(".")[0]
                    if top not in stdlib and top != "ryx":
                        outside.append(f"{file.name}: {name}")
        self.assertEqual(outside, [])

    def test_subprocess_so_com_lista_de_argumentos(self):
        offenders = []
        for file, tree in parsed():
            for node in ast.walk(tree):
                is_call = (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "subprocess"
                )
                if is_call and node.args and not isinstance(node.args[0], (ast.List, ast.Name)):
                    offenders.append(f"{file.name}:{node.lineno}")
        self.assertEqual(offenders, [])


WAITING_CALLS = {"run", "check_output", "check_call", "call"}


def waiting_subprocess_calls(tree):
    """Chamadas subprocess.run/check_output/... (ou `run(...)` importado) que esperam o processo."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        via_module = (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
            and func.attr in WAITING_CALLS
        )
        bare = isinstance(func, ast.Name) and func.id in {"check_output", "check_call"}
        if via_module or bare:
            yield node


class SubprocessTimeoutTest(unittest.TestCase):
    def test_todo_subprocess_que_espera_tem_timeout(self):
        offenders, seen = [], 0
        for file, tree in [*parsed(), *((f, ast.parse(f.read_text(encoding="utf-8"))) for f in SCRIPTS)]:
            for node in waiting_subprocess_calls(tree):
                seen += 1
                if not any(kw.arg == "timeout" for kw in node.keywords):
                    offenders.append(f"{file.name}:{node.lineno}")
        self.assertGreaterEqual(seen, 3, "o teste deixou de enxergar as chamadas de subprocess")
        self.assertEqual(offenders, [])

    def test_o_detector_pega_chamada_sem_timeout(self):
        tree = ast.parse("import subprocess\nsubprocess.run(['x'], check=False)\nsubprocess.check_output(['y'])")
        found = list(waiting_subprocess_calls(tree))
        self.assertEqual(len(found), 2)
        self.assertFalse(any(kw.arg == "timeout" for node in found for kw in node.keywords))


class RepositoryHygieneTest(unittest.TestCase):
    def test_sem_segredos_no_repositorio(self):
        hits = []
        for path in repo_text_files():
            if path.resolve() == THIS_FILE or "tests" in path.relative_to(REPO).parts:
                continue  # os testes citam chaves falsas de propósito
            text = path.read_text(encoding="utf-8", errors="ignore")
            hits += [f"{path.relative_to(REPO)}: {p.pattern}" for p in SECRET_PATTERNS if p.search(text)]
        self.assertEqual(hits, [])

    def test_sem_caminhos_pessoais_nem_nome_do_dono(self):
        hits = []
        for path in repo_text_files():
            if path.resolve() == THIS_FILE:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            hits += [f"{path.relative_to(REPO)}: {p.pattern}" for p in PERSONAL if p.search(text)]
        self.assertEqual(hits, [])

    def test_gitignore_cobre_segredos_e_artefatos(self):
        text = (REPO / ".gitignore").read_text(encoding="utf-8")
        for needle in (".env", "*.pem", "__pycache__", "dist/"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
