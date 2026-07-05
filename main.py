import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.router import auth, equipment, history, movement, school, test_auth
from database.database import engine

app = FastAPI(
    title="SIGTEC API",
    description="Sistema Integrado de Gestao do Parque Tecnologico",
    version="1.0.0",
)

frontend_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(equipment.router)
app.include_router(movement.router)
app.include_router(history.router)
app.include_router(school.router)
app.include_router(test_auth.router)


@app.get("/")
def health_check():
    return {"message": "SIGTEC API rodando"}


@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DATABASE();"))
        db_name = result.scalar()

    return {
        "message": "Conexao com MySQL funcionando",
        "database": db_name,
    }

