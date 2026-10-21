import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import REPO

SCRIPT = REPO / "scripts" / "generate-release-notes.py"
spec = importlib.util.spec_from_file_location("generate_release_notes", SCRIPT)
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)

SAMPLE = """# Changelog

## [Unreleased]

## [0.2.0] - 2026-11-01

### Corrigido
- coisa B

## [0.1.0] - 2026-10-20

### Adicionado
- coisa A
"""


class ExtractTest(unittest.TestCase):
    def test_pega_so_a_secao_pedida(self):
        text = notes.extract(SAMPLE, "0.2.0")
        self.assertIn("coisa B", text)
        self.assertNotIn("coisa A", text)
        self.assertFalse([line for line in text.splitlines() if line.startswith("## ")])

    def test_ultima_secao_vai_ate_o_fim(self):
        self.assertIn("coisa A", notes.extract(SAMPLE, "0.1.0"))

    def test_versao_inexistente_e_none_e_unreleased_vazia(self):
        self.assertIsNone(notes.extract(SAMPLE, "9.9.9"))
        self.assertEqual(notes.extract(SAMPLE, "Unreleased"), "")

    def test_changelog_real_tem_a_versao_do_pacote(self):
        from ryx import __version__

        text = notes.extract((REPO / "CHANGELOG.md").read_text(encoding="utf-8"), __version__)
        self.assertTrue(text, f"CHANGELOG sem notas para {__version__}")


class CliTest(unittest.TestCase):
    def run_script(self, *argv):
        done = subprocess.run(  # noqa: S603
            [sys.executable, str(SCRIPT), *argv],
            capture_output=True, text=True, encoding="utf-8", check=False, timeout=30,
        )
        return done.returncode, done.stdout, done.stderr

    def test_prefixo_v_e_changelog_alternativo(self):
        with tempfile.TemporaryDirectory() as tmp:
            changelog = Path(tmp) / "C.md"
            changelog.write_text(SAMPLE, encoding="utf-8")
            code, out, _ = self.run_script("v0.2.0", "--changelog", str(changelog))
        self.assertEqual(code, 0)
        self.assertIn("coisa B", out)

    def test_versao_ausente_e_arquivo_inexistente_saem_com_1(self):
        self.assertEqual(self.run_script("9.9.9")[0], 1)
        self.assertEqual(self.run_script("0.1.0", "--changelog", "nao-existe.md")[0], 1)


if __name__ == "__main__":
    unittest.main()
