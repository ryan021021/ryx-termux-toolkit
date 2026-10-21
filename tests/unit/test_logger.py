import logging
import tempfile
import unittest
from pathlib import Path

from ryx.logger import REDACTED, get_logger, redact
from tests.helpers import IS_WINDOWS


class RedactTest(unittest.TestCase):
    def test_mascara_chave_valor(self):
        for text in ("password=abc123", "token: abc123", "API_KEY=abc123", "api-key = abc123"):
            with self.subTest(text=text):
                out = redact(text)
                self.assertNotIn("abc123", out)
                self.assertIn(REDACTED, out)

    def test_mascara_bearer_e_chaves_conhecidas(self):
        self.assertNotIn("abcdefgh12345", redact("Authorization: Bearer abcdefgh12345"))
        self.assertNotIn("sk-ABCDEFGHIJKLMNOPQRST", redact("usei sk-ABCDEFGHIJKLMNOPQRST aqui"))
        self.assertNotIn("ghp_" + "a" * 24, redact("ghp_" + "a" * 24))

    def test_texto_comum_passa_intacto(self):
        text = "backup criado em /data/x com 3 arquivos"
        self.assertEqual(redact(text), text)

    def test_mantem_o_nome_da_chave_para_o_leitor_entender(self):
        self.assertEqual(redact("password=xyz"), f"password={REDACTED}")

    def test_mascara_json_e_valores_entre_aspas_com_espaco(self):
        cases = {
            '{"password": "hunter2"}': "hunter2",
            '{"user": "ana", "token":"abc123xyz", "n": 1}': "abc123xyz",
            'password="meu segredo grande"': "segredo",
            "token='a b c d'": "b c d",
            'login com api_key = "k e y 99" ok': "k e y 99",
        }
        for text, secret in cases.items():
            with self.subTest(text=text):
                out = redact(text)
                self.assertNotIn(secret, out)
                self.assertIn(REDACTED, out)

    def test_json_continua_legivel_depois_da_mascara(self):
        out = redact('{"user": "ana", "password": "hunter2", "n": 1}')
        self.assertIn('"user": "ana"', out)
        self.assertIn('"n": 1', out)

    def test_mascara_opcao_de_linha_de_comando(self):
        cases = {
            "curl --token abc123xyz https://x": "abc123xyz",
            "cmd --password s3nha!! --verbose": "s3nha!!",
            "cmd --api-key=ABCD1234 --x": "ABCD1234",
            "cmd --client-secret 'a b' fim": "a b",
        }
        for text, secret in cases.items():
            with self.subTest(text=text):
                self.assertNotIn(secret, redact(text))

    def test_opcao_sem_valor_nao_engole_a_proxima_opcao(self):
        self.assertEqual(redact("cmd --token --verbose"), "cmd --token --verbose")

    def test_mascara_chaves_com_prefixo_e_sublinhado(self):
        for name in ("AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN", "MY_API_KEY", "db_password", "X-Auth-Token"):
            with self.subTest(name=name):
                out = redact(f"{name}=valor-secreto-123")
                self.assertNotIn("valor-secreto-123", out)
                self.assertIn(name, out)

    def test_mascara_senha_dentro_de_url(self):
        out = redact("clonando https://ana:senha-forte@exemplo.org/repo.git agora")
        self.assertNotIn("senha-forte", out)
        self.assertIn("https://ana:", out)
        self.assertIn("@exemplo.org/repo.git", out)

    def test_url_sem_senha_passa_intacta(self):
        text = "baixando https://exemplo.org:8080/a/b@c e git@exemplo.org:ryx.git"
        self.assertEqual(redact(text), text)

    def test_mascara_chaves_de_provedores_conhecidos(self):
        for secret in ("AKIAABCDEFGHIJKLMNOP", "gho_" + "b" * 25, "xoxb-" + "1" * 12 + "-abcdefghij"):
            with self.subTest(secret=secret):
                self.assertNotIn(secret, redact(f"usei {secret} aqui"))


class LoggerTest(unittest.TestCase):
    def test_arquivo_de_log_nao_leva_segredo(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "sub" / "ryx.log"
            logger = get_logger("info", log)
            logger.info("login com password=segredo123")
            for handler in logger.handlers:
                handler.flush()
            text = log.read_text(encoding="utf-8")
            self.assertIn("login com", text)
            self.assertNotIn("segredo123", text)
            for handler in list(logger.handlers):
                handler.close()
                logger.removeHandler(handler)

    def test_recriar_o_logger_fecha_os_handlers_antigos(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = get_logger("info", Path(tmp) / "a.log")
            old_file_handler = first.handlers[-1]
            self.assertIsNotNone(old_file_handler.stream)
            second = get_logger("info")
            self.assertIsNotNone(second)
            self.assertIsNone(old_file_handler.stream)
            self.assertNotIn(old_file_handler, second.handlers)

    @unittest.skipIf(IS_WINDOWS, "permissão POSIX")
    def test_arquivo_de_log_fica_com_modo_0600(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "ryx.log"
            logger = get_logger("info", log)
            logger.info("oi")
            self.assertEqual(log.stat().st_mode & 0o777, 0o600)
            get_logger("info")

    @unittest.skipIf(IS_WINDOWS, "permissão POSIX")
    def test_log_que_ja_existia_aberto_demais_e_fechado(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "ryx.log"
            log.write_text("antigo")
            log.chmod(0o644)
            get_logger("info", log)
            self.assertEqual(log.stat().st_mode & 0o777, 0o600)
            get_logger("info")

    def test_log_em_lugar_impossivel_nao_derruba_o_programa(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "arquivo"
            blocker.write_text("x")
            logger = get_logger("info", blocker / "ryx.log")
            self.assertEqual(len(logger.handlers), 1)
            logger.info("segue só na tela")

    def test_nivel_e_aplicado(self):
        self.assertEqual(get_logger("warning").level, logging.WARNING)
        self.assertEqual(get_logger("desconhecido").level, logging.INFO)


if __name__ == "__main__":
    unittest.main()
