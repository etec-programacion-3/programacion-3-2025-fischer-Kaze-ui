from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# Cargar variables de entorno (Sin valores por defecto para credenciales)
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Validar que las variables esenciales estén presentes
if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
    raise EnvironmentError("Faltan variables de entorno críticas (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB) en el archivo .env")

# Codificar la contraseña para la URL
encoded_password = quote_plus(POSTGRES_PASSWORD)
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()