"""Backup forjado: o manifesto e o .sha256 podem estar 'certos' e o arquivo ainda ser hostil."""

import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from ryx.backup import BackupError, restore_backup, verify_backup


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def forge(
    directory: Path, entries, members, name="ryx-20260101-000000.tar.gz", manifest=None, raw_manifest=None
) -> Path:
    """Monta um .tar.gz com sidecar válido. `members` mapeia nome (ou TarInfo) -> bytes."""
    archive = directory / name
    payload = manifest if manifest is not None else {"version": 1, "files": entries}
    raw = raw_manifest if raw_manifest is not None else json.dumps(payload).encode()
    with tarfile.open(archive, "w:gz") as tar:
        info = tarfile.TarInfo("manifest.json")
        info.size = len(raw)
        tar.addfile(info, io.BytesIO(raw))
        for member, data in members.items():
            if isinstance(member, tarfile.TarInfo):
                tar.addfile(member)
                continue
            info = tarfile.TarInfo(member)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_name(archive.name + ".sha256").write_text(f"{digest}  {archive.name}\n")
    return archive


def entry(rel, data=b"conteudo", member="files/0", **extra):
    base = {"member": member, "rel": rel, "sha256": sha(data), "size": len(data), "mode": 0o600}
    return {**base, **extra}


class HostileBackupTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.dest = self.root / "dest"

    def tearDown(self):
        self._tmp.cleanup()

    def assert_nothing_outside_dest(self):
        self.assertEqual(list(self.root.rglob("evil*")), [])

    def test_caminhos_que_escapam_do_destino_sao_recusados(self):
        for rel in ("../evil", "a/../../evil", "/abs/evil", "C:/evil", "a\\..\\evil", "x\x00/evil", ".."):
            with self.subTest(rel=rel):
                archive = forge(self.root, [entry(rel)], {"files/0": b"conteudo"})
                with self.assertRaises(BackupError):
                    restore_backup(archive, self.dest)
                self.assert_nothing_outside_dest()
                archive.unlink()

    def test_conteudo_diferente_do_manifesto_e_detectado(self):
        archive = forge(self.root, [entry("home/a")], {"files/0": b"trocado!"})
        self.assertTrue(any("difere" in p for p in verify_backup(archive)))
        with self.assertRaises(BackupError):
            restore_backup(archive, self.dest)
        self.assertFalse((self.dest / "home" / "a").exists())

    def test_nome_de_membro_fora_do_padrao_e_recusado(self):
        for member in ("../evil", "files/../../evil", "/etc/passwd", "manifest.json", "files/x"):
            with self.subTest(member=member):
                archive = forge(self.root, [entry("home/a", member=member)], {"files/0": b"conteudo"})
                problems = verify_backup(archive)
                self.assertTrue(any("ausente ou nome inválido" in p for p in problems), problems)
                with self.assertRaises(BackupError):
                    restore_backup(archive, self.dest)
                archive.unlink()

    def test_membro_que_e_link_simbolico_nao_e_seguido(self):
        link = tarfile.TarInfo("files/0")
        link.type = tarfile.SYMTYPE
        link.linkname = "/etc/passwd"
        archive = forge(self.root, [entry("home/a")], {link: b""})
        problems = verify_backup(archive)
        self.assertTrue(any("files/0: ausente ou nome inválido" in p for p in problems), problems)
        with self.assertRaises(BackupError):
            restore_backup(archive, self.dest)
        self.assertFalse((self.dest / "home" / "a").exists())

    def test_manifesto_malformado_nao_vira_traceback(self):
        cases = {
            "entradas que nao sao objetos": ({"version": 1, "files": ["x", 3, None]}, "lista de arquivos válida"),
            "files nao e lista": ({"version": 1, "files": {"a": 1}}, "lista de arquivos válida"),
            "versao desconhecida": ({"version": 99, "files": []}, "versão de manifesto desconhecida"),
            "raiz nao e objeto": ([1, 2], "versão de manifesto desconhecida"),
        }
        for label, (manifest, expected) in cases.items():
            with self.subTest(label=label):
                archive = forge(self.root, [], {}, manifest=manifest)
                problems = verify_backup(archive)
                self.assertTrue(any(expected in p for p in problems), problems)
                with self.assertRaises(BackupError):
                    restore_backup(archive, self.dest)
                archive.unlink()

    def test_modo_invalido_no_manifesto_vira_erro_de_backup(self):
        archive = forge(self.root, [entry("home/a", mode="abc")], {"files/0": b"conteudo"})
        with self.assertRaises(BackupError):
            restore_backup(archive, self.dest)
        self.assertFalse((self.dest / "home" / "a").exists())

    def test_modo_nao_vira_setuid(self):
        archive = forge(self.root, [entry("home/a", mode=0o4777)], {"files/0": b"conteudo"})
        restore_backup(archive, self.dest)
        self.assertEqual((self.dest / "home" / "a").stat().st_mode & 0o7000, 0)

    def test_gzip_truncado_nao_levanta_excecao_solta(self):
        junk = self.root / "ryx-20260101-000001.tar.gz"
        junk.write_bytes(b"\x1f\x8b\x08\x00lixo")
        junk.with_name(junk.name + ".sha256").write_text(f"{sha(junk.read_bytes())}  x\n")
        problems = verify_backup(junk)
        self.assertTrue(any("arquivo ilegível" in p for p in problems), problems)
        with self.assertRaises(BackupError):
            restore_backup(junk, self.dest)

    def test_sidecar_de_outro_arquivo_e_recusado(self):
        archive = forge(self.root, [entry("home/a")], {"files/0": b"conteudo"})
        archive.with_name(archive.name + ".sha256").write_text(f"{'0' * 64}  x\n")
        self.assertTrue(any("SHA-256" in p for p in verify_backup(archive)))
        with self.assertRaises(BackupError):
            restore_backup(archive, self.dest)

    def test_manifesto_ilegivel_vira_problema_e_nao_excecao(self):
        cases = {
            "bytes que nao sao utf-8": b"{\x80\x81",
            "aninhamento absurdo": b"[" * 200_000,
            "json vazio": b"",
        }
        for label, raw in cases.items():
            with self.subTest(label=label):
                archive = forge(self.root, [], {}, raw_manifest=raw)
                problems = verify_backup(archive)
                self.assertTrue(any("manifesto ausente ou ilegível" in p for p in problems), problems)
                with self.assertRaises(BackupError):
                    restore_backup(archive, self.dest)
                archive.unlink()

    def test_sidecar_ilegivel_ou_vazio_vira_problema(self):
        archive = forge(self.root, [entry("home/a")], {"files/0": b"conteudo"})
        sidecar = archive.with_name(archive.name + ".sha256")
        for label, raw in (("nao utf-8", b"\xff\xfe\x80"), ("vazio", b"")):
            with self.subTest(label=label):
                sidecar.write_bytes(raw)
                problems = verify_backup(archive)
                self.assertTrue(any(".sha256" in p for p in problems), problems)
                with self.assertRaises(BackupError):
                    restore_backup(archive, self.dest)

    def test_targz_que_sumiu_nao_levanta_filenotfound(self):
        problems = verify_backup(self.root / "ryx-20260101-000000.tar.gz")
        self.assertTrue(any("não existe" in p for p in problems), problems)

    def test_destinos_repetidos_ou_aninhados_sao_recusados_antes_de_gravar(self):
        cases = {
            "mesmo rel duas vezes": ["home/a", "home/a"],
            "rel e prefixo dele": ["home/a", "home/a/b"],
            "prefixo vem depois": ["home/a/b", "home/a"],
            "mesmo rel com ponto": ["home/a", "home/./a"],
        }
        for label, rels in cases.items():
            with self.subTest(label=label):
                entries = [entry(rel, member=f"files/{i}") for i, rel in enumerate(rels)]
                members = {f"files/{i}": b"conteudo" for i in range(len(rels))}
                archive = forge(self.root, entries, members)
                with self.assertRaisesRegex(BackupError, "repetido|aninhado"):
                    restore_backup(archive, self.dest)
                self.assertFalse(self.dest.exists() and any(self.dest.rglob("*")))
                archive.unlink()

    def test_rel_ponto_e_dois_pontos_viram_backup_error(self):
        for rel in (".", "./", "home/C:/x", "a:b"):
            with self.subTest(rel=rel):
                archive = forge(self.root, [entry(rel)], {"files/0": b"conteudo"})
                with self.assertRaisesRegex(BackupError, "caminho recusado"):
                    restore_backup(archive, self.dest)
                archive.unlink()


if __name__ == "__main__":
    unittest.main()
