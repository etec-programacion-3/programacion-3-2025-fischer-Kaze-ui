# backend/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# --- Configuración de SQLite ---
# Usaremos un archivo de base de datos llamado 'sql_app.db' 
# que se creará dentro de la carpeta 'backend/'
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # 'connect_args' es necesario solo para SQLite
    # para permitir que sea usado por múltiples hilos (como FastAPI)
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()