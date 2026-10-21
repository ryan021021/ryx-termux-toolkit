import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock

from ryx.modules import FAIL, OK, WARN, Check, UserError
from ryx.modules import server
from tests.helpers import make_ctx


class FakeConn:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def connect_ok(conn):
    return lambda *_a, **_k: conn


def connect_refused(*_a, **_k):
    raise ConnectionRefusedError("recusado")


GOOD_SSHD = {"passwordauthentication": "no", "listenaddress": "127.0.0.1"}


def by_name(checks):
    return {c.name: c for c in checks}


class PortOpenTest(unittest.TestCase):
    def test_aberta_fecha_a_conexao(self):
        conn = FakeConn()
        self.assertTrue(server.port_open(8022, connect_ok(conn)))
        self.assertTrue(conn.closed)

    def test_recusada_e_falsa(self):
        self.assertFalse(server.port_open(8022, connect_refused))


class ServiceCheckTest(unittest.TestCase):
    def test_nome_invalido_e_recusado(self):
        for name in ("a;b", "A", "", "x" * 33, "../sshd", "a b"):
            with self.subTest(name=name), self.assertRaises(UserError):
                server.service_check(name, None, which=lambda _c: "/bin/sv", runner=lambda _c: "run: x")

    def test_sem_sv_e_aviso(self):
        check = server.service_check("sshd", None, which=lambda _c: None)
        self.assertEqual(check.status, WARN)
        self.assertIn("termux-services", check.fix)

    def test_rodando_parado_e_nao_cadastrado(self):
        up = server.service_check("sshd", None, lambda _c: "/bin/sv", lambda _c: "run: sshd: (pid 1) 5s")
        down = server.service_check("sshd", None, lambda _c: "/bin/sv", lambda _c: "down: sshd: 3s")
        none = server.service_check("sshd", None, lambda _c: "/bin/sv", lambda _c: None)
        self.assertEqual((up.status, down.status, none.status), (OK, WARN, WARN))
        self.assertIn("sv up sshd", down.fix)
        self.assertIn("não cadastrado", none.detail)

    def test_runner_recebe_lista(self):
        seen = []
        server.service_check("sshd", None, lambda _c: "/bin/sv", lambda cmd: seen.append(cmd))
        self.assertEqual(seen, [["sv", "status", "sshd"]])

    def test_servico_cadastrado_mas_sem_resposta(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "var" / "service" / "sshd").mkdir(parents=True)
            check = server.service_check("sshd", Path(tmp), lambda _c: "/bin/sv", lambda _c: None)
        self.assertIn("não respondeu", check.detail)


class RunChecksTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_fora_do_termux_so_avisa(self):
        ctx, _ = make_ctx(self.root, termux=False)
        checks = server.run_checks(ctx)
        self.assertEqual([c.status for c in checks], [WARN])

    def test_termux_saudavel(self):
        ctx, _ = make_ctx(self.root, termux=True)
        (ctx.paths.home / ".ssh").mkdir(parents=True, exist_ok=True)
        (ctx.paths.home / ".ssh" / "authorized_keys").write_text("ssh-ed25519 AAAA um\n", encoding="utf-8")
        checks = by_name(
            server.run_checks(
                ctx,
                connect=connect_ok(FakeConn()),
                which=lambda c: f"/bin/{c}",
                runner=lambda _c: "run: sshd: (pid 9) 1s",
                sshd_settings=lambda: GOOD_SSHD,
            )
        )
        self.assertEqual({c.status for c in checks.values()}, {OK})
        self.assertIn("8022", checks["sshd"].detail)

    def test_sshd_fora_do_ar_e_falha_e_wake_lock_ausente_e_aviso(self):
        ctx, _ = make_ctx(self.root, termux=True)
        checks = by_name(
            server.run_checks(
                ctx,
                connect=connect_refused,
                which=lambda c: None,
                runner=lambda _c: None,
            )
        )
        self.assertEqual(checks["sshd"].status, FAIL)
        self.assertEqual(checks["wake-lock"].status, WARN)

    def test_servico_malicioso_na_config_e_recusado(self):
        ctx, _ = make_ctx(self.root, termux=True, overrides={"server": {"services": ["sshd;reboot"]}})
        with self.assertRaises(UserError):
            server.run_checks(ctx, connect=connect_ok(FakeConn()), which=lambda c: "/b", runner=lambda _c: "run:")


