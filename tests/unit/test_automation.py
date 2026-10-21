import tempfile
import unittest
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from unittest import mock

from ryx.backup import create_backup, list_backups
from ryx.modules import OK, Check, UserError
from ryx.modules import automation
from ryx.permissions import Risk
from tests.helpers import make_ctx, write


def args(action="run", name=None, apply=False, yes=False):
    return Namespace(action=action, name=name, apply=apply, yes=yes)


class AutomationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ctx, self.lines = make_ctx(self.root, overrides={"backup": {"keep": 1}})

    def tearDown(self):
        self._tmp.cleanup()

    def seed_backups(self, count):
        source = write(self.ctx.paths.config_dir / "config.toml", "[core]\n")
        for day in range(1, count + 1):
            create_backup(self.ctx.paths, [source], datetime(2026, 1, day))

    def test_rotinas_sao_fechadas_e_tem_risco_declarado(self):
        self.assertEqual(set(automation.ROUTINES), {"doctor", "backup-config", "prune-backups"})
        risks = {n: r.risk for n, r in automation.ROUTINES.items()}
        self.assertEqual(risks["doctor"], Risk.READ)
        self.assertEqual(risks["backup-config"], Risk.REVERSIBLE)
        self.assertEqual(risks["prune-backups"], Risk.SENSITIVE)

    def test_list_mostra_todas(self):
        automation.run(args("list"), self.ctx)
        self.assertEqual(len(self.lines), 3)
        self.assertTrue(any("prune-backups [" in line for line in self.lines))

    def test_rotina_desconhecida_e_erro(self):
        with self.assertRaisesRegex(UserError, "desconhecida"):
            automation.run(args(name="rm -rf"), self.ctx)

    def test_doctor_roda_sem_apply(self):
        with mock.patch.object(automation, "doctor_checks", return_value=[Check("x", OK, "bem")]):
            self.assertEqual(automation.run(args(name="doctor"), self.ctx), 0)
        self.assertIn("[ok]    x: bem", self.lines)

    def test_backup_config_simulacao_nao_cria_nada(self):
        self.seed_backups(0)
        automation.run(args(name="backup-config"), self.ctx)
        self.assertEqual(list_backups(self.ctx.paths), [])
        self.assertIn("[simulação]", self.lines[0])

    def test_backup_config_apply_cria_o_arquivo(self):
        write(self.ctx.paths.config_dir / "config.toml", "[core]\n")
        self.assertEqual(automation.run(args(name="backup-config", apply=True), self.ctx), 0)
        self.assertEqual(len(list_backups(self.ctx.paths)), 1)

    def test_backup_config_sem_nada_para_salvar_vira_erro_de_usuario(self):
        with self.assertRaisesRegex(UserError, "nada para salvar"):
            automation.run(args(name="backup-config", apply=True), self.ctx)

    def test_prune_exige_apply_e_yes(self):
        self.seed_backups(3)
        automation.run(args(name="prune-backups"), self.ctx)
        automation.run(args(name="prune-backups", apply=True), self.ctx)
        self.assertEqual(len(list_backups(self.ctx.paths)), 3)
        automation.run(args(name="prune-backups", apply=True, yes=True), self.ctx)
        self.assertEqual(len(list_backups(self.ctx.paths)), 1)

    def test_crontab_so_sugere(self):
        automation.run(args("crontab"), self.ctx)
        self.assertTrue(any("backup-config --apply" in line for line in self.lines))
        self.assertTrue(any("prune-backups --apply --yes" in line for line in self.lines))


if __name__ == "__main__":
    unittest.main()
