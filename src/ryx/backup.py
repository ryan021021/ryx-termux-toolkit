"""Backup em .tar.gz com manifesto e SHA-256. A restauração só escreve dentro do destino pedido."""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tarfile
import tempfile
import zlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PurePosixPath

from ryx.paths import Paths
from ryx.permissions import inside, safe_relative

MANIFEST = "manifest.json"
MANIFEST_VERSION = 1
MEMBER_RE = re.compile(r"^files/\d+$")
NAME_RE = re.compile(r"^ryx-(\d{8}-\d{6})(?:-(\d+))?\.tar\.gz$")
CHUNK = 1024 * 1024
PRIVATE_FILE = 0o600
PRIVATE_DIR = 0o700


class BackupError(RuntimeError):
    """Backup impossível, corrompido ou inseguro; a mensagem diz o motivo."""


@dataclass(frozen=True)
class BackupResult:
    archive: Path
    files: int
    skipped: list[str] = field(default_factory=list)


class _HashingReader:
    """Repassa a leitura e calcula o SHA-256 do que de fato foi lido (uma leitura só)."""

    def __init__(self, handle) -> None:
        self._handle = handle
        self.digest = hashlib.sha256()

    def read(self, size: int = -1) -> bytes:
        chunk = self._handle.read(size)
        self.digest.update(chunk)
        return chunk


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _logical_name(path: Path, home: Path) -> str:
    """Caminho relativo e portátil para guardar no manifesto (nunca absoluto, nunca `..`, nunca `:`)."""
    resolved = path.resolve()
    try:
        prefix, parts = "home", resolved.relative_to(home.resolve()).parts
    except ValueError:
        prefix, parts = "abs", tuple(p for p in resolved.parts if p not in (resolved.anchor, ""))
    return str(PurePosixPath(prefix, *[p.replace(":", "_") for p in parts]))


def _collect(sources: list[Path]) -> tuple[list[Path], list[str]]:
    """Arquivos a salvar, sem repetir o mesmo arquivo (mesmo caminho resolvido) e sem links."""
    files: list[Path] = []
    skipped: list[str] = []
    seen: set[Path] = set()

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            files.append(path)

    for source in sources:
        if source.is_symlink():
            skipped.append(f"{source}: link simbólico")
        elif source.is_file():
            add(source)
        elif source.is_dir():
            for item in sorted(source.rglob("*")):
                if item.is_symlink():
                    skipped.append(f"{item}: link simbólico")
                elif item.is_file():
                    add(item)
        else:
            skipped.append(f"{source}: não existe")
    return files, skipped


def _reserve_archive(directory: Path, stamp: str) -> Path:
    """Cria (O_EXCL) um arquivo vazio com nome livre; dois processos nunca ganham o mesmo nome."""
    counter = 1
    while True:
        suffix = "" if counter == 1 else f"-{counter}"
        candidate = directory / f"ryx-{stamp}{suffix}.tar.gz"
        try:
            fd = os.open(candidate, os.O_CREAT | os.O_EXCL | os.O_WRONLY, PRIVATE_FILE)
        except FileExistsError:
            counter += 1
            continue
        os.close(fd)
        return candidate


def _private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=PRIVATE_DIR)
    if os.name == "posix":
        os.chmod(path, PRIVATE_DIR)


def _write_private(path: Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, PRIVATE_FILE)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    os.chmod(path, PRIVATE_FILE)


def _add_file(tar: tarfile.TarFile, file: Path, member: str, home: Path) -> dict:
    """Grava o arquivo no tar lendo uma vez só; o hash do manifesto é o do que foi gravado."""
    mode = file.stat().st_mode & 0o777
    with file.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(0)
        info = tarfile.TarInfo(member)
        info.size = size
        info.mode = mode
        reader = _HashingReader(handle)
        tar.addfile(info, reader)
    return {
        "member": member,
        "rel": _logical_name(file, home),
        "sha256": reader.digest.hexdigest(),
        "size": size,
        "mode": mode,
    }


def _write_archive(fd: int, files: list[Path], home: Path) -> None:
    with os.fdopen(fd, "wb") as raw, tarfile.open(fileobj=raw, mode="w:gz") as tar:
        entries = [_add_file(tar, file, f"files/{index}", home) for index, file in enumerate(files)]
        manifest = json.dumps({"version": MANIFEST_VERSION, "files": entries}, indent=2).encode()
        info = tarfile.TarInfo(MANIFEST)
        info.size = len(manifest)
        tar.addfile(info, io.BytesIO(manifest))


def create_backup(
    paths: Paths, sources: list[Path], now: datetime | None = None
) -> BackupResult:
    files, skipped = _collect(sources)
    if not files:
        raise BackupError("nada para salvar: nenhuma das origens tem arquivo")
    _private_dir(paths.backup_dir)
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    fd, tmp = tempfile.mkstemp(dir=paths.backup_dir, prefix=".backup-", suffix=".tmp")
    archive: Path | None = None
    try:
        _write_archive(fd, files, paths.home)
        os.chmod(tmp, PRIVATE_FILE)
        archive = _reserve_archive(paths.backup_dir, stamp)
        os.replace(tmp, archive)
        sidecar = archive.with_name(archive.name + ".sha256")
        _write_private(sidecar, f"{_sha256_file(archive)}  {archive.name}\n")
        problems = verify_backup(archive)
        if problems:
            raise BackupError("verificação final do backup falhou: " + "; ".join(problems))
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        if archive is not None:
            archive.unlink(missing_ok=True)
            archive.with_name(archive.name + ".sha256").unlink(missing_ok=True)
        raise
    return BackupResult(archive, len(files), skipped)


