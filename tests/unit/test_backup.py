import io
import json
import tarfile
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from ryx import backup as backup_module

from ryx.backup import (
    BackupError,
    create_backup,
    list_backups,
    prune_backups,
    restore_backup,
    verify_backup,
)
from ryx.paths import resolve_paths
from tests.helpers import IS_WINDOWS, write

NOW = datetime(2026, 10, 20, 12, 0, 0)


class BackupTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.home = self.root / "home"
        self.paths = resolve_paths({"HOME": str(self.home), "RYX_HOME": str(self.root / "ryx")})
        self.a = write(self.home / "dir" / "a.txt", "alfa")
        self.b = write(self.home / "dir" / "sub" / "b.txt", "beta")

    def tearDown(self):
        self._tmp.cleanup()

    def test_cria_arquivo_e_sidecar_e_passa_na_verificacao(self):
        result = create_backup(self.paths, [self.home / "dir"], NOW)
        self.assertEqual(result.files, 2)
        self.assertEqual(result.archive.name, "ryx-20261020-120000.tar.gz")
        self.assertTrue(result.archive.with_name(result.archive.name + ".sha256").is_file())
        self.assertEqual(verify_backup(result.archive), [])

    def test_manifesto_guarda_caminho_relativo_ao_home(self):
        archive = create_backup(self.paths, [self.a], NOW).archive
        with tarfile.open(archive) as tar:
            manifest = json.loads(tar.extractfile("manifest.json").read())
        self.assertEqual(manifest["files"][0]["rel"], "home/dir/a.txt")
        self.assertEqual(manifest["files"][0]["size"], 4)

    def test_origem_que_nao_existe_e_registrada_como_ignorada(self):
        result = create_backup(self.paths, [self.a, self.root / "nada"], NOW)
        self.assertEqual(result.files, 1)
        self.assertTrue(any("não existe" in s for s in result.skipped))

    def test_sem_nenhum_arquivo_e_erro(self):
        with self.assertRaisesRegex(BackupError, "nada para salvar"):
            create_backup(self.paths, [self.root / "nada"], NOW)

    def test_mesmo_segundo_gera_nomes_diferentes(self):
        first = create_backup(self.paths, [self.a], NOW).archive
        second = create_backup(self.paths, [self.a], NOW).archive
        self.assertNotEqual(first, second)
        self.assertEqual(second.name, "ryx-20261020-120000-2.tar.gz")

    def test_link_simbolico_e_ignorado(self):
        link = self.home / "dir" / "link.txt"
        try:
            link.symlink_to(self.a)
        except (OSError, NotImplementedError):
            self.skipTest("sem permissão para criar link simbólico")
        result = create_backup(self.paths, [self.home / "dir"], NOW)
        self.assertEqual(result.files, 2)
        self.assertTrue(any("link simbólico" in s for s in result.skipped))

    @unittest.skipIf(IS_WINDOWS, "permissão POSIX")
    def test_arquivo_de_backup_fica_com_modo_0600(self):
        archive = create_backup(self.paths, [self.a], NOW).archive
        self.assertEqual(archive.stat().st_mode & 0o777, 0o600)

    def test_verificacao_pega_arquivo_adulterado_e_sidecar_ausente(self):
        archive = create_backup(self.paths, [self.a], NOW).archive
        sidecar = archive.with_name(archive.name + ".sha256")
        archive.write_bytes(archive.read_bytes() + b"x")
        self.assertTrue(any("SHA-256" in p for p in verify_backup(archive)))
        sidecar.unlink()
        self.assertTrue(any("sem arquivo .sha256" in p for p in verify_backup(archive)))

    def test_verificacao_de_lixo_nao_levanta_excecao(self):
        junk = write(self.root / "lixo.tar.gz", "isto nao e tar")
        problems = verify_backup(junk)
        self.assertTrue(any("arquivo ilegível" in p for p in problems), problems)

    def test_restaura_conteudo_e_estrutura_sob_o_destino(self):
        archive = create_backup(self.paths, [self.home / "dir"], NOW).archive
        dest = self.root / "out"
        written = restore_backup(archive, dest)
        self.assertEqual(len(written), 2)
        self.assertEqual((dest / "home" / "dir" / "a.txt").read_text(), "alfa")
        self.assertEqual((dest / "home" / "dir" / "sub" / "b.txt").read_text(), "beta")

    def test_conflito_sem_overwrite_nao_grava_nada(self):
        archive = create_backup(self.paths, [self.home / "dir"], NOW).archive
        dest = self.root / "out"
        write(dest / "home" / "dir" / "sub" / "b.txt", "antigo")
        with self.assertRaisesRegex(BackupError, "já existe"):
            restore_backup(archive, dest)
        self.assertFalse((dest / "home" / "dir" / "a.txt").exists())
        self.assertEqual((dest / "home" / "dir" / "sub" / "b.txt").read_text(), "antigo")

    def test_overwrite_substitui(self):
        archive = create_backup(self.paths, [self.a], NOW).archive
        dest = self.root / "out"
        write(dest / "home" / "dir" / "a.txt", "antigo")
        restore_backup(archive, dest, overwrite=True)
        self.assertEqual((dest / "home" / "dir" / "a.txt").read_text(), "alfa")

    def test_restauracao_recusa_backup_adulterado(self):
        archive = create_backup(self.paths, [self.a], NOW).archive
        archive.write_bytes(archive.read_bytes() + b"x")
        with self.assertRaisesRegex(BackupError, "não passou na verificação"):
            restore_backup(archive, self.root / "out")
        self.assertFalse((self.root / "out" / "home").exists())

    def test_list_ordena_e_ignora_arquivos_de_fora(self):
        old = create_backup(self.paths, [self.a], datetime(2026, 1, 1, 0, 0, 0)).archive
        new = create_backup(self.paths, [self.a], NOW).archive
        write(self.paths.backup_dir / "outro.txt", "x")
        self.assertEqual(list_backups(self.paths), [old, new])

    def test_list_sem_pasta_devolve_vazio(self):
        self.assertEqual(list_backups(self.paths), [])

    def test_prune_mantem_os_mais_novos_e_remove_sidecar(self):
        archives = [
            create_backup(self.paths, [self.a], datetime(2026, 1, day, 0, 0, 0)).archive
            for day in (1, 2, 3)
        ]
        removed = prune_backups(self.paths, keep=1)
        self.assertEqual(removed, archives[:2])
        self.assertEqual(list_backups(self.paths), [archives[2]])
        self.assertFalse(archives[0].with_name(archives[0].name + ".sha256").exists())
        self.assertTrue(archives[2].with_name(archives[2].name + ".sha256").exists())

    def test_prune_com_keep_maior_que_o_total_nao_remove(self):
        create_backup(self.paths, [self.a], NOW)
        self.assertEqual(prune_backups(self.paths, keep=5), [])

    def test_ordem_trata_o_contador_como_numero_e_o_base_vem_primeiro(self):
        names = [
            "ryx-20261020-120000.tar.gz",
            "ryx-20261020-120000-2.tar.gz",
            "ryx-20261020-120000-10.tar.gz",
            "ryx-20261020-120001.tar.gz",
            "ryx-20261020-115959-3.tar.gz",
        ]
        for name in reversed(names):
            write(self.paths.backup_dir / name, "x")
        listed = [p.name for p in list_backups(self.paths)]
        self.assertEqual(
            listed,
            [
                "ryx-20261020-115959-3.tar.gz",
                "ryx-20261020-120000.tar.gz",
                "ryx-20261020-120000-2.tar.gz",
                "ryx-20261020-120000-10.tar.gz",
                "ryx-20261020-120001.tar.gz",
            ],
        )

    def test_prune_nao_apaga_o_mais_novo_quando_ha_contador(self):
        archives = [create_backup(self.paths, [self.a], NOW).archive for _ in range(3)]
        self.assertEqual(
            [a.name for a in archives],
            ["ryx-20261020-120000.tar.gz", "ryx-20261020-120000-2.tar.gz", "ryx-20261020-120000-3.tar.gz"],
        )
        removed = prune_backups(self.paths, keep=1)
        self.assertEqual(removed, archives[:2])
        self.assertEqual(list_backups(self.paths), [archives[2]])

    def test_reserva_do_nome_e_exclusiva(self):
        self.paths.backup_dir.mkdir(parents=True)
        first = backup_module._reserve_archive(self.paths.backup_dir, "20261020-120000")
        second = backup_module._reserve_archive(self.paths.backup_dir, "20261020-120000")
        self.assertNotEqual(first, second)
        self.assertTrue(first.exists() and second.exists())

    def test_nao_sobrescreve_backup_que_apareceu_no_meio(self):
        taken = write(self.paths.backup_dir / "ryx-20261020-120000.tar.gz", "de outro processo")
        archive = create_backup(self.paths, [self.a], NOW).archive
        self.assertNotEqual(archive, taken)
        self.assertEqual(taken.read_text(), "de outro processo")

    def test_origens_repetidas_entram_uma_vez_so(self):
        result = create_backup(self.paths, [self.home / "dir", self.a, self.a, self.home / "dir" / "."], NOW)
        self.assertEqual(result.files, 2)
        with tarfile.open(result.archive) as tar:
            manifest = json.loads(tar.extractfile("manifest.json").read())
        rels = [e["rel"] for e in manifest["files"]]
        self.assertEqual(len(rels), len(set(rels)))

    def test_hash_e_conteudo_vem_da_mesma_leitura(self):
        # Cada abertura devolve um conteúdo diferente (arquivo mudando enquanto o backup roda).
        contents = iter([b"alfa", b"ZZZZ", b"YYYY", b"XXXX"])
        real_open = Path.open
        real_bltn = tarfile.bltn_open

        def fake_path_open(self_path, *args, **kwargs):
            if self_path == self.a:
                return io.BytesIO(next(contents))
            return real_open(self_path, *args, **kwargs)

        def fake_bltn(name, *args, **kwargs):
            if Path(name) == self.a:
                return io.BytesIO(next(contents))
            return real_bltn(name, *args, **kwargs)

        with (
            mock.patch.object(Path, "open", fake_path_open),
            mock.patch.object(tarfile, "bltn_open", fake_bltn),
        ):
            archive = create_backup(self.paths, [self.a], NOW).archive
        self.assertEqual(verify_backup(archive), [])

    def test_hash_do_manifesto_e_o_do_conteudo_gravado(self):
        archive = create_backup(self.paths, [self.a, self.b], NOW).archive
        self.assertEqual(verify_backup(archive), [])
        restored = restore_backup(archive, self.root / "out")
        self.assertEqual(sorted(p.read_text() for p in restored), ["alfa", "beta"])

    def test_arquivo_final_que_nao_confere_vira_erro_e_nao_deixa_resto(self):
        with (
            mock.patch.object(backup_module, "verify_backup", return_value=["files/0: conteúdo difere do manifesto"]),
            self.assertRaisesRegex(BackupError, "verificação final"),
        ):
            create_backup(self.paths, [self.a], NOW)
        self.assertEqual(list(self.paths.backup_dir.iterdir()), [])

    def test_falha_no_meio_nao_deixa_temporario_nem_nome_reservado(self):
        with mock.patch.object(backup_module.tarfile.TarFile, "addfile", side_effect=OSError("disco cheio")):
            with self.assertRaises(OSError):
                create_backup(self.paths, [self.a], NOW)
        self.assertEqual(list(self.paths.backup_dir.iterdir()), [])

    def test_verificacao_de_arquivo_que_sumiu_nao_levanta_excecao(self):
        problems = verify_backup(self.root / "nao-existe.tar.gz")
        self.assertTrue(any("não existe" in p for p in problems), problems)

    @unittest.skipIf(IS_WINDOWS, "permissão POSIX")
    def test_sidecar_0600_e_pasta_de_backups_0700(self):
        archive = create_backup(self.paths, [self.a], NOW).archive
        sidecar = archive.with_name(archive.name + ".sha256")
        self.assertEqual(sidecar.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.paths.backup_dir.stat().st_mode & 0o777, 0o700)

    @unittest.skipIf(IS_WINDOWS, "permissão POSIX")
    def test_pasta_de_backups_que_ja_existia_aberta_e_fechada(self):
        self.paths.backup_dir.mkdir(parents=True)
        self.paths.backup_dir.chmod(0o755)
        create_backup(self.paths, [self.a], NOW)
        self.assertEqual(self.paths.backup_dir.stat().st_mode & 0o777, 0o700)

    @unittest.skipIf(IS_WINDOWS, "nome com dois pontos só existe em POSIX")
    def test_dois_pontos_no_nome_nao_gera_backup_irrestauravel(self):
        odd = write(self.home / "dir" / "a:b.txt", "estranho")
        archive = create_backup(self.paths, [odd], NOW).archive
        restored = restore_backup(archive, self.root / "out")
        self.assertEqual(restored[0].read_text(), "estranho")

    def test_backup_de_arquivo_fora_do_home_usa_prefixo_abs(self):
        ext = write(self.root / "externo" / "cfg.txt", "dados_externos")
        result = create_backup(self.paths, [ext], NOW)
        self.assertEqual(result.files, 1)
        with tarfile.open(result.archive) as tar:
            manifest = json.loads(tar.extractfile("manifest.json").read())
        rel = manifest["files"][0]["rel"]
        self.assertTrue(rel.startswith("abs/"), f"esperava prefixo abs/: {rel}")
        dest = self.root / "out_abs"
        written = restore_backup(result.archive, dest)
        self.assertEqual(len(written), 1)
        self.assertEqual(written[0].read_text(), "dados_externos")

    def test_cria_backup_sem_passar_now_usa_data_atual(self):
        result = create_backup(self.paths, [self.a])
        self.assertEqual(result.files, 1)
        self.assertTrue(result.archive.is_file())
        self.assertEqual(verify_backup(result.archive), [])
        today_stamp = datetime.now().strftime("%Y%m%d")
        self.assertIn(today_stamp, result.archive.name)

    def test_falha_na_escrita_da_restauracao_limpa_arquivos_temporarios(self):
        archive = create_backup(self.paths, [self.a], NOW).archive
        dest = self.root / "out_fail"
        with mock.patch("os.replace", side_effect=OSError("erro simulado ao mover")):
            with self.assertRaises(OSError):
                restore_backup(archive, dest)
        if dest.exists():
            restores = list(dest.rglob(".restore-*"))
            self.assertEqual(restores, [], f"temporários de restauração não foram limpos: {restores}")

    def test_prune_com_keep_zero_remove_todos_os_backups(self):
        create_backup(self.paths, [self.a], datetime(2026, 1, 1))
        create_backup(self.paths, [self.a], datetime(2026, 1, 2))
        removed = prune_backups(self.paths, keep=0)
        self.assertEqual(len(removed), 2)
        self.assertEqual(list_backups(self.paths), [])

    @unittest.skipIf(IS_WINDOWS, "permissões POSIX de modo")
    def test_restauracao_aplica_modo_do_manifesto(self):
        archive = create_backup(self.paths, [self.a], NOW).archive
        dest = self.root / "out_mode"
        restore_backup(archive, dest)
        restored = dest / "home" / "dir" / "a.txt"
        self.assertEqual(restored.stat().st_mode & 0o777, self.a.stat().st_mode & 0o777)


if __name__ == "__main__":
    unittest.main()
