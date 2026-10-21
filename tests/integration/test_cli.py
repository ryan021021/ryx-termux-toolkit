"""CLI de ponta a ponta: processo real `python -m ryx`, HOME e RYX_HOME numa pasta temporária."""

import contextlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ryx import cli

from tests.helpers import FIXTURES, REPO, write

SRC = REPO / "src"
BLOCK_START = "# >>> ryx >>>"


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.ryx_home = self.root / "ryx"
        self.env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.home),
            "USERPROFILE": str(self.home),
            "RYX_HOME": str(self.ryx_home),
            "PYTHONPATH": str(SRC),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        for key in ("SYSTEMROOT", "TEMP", "TMP"):
            if key in os.environ:
                self.env[key] = os.environ[key]

    def tearDown(self):
        self._tmp.cleanup()

    def ryx(self, *argv):
        done = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "ryx", *argv],
            env=self.env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
        return done.returncode, done.stdout, done.stderr


class BasicsTest(CliTestCase):
    def test_version(self):
        code, out, _ = self.ryx("--version")
        self.assertEqual((code, out.strip()), (0, "ryx 0.1.0"))

    def test_modules_lista_os_seis(self):
        code, out, _ = self.ryx("modules")
        self.assertEqual(code, 0)
        for name in ("shell", "diagnostics", "packages", "server", "automation", "ai"):
            self.assertIn(f"{name} [experimental, ligado]", out)

    def test_uso_incorreto_sai_com_2(self):
        for argv in ((), ("comando-que-nao-existe",), ("shell",), ("backup", "restore")):
            with self.subTest(argv=argv):
                self.assertEqual(self.ryx(*argv)[0], 2)

    def test_doctor_texto_e_json(self):
        code, out, _ = self.ryx("doctor")
        self.assertEqual(code, 0, out)
        self.assertIn("resultado:", out)
        code, out, _ = self.ryx("doctor", "--json")
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertIn(payload["status"], {"ok", "warn"})

    def test_info(self):
        code, out, _ = self.ryx("info")
        self.assertEqual(code, 0)
        self.assertIn(str(self.ryx_home / "data"), out)

    def test_modulo_desligado_some_da_cli(self):
        write(self.ryx_home / "config" / "modules.toml", "[modules]\nai = false\n")
        self.assertIn("ai [experimental, desligado]", self.ryx("modules")[1])
        self.assertEqual(self.ryx("ai", "check")[0], 2)
        self.assertEqual(self.ryx("server", "status")[0], 0)


class ConfigErrorTest(CliTestCase):
    def test_config_com_chave_desconhecida_bloqueia_comandos_mas_nao_o_doctor(self):
        write(self.ryx_home / "config" / "config.toml", "[core]\nnao_existe = 1\n")
        code, _, err = self.ryx("backup", "list")
        self.assertEqual(code, 1)
        self.assertIn("erro:", err)
        code, out, _ = self.ryx("doctor")
        self.assertEqual(code, 1)
        self.assertIn("[FALHA] config", out)
        self.assertEqual(self.ryx("modules")[0], 0)
        self.assertEqual(self.ryx("info")[0], 0)

    def test_toml_quebrado_e_erro_claro_sem_traceback(self):
        write(self.ryx_home / "config" / "config.toml", "[core\n")
        code, _, err = self.ryx("backup", "list")
        self.assertEqual(code, 1)
        self.assertNotIn("Traceback", err)

    def test_estado_corrompido_e_erro_claro(self):
        write(self.ryx_home / "state" / "state.json", "{quebrado")
        code, out, _ = self.ryx("doctor")
        self.assertEqual(code, 1)
        self.assertIn("[FALHA] estado", out)


