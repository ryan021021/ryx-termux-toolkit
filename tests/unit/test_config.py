import tempfile
import tomllib
import unittest
from pathlib import Path

from ryx.config import (
    BUILTIN_DEFAULTS,
    ConfigError,
    load_config,
    load_modules_flags,
    validate,
)
from ryx.registry import MODULE_NAMES
from tests.helpers import REPO, write

NL = bytes([10])


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def load(self, text: str):
        return load_config([write(self.root / "c.toml", text)])

    def test_sem_camadas_vale_o_padrao(self):
        self.assertEqual(load_config([]).values, BUILTIN_DEFAULTS)

    def test_camada_do_usuario_muda_so_a_chave_dela(self):
        config = self.load("[server]\nssh_port = 2222\n")
        self.assertEqual(config.get("server", "ssh_port"), 2222)
        self.assertEqual(config.get("server", "services"), ["sshd"])
        self.assertEqual(config.get("backup", "keep"), 10)

    def test_arquivo_inexistente_e_ignorado(self):
        self.assertEqual(load_config([self.root / "nada.toml"]).values, BUILTIN_DEFAULTS)

    def test_secao_e_chave_desconhecidas_sao_recusadas(self):
        with self.assertRaisesRegex(ConfigError, r"chave desconhecida: server\.porta"):
            self.load("[server]\nporta = 1\n")
        with self.assertRaisesRegex(ConfigError, r"seção desconhecida: \[extra\]"):
            self.load("[extra]\na = 1\n")

    def test_tipos_errados_sao_recusados(self):
        with self.assertRaisesRegex(ConfigError, "server.ssh_port: precisa ser inteiro"):
            self.load('[server]\nssh_port = "22"\n')
        with self.assertRaisesRegex(ConfigError, "server.ssh_port: precisa ser inteiro"):
            self.load("[server]\nssh_port = true\n")
        with self.assertRaisesRegex(ConfigError, "lista de textos"):
            self.load("[packages]\nrecommended = [1, 2]\n")
        with self.assertRaisesRegex(ConfigError, "shell.theme: precisa ser texto"):
            self.load("[shell]\ntheme = 3\n")

    def test_faixas_sao_conferidas(self):
        for text in (
            "[server]\nssh_port = 0\n",
            "[server]\nssh_port = 70000\n",
            "[backup]\nkeep = 0\n",
            "[backup]\nkeep = 1001\n",
            '[core]\nlog_level = "loud"\n',
        ):
            with self.subTest(text=text), self.assertRaises(ConfigError):
                self.load(text)
        self.assertEqual(self.load("[server]\nssh_port = 65535\n").get("server", "ssh_port"), 65535)
        self.assertEqual(self.load("[backup]\nkeep = 1\n").get("backup", "keep"), 1)

    def test_toml_quebrado_cita_o_arquivo(self):
        path = write(self.root / "ruim.toml", "[server\n")
        with self.assertRaisesRegex(ConfigError, "ruim.toml: TOML inválido"):
            load_config([path])

    def test_toml_ilegivel_vira_config_error_e_nao_traceback(self):
        cases = {
            "bytes que nao sao utf-8": b"[core]" + NL + b"log_level = " + bytes([0x80, 0x81]) + NL,
            "aninhamento absurdo": b"a = " + b"[" * 200_000,
            "byte nulo": b"a" + bytes([0]) + b" = 1" + NL,
        }
        for label, raw in cases.items():
            with self.subTest(label=label):
                path = self.root / "ruim.toml"
                path.write_bytes(raw)
                with self.assertRaisesRegex(ConfigError, "ruim.toml: TOML inválido"):
                    load_config([path])

    def test_validate_lista_todos_os_problemas(self):
        problems = validate({"core": {"x": 1}, "zzz": {}, "backup": {"keep": "a"}})
        self.assertEqual(len(problems), 3)

    def test_default_toml_do_repositorio_bate_com_o_padrao_embutido(self):
        with (REPO / "config" / "default.toml").open("rb") as handle:
            self.assertEqual(tomllib.load(handle), BUILTIN_DEFAULTS)


class ModulesFlagsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_sem_arquivo_tudo_ligado(self):
        self.assertEqual(load_modules_flags(None, ["a", "b"]), {"a": True, "b": True})

    def test_arquivo_desliga_modulo(self):
        path = write(self.root / "m.toml", "[modules]\nb = false\n")
        self.assertEqual(load_modules_flags(path, ["a", "b"]), {"a": True, "b": False})

    def test_modulo_desconhecido_e_valor_nao_booleano_sao_recusados(self):
        with self.assertRaisesRegex(ConfigError, "módulo desconhecido 'c'"):
            load_modules_flags(write(self.root / "x.toml", "[modules]\nc = true\n"), ["a"])
        with self.assertRaisesRegex(ConfigError, "precisa ser true ou false"):
            load_modules_flags(write(self.root / "y.toml", '[modules]\na = "sim"\n'), ["a"])

    def test_modules_que_nao_e_tabela_e_recusado(self):
        for text in ("modules = 3", 'modules = ["a"]', 'modules = "sim"'):
            with self.subTest(text=text), self.assertRaisesRegex(ConfigError, "modules precisa ser uma tabela"):
                load_modules_flags(write(self.root / "z.toml", text + "\n"), ["a"])

    def test_modules_toml_ilegivel_vira_config_error(self):
        path = self.root / "w.toml"
        path.write_bytes(bytes([0xFF, 0xFE, 0x80]))
        with self.assertRaisesRegex(ConfigError, "w.toml: TOML inválido"):
            load_modules_flags(path, ["a"])

    def test_modules_toml_do_repositorio_lista_exatamente_os_modulos(self):
        with (REPO / "config" / "modules.toml").open("rb") as handle:
            declared = tomllib.load(handle)["modules"]
        self.assertEqual(sorted(declared), sorted(MODULE_NAMES))


if __name__ == "__main__":
    unittest.main()
