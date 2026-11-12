"""Cria um backup local consistente do PostgreSQL e dos ficheiros enviados."""

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

from app.settings import settings


def _archive_directory(source: Path, destination: Path) -> None:
    with tarfile.open(destination, "w:gz") as archive:
        if source.exists():
            archive.add(source, arcname=source.name, recursive=True)


def main() -> int:
    pg_dump = shutil.which("pg_dump")
    if pg_dump is None:
        print(
            "pg_dump não foi encontrado. Instala os utilitários de cliente "
            "PostgreSQL e tenta novamente.",
            file=sys.stderr,
        )
        return 1

    settings.backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(settings.backup_dir, 0o700)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    final_path = settings.backup_dir / f"taskflow-backup-{timestamp}.tar.gz"

    with tempfile.TemporaryDirectory(
        prefix=".taskflow-backup-",
        dir=settings.backup_dir,
    ) as temporary:
        work_dir = Path(temporary)
        dump_path = work_dir / "database.dump"
        environment = os.environ.copy()
        environment["PGPASSWORD"] = settings.db_password
        subprocess.run(
            [
                pg_dump,
                "--format=custom",
                "--no-owner",
                "--host",
                settings.db_host,
                "--port",
                str(settings.db_port),
                "--username",
                settings.db_user,
                "--dbname",
                settings.db_name,
                "--file",
                str(dump_path),
            ],
            env=environment,
            check=True,
        )
        _archive_directory(settings.uploads_dir, work_dir / "uploads.tar.gz")
        _archive_directory(
            settings.task_attachments_dir,
            work_dir / "task-attachments.tar.gz",
        )
        archive_path = work_dir / "backup.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            for name in ("database.dump", "uploads.tar.gz", "task-attachments.tar.gz"):
                archive.add(work_dir / name, arcname=name)
        os.replace(archive_path, final_path)

    os.chmod(final_path, 0o600)
    cutoff = datetime.now(timezone.utc) - timedelta(
        days=settings.backup_retention_days,
    )
    for candidate in settings.backup_dir.glob("taskflow-backup-*.tar.gz"):
        if candidate == final_path or not candidate.is_file():
            continue
        if datetime.fromtimestamp(candidate.stat().st_mtime, timezone.utc) < cutoff:
            candidate.unlink()

    print(f"Backup criado: {final_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
