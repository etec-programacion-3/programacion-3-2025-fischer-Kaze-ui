# ...existing code...
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# ...existing code...
from urllib.parse import quote_plus

# Preferir DATABASE_URL si está definida (ej. en .env)
_db_url = os.getenv("DATABASE_URL")
if _db_url:
    SQLALCHEMY_DATABASE_URL = _db_url
else:
    # Desglosar componentes y codificar la contraseña para evitar errores por caracteres especiales
    _user = os.getenv("POSTGRES_USER", "postgres")
    _password = os.getenv("POSTGRES_PASSWORD", "12345*")
    _host = os.getenv("POSTGRES_HOST", "localhost")
    _port = os.getenv("POSTGRES_PORT", "5432")
    _name = os.getenv("POSTGRES_DB", "electro_tech_db")
    SQLALCHEMY_DATABASE_URL = f"postgresql://{_user}:{quote_plus(_password)}@{_host}:{_port}/{_name}"
# ...existing code...

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# ...existing code...