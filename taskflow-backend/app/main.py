
from app.routers.users import router as users_router
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

app = FastAPI(
    title="TaskFlow API",
    description="API para gestão de projectos e tarefas académicas",
    version="1.0.0",
)
app.include_router(users_router)


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


@app.get("/")
def inicio():
    return {
        "message": "TaskFlow API está a funcionar",
        "status": "ok",
    }


@app.get("/health")
def verificar_estado():
    return {
        "status": "ok",
        "service": "taskflow-backend",
    }


@app.get("/health/db")
def verificar_base_dados():
    try:
        with engine.connect() as connection:
            database = connection.execute(
                text("SELECT current_database()")
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