class ShellFlowTest(CliTestCase):
    def setUp(self):
        super().setUp()
        self.rc = self.home / ".bashrc"
        self.original = (FIXTURES / "bashrc-sample").read_bytes()
        self.rc.write_bytes(self.original)

    def test_simulacao_apply_idempotencia_e_remocao(self):
        code, out, _ = self.ryx("shell", "install")
        self.assertEqual(code, 0)
        self.assertIn("[simulação]", out)
        self.assertEqual(self.rc.read_bytes(), self.original)

        self.assertEqual(self.ryx("shell", "install", "--apply")[0], 0)
        installed = self.rc.read_bytes()
        self.assertIn(BLOCK_START.encode(), installed)

        code, out, _ = self.ryx("shell", "install", "--apply")
        self.assertIn("nada a fazer", out)
        self.assertEqual(self.rc.read_bytes(), installed)
        self.assertIn("em dia", self.ryx("shell", "status")[1])

        self.assertEqual(self.ryx("shell", "uninstall", "--apply")[0], 0)
        self.assertEqual(self.rc.read_bytes(), self.original)

    def test_tema_inexistente_nao_altera_o_rc(self):
        code, _, err = self.ryx("shell", "install", "--apply", "--theme", "nao-existe")
        self.assertEqual(code, 1)
        self.assertIn("erro:", err)
        self.assertEqual(self.rc.read_bytes(), self.original)

    def test_bash_le_o_rc_sem_erro_de_sintaxe(self):
        self.ryx("shell", "install", "--apply")
        bash = next((p for p in (Path("/bin/bash"), Path("/usr/bin/bash")) if p.exists()), None)
        if bash is None or os.name == "nt":
            self.skipTest("bash indisponível")
        done = subprocess.run(  # noqa: S603
            [str(bash), "-n", str(self.rc)], capture_output=True, text=True, check=False, timeout=30
        )
        self.assertEqual(done.returncode, 0, done.stderr)


class BackupFlowTest(CliTestCase):
    def archives(self):
        return sorted((self.ryx_home / "backups").glob("*.tar.gz"))

    def test_ida_e_volta(self):
        cfg = write(self.ryx_home / "config" / "config.toml", "[backup]\nkeep = 3\n")
        code, out, _ = self.ryx("backup", "create")
        self.assertEqual(code, 0)
        self.assertIn("[simulação]", out)
        self.assertEqual(self.archives(), [])

        self.assertEqual(self.ryx("backup", "create", "--apply")[0], 0)
        (archive,) = self.archives()
        self.assertIn(archive.name, self.ryx("backup", "list")[1])
        code, out, _ = self.ryx("backup", "verify", str(archive))
        self.assertEqual((code, "íntegro" in out), (0, True))

        dest = self.root / "restaurado"
        self.assertEqual(self.ryx("backup", "restore", str(archive), "--to", str(dest))[0], 0)
        self.assertFalse(dest.exists(), "sem --apply é só simulação")
        self.assertEqual(self.ryx("backup", "restore", str(archive), "--to", str(dest), "--apply")[0], 0)
        restored = list(dest.rglob("config.toml"))
        self.assertEqual(len(restored), 1)
        self.assertEqual(restored[0].read_bytes(), cfg.read_bytes())

    def test_backup_adulterado_falha_na_verificacao_e_na_restauracao(self):
        write(self.ryx_home / "config" / "config.toml", "[backup]\nkeep = 3\n")
        self.ryx("backup", "create", "--apply")
        (archive,) = self.archives()
        archive.write_bytes(archive.read_bytes() + b"lixo")
        self.assertEqual(self.ryx("backup", "verify", str(archive))[0], 1)
        dest = self.root / "out"
        code, _, err = self.ryx("backup", "restore", str(archive), "--to", str(dest), "--apply")
        self.assertEqual(code, 1)
        self.assertIn("erro:", err)
        self.assertFalse(dest.exists())

    def test_prune_exige_apply_e_yes_e_mantem_os_mais_novos(self):
        write(self.ryx_home / "config" / "config.toml", "[backup]\nkeep = 1\n")
        for _ in range(3):
            self.ryx("backup", "create", "--apply")
        self.assertEqual(len(self.archives()), 3)
        self.ryx("backup", "prune")
        self.ryx("backup", "prune", "--apply")
        self.assertEqual(len(self.archives()), 3)
        self.assertEqual(self.ryx("backup", "prune", "--apply", "--yes")[0], 0)
        self.assertEqual(len(self.archives()), 1)

    def test_restore_com_overwrite_e_sensivel(self):
        write(self.ryx_home / "config" / "config.toml", "[backup]\nkeep = 3\n")
        self.ryx("backup", "create", "--apply")
        (archive,) = self.archives()
        dest = self.root / "out"
        self.ryx("backup", "restore", str(archive), "--to", str(dest), "--apply")
        code, _, err = self.ryx("backup", "restore", str(archive), "--to", str(dest), "--apply")
        self.assertEqual(code, 1)
        self.assertIn("já existe", err)
        code, out, _ = self.ryx("backup", "restore", str(archive), "--to", str(dest), "--overwrite", "--apply")
        self.assertIn("[simulação]", out)
        code, _, _ = self.ryx(
            "backup", "restore", str(archive), "--to", str(dest), "--overwrite", "--apply", "--yes"
        )
        self.assertEqual(code, 0)


