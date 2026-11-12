import io
import tarfile
from pathlib import Path

import pytest

from scripts.restore import _extract_validated


def make_archive(path: Path, member_name: str, content: bytes = b"backup") -> None:
    with tarfile.open(path, "w:gz") as archive:
        info = tarfile.TarInfo(member_name)
        info.size = len(content)
        archive.addfile(info, io.BytesIO(content))


def test_restore_extracts_regular_file(tmp_path: Path) -> None:
    archive_path = tmp_path / "backup.tar.gz"
    destination = tmp_path / "extracted"
    destination.mkdir()
    make_archive(archive_path, "database.dump")

    _extract_validated(archive_path, destination)

    assert (destination / "database.dump").read_bytes() == b"backup"


def test_restore_rejects_path_traversal(tmp_path: Path) -> None:
    archive_path = tmp_path / "malicious.tar.gz"
    destination = tmp_path / "extracted"
    destination.mkdir()
    make_archive(archive_path, "../outside.txt")

    with pytest.raises(ValueError, match="caminhos de extração inválidos"):
        _extract_validated(archive_path, destination)

    assert not (tmp_path / "outside.txt").exists()
