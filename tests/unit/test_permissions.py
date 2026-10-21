import tempfile
import unittest
from pathlib import Path, PurePosixPath

from ryx.permissions import Risk, decide, inside, safe_relative


class DecideTest(unittest.TestCase):
    def test_leitura_sempre_executa(self):
        for apply in (False, True):
            for yes in (False, True):
                self.assertTrue(decide(Risk.READ, apply, yes).execute)

    def test_reversivel_so_executa_com_apply(self):
        self.assertFalse(decide(Risk.REVERSIBLE).execute)
        self.assertFalse(decide(Risk.REVERSIBLE, apply=False, yes=True).execute)
        self.assertTrue(decide(Risk.REVERSIBLE, apply=True).execute)

    def test_sensivel_exige_apply_e_yes(self):
        self.assertFalse(decide(Risk.SENSITIVE).execute)
        self.assertFalse(decide(Risk.SENSITIVE, apply=True).execute)
        self.assertFalse(decide(Risk.SENSITIVE, apply=False, yes=True).execute)
        self.assertTrue(decide(Risk.SENSITIVE, apply=True, yes=True).execute)

    def test_o_motivo_explica_o_que_falta(self):
        self.assertIn("--apply", decide(Risk.REVERSIBLE).reason)
        self.assertIn("--yes", decide(Risk.SENSITIVE, apply=True).reason)


class SafeRelativeTest(unittest.TestCase):
    def test_aceita_relativo_simples(self):
        self.assertEqual(safe_relative("home/a/b.txt"), PurePosixPath("home/a/b.txt"))

    def test_recusa_o_que_escapa(self):
        cases = ("", ".", "./", "../x", "a/../b", "/abs", "C:/x", "a\\b", "a\x00b", "..", "x/..")
        for raw in (*cases, "a/b:c", "a:b", "x/C:/y"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                safe_relative(raw)


class SafeRelativeBordasTest(unittest.TestCase):
    def test_ponto_e_dois_pontos_viram_valueerror_e_nao_indexerror(self):
        for raw in (".", "./", "./."):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "caminho recusado"):
                safe_relative(raw)

    def test_ponto_no_meio_e_normalizado(self):
        self.assertEqual(safe_relative("a/./b"), PurePosixPath("a/b"))


class InsideTest(unittest.TestCase):
    def test_dentro_e_fora(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "base"
            base.mkdir()
            self.assertTrue(inside(base, base / "a" / "b"))
            self.assertFalse(inside(base, base / ".." / "fora"))
            self.assertFalse(inside(base, Path(tmp) / "outra"))


if __name__ == "__main__":
    unittest.main()
