import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

from ryx.modules import UserError
from ryx.modules.shell import (
    END,
    START,
    apply_block,
    find_block,
    remove_block,
    render_block,
    run,
    write_atomic,
)
from ryx.backup import list_backups, restore_backup
from ryx.state import StateError, load_state
from tests.helpers import FIXTURES, IS_WINDOWS, make_ctx, write


def args(action, apply=False, yes=False, shell=None, theme=None):
    return Namespace(action=action, apply=apply, yes=yes, shell=shell, theme=theme)


class BlockTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ctx, _ = make_ctx(self.root)
        self.block = render_block("bash", "default", self.ctx.paths)

    def tearDown(self):
        self._tmp.cleanup()

    def test_bloco_tem_marcadores_e_conteudo_do_template(self):
        self.assertTrue(self.block.startswith(START + "\n"))
        self.assertTrue(self.block.endswith(END + "\n"))
        self.assertGreater(len(self.block.splitlines()), 4)

    def test_shell_e_tema_invalidos_sao_recusados(self):
        for shell, theme in (("fish", "default"), ("bash", "../x"), ("bash", "A;b"), ("bash", "nao-existe")):
            with self.subTest(shell=shell, theme=theme), self.assertRaises(UserError):
                render_block(shell, theme, self.ctx.paths)

    def test_aplicar_duas_vezes_da_o_mesmo_texto(self):
        original = (FIXTURES / "bashrc-sample").read_text(encoding="utf-8")
        once = apply_block(original, self.block)
        self.assertEqual(apply_block(once, self.block), once)
        self.assertTrue(once.startswith(original))

    def test_remover_devolve_o_original(self):
        original = (FIXTURES / "bashrc-sample").read_text(encoding="utf-8")
        self.assertEqual(remove_block(apply_block(original, self.block)), original)

    def test_texto_vazio_e_texto_sem_bloco(self):
        self.assertEqual(apply_block("", self.block), self.block)
        self.assertEqual(remove_block("export A=1\n"), "export A=1\n")
        self.assertIsNone(find_block("export A=1\n"))

    def test_atualiza_so_o_que_esta_entre_os_marcadores(self):
        text = f"antes\n{START}\nvelho\n{END}\ndepois\n"
        new = apply_block(text, self.block)
        self.assertTrue(new.startswith("antes\n"))
        self.assertTrue(new.endswith("depois\n"))
        self.assertNotIn("velho", new)

    def test_marcador_quebrado_e_erro(self):
        broken = (
            f"{START}\n",
            f"{END}\n",
            f"{END}\n{START}\n",
            f"{START}\n{END}\n{START}\n{END}\n",
        )
        for text in broken:
            with self.subTest(text=text), self.assertRaisesRegex(UserError, "marcadores"):
                find_block(text)


class WriteAtomicTest(unittest.TestCase):
    def test_grava_sem_deixar_temporario(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sub" / "rc"
            write_atomic(target, "a\n")
            self.assertEqual(target.read_text(), "a\n")
            self.assertEqual([p.name for p in target.parent.iterdir()], ["rc"])

    @unittest.skipIf(IS_WINDOWS, "permissão POSIX")
    def test_preserva_o_modo_do_arquivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = write(Path(tmp) / "rc", "a\n")
            target.chmod(0o600)
            write_atomic(target, "b\n")
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)


class CommandTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ctx, self.lines = make_ctx(self.root)
        self.rc = self.ctx.paths.home / ".bashrc"
        self.original = (FIXTURES / "bashrc-sample").read_text(encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_simulacao_nao_cria_nem_altera_nada(self):
        self.assertEqual(run(args("install"), self.ctx), 0)
        self.assertFalse(self.rc.exists())
        write(self.rc, self.original)
        run(args("install"), self.ctx)
        self.assertEqual(self.rc.read_text(encoding="utf-8"), self.original)
        self.assertTrue(any("[simulação]" in line for line in self.lines))
        self.assertEqual(list_backups(self.ctx.paths), [])

    def test_apply_grava_bloco_faz_backup_e_registra_estado(self):
        write(self.rc, self.original)
        run(args("install", apply=True), self.ctx)
        text = self.rc.read_text(encoding="utf-8")
        self.assertIn(START, text)
        self.assertTrue(text.startswith(self.original))
        self.assertEqual(len(list_backups(self.ctx.paths)), 1)
        self.assertIn(str(self.rc), load_state(self.ctx.paths.state_file)["shell"])

    def test_apply_repetido_nao_muda_nada_nem_novo_backup(self):
        write(self.rc, self.original)
        run(args("install", apply=True), self.ctx)
        first = self.rc.read_bytes()
        run(args("install", apply=True), self.ctx)
        self.assertEqual(self.rc.read_bytes(), first)
        self.assertEqual(len(list_backups(self.ctx.paths)), 1)
        self.assertTrue(any("nada a fazer" in line for line in self.lines))

    def test_uninstall_devolve_os_bytes_originais(self):
        write(self.rc, self.original)
        run(args("install", apply=True), self.ctx)
        run(args("uninstall", apply=True), self.ctx)
        self.assertEqual(self.rc.read_text(encoding="utf-8"), self.original)
        self.assertEqual(load_state(self.ctx.paths.state_file)["shell"], {})

    def test_instala_em_rc_que_nao_existe_sem_backup(self):
        run(args("install", apply=True), self.ctx)
        self.assertIn(START, self.rc.read_text(encoding="utf-8"))
        self.assertEqual(list_backups(self.ctx.paths), [])

    def test_shell_zsh_escolhe_o_zshrc(self):
        run(args("install", apply=True, shell="zsh"), self.ctx)
        self.assertTrue((self.ctx.paths.home / ".zshrc").exists())
        self.assertFalse(self.rc.exists())

    def test_status_descreve_cada_situacao(self):
        run(args("status"), self.ctx)
        self.assertIn("não instalado", self.lines[-1])
        run(args("install", apply=True), self.ctx)
        run(args("status"), self.ctx)
        self.assertIn("em dia", self.lines[-1])
        text = self.rc.read_text(encoding="utf-8")
        self.rc.write_text(text.replace(END, "# alterado\n" + END), encoding="utf-8")
        run(args("status"), self.ctx)
        self.assertIn("diferente", self.lines[-1])

    def test_marcador_quebrado_no_rc_aborta_sem_gravar(self):
        write(self.rc, f"x\n{START}\n")
        with self.assertRaises(UserError):
            run(args("install", apply=True), self.ctx)
        self.assertEqual(self.rc.read_text(encoding="utf-8"), f"x\n{START}\n")


class SafetyTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ctx, self.lines = make_ctx(self.root)
        self.rc = self.ctx.paths.home / ".bashrc"
        self.original = (FIXTURES / "bashrc-sample").read_text(encoding="utf-8")
        write(self.rc, self.original)

    def tearDown(self):
        self._tmp.cleanup()

    def assert_rc_intocado(self):
        self.assertEqual(self.rc.read_text(encoding="utf-8"), self.original)
        self.assertEqual(list_backups(self.ctx.paths), [])

    def test_estado_corrompido_aborta_antes_de_gravar_o_rc(self):
        write(self.ctx.paths.state_file, "{quebrado")
        for action in ("install", "uninstall"):
            with self.subTest(action=action), self.assertRaises(StateError):
                run(args(action, apply=True), self.ctx)
            self.assert_rc_intocado()

    def test_estado_com_tipo_errado_aborta_antes_de_gravar_o_rc(self):
        write(self.ctx.paths.state_file, '{"version": 1, "shell": []}')
        with self.assertRaises(StateError):
            run(args("install", apply=True), self.ctx)
        self.assert_rc_intocado()

    def test_simulacao_nao_exige_estado_valido(self):
        write(self.ctx.paths.state_file, "{quebrado")
        self.assertEqual(run(args("install"), self.ctx), 0)
        self.assert_rc_intocado()

    def test_rc_fora_do_home_e_recusado(self):
        outside = (self.root / "fora" / "bashrc").as_posix()
        bad = ["/etc/profile", outside, "~/../fora/bashrc", "~/a/../../fora/x", "../x", ".bashrc", "~"]
        for raw in bad:
            ctx, _ = make_ctx(self.root, overrides={"shell": {"rc_files": [raw]}})
            for action in ("status", "install"):
                with self.subTest(raw=raw, action=action), self.assertRaisesRegex(UserError, "rc_files"):
                    run(args(action, apply=True), ctx)
        self.assertFalse((self.root / "fora").exists())

    def test_rc_absoluto_dentro_do_home_e_aceito(self):
        inside = (self.ctx.paths.home / ".bashrc").as_posix()
        ctx, _ = make_ctx(self.root, overrides={"shell": {"rc_files": [inside]}})
        run(args("install", apply=True), ctx)
        self.assertIn(START, self.rc.read_text(encoding="utf-8"))

    def test_rc_com_bytes_invalidos_vira_erro_claro_e_nao_e_tocado(self):
        self.rc.write_bytes(bytes([0x80, 0x81, 0x82]))
        for action in ("status", "install", "uninstall"):
            with self.subTest(action=action), self.assertRaisesRegex(UserError, "UTF-8"):
                run(args(action, apply=True), self.ctx)
        self.assertEqual(self.rc.read_bytes(), bytes([0x80, 0x81, 0x82]))
        self.assertEqual(list_backups(self.ctx.paths), [])

    def test_rc_que_e_uma_pasta_vira_erro_claro(self):
        self.rc.unlink()
        self.rc.mkdir()
        with self.assertRaisesRegex(UserError, "não consegui ler"):
            run(args("install", apply=True), self.ctx)

    def test_rc_symlink_grava_no_alvo_e_faz_backup_do_conteudo(self):
        target = write(self.ctx.paths.home / "dotfiles" / "bashrc", self.original)
        self.rc.unlink()
        try:
            self.rc.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("sem permissão para criar link simbólico")
        run(args("install", apply=True), self.ctx)
        self.assertTrue(self.rc.is_symlink(), "o link tem de continuar link")
        self.assertIn(START, target.read_text(encoding="utf-8"))
        (archive,) = list_backups(self.ctx.paths)
        restored = restore_backup(archive, self.root / "out")
        self.assertEqual([p.read_text(encoding="utf-8") for p in restored], [self.original])
        run(args("uninstall", apply=True), self.ctx)
        self.assertTrue(self.rc.is_symlink())
        self.assertEqual(target.read_text(encoding="utf-8"), self.original)


if __name__ == "__main__":
    unittest.main()
