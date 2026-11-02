import os
from getpass import getpass

from pwdlib import PasswordHash
from sqlalchemy import func

from app.database import SessionLocal
from app.models.user import User

password_hash = PasswordHash.recommended()


def main() -> None:
    email = os.getenv("TASKFLOW_INITIAL_ADMIN_EMAIL", "").strip().lower()
    if not email:
        raise SystemExit(
            "Define TASKFLOW_INITIAL_ADMIN_EMAIL no .env antes de promover "
            "o primeiro administrador."
        )

    db = SessionLocal()
    try:
        user = db.query(User).filter(func.lower(User.email) == email).first()
        if user is None:
            name = input("Nome do primeiro administrador: ").strip()
            password = getpass("Palavra-passe (mínimo 8 caracteres): ")
            confirmation = getpass("Confirme a palavra-passe: ")
            if len(name) < 2:
                raise SystemExit("O nome deve ter pelo menos 2 caracteres.")
            if len(password) < 8:
                raise SystemExit("A palavra-passe deve ter pelo menos 8 caracteres.")
            if password != confirmation:
                raise SystemExit("As palavras-passe não coincidem.")

            user = User(
                name=name,
                email=email,
                password_hash=password_hash.hash(password),
                role="admin",
            )
            db.add(user)
        elif not user.is_active:
            raise SystemExit("Não é possível promover um utilizador inativo.")
        else:
            user.role = "admin"
        db.commit()
        print(f"Permissão de administrador atribuída a {user.email}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
