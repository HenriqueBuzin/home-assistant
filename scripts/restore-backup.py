#!/usr/bin/env python3

from __future__ import annotations

import shutil
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


SUPPORTED_SUFFIXES = (".tar", ".tar.gz", ".tgz")
OFFICIAL_CORE_ARCHIVES = ("homeassistant.tar", "homeassistant.tar.gz")


def normalized_parts(name: str) -> tuple[str, ...]:
    path = PurePosixPath(name)
    parts = tuple(part for part in path.parts if part not in ("", "."))
    if path.is_absolute() or ".." in parts:
        raise ValueError(f"Caminho inseguro no backup: {name}")
    return parts


def config_prefix(members: list[tarfile.TarInfo]) -> tuple[str, ...]:
    prefixes: set[tuple[str, ...]] = set()
    for member in members:
        parts = normalized_parts(member.name)
        if not parts:
            continue
        if parts[-1] == "configuration.yaml":
            prefixes.add(parts[:-1])
        if ".storage" in parts:
            prefixes.add(parts[: parts.index(".storage")])

    if not prefixes:
        raise ValueError("Backup não contém configuration.yaml nem .storage.")

    shortest = min(prefixes, key=len)
    if any(prefix[: len(shortest)] != shortest for prefix in prefixes):
        raise ValueError("Backup contém mais de uma raiz de configuração.")
    return shortest


def extract_config(archive: tarfile.TarFile, destination: Path) -> None:
    members = archive.getmembers()
    prefix = config_prefix(members)
    extracted = 0

    for member in members:
        parts = normalized_parts(member.name)
        if parts[: len(prefix)] != prefix:
            continue
        relative_parts = parts[len(prefix) :]
        if not relative_parts:
            continue
        if member.issym() or member.islnk() or member.isdev():
            raise ValueError(f"Tipo de arquivo não permitido no backup: {member.name}")

        target = destination.joinpath(*relative_parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if not member.isfile():
            continue

        source = archive.extractfile(member)
        if source is None:
            raise ValueError(f"Não foi possível ler {member.name}.")
        with source, target.open("wb") as output:
            shutil.copyfileobj(source, output)
        target.chmod(member.mode & 0o777)
        extracted += 1

    if extracted == 0:
        raise ValueError("Backup não contém arquivos de configuração restauráveis.")


def restore_archive(backup: Path, staging: Path) -> None:
    try:
        with tarfile.open(backup, "r:*") as outer:
            core_members = [
                member
                for member in outer.getmembers()
                if member.isfile() and PurePosixPath(member.name).name in OFFICIAL_CORE_ARCHIVES
            ]
            if len(core_members) > 1:
                raise ValueError("Backup oficial contém mais de um arquivo do Home Assistant.")
            if not core_members:
                extract_config(outer, staging)
                return

            core_member = core_members[0]
            source = outer.extractfile(core_member)
            if source is None:
                raise ValueError("Não foi possível ler o conteúdo do Home Assistant no backup.")
            suffix = ".tar.gz" if core_member.name.endswith(".gz") else ".tar"
            inner_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as inner_file:
                    inner_path = Path(inner_file.name)
                    with source:
                        shutil.copyfileobj(source, inner_file)
                with tarfile.open(inner_path, "r:*") as inner:
                    extract_config(inner, staging)
            finally:
                if inner_path is not None:
                    inner_path.unlink(missing_ok=True)
    except tarfile.ReadError as error:
        raise ValueError(
            "Backup ilegível ou criptografado. Baixe-o descriptografado pela interface do Home Assistant."
        ) from error


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: restore-backup.py RESTORE_DIR CONFIG_DIR", file=sys.stderr)
        return 2

    restore_dir = Path(sys.argv[1])
    config_dir = Path(sys.argv[2])
    restore_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    if any(config_dir.iterdir()):
        print("Configuração existente; restauração automática ignorada.")
        return 0

    backups = sorted(
        path
        for path in restore_dir.iterdir()
        if path.is_file() and path.name.lower().endswith(SUPPORTED_SUFFIXES)
    )
    if not backups:
        print("Configuração vazia e nenhum backup encontrado; iniciando instalação nova.")
        return 0
    if len(backups) != 1:
        print("Mantenha exatamente um arquivo .tar, .tar.gz ou .tgz na pasta de restauração.", file=sys.stderr)
        return 1

    backup = backups[0]
    try:
        with tempfile.TemporaryDirectory(prefix="ha-restore-") as temporary:
            staging = Path(temporary) / "config"
            staging.mkdir()
            restore_archive(backup, staging)
            if not ((staging / "configuration.yaml").is_file() or (staging / ".storage").is_dir()):
                raise ValueError("A configuração restaurada não contém configuration.yaml nem .storage.")
            shutil.copytree(staging, config_dir, dirs_exist_ok=True)
    except (OSError, ValueError) as error:
        print(f"Falha ao restaurar {backup.name}: {error}", file=sys.stderr)
        return 1

    print(f"Backup restaurado automaticamente: {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