def _read_manifest(tar: tarfile.TarFile) -> list[dict]:
    try:
        raw = tar.extractfile(MANIFEST)
        data = json.loads(raw.read()) if raw else None
    except (KeyError, ValueError, RecursionError) as exc:
        raise BackupError("manifesto ausente ou ilegível") from exc
    if not isinstance(data, dict) or data.get("version") != MANIFEST_VERSION:
        raise BackupError("versão de manifesto desconhecida")
    entries = data.get("files")
    if not isinstance(entries, list) or not all(isinstance(e, dict) for e in entries):
        raise BackupError("manifesto sem lista de arquivos válida")
    return entries


def _member_hash(tar: tarfile.TarFile, member: str) -> str | None:
    if not MEMBER_RE.match(member):
        return None
    try:
        handle = tar.extractfile(member)
    except KeyError:
        return None
    if handle is None:
        return None
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(CHUNK), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _check_sidecar(archive: Path) -> list[str]:
    sidecar = archive.with_name(archive.name + ".sha256")
    if not sidecar.is_file():
        return ["sem arquivo .sha256 ao lado"]
    try:
        expected = sidecar.read_text(encoding="utf-8").split()[0:1]
        actual = _sha256_file(archive)
    except (OSError, ValueError) as exc:
        return [f"arquivo .sha256 ilegível: {exc}"]
    return [] if expected == [actual] else ["SHA-256 do arquivo não confere com o .sha256"]


def verify_backup(archive: Path) -> list[str]:
    """Lista de problemas; vazia significa íntegro."""
    if not archive.is_file():
        return [f"{archive.name}: arquivo não existe"]
    problems = _check_sidecar(archive)
    try:
        with tarfile.open(archive, "r:gz") as tar:
            for entry in _read_manifest(tar):
                member = str(entry.get("member", ""))
                actual = _member_hash(tar, member)
                if actual is None:
                    problems.append(f"{member}: ausente ou nome inválido")
                elif actual != entry.get("sha256"):
                    problems.append(f"{member}: conteúdo difere do manifesto")
    except (tarfile.TarError, OSError, EOFError, zlib.error, ValueError, RecursionError, BackupError) as exc:
        problems.append(f"arquivo ilegível: {exc}")
    return problems


def _entry_mode(entry: dict) -> int:
    try:
        return int(entry.get("mode", 0o600)) & 0o777
    except (TypeError, ValueError) as exc:
        raise BackupError(f"modo inválido no manifesto: {entry.get('mode')!r}") from exc


def _check_overlaps(rels: list[PurePosixPath]) -> None:
    """Dois itens não podem cair no mesmo destino nem um dentro do outro (a e a/b)."""
    exact: set[PurePosixPath] = set()
    for rel in rels:
        if rel in exact:
            raise BackupError(f"destino repetido no backup: {rel}")
        exact.add(rel)
    for rel in rels:
        for parent in rel.parents:
            if parent in exact:
                raise BackupError(f"destino aninhado em outro item do backup: {rel} dentro de {parent}")


def _plan_restore(tar: tarfile.TarFile, dest: Path) -> list[tuple[dict, Path]]:
    plan = []
    rels = []
    for entry in _read_manifest(tar):
        try:
            rel = safe_relative(str(entry["rel"]))
        except (KeyError, ValueError) as exc:
            raise BackupError(f"caminho recusado no manifesto: {exc}") from exc
        target = dest / rel
        if not inside(dest, target):
            raise BackupError(f"caminho sairia do destino: {entry['rel']}")
        _entry_mode(entry)
        plan.append((entry, target))
        rels.append(rel)
    _check_overlaps(rels)
    return plan


def restore_backup(archive: Path, dest: Path, overwrite: bool = False) -> list[Path]:
    """Restaura sob `dest`. Nada é gravado se houver problema ou conflito."""
    problems = verify_backup(archive)
    if problems:
        raise BackupError("backup não passou na verificação: " + "; ".join(problems))
    with tarfile.open(archive, "r:gz") as tar:
        plan = _plan_restore(tar, dest)
        conflicts = [str(t) for _, t in plan if t.exists()]
        if conflicts and not overwrite:
            raise BackupError("já existe (use --overwrite): " + ", ".join(conflicts))
        dest.mkdir(parents=True, exist_ok=True)
        written = []
        for entry, target in plan:
            handle = tar.extractfile(entry["member"])
            if handle is None:
                raise BackupError(f"{entry['member']}: não é arquivo")
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".restore-")
            try:
                with os.fdopen(fd, "wb") as out:
                    for chunk in iter(lambda: handle.read(CHUNK), b""):
                        out.write(chunk)
                os.chmod(tmp, _entry_mode(entry))
                os.replace(tmp, target)
            except BaseException:
                Path(tmp).unlink(missing_ok=True)
                raise
            written.append(target)
    return written


def _archive_key(path: Path) -> tuple[str, int]:
    """(carimbo, contador): o arquivo sem contador é o 1º, `-2` o 2º, `-10` o 10º do segundo."""
    match = NAME_RE.match(path.name)
    return (match.group(1), int(match.group(2) or 1)) if match else ("", 0)


def list_backups(paths: Paths) -> list[Path]:
    """Do mais antigo para o mais novo."""
    if not paths.backup_dir.is_dir():
        return []
    found = (p for p in paths.backup_dir.iterdir() if NAME_RE.match(p.name))
    return sorted(found, key=_archive_key)


def prune_backups(paths: Paths, keep: int) -> list[Path]:
    """Remove os mais antigos além de `keep` (e os .sha256 deles). Devolve o que removeu."""
    archives = list_backups(paths)
    old = archives[: max(0, len(archives) - keep)]
    for archive in old:
        archive.unlink(missing_ok=True)
        archive.with_name(archive.name + ".sha256").unlink(missing_ok=True)
    return old