class RunTest(unittest.TestCase):
    def test_codigo_de_saida_segue_a_pior_checagem(self):
        with tempfile.TemporaryDirectory() as tmp:
            ctx, lines = make_ctx(Path(tmp), termux=True)
            with mock.patch.object(server, "run_checks", return_value=[Check("sshd", FAIL, "x", "y")]):
                self.assertEqual(server.run(Namespace(action="status"), ctx), 1)
            with mock.patch.object(server, "run_checks", return_value=[Check("sshd", WARN, "x")]):
                self.assertEqual(server.run(Namespace(action="status"), ctx), 0)
        self.assertTrue(any("[FALHA]" in line for line in lines))




SSHD_T_SENHA = """port 8022
listenaddress 0.0.0.0:8022
passwordauthentication yes
pubkeyauthentication yes
"""


class SshdSettingsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.prefix = self.root / "usr"
        (self.prefix / "etc" / "ssh" / "sshd_config.d").mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_sshd_t_e_a_fonte_preferida(self):
        got = server.read_sshd_settings(self.prefix, lambda cmd: SSHD_T_SENHA if cmd == ["sshd", "-T"] else None)
        self.assertEqual(got["passwordauthentication"], "yes")
        self.assertEqual(got["listenaddress"], "0.0.0.0:8022")

    def test_sem_sshd_t_le_o_arquivo_e_o_dropin_vence_o_principal(self):
        ssh = self.prefix / "etc" / "ssh"
        (ssh / "sshd_config").write_text("Include sshd_config.d/*.conf\nPasswordAuthentication yes\n", encoding="utf-8")
        (ssh / "sshd_config.d" / "10-servidor.conf").write_text("PasswordAuthentication no\n", encoding="utf-8")
        got = server.read_sshd_settings(self.prefix, lambda _c: None)
        self.assertEqual(got["passwordauthentication"], "no", "a primeira ocorrência vale (regra do sshd)")

    def test_match_nao_vira_global(self):
        (self.prefix / "etc" / "ssh" / "sshd_config").write_text("Match User x\nPasswordAuthentication no\n", encoding="utf-8")
        got = server.read_sshd_settings(self.prefix, lambda _c: None)
        self.assertIsNone(got, "diretiva dentro de Match não vale como global")

    def test_include_absoluto_e_varios_padroes_nao_quebram(self):
        ssh = self.prefix / "etc" / "ssh"
        extra = self.root / "extra.conf"
        extra.write_text("PasswordAuthentication no\n", encoding="utf-8")
        (ssh / "sshd_config").write_text(f"Include {extra} sshd_config.d/*.conf\n", encoding="utf-8")
        got = server.read_sshd_settings(self.prefix, lambda _c: None)
        self.assertEqual(got["passwordauthentication"], "no")

    def test_varios_listenaddress_avisam_se_algum_for_amplo(self):
        saida = "passwordauthentication no\nlistenaddress 127.0.0.1:8022\nlistenaddress 0.0.0.0:8022\n"
        got = server.read_sshd_settings(self.prefix, lambda _c: saida)
        self.assertTrue(server._listens_everywhere(got["listenaddress"]))
        self.assertTrue(server._listens_everywhere("[::]:8022"))
        self.assertFalse(server._listens_everywhere("127.0.0.1:8022"))

    def test_so_o_arquivo_com_senha_ligada(self):
        (self.prefix / "etc" / "ssh" / "sshd_config").write_text("PasswordAuthentication yes\n# PasswordAuthentication no\n", encoding="utf-8")
        got = server.read_sshd_settings(self.prefix, lambda _c: None)
        self.assertEqual(got["passwordauthentication"], "yes")

    def test_nada_legivel_devolve_none(self):
        self.assertIsNone(server.read_sshd_settings(self.prefix, lambda _c: None))
        self.assertIsNone(server.read_sshd_settings(None, lambda _c: None))
        self.assertIsNone(server.read_sshd_settings(self.prefix, lambda _c: "run: sshd: (pid 9) 1s"), "saída que não é config não conta")

    def test_leitura_nao_altera_nenhum_arquivo(self):
        f = self.prefix / "etc" / "ssh" / "sshd_config"
        f.write_text("PasswordAuthentication yes\n", encoding="utf-8")
        before = (f.read_bytes(), f.stat().st_mtime_ns)
        server.read_sshd_settings(self.prefix, lambda _c: None)
        self.assertEqual((f.read_bytes(), f.stat().st_mtime_ns), before)


class SshdConfigChecksTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        (self.home / ".ssh").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def keys(self, text):
        (self.home / ".ssh" / "authorized_keys").write_text(text, encoding="utf-8")

    def test_senha_ligada_gera_aviso_com_como_resolver(self):
        self.keys("ssh-ed25519 AAAA um\n")
        checks = by_name(server.sshd_config_checks({"passwordauthentication": "yes", "listenaddress": "127.0.0.1"}, self.home))
        self.assertEqual(checks["sshd senha"].status, WARN)
        self.assertIn("PasswordAuthentication no", checks["sshd senha"].fix)
        self.assertNotIn("AAAA", checks["sshd senha"].detail + checks["sshd chaves"].detail, "chave nunca vai para a tela")

    def test_senha_desligada_e_ok(self):
        self.keys("ssh-ed25519 AAAA um\n")
        checks = by_name(server.sshd_config_checks(GOOD_SSHD, self.home))
        self.assertEqual({c.status for c in checks.values()}, {OK})

    def test_senha_ausente_na_config_vale_como_ligada(self):
        self.keys("ssh-ed25519 AAAA um\n")
        checks = by_name(server.sshd_config_checks({"listenaddress": "127.0.0.1"}, self.home))
        self.assertEqual(checks["sshd senha"].status, WARN)

    def test_chaves_contadas_sem_comentario_e_ausencia_avisa(self):
        self.keys("# nota\nssh-ed25519 AAAA um\n\nssh-rsa BBBB dois\n")
        self.assertIn("2 chave(s)", by_name(server.sshd_config_checks(GOOD_SSHD, self.home))["sshd chaves"].detail)
        (self.home / ".ssh" / "authorized_keys").unlink()
        sem = by_name(server.sshd_config_checks(GOOD_SSHD, self.home))["sshd chaves"]
        self.assertEqual(sem.status, WARN)

    def test_escuta_em_todas_as_interfaces_avisa(self):
        self.keys("ssh-ed25519 AAAA um\n")
        for addr in ("0.0.0.0:8022", "[::]:8022", "0.0.0.0", None):
            cfg = {"passwordauthentication": "no"}
            if addr:
                cfg["listenaddress"] = addr
            with self.subTest(addr=addr):
                self.assertEqual(by_name(server.sshd_config_checks(cfg, self.home))["sshd escuta"].status, WARN)

    def test_config_ilegivel_e_nao_verificado_nunca_ok(self):
        checks = server.sshd_config_checks(None, self.home)
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].status, WARN)
        self.assertIn("NÃO VERIFICADO", checks[0].detail)

    def test_run_checks_inclui_o_sshd_sem_mudar_o_codigo_para_falha(self):
        ctx, _ = make_ctx(self.home, termux=True)
        (ctx.paths.home / ".ssh").mkdir(parents=True, exist_ok=True)
        checks = by_name(
            server.run_checks(
                ctx, connect=connect_ok(FakeConn()), which=lambda c: f"/bin/{c}",
                runner=lambda _c: "run: sshd: (pid 9) 1s",
                sshd_settings=lambda: {"passwordauthentication": "yes", "listenaddress": "0.0.0.0:8022"},
            )
        )
        self.assertEqual(checks["sshd senha"].status, WARN)
        self.assertEqual(checks["sshd"].status, OK)
        self.assertNotIn(FAIL, {c.status for c in checks.values()})


class SvdirTest(unittest.TestCase):
    def test_sem_svdir_o_sv_roda_com_o_svdir_do_prefixo(self):
        seen = []
        with mock.patch.dict("os.environ", {}, clear=False) as env:
            env.pop("SVDIR", None)
            server.service_check("sshd", Path("/p/usr"), lambda _c: "/bin/sv", lambda cmd: seen.append(cmd))
        self.assertEqual(seen[0][:2], ["env", f"SVDIR={Path('/p/usr') / 'var' / 'service'}"])
        self.assertEqual(seen[0][2:], ["sv", "status", "sshd"])

    def test_com_svdir_definido_nao_mexe_no_comando(self):
        seen = []
        with mock.patch.dict("os.environ", {"SVDIR": "/x"}):
            server.service_check("sshd", Path("/p/usr"), lambda _c: "/bin/sv", lambda cmd: seen.append(cmd))
        self.assertEqual(seen, [["sv", "status", "sshd"]])

    def test_sv_mudo_com_servico_cadastrado_nao_manda_sv_enable(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "var" / "service" / "sshd").mkdir(parents=True)
            check = server.service_check("sshd", Path(tmp), lambda _c: "/bin/sv", lambda _c: None)
        self.assertNotIn("sv-enable", check.fix)
        self.assertIn("SVDIR", check.fix)


if __name__ == "__main__":
    unittest.main()
