import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from ryx import __version__
from ryx.modules import FAIL, OK, WARN, worst
from ryx.modules import diagnostics
from tests.helpers import FIXTURES, make_ctx, write

MB = 1024 * 1024


def which_all(command):
    return f"/bin/{command}"


def disk(free_mb):
    return lambda _path: SimpleNamespace(free=free_mb * MB)


def by_name(checks):
    return {c.name: c for c in checks}


class RunChecksTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ctx, _ = make_ctx(self.root, termux=True)

    def tearDown(self):
        self._tmp.cleanup()

    def checks(self, **kwargs):
        defaults = {"which": which_all, "disk_usage": disk(5000), "meminfo": FIXTURES / "meminfo.txt"}
        return by_name(diagnostics.run_checks(self.ctx, **{**defaults, **kwargs}))

    def test_ambiente_saudavel_tudo_ok(self):
        checks = self.checks()
        self.assertEqual(worst(list(checks.values())), OK)
        self.assertIn("Termux", checks["ambiente"].detail)

    def test_python_antigo_e_falha(self):
        self.assertEqual(self.checks(version_info=(3, 10))["python"].status, FAIL)
        self.assertEqual(self.checks(version_info=(3, 11))["python"].status, OK)

    def test_disco_nos_tres_niveis(self):
        self.assertEqual(self.checks(disk_usage=disk(50))["disco"].status, FAIL)
        self.assertEqual(self.checks(disk_usage=disk(300))["disco"].status, WARN)
        self.assertEqual(self.checks(disk_usage=disk(2000))["disco"].status, OK)

    def test_disco_que_nao_da_para_medir_vira_aviso(self):
        def boom(_path):
            raise OSError(5, "erro de E/S")

        self.assertEqual(self.checks(disk_usage=boom)["disco"].status, WARN)

    def test_memoria_baixa_e_ausente(self):
        low = write(self.root / "meminfo", "MemAvailable:  102400 kB\n")
        self.assertEqual(self.checks(meminfo=low)["memória"].status, WARN)
        self.assertEqual(self.checks(meminfo=self.root / "nao-existe")["memória"].status, WARN)
        self.assertIn("1205", self.checks()["memória"].detail)

    def test_comando_ausente_e_aviso_com_dica(self):
        check = self.checks(which=lambda c: None if c == "git" else f"/bin/{c}")["comando git"]
        self.assertEqual(check.status, WARN)
        self.assertIn("pkg install", check.fix)

    def test_fora_do_termux_e_aviso(self):
        ctx, _ = make_ctx(self.root / "outro", termux=False)
        checks = by_name(diagnostics.run_checks(ctx, which=which_all, disk_usage=disk(5000)))
        self.assertEqual(checks["ambiente"].status, WARN)

    def test_config_invalida_e_estado_corrompido_sao_falhas(self):
        self.ctx.config_error = "config.toml: chave desconhecida"
        self.assertEqual(self.checks()["config"].status, FAIL)
        write(self.ctx.paths.state_file, "{quebrado")
        self.assertEqual(self.checks()["estado"].status, FAIL)


class MemInfoTest(unittest.TestCase):
    def test_le_o_valor_em_mb(self):
        self.assertEqual(diagnostics.read_mem_available_mb(FIXTURES / "meminfo.txt"), 1205)

    def test_lixo_devolve_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            junk = write(Path(tmp) / "m", "MemAvailable: abc kB\n")
            self.assertIsNone(diagnostics.read_mem_available_mb(junk))


class CommandsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ctx, self.lines = make_ctx(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def test_doctor_json_e_valido(self):
        code = diagnostics.run(Namespace(handler=diagnostics._doctor, json=True), self.ctx)
        payload = json.loads("\n".join(self.lines))
        self.assertIn(payload["status"], {OK, WARN, FAIL})
        self.assertIn("python", {c["name"] for c in payload["checks"]})
        self.assertEqual(code, 1 if payload["status"] == FAIL else 0)

    def test_doctor_sai_com_1_quando_ha_falha(self):
        self.ctx.config_error = "config.toml: ruim"
        code = diagnostics.run(Namespace(handler=diagnostics._doctor, json=False), self.ctx)
        self.assertEqual(code, 1)
        self.assertTrue(any("[FALHA]" in line for line in self.lines))
        self.assertEqual(self.lines[-1], "resultado: fail")

    def test_info_mostra_versao_e_pastas(self):
        self.assertEqual(diagnostics.run(Namespace(handler=diagnostics._info), self.ctx), 0)
        text = "\n".join(self.lines)
        self.assertIn(f"ryx {__version__}", text)
        self.assertIn("data_dir:", text)

    def test_doctor_nao_cria_nenhum_arquivo(self):
        diagnostics.run(Namespace(handler=diagnostics._doctor, json=False), self.ctx)
        self.assertFalse(self.ctx.paths.state_file.exists())
        self.assertFalse(self.ctx.paths.backup_dir.exists())


if __name__ == "__main__":
    unittest.main()
