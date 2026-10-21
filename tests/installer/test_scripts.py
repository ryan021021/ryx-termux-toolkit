"""install.sh, uninstall.sh, bootstrap.sh e scripts/: processo real com `sh`, tudo numa pasta temporária."""

import hashlib
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from tests.helpers import FIXTURES, REPO

SH = shutil.which("sh")
GIT = shutil.which("git")


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


@unittest.skipUnless(SH, "sh indisponível")
class ScriptTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.ryx_home = self.root / "ryx"
        self.env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": self.home.as_posix(),
            "USERPROFILE": str(self.home),
            "RYX_HOME": self.ryx_home.as_posix(),
            "PYTHON": Path(sys.executable).as_posix(),
            "PYTHONPATH": str(REPO / "src"),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        for key in ("SYSTEMROOT", "TEMP", "TMP"):
            if key in os.environ:
                self.env[key] = os.environ[key]

    def tearDown(self):
        self._tmp.cleanup()

    def sh(self, script, *args, env=None, cwd=REPO):
        done = subprocess.run(  # noqa: S603
            [SH, script, *args],
            env={**self.env, **(env or {})},
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
            check=False,
        )
        return done.returncode, done.stdout, done.stderr

    def ryx(self, *argv, env=None):
        return subprocess.run(  # noqa: S603
            [sys.executable, "-m", "ryx", *argv],
            env={**self.env, **(env or {})},
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=60,
        )

    @property
    def data(self):
        return self.ryx_home / "data"

    def planted(self):
        """Pasta com um `ryx` e um `pip` falsos: quem importar dali imprime PLANTADO."""
        folder = self.root / "plantada"
        for name in ("ryx", "pip"):
            package = folder / name
            package.mkdir(parents=True)
            (package / "__init__.py").write_text('print("PLANTADO")\n', encoding="utf-8")
            (package / "__main__.py").write_text('print("PLANTADO")\n', encoding="utf-8")
        return folder


