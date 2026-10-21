import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from ryx.modules import OK, WARN, UserError
from ryx.modules import ai
from tests.helpers import make_ctx

SECRET = "sk-ant-SEGREDO-que-nao-pode-vazar-123456"


def found(path="/bin/claude"):
    return lambda _name: path


class CheckProviderTest(unittest.TestCase):
    def test_nao_instalado_e_aviso(self):
        check = ai.check_provider("claude", {}, which=lambda _n: None)
        self.assertEqual(check.status, WARN)
        self.assertIn("não instalado", check.detail)

    def test_instalado_com_chave_nunca_imprime_o_valor(self):
        check = ai.check_provider(
            "claude", {"ANTHROPIC_API_KEY": SECRET}, which=found(), runner=lambda _c: "1.2.3 (Claude)"
        )
        self.assertEqual(check.status, OK)
        self.assertIn("chave no ambiente: sim", check.detail)
        self.assertNotIn(SECRET, repr(check))

    def test_sem_chave(self):
        check = ai.check_provider("gemini", {}, which=found("/bin/gemini"), runner=lambda _c: "0.1")
        self.assertIn("chave no ambiente: não", check.detail)

    def test_chave_vazia_nao_conta(self):
        check = ai.check_provider("codex", {"OPENAI_API_KEY": ""}, which=found(), runner=lambda _c: "1")
        self.assertIn("chave no ambiente: não", check.detail)

    def test_qualquer_das_variaveis_do_gemini_serve(self):
        check = ai.check_provider("gemini", {"GOOGLE_API_KEY": "x"}, which=found(), runner=lambda _c: "1")
        self.assertIn("chave no ambiente: sim", check.detail)

    def test_provider_desconhecido_e_sem_chave_conhecida(self):
        check = ai.check_provider("meu-cli", {}, which=found(), runner=lambda _c: "9")
        self.assertIn("sem chave conhecida", check.detail)

    def test_versao_so_a_primeira_linha_e_limitada(self):
        long_line = "v" * 500 + "\nsegunda linha"
        check = ai.check_provider("claude", {}, which=found(), runner=lambda _c: long_line)
        self.assertNotIn("segunda", check.detail)
        self.assertLess(len(check.detail), ai.VERSION_MAX + 60)

    def test_versao_indisponivel(self):
        check = ai.check_provider("claude", {}, which=found(), runner=lambda _c: None)
        self.assertIn("versão desconhecida", check.detail)

    def test_nome_com_injecao_e_recusado(self):
        for name in ("a;b", "A", "", "../x", "a b", "x" * 33):
            with self.subTest(name=name), self.assertRaises(UserError):
                ai.check_provider(name, {}, which=found(), runner=lambda _c: "1")

    def test_runner_recebe_lista_com_o_caminho_achado(self):
        seen = []
        ai.check_provider("claude", {}, which=found("/x/claude"), runner=lambda cmd: seen.append(cmd))
        self.assertEqual(seen, [["/x/claude", "--version"]])


class RunTest(unittest.TestCase):
    def test_run_lista_os_providers_da_config_e_nao_vaza_a_chave(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, lines = make_ctx(Path(tmp), overrides={"ai": {"providers": ["ryx-inexistente-xyz"]}})
            code = ai.run(Namespace(action="check"), ctx, env={"ANTHROPIC_API_KEY": SECRET})
        self.assertEqual(code, 0)
        self.assertTrue(any("ryx-inexistente-xyz" in line for line in lines))
        self.assertNotIn(SECRET, "\n".join(lines))


if __name__ == "__main__":
    unittest.main()