class ErrosSemTracebackTest(CliTestCase):
    def test_verify_de_arquivo_que_nao_existe_lista_problema_e_sai_com_1(self):
        code, out, err = self.ryx("backup", "verify", str(self.root / "ryx-20260101-000000.tar.gz"))
        self.assertEqual(code, 1)
        self.assertIn("problema: ", out)
        self.assertIn("não existe", out)
        self.assertNotIn("Traceback", err)

    def test_path_explicito_que_nao_existe_e_erro_com_ou_sem_apply(self):
        write(self.ryx_home / "config" / "config.toml", "[backup]\nkeep = 3\n")
        missing = str(self.root / "nao-existe.txt")
        for extra in ((), ("--apply",)):
            with self.subTest(extra=extra):
                code, _, err = self.ryx("backup", "create", "--path", missing, *extra)
                self.assertEqual(code, 1)
                self.assertIn("erro:", err)
                self.assertIn("nao-existe.txt", err)
                self.assertNotIn("Traceback", err)
        self.assertEqual(list((self.ryx_home / "backups").glob("*.tar.gz")), [])

    def test_fonte_padrao_ausente_continua_so_ignorada(self):
        write(self.ryx_home / "config" / "config.toml", "[backup]\nkeep = 3\n")
        code, out, _ = self.ryx("backup", "create", "--apply")
        self.assertEqual(code, 0)
        self.assertIn("ignorado: ", out)
        self.assertIn("state.json: não existe", out)

    def test_path_explicito_existente_entra_no_backup(self):
        extra = write(self.root / "extra.txt", "dados")
        code, out, _ = self.ryx("backup", "create", "--apply", "--path", str(extra))
        self.assertEqual(code, 0, out)
        self.assertIn("1 arquivo(s)", out)

    def test_restaurar_em_destino_que_e_arquivo_vira_erro_e_nao_traceback(self):
        write(self.ryx_home / "config" / "config.toml", "[backup]\nkeep = 3\n")
        self.ryx("backup", "create", "--apply")
        (archive,) = (self.ryx_home / "backups").glob("*.tar.gz")
        blocker = write(self.root / "arquivo", "x")
        code, _, err = self.ryx("backup", "restore", str(archive), "--to", str(blocker), "--apply")
        self.assertEqual(code, 1)
        self.assertIn("erro:", err)
        self.assertNotIn("Traceback", err)

    def test_modules_toml_ilegivel_ou_sem_tabela_e_erro_claro(self):
        target = self.ryx_home / "config" / "modules.toml"
        target.parent.mkdir(parents=True)
        for label, raw in (("nao utf-8", bytes([0x80, 0x81])), ("sem tabela", b"modules = 3")):
            with self.subTest(label=label):
                target.write_bytes(raw)
                code, _, err = self.ryx("backup", "list")
                self.assertEqual(code, 1)
                self.assertIn("erro:", err)
                self.assertNotIn("Traceback", err)


class MainCapturaOsErrosDeSistemaTest(unittest.TestCase):
    def run_main(self, side_effect):
        with tempfile.TemporaryDirectory() as tmp:
            env = {"HOME": tmp, "RYX_HOME": str(Path(tmp) / "ryx"), "RYX_RESOURCES": str(REPO)}
            err = io.StringIO()
            with (
                mock.patch.object(cli, "create_backup", side_effect=side_effect),
                contextlib.redirect_stderr(err),
            ):
                code = cli.main(["backup", "create", "--apply"], env, lambda _line: None)
        return code, err.getvalue()

    def test_oserror_vira_erro_e_saida_1(self):
        code, err = self.run_main(PermissionError(13, "Permission denied", "/x/y"))
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("erro: "), err)
        self.assertIn("Permission denied", err)

    def test_tarerror_vira_erro_e_saida_1(self):
        code, err = self.run_main(tarfile.ReadError("arquivo truncado"))
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("erro: "), err)
        self.assertIn("arquivo truncado", err)


class AutomationFlowTest(CliTestCase):
    def test_lista_e_simulacao(self):
        code, out, _ = self.ryx("automation", "list")
        self.assertEqual(code, 0)
        self.assertIn("backup-config", out)
        code, out, _ = self.ryx("automation", "run", "prune-backups", "--apply")
        self.assertIn("[simulação]", out)
        self.assertEqual(self.ryx("automation", "run", "nao-existe")[0], 1)


if __name__ == "__main__":
    unittest.main()
