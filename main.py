from fastapi import FastAPI
from sqlalchemy import text
from database.database import engine
from app.router import auth, equipment, history, movement, test_auth

app = FastAPI(
    title="SIGTEC API",
    description="Sistema Integrado de Gestão do Parque Tecnológico",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(equipment.router)
app.include_router(movement.router)
app.include_router(history.router)
app.include_router(test_auth.router)


@app.get("/")
def health_check():
    return {"message": "SIGTEC API rodando 🚀"}


@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT DATABASE();"))
        db_name = result.scalar()

    return {
        "message": "Conexão com MySQL funcionando",
        "database": db_name
    }
