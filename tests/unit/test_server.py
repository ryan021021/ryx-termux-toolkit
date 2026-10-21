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
        checks = by_name(
            server.run_checks(
                ctx,
                connect=connect_ok(FakeConn()),
                which=lambda c: f"/bin/{c}",
                runner=lambda _c: "run: sshd: (pid 9) 1s",
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


if __name__ == "__main__":
    unittest.main()
