
"""Configuração do motor PostgreSQL e da fábrica de sessões SQLAlchemy."""

from sqlalchemy import URL, create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.settings import settings

DATABASE_URL = URL.create(
    "postgresql+psycopg",
    username=settings.db_user,
    password=settings.db_password,
    host=settings.db_host,
    port=settings.db_port,
    database=settings.db_name,
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Classe base declarativa partilhada pelos modelos da aplicação."""

    pass


def testar_ligacao():
    """Consulta a base de dados atual e a versão do servidor."""
    with engine.connect() as connection:
        resultado = connection.execute(
            text("SELECT current_database(), version()")
        )
        return resultado.fetchone()
