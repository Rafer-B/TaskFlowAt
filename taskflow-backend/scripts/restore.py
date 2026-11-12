"""Restaura um backup após confirmação explícita da base de destino."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

from app.settings import settings


def _extract_validated(archive_path: Path, destination: Path) -> None:
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            path = Path(member.name)
            if (
                path.is_absolute()
                or ".." in path.parts
                or not (member.isfile() or member.isdir())
            ):
                raise ValueError("O arquivo contém caminhos de extração inválidos.")
            member.mode &= 0o777
        archive.extractall(destination, members=members)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Backup .tar.gz a restaurar")
    parser.add_argument(
        "--confirm-database",
        required=True,
        help="Nome exato da base de dados que será substituída",
    )
    parser.add_argument(
        "--restore-uploads",
        action="store_true",
        help="Também repõe os diretórios de uploads e anexos",
    )
    args = parser.parse_args()

    if args.confirm_database != settings.db_name:
        parser.error(
            f"A confirmação tem de corresponder à base configurada "
            f"({settings.db_name})."
        )
    if not args.archive.is_file():
        parser.error("O ficheiro de backup não existe.")
    pg_restore = shutil.which("pg_restore")
    if pg_restore is None:
        print(
            "pg_restore não foi encontrado. Instala os utilitários de cliente "
            "PostgreSQL e tenta novamente.",
            file=sys.stderr,
        )
        return 1

    with tempfile.TemporaryDirectory(prefix="taskflow-restore-") as temporary:
        work_dir = Path(temporary)
        _extract_validated(args.archive, work_dir)
        dump_path = work_dir / "database.dump"
        if not dump_path.is_file():
            raise ValueError("O backup não contém database.dump.")
        environment = os.environ.copy()
        environment["PGPASSWORD"] = settings.db_password
        subprocess.run(
            [
                pg_restore,
                "--single-transaction",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--dbname",
                (
                    f"host={settings.db_host} port={settings.db_port} "
                    f"dbname={settings.db_name} user={settings.db_user}"
                ),
                str(dump_path),
            ],
            env=environment,
            check=True,
        )

        if args.restore_uploads:
            for archive_name, target in (
                ("uploads.tar.gz", settings.uploads_dir),
                ("task-attachments.tar.gz", settings.task_attachments_dir),
            ):
                archive_path = work_dir / archive_name
                if archive_path.is_file():
                    extracted = work_dir / archive_name.removesuffix(".tar.gz")
                    extracted.mkdir()
                    _extract_validated(archive_path, extracted)
                    source = extracted / target.name
                    if source.exists():
                        shutil.copytree(source, target, dirs_exist_ok=True)

    print(
        f"Base {settings.db_name} restaurada. "
        "Reinicia a API antes de a voltar a utilizar."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