class InstallTest(ScriptTestCase):
    def test_dry_run_nao_grava_nada(self):
        code, out, _ = self.sh("install.sh", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("[simulação]", out)
        self.assertFalse(self.ryx_home.exists())

    def test_opcao_desconhecida_sai_com_2(self):
        self.assertEqual(self.sh("install.sh", "--nao-existe")[0], 2)
        self.assertEqual(self.sh("install.sh", "--help")[0], 0)

    def test_python_inexistente_e_erro_claro(self):
        code, _, err = self.sh("install.sh", "--no-pip", env={"PYTHON": "python-que-nao-existe"})
        self.assertEqual(code, 1)
        self.assertIn("não encontrado", err)

    def test_copia_recursos_e_e_idempotente(self):
        self.assertEqual(self.sh("install.sh", "--no-pip", "--skip-doctor")[0], 0)
        for item in ("config/default.toml", "config/modules.toml", "templates/bash/ryx.sh"):
            self.assertTrue((self.data / item).is_file(), item)
        first = tree_hashes(self.data)
        self.assertEqual(self.sh("install.sh", "--no-pip", "--skip-doctor")[0], 0)
        self.assertEqual(tree_hashes(self.data), first)

    def test_roda_o_doctor_no_fim(self):
        code, out, _ = self.sh("install.sh", "--no-pip")
        self.assertEqual(code, 0)
        self.assertIn("resultado:", out)
        self.assertNotIn("doctor reportou FALHA", out)

    def break_config(self):
        config = self.ryx_home / "config" / "config.toml"
        config.parent.mkdir(parents=True)
        config.write_text("[core", encoding="utf-8")

    def test_falha_do_doctor_nao_e_engolida_mas_sem_strict_sai_com_0(self):
        self.break_config()
        code, out, _ = self.sh("install.sh", "--no-pip")
        self.assertEqual(code, 0)
        self.assertIn("[FALHA] config", out)
        self.assertIn("doctor reportou FALHA", out.strip().splitlines()[-1])

    def test_strict_transforma_a_falha_do_doctor_em_saida_1(self):
        self.break_config()
        code, out, _ = self.sh("install.sh", "--no-pip", "--strict")
        self.assertEqual(code, 1)
        self.assertIn("doctor reportou FALHA", out.strip().splitlines()[-1])
        self.assertTrue((self.data / "config" / "default.toml").is_file(), "instalou antes de reprovar")

    def test_strict_com_doctor_saudavel_sai_com_0(self):
        code, out, _ = self.sh("install.sh", "--no-pip", "--strict")
        self.assertEqual(code, 0, out)
        self.assertNotIn("doctor reportou FALHA", out)

    def test_strict_sem_doctor_nao_tem_o_que_reprovar(self):
        self.break_config()
        self.assertEqual(self.sh("install.sh", "--no-pip", "--skip-doctor", "--strict")[0], 0)

    def test_ryx_plantado_na_pasta_atual_nao_vira_o_ryx_importado(self):
        code, out, _ = self.sh(str(REPO / "install.sh"), "--no-pip", cwd=self.planted())
        self.assertEqual(code, 0, out)
        self.assertNotIn("PLANTADO", out)
        self.assertIn("resultado:", out)

    def test_recursos_instalados_bastam_para_o_ryx_achar_os_templates(self):
        self.sh("install.sh", "--no-pip", "--skip-doctor")
        done = self.ryx("shell", "status", env={"RYX_RESOURCES": str(self.root / "vazio")})
        self.assertEqual(done.returncode, 0, done.stderr)


class UninstallTest(ScriptTestCase):
    def installed(self):
        self.sh("install.sh", "--no-pip", "--skip-doctor")
        (self.ryx_home / "config").mkdir(parents=True, exist_ok=True)
        (self.ryx_home / "config" / "config.toml").write_text("[backup]\nkeep = 2\n")

    def test_dry_run_nao_muda_nada(self):
        self.installed()
        before = tree_hashes(self.ryx_home)
        code, out, _ = self.sh("uninstall.sh", "--dry-run", "--no-pip", "--purge")
        self.assertEqual(code, 0)
        self.assertIn("[simulação]", out)
        self.assertEqual(tree_hashes(self.ryx_home), before)

    def test_purge_sem_yes_e_recusado(self):
        self.installed()
        code, _, err = self.sh("uninstall.sh", "--no-pip", "--purge")
        self.assertEqual(code, 1)
        self.assertIn("--yes", err)
        self.assertTrue(self.data.exists())

    def test_purge_apaga_so_os_recursos_e_preserva_config(self):
        self.installed()
        code, _, _ = self.sh("uninstall.sh", "--no-pip", "--purge", "--yes")
        self.assertEqual(code, 0)
        self.assertFalse(self.data.exists())
        self.assertTrue((self.ryx_home / "config" / "config.toml").is_file())

    def test_sem_purge_mantem_os_recursos(self):
        self.installed()
        self.assertEqual(self.sh("uninstall.sh", "--no-pip")[0], 0)
        self.assertTrue(self.data.exists())

    def standalone_env(self, **extra):
        """Sem RYX_HOME: os dados vão para XDG_DATA_HOME (ou para HOME/.local/share)."""
        env = {"RYX_HOME": "", "XDG_DATA_HOME": "", "XDG_CONFIG_HOME": "", "XDG_STATE_HOME": ""}
        env.update(extra)
        return env

    def plant_backups(self, data_dir):
        backups = data_dir / "backups"
        backups.mkdir(parents=True)
        archive = backups / "ryx-20260101-000000.tar.gz"
        archive.write_bytes(b"backup precioso")
        archive.with_name(archive.name + ".sha256").write_text("x  y")
        return backups

    def test_purge_fora_do_ryx_home_preserva_os_backups_que_vivem_no_data_dir(self):
        env = self.standalone_env()
        data_dir = self.home / ".local" / "share" / "ryx"
        self.assertEqual(self.sh("install.sh", "--no-pip", "--skip-doctor", env=env)[0], 0)
        backups = self.plant_backups(data_dir)
        (data_dir / "outro.txt").write_text("meu")
        code, out, _ = self.sh("uninstall.sh", "--no-pip", "--purge", "--yes", env=env)
        self.assertEqual(code, 0, out)
        self.assertFalse((data_dir / "templates").exists())
        self.assertFalse((data_dir / "config").exists())
        self.assertEqual((backups / "ryx-20260101-000000.tar.gz").read_bytes(), b"backup precioso")
        self.assertTrue((backups / "ryx-20260101-000000.tar.gz.sha256").is_file())
        self.assertEqual((data_dir / "outro.txt").read_text(), "meu")
        self.assertIn("backups não foram tocados", out)

    def test_purge_com_xdg_data_home_preserva_os_backups(self):
        xdg = self.root / "xdg"
        env = self.standalone_env(XDG_DATA_HOME=xdg.as_posix())
        self.assertEqual(self.sh("install.sh", "--no-pip", "--skip-doctor", env=env)[0], 0)
        backups = self.plant_backups(xdg / "ryx")
        self.assertEqual(self.sh("uninstall.sh", "--no-pip", "--purge", "--yes", env=env)[0], 0)
        self.assertFalse((xdg / "ryx" / "templates").exists())
        self.assertTrue((backups / "ryx-20260101-000000.tar.gz").is_file())

    def test_purge_sem_nada_dentro_tira_a_pasta_vazia(self):
        env = self.standalone_env()
        self.assertEqual(self.sh("install.sh", "--no-pip", "--skip-doctor", env=env)[0], 0)
        self.assertEqual(self.sh("uninstall.sh", "--no-pip", "--purge", "--yes", env=env)[0], 0)
        self.assertFalse((self.home / ".local" / "share" / "ryx").exists())

    def test_dry_run_do_purge_fora_do_ryx_home_nao_apaga_nada(self):
        env = self.standalone_env()
        self.sh("install.sh", "--no-pip", "--skip-doctor", env=env)
        self.plant_backups(self.home / ".local" / "share" / "ryx")
        before = tree_hashes(self.home)
        code, out, _ = self.sh("uninstall.sh", "--dry-run", "--no-pip", "--purge", env=env)
        self.assertEqual(code, 0)
        self.assertIn("[simulação]", out)
        rm_lines = [line for line in out.splitlines() if line.startswith("[simulação] rm -rf")]
        self.assertEqual(len(rm_lines), 1, out)
        targets = rm_lines[0].split()[4:]
        self.assertEqual([Path(t).name for t in targets], ["templates", "config"], rm_lines[0])
        self.assertEqual(tree_hashes(self.home), before)

    def test_ryx_plantado_na_pasta_atual_nao_atrapalha_o_uninstall(self):
        rc = self.home / ".bashrc"
        original = (FIXTURES / "bashrc-sample").read_bytes()
        rc.write_bytes(original)
        self.installed()
        self.assertEqual(self.ryx("shell", "install", "--apply").returncode, 0)
        code, out, _ = self.sh((REPO / "uninstall.sh").as_posix(), "--no-pip", cwd=self.planted())
        self.assertEqual(code, 0, out)
        self.assertNotIn("PLANTADO", out)
        self.assertEqual(rc.read_bytes(), original)

    def test_purge_recusa_caminho_perigoso(self):
        (self.home / "data").mkdir()
        for bad in ("/", self.home.as_posix()):
            with self.subTest(ryx_home=bad):
                code, _, err = self.sh("uninstall.sh", "--no-pip", "--purge", "--yes", env={"RYX_HOME": bad})
                self.assertEqual(code, 1)
                self.assertIn("suspeito", err)
                self.assertTrue((self.home / "data").exists())

    def test_remove_o_bloco_do_shell_e_devolve_o_rc(self):
        rc = self.home / ".bashrc"
        original = (FIXTURES / "bashrc-sample").read_bytes()
        rc.write_bytes(original)
        self.installed()
        self.assertEqual(self.ryx("shell", "install", "--apply").returncode, 0)
        self.assertNotEqual(rc.read_bytes(), original)
        self.assertEqual(self.sh("uninstall.sh", "--no-pip")[0], 0)
        self.assertEqual(rc.read_bytes(), original)


class ScriptsDirTest(ScriptTestCase):
    def test_check_environment(self):
        code, out, _ = self.sh("scripts/check-environment.sh")
        self.assertEqual(code, 0, out)
        self.assertIn("[ok]    python", out)
        code, out, _ = self.sh("scripts/check-environment.sh", env={"PYTHON": "python-que-nao-existe"})
        self.assertEqual(code, 1)
        self.assertIn("[FALHA]", out)

    def test_ryx_plantado_na_pasta_atual_nao_engana_o_verify_install(self):
        self.sh("install.sh", "--no-pip", "--skip-doctor")
        code, out, _ = self.sh((REPO / "scripts" / "verify-install.sh").as_posix(), cwd=self.planted())
        self.assertEqual(code, 0, out)
        self.assertNotIn("PLANTADO", out)
        self.assertIn("[ok]    ryx 0.1.0", out)

    def test_pip_plantado_na_pasta_atual_nao_engana_o_check_environment(self):
        code, out, _ = self.sh((REPO / "scripts" / "check-environment.sh").as_posix(), cwd=self.planted())
        self.assertEqual(code, 0, out)
        self.assertNotIn("PLANTADO", out)

    def test_verify_install_antes_e_depois(self):
        code, out, _ = self.sh("scripts/verify-install.sh")
        self.assertEqual(code, 1)
        self.assertIn("faltando", out)
        self.sh("install.sh", "--no-pip", "--skip-doctor")
        code, out, _ = self.sh("scripts/verify-install.sh")
        self.assertEqual(code, 0, out)


@unittest.skipUnless(SH and GIT, "sh e git indisponíveis")
class BootstrapTest(ScriptTestCase):
    def make_remote(self):
        remote = self.root / "remote"
        remote.mkdir()
        (remote / "install.sh").write_text('#!/bin/sh\necho "STUB-INSTALL $*"\n', newline="\n")
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        subprocess.run([*git, "init", "-q", "-b", "main"], cwd=remote, check=True)  # noqa: S603
        subprocess.run([*git, "add", "."], cwd=remote, check=True)  # noqa: S603
        subprocess.run([*git, "commit", "-q", "-m", "x"], cwd=remote, check=True)  # noqa: S603
        sha = subprocess.run(  # noqa: S603
            [*git, "rev-parse", "HEAD"], cwd=remote, capture_output=True, text=True, check=True
        ).stdout.strip()
        return remote, sha

    def test_sem_url_e_erro(self):
        code, _, err = self.sh("bootstrap.sh", env={"RYX_REPO_URL": ""})
        self.assertEqual(code, 1)
        self.assertIn("RYX_REPO_URL", err)

    def test_url_inexistente_falha(self):
        code, _, _ = self.sh("bootstrap.sh", env={"RYX_REPO_URL": (self.root / "nada").as_posix()})
        self.assertNotEqual(code, 0)

    def test_repassa_argumentos_e_confere_o_commit(self):
        remote, sha = self.make_remote()
        env = {"RYX_REPO_URL": remote.as_posix(), "RYX_COMMIT": sha}
        code, out, _ = self.sh("bootstrap.sh", "--dry-run", env=env)
        self.assertEqual(code, 0, out)
        self.assertIn("STUB-INSTALL --dry-run", out)
        self.assertIn("commit conferido", out)

    def test_commit_diferente_aborta_antes_de_instalar(self):
        remote, _ = self.make_remote()
        env = {"RYX_REPO_URL": remote.as_posix(), "RYX_COMMIT": "0" * 40}
        code, out, err = self.sh("bootstrap.sh", env=env)
        self.assertEqual(code, 1)
        self.assertIn("difere", err)
        self.assertNotIn("STUB-INSTALL", out)

    def test_sem_commit_e_recusado_antes_de_baixar_qualquer_coisa(self):
        remote, _ = self.make_remote()
        env = {"RYX_REPO_URL": remote.as_posix(), "RYX_COMMIT": ""}
        code, out, err = self.sh("bootstrap.sh", env=env)
        self.assertEqual(code, 1)
        self.assertIn("RYX_COMMIT", err)
        self.assertIn("RYX_INSECURE=1", err)
        self.assertNotIn("STUB-INSTALL", out)
        self.assertNotIn("baixando", out)

    def test_insecure_so_vale_com_o_valor_exato_1(self):
        remote, _ = self.make_remote()
        for value in ("0", "true", "yes", ""):
            with self.subTest(value=value):
                env = {"RYX_REPO_URL": remote.as_posix(), "RYX_INSECURE": value}
                code, out, _ = self.sh("bootstrap.sh", env=env)
                self.assertEqual(code, 1)
                self.assertNotIn("STUB-INSTALL", out)

    def test_insecure_explicito_instala_e_avisa_que_nao_conferiu(self):
        remote, _ = self.make_remote()
        env = {"RYX_REPO_URL": remote.as_posix(), "RYX_INSECURE": "1"}
        code, out, _ = self.sh("bootstrap.sh", env=env)
        self.assertEqual(code, 0, out)
        self.assertIn("não foi conferido", out)
        self.assertIn("STUB-INSTALL", out)

    def test_commit_certo_ignora_o_insecure(self):
        remote, sha = self.make_remote()
        env = {"RYX_REPO_URL": remote.as_posix(), "RYX_COMMIT": sha, "RYX_INSECURE": "1"}
        code, out, _ = self.sh("bootstrap.sh", env=env)
        self.assertEqual(code, 0, out)
        self.assertIn("commit conferido", out)

    def test_commit_errado_aborta_mesmo_com_insecure(self):
        remote, _ = self.make_remote()
        env = {"RYX_REPO_URL": remote.as_posix(), "RYX_COMMIT": "0" * 40, "RYX_INSECURE": "1"}
        code, out, err = self.sh("bootstrap.sh", env=env)
        self.assertEqual(code, 1)
        self.assertIn("difere", err)
        self.assertNotIn("STUB-INSTALL", out)

    def test_pasta_temporaria_some_no_sucesso_e_na_falha(self):
        remote, sha = self.make_remote()
        tmpdir = self.root / "tmp"
        tmpdir.mkdir()
        for commit in (sha, "0" * 40):
            with self.subTest(commit=commit):
                env = {"RYX_REPO_URL": remote.as_posix(), "RYX_COMMIT": commit, "TMPDIR": tmpdir.as_posix()}
                self.sh("bootstrap.sh", env=env)
                self.assertEqual(list(tmpdir.iterdir()), [])

    @unittest.skipIf(os.name == "nt", "sinais POSIX")
    def test_sinal_interrompe_de_verdade_e_limpa_a_pasta_temporaria(self):
        remote, _ = self.make_remote()
        script = '#!/bin/sh\necho "STUB-RODANDO"\nsleep 30\necho "STUB-DEPOIS-DO-SONO"\n'
        (remote / "install.sh").write_text(script, newline="\n")
        git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        subprocess.run([*git, "commit", "-q", "-am", "y"], cwd=remote, check=True)  # noqa: S603
        sha = subprocess.run(  # noqa: S603
            [*git, "rev-parse", "HEAD"], cwd=remote, capture_output=True, text=True, check=True
        ).stdout.strip()
        tmpdir = self.root / "tmp"
        tmpdir.mkdir()
        env = {**self.env, "RYX_REPO_URL": remote.as_posix(), "RYX_COMMIT": sha, "TMPDIR": tmpdir.as_posix()}
        proc = subprocess.Popen(  # noqa: S603
            [SH, "bootstrap.sh"],
            cwd=REPO,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline and not any(tmpdir.glob("*/ryx/install.sh")):
                time.sleep(0.1)
            time.sleep(0.5)
            os.killpg(proc.pid, signal.SIGTERM)
            out, _ = proc.communicate(timeout=30)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
        self.assertEqual(proc.returncode, 130)
        self.assertNotIn("STUB-DEPOIS-DO-SONO", out)
        self.assertEqual(list(tmpdir.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
