import sys
import unittest

from ryx.platform import detect, run_status, run_text

TERMUX_PREFIX = "/data/data/com.termux/files/usr"


class DetectTest(unittest.TestCase):
    def test_termux_por_variavel(self):
        calls = []
        info = detect({"TERMUX_VERSION": "0.118"}, "Linux", "aarch64", lambda c: calls.append(c) or "14")
        self.assertTrue(info.is_termux)
        self.assertEqual(info.android_release, "14")
        self.assertEqual(calls, [["getprop", "ro.build.version.release"]])

    def test_termux_pelo_prefix(self):
        info = detect({"PREFIX": TERMUX_PREFIX}, "Linux", "aarch64", lambda _c: None)
        self.assertTrue(info.is_termux)
        self.assertEqual(info.prefix, TERMUX_PREFIX)
        self.assertIsNone(info.android_release)

    def test_fora_do_termux_nao_chama_getprop(self):
        def runner(_command):
            raise AssertionError("getprop não devia rodar fora do Termux")

        info = detect({"PREFIX": "/usr", "SHELL": "/bin/zsh"}, "Linux", "x86_64", runner)
        self.assertFalse(info.is_termux)
        self.assertEqual(info.shell, "zsh")
        self.assertEqual((info.system, info.machine), ("Linux", "x86_64"))

    def test_sem_shell_na_variavel(self):
        self.assertIsNone(detect({}, "Linux", "x", lambda _c: None).shell)

    def test_as_dict_tem_todos_os_campos(self):
        keys = set(detect({}, "Linux", "x", lambda _c: None).as_dict())
        self.assertEqual(
            keys,
            {"system", "machine", "python", "is_termux", "prefix", "android_release", "shell"},
        )


class RunTextTest(unittest.TestCase):
    def test_comando_inexistente_devolve_none(self):
        self.assertIsNone(run_text(["comando-que-nao-existe-ryx"]))

    def test_devolve_a_saida_aparada(self):
        self.assertEqual(run_text([sys.executable, "-c", "print('oi')"]), "oi")

    def test_codigo_de_saida_diferente_de_zero_devolve_none(self):
        self.assertIsNone(run_text([sys.executable, "-c", "import sys; sys.exit(3)"]))

    def test_estouro_de_tempo_devolve_none(self):
        self.assertIsNone(
            run_text([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.3)
        )


class RunStatusTest(unittest.TestCase):
    def test_devolve_codigo_e_saida_aparada(self):
        self.assertEqual(run_status([sys.executable, "-c", "print('oi')"]), (0, "oi"))

    def test_codigo_diferente_de_zero_nao_e_falha_de_execucao(self):
        self.assertEqual(run_status([sys.executable, "-c", "import sys; sys.exit(3)"]), (3, ""))

    def test_comando_inexistente_e_estouro_de_tempo_devolvem_none(self):
        self.assertIsNone(run_status(["comando-que-nao-existe-ryx"]))
        self.assertIsNone(run_status([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.3))


if __name__ == "__main__":
    unittest.main()
