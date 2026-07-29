#!/usr/bin/env python3

from __future__ import annotations

import io
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("restore-backup.py")


def add_text(archive: tarfile.TarFile, name: str, value: str) -> None:
    content = value.encode()
    member = tarfile.TarInfo(name)
    member.size = len(content)
    member.mode = 0o600
    archive.addfile(member, io.BytesIO(content))


class RestoreBackupTest(unittest.TestCase):
    def run_restore(self, restore_dir: Path, config_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(restore_dir), str(config_dir)],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_restores_direct_config_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            restore_dir = root / "restore"
            config_dir = root / "config"
            restore_dir.mkdir()
            with tarfile.open(restore_dir / "config.tar.gz", "w:gz") as archive:
                add_text(archive, "configuration.yaml", "default_config:\n")
                add_text(archive, ".storage/core.config", "{}")

            result = self.run_restore(restore_dir, config_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((config_dir / "configuration.yaml").read_text(), "default_config:\n")
            self.assertIn("restaurado automaticamente", result.stdout)

    def test_restores_official_homeassistant_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            restore_dir = root / "restore"
            config_dir = root / "config"
            restore_dir.mkdir()
            inner_path = root / "homeassistant.tar.gz"
            with tarfile.open(inner_path, "w:gz") as inner:
                add_text(inner, "data/configuration.yaml", "default_config:\n")
                add_text(inner, "data/.storage/core.config", "{}")
            with tarfile.open(restore_dir / "official.tar", "w") as outer:
                outer.add(inner_path, arcname="./homeassistant.tar.gz")

            result = self.run_restore(restore_dir, config_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((config_dir / ".storage" / "core.config").is_file())

    def test_does_not_overwrite_existing_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            restore_dir = root / "restore"
            config_dir = root / "config"
            restore_dir.mkdir()
            config_dir.mkdir()
            existing = config_dir / "configuration.yaml"
            existing.write_text("existing: true\n")
            with tarfile.open(restore_dir / "config.tar", "w") as archive:
                add_text(archive, "configuration.yaml", "replacement: true\n")

            result = self.run_restore(restore_dir, config_dir)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(existing.read_text(), "existing: true\n")

    def test_rejects_multiple_backups(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            restore_dir = root / "restore"
            config_dir = root / "config"
            restore_dir.mkdir()
            for name in ("one.tar", "two.tar"):
                with tarfile.open(restore_dir / name, "w") as archive:
                    add_text(archive, "configuration.yaml", "default_config:\n")

            result = self.run_restore(restore_dir, config_dir)

            self.assertEqual(result.returncode, 1)
            self.assertIn("exatamente um arquivo", result.stderr)
            self.assertFalse(config_dir.joinpath("configuration.yaml").exists())

    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            restore_dir = root / "restore"
            config_dir = root / "config"
            restore_dir.mkdir()
            with tarfile.open(restore_dir / "unsafe.tar", "w") as archive:
                add_text(archive, "configuration.yaml", "default_config:\n")
                add_text(archive, "../outside.txt", "unsafe")

            result = self.run_restore(restore_dir, config_dir)

            self.assertEqual(result.returncode, 1)
            self.assertFalse(root.joinpath("outside.txt").exists())


if __name__ == "__main__":
    unittest.main()
