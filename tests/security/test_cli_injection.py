"""Argumentos e ambiente hostis pela CLI real: nada de injeção, nada de vazamento de chave."""

import json
import unittest

from tests.helpers import FIXTURES, write
from tests.integration.test_cli import CliTestCase

SECRET = "sk-ant-SEGREDO-que-jamais-deve-aparecer-0123456789"
EVIL = ("x;rm -rf /", "$(id)", "`id`", "a|b", "../../etc/passwd", "a b", "-rf")


class InjectionTest(CliTestCase):
    def test_pacote_extra_com_injecao_e_recusado(self):
        for bad in EVIL:
            with self.subTest(bad=bad):
                code, _, err = self.ryx("packages", "check", "--add", bad)
                self.assertIn(code, (1, 2))
                self.assertNotIn("Traceback", err)
        code, _, err = self.ryx("packages", "check", "--add", "x;rm -rf /")
        self.assertEqual(code, 1)
        self.assertIn("nome de pacote inválido", err)

    def test_tema_com_caminho_nao_le_arquivo_de_fora(self):
        rc = self.home / ".bashrc"
        rc.write_bytes((FIXTURES / "bashrc-sample").read_bytes())
        before = rc.read_bytes()
        for bad in ("../../etc/passwd", "..\\x", "A", "a;b", "x" * 40):
            with self.subTest(bad=bad):
                code, _, err = self.ryx("shell", "install", "--apply", "--theme", bad)
                self.assertEqual(code, 1)
                self.assertNotIn("Traceback", err)
                self.assertEqual(rc.read_bytes(), before)

    def test_rotina_so_executa_o_que_esta_na_lista_fechada(self):
        for bad in EVIL:
            with self.subTest(bad=bad):
                code, _, err = self.ryx("automation", "run", bad, "--apply", "--yes")
                self.assertIn(code, (1, 2))
                self.assertNotIn("Traceback", err)

    def test_config_nao_consegue_trocar_comando(self):
        write(self.ryx_home / "config" / "config.toml", '[packages]\nrecommended = ["git;reboot"]\n')
        code, _, err = self.ryx("packages", "check")
        self.assertEqual(code, 1)
        self.assertNotIn("Traceback", err)

    def test_restore_nao_escreve_fora_do_destino_pedido(self):
        write(self.ryx_home / "config" / "config.toml", "[backup]\nkeep = 3\n")
        self.ryx("backup", "create", "--apply")
        (archive,) = (self.ryx_home / "backups").glob("*.tar.gz")
        dest = self.root / "so-aqui"
        self.assertEqual(self.ryx("backup", "restore", str(archive), "--to", str(dest), "--apply")[0], 0)
        stray = [
            p
            for p in self.root.rglob("config.toml")
            if dest not in p.parents and self.ryx_home not in p.parents
        ]
        self.assertEqual(stray, [])


class KeyLeakTest(CliTestCase):
    def test_chave_do_ambiente_nunca_aparece_na_saida_nem_no_log(self):
        self.env.update({"ANTHROPIC_API_KEY": SECRET, "OPENAI_API_KEY": SECRET, "RYX_LOG_FILE": "1"})
        outputs = []
        for argv in (("ai", "check"), ("doctor",), ("doctor", "--json"), ("info",), ("modules",)):
            code, out, err = self.ryx(*argv)
            outputs.append(out + err)
            self.assertIn(code, (0, 1))
        log = self.ryx_home / "state" / "ryx.log"
        if log.exists():
            outputs.append(log.read_text(encoding="utf-8"))
        self.assertNotIn(SECRET, "\n".join(outputs))

    def test_doctor_json_continua_json_valido_com_ambiente_hostil(self):
        self.env["ANTHROPIC_API_KEY"] = SECRET
        _, out, _ = self.ryx("doctor", "--json")
        json.loads(out)


if __name__ == "__main__":
    unittest.main()
