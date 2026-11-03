"""Reset a user's password without changing their platform role."""

from getpass import getpass

from pwdlib import PasswordHash
from sqlalchemy import func

from app.database import SessionLocal
from app.models.user import User


password_hash = PasswordHash.recommended()


def main() -> None:
    email = input("Email da conta: ").strip().lower()
    if not email:
        raise SystemExit("Indique o email da conta.")

    password = getpass("Nova palavra-passe (mínimo 12 caracteres): ")
    confirmation = getpass("Confirme a nova palavra-passe: ")
    if len(password) < 12:
        raise SystemExit("A palavra-passe deve ter pelo menos 12 caracteres.")
    if password != confirmation:
        raise SystemExit("As palavras-passe não coincidem.")

    db = SessionLocal()
    try:
        user = (
            db.query(User)
            .filter(func.lower(User.email) == email)
            .with_for_update()
            .first()
        )
        if user is None:
            raise SystemExit("Não existe uma conta com esse email.")
        if not user.is_active:
            raise SystemExit("A conta está inativa; a palavra-passe não foi alterada.")

        user.password_hash = password_hash.hash(password)
        db.commit()
        print("Palavra-passe atualizada. O perfil da conta não foi alterado.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
