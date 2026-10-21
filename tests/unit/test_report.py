import tempfile
import unittest
from pathlib import Path

from ryx.modules import FAIL, OK, WARN, Check, render_checks, report
from tests.helpers import make_ctx


class ReportTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ctx, self.lines = make_ctx(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_imprime_cada_check_e_devolve_0_sem_falha(self):
        checks = [Check("a", OK, "bom"), Check("b", WARN, "meh", "arrume")]
        self.assertEqual(report(self.ctx, checks), 0)
        self.assertEqual(self.lines, render_checks(checks))

    def test_devolve_1_se_algum_check_falhou(self):
        checks = [Check("a", OK, "bom"), Check("b", FAIL, "ruim", "conserte")]
        self.assertEqual(report(self.ctx, checks), 1)
        self.assertTrue(any("[FALHA] b: ruim" in line for line in self.lines))
        self.assertTrue(any("como resolver: conserte" in line for line in self.lines))

    def test_lista_vazia_e_zero(self):
        self.assertEqual(report(self.ctx, []), 0)
        self.assertEqual(self.lines, [])


if __name__ == "__main__":
    unittest.main()
