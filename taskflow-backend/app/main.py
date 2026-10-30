from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine
from app.routers import project_members
from app.routers.projects import router as projects_router
from app.routers.tasks import router as tasks_router
from app.routers.users import router as users_router


app = FastAPI(
    title="TaskFlow API",
    description="API para gestão de projetos e tarefas académicas",
    version="1.0.0",
)


# --------------------------------------------------
# DIRETÓRIO DE FOTOGRAFIAS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
AVATARS_DIR = UPLOADS_DIR / "avatars"

AVATARS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# --------------------------------------------------
# FICHEIROS ESTÁTICOS
# --------------------------------------------------

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR)),
    name="uploads",
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# REGISTO DOS ROUTERS
# --------------------------------------------------

app.include_router(users_router)
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(project_members.router)


# --------------------------------------------------
# PÁGINA INICIAL
# --------------------------------------------------

@app.get("/")
def inicio():
    return {
        "message": "TaskFlow API está a funcionar",
        "status": "ok",
    }


# --------------------------------------------------
# VERIFICAR API
# --------------------------------------------------

@app.get("/health")
def verificar_estado():
    return {
        "status": "ok",
        "service": "taskflow-backend",
    }


# --------------------------------------------------
# VERIFICAR BASE DE DADOS
# --------------------------------------------------

@app.get("/health/db")
def verificar_base_dados():

    try:
        with engine.connect() as connection:

            database = connection.execute(
                text("SELECT current_database()"),
            ).scalar_one()

        return {
            "status": "ok",
            "database": database,
            "service": "taskflow-backend",
        }

    except SQLAlchemyError:

        raise HTTPException(
            status_code=503,
            detail="Não foi possível ligar à base de dados.",
        )