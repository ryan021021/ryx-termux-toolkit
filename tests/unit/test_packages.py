import subprocess
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ryx.modules import UserError
from ryx.modules import packages
from tests.helpers import make_ctx


def args(action="install", apply=False, yes=False, add=None):
    return Namespace(action=action, apply=apply, yes=yes, add=add or [])


class ValidateNamesTest(unittest.TestCase):
    def test_aceita_nomes_reais_de_pacote(self):
        names = ["git", "libc++", "python3.11", "openssh", "x-y_z".replace("_", "-")]
        self.assertEqual(packages.validate_names(names), names)

    def test_recusa_injecao_e_nomes_estranhos(self):
        for bad in ("", "a;rm -rf /", "-rf", "Upper", "a b", "$(x)", "a`b`", "a|b", "../x", "x" * 65):
            with self.subTest(bad=bad), self.assertRaises(UserError):
                packages.validate_names(["git", bad])


class PackageStatusTest(unittest.TestCase):
    def test_sem_dpkg_query_nao_ha_como_saber(self):
        status = packages.package_status(["git", "curl"], which=lambda _c: None)
        self.assertEqual(status, {"git": None, "curl": None})

    def test_instalado_ausente_removido_e_sem_resposta_sao_coisas_diferentes(self):
        answers = {
            "git": (0, "install ok installed"),
            "curl": (1, ""),
            "jq": (0, "deinstall ok config-files"),
            "nano": None,
            "vim": (2, ""),
        }
        status = packages.package_status(
            list(answers), which=lambda _c: "/bin/dpkg-query", runner=lambda cmd: answers[cmd[-1]]
        )
        self.assertEqual(status, {"git": True, "curl": False, "jq": False, "nano": None, "vim": None})

    def test_runner_recebe_lista_sem_shell(self):
        seen = []
        packages.package_status(["git"], which=lambda _c: "/x", runner=lambda cmd: seen.append(cmd) or (0, ""))
        self.assertEqual(seen, [["dpkg-query", "-W", "-f=${Status}", "git"]])


class CommandTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ctx, self.lines = make_ctx(self.root, termux=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_check_mostra_falta_e_instalado(self):
        status = {"git": True, "curl": False}
        with mock.patch.object(packages, "package_status", return_value=status):
            self.assertEqual(packages.run(args("check"), self.ctx), 0)
        self.assertIn("git: instalado", self.lines)
        self.assertIn("curl: FALTA", self.lines)

    def test_check_mostra_desconhecido_quando_nao_conseguiu_consultar(self):
        status = {"git": True, "curl": None}
        with mock.patch.object(packages, "package_status", return_value=status):
            packages.run(args("check"), self.ctx)
        self.assertIn("curl: desconhecido", self.lines)
        self.assertNotIn("curl: FALTA", self.lines)

    def test_check_fora_do_termux_avisa(self):
        with mock.patch.object(packages, "package_status", return_value={"git": None}):
            packages.run(args("check"), self.ctx)
        self.assertTrue(any("dpkg-query" in line for line in self.lines))

    def test_extra_invalido_e_recusado_antes_de_qualquer_coisa(self):
        with self.assertRaises(UserError):
            packages.run(args("check", add=["ok", "a;b"]), self.ctx)

    def test_nada_a_instalar(self):
        with mock.patch.object(packages, "package_status", return_value={"git": True}):
            self.assertEqual(packages.run(args(), self.ctx), 0)
        self.assertEqual(self.lines, ["nada a instalar"])

    def test_install_com_algum_desconhecido_e_erro_claro_e_nunca_nada_a_instalar(self):
        for status in ({"git": None}, {"git": True, "curl": None}, {"git": False, "curl": None}):
            for apply in (False, True):
                self.lines.clear()
                with self.subTest(status=status, apply=apply):
                    with (
                        mock.patch.object(packages, "package_status", return_value=status),
                        mock.patch.object(packages.subprocess, "run", side_effect=AssertionError("não devia rodar")),
                        self.assertRaisesRegex(UserError, "não consegui consultar"),
                    ):
                        packages.run(args(apply=apply), self.ctx)
                    self.assertNotIn("nada a instalar", self.lines)

    def test_simulacao_nao_roda_nada(self):
        with (
            mock.patch.object(packages, "package_status", return_value={"git": False}),
            mock.patch.object(packages.subprocess, "run", side_effect=AssertionError("não devia rodar")),
        ):
            self.assertEqual(packages.run(args(), self.ctx), 0)
        self.assertIn("[simulação] pkg install -y git", self.lines[0])

    def test_apply_fora_do_termux_e_erro(self):
        ctx, _ = make_ctx(self.root / "outro", termux=False)
        with (
            mock.patch.object(packages, "package_status", return_value={"git": False}),
            self.assertRaisesRegex(UserError, "só funciona no Termux"),
        ):
            packages.run(args(apply=True), ctx)

    def test_apply_roda_pkg_sem_shell_e_devolve_o_codigo(self):
        fake = SimpleNamespace(returncode=7)
        with (
            mock.patch.object(packages, "package_status", return_value={"git": False, "curl": True}),
            mock.patch.object(packages.shutil, "which", return_value="/bin/pkg"),
            mock.patch.object(packages.subprocess, "run", return_value=fake) as run,
        ):
            self.assertEqual(packages.run(args(apply=True), self.ctx), 7)
        command = run.call_args.args[0]
        self.assertEqual(command, ["pkg", "install", "-y", "git"])
        self.assertNotIn("shell", run.call_args.kwargs)
        self.assertIn("timeout", run.call_args.kwargs)

    def test_estouro_de_tempo_vira_erro_claro(self):
        with (
            mock.patch.object(packages, "package_status", return_value={"git": False}),
            mock.patch.object(packages.shutil, "which", return_value="/bin/pkg"),
            mock.patch.object(
                packages.subprocess, "run", side_effect=subprocess.TimeoutExpired("pkg", 1)
            ),
            self.assertRaisesRegex(UserError, "interrompido"),
        ):
            packages.run(args(apply=True), self.ctx)


if __name__ == "__main__":
    unittest.main()
