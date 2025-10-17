# ...existing code...
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

import os
import sys
from pathlib import Path
import importlib
import pkgutil
import logging

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Asegurar que la raíz del proyecto esté en sys.path para permitir 'import backend'
# env.py está en <project>/backend/alembic/env.py -> parents[2] es la carpeta que contiene 'backend'
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Cargar .env opcionalmente
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except Exception:
    pass

# Si hay una URL de BD en variables de entorno, forzarla en la configuración de Alembic
db_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Intentar importar Base desde ubicaciones comunes
Base = None
_import_errors = []
try:
    from backend.database import Base  # paquete habitual
    Base = Base
except Exception as e:
    _import_errors.append(e)
    try:
        from database import Base  # si alembic se ejecuta dentro de backend
        Base = Base
    except Exception as e2:
        _import_errors.append(e2)

if Base is None:
    raise ImportError(
        "No se pudo importar 'Base'. Comprueba backend/database.py o la estructura de paquetes. Errores: %s"
        % (_import_errors,)
    )

# Importar dinámicamente módulos dentro de backend.models para poblar Base.metadata
try:
    # Preferimos paquete backend.models (directorio)
    models_pkg = importlib.import_module("backend.models")
    models_path = Path(models_pkg.__file__).parent if hasattr(models_pkg, "__file__") else None
    if models_path and models_path.is_dir():
        for finder, name, ispkg in pkgutil.iter_modules([str(models_path)]):
            if name.startswith("__"):
                continue
            importlib.import_module(f"backend.models.{name}")
    else:
        # Si backend.models es un único archivo (backend/models.py), ya está importado
        pass
except ModuleNotFoundError:
    # No hay paquete backend.models, intentar importar backend.models (archivo) de todos modos
    try:
        importlib.import_module("backend.models")
    except Exception:
        # si falla, no interrumpimos: puede que los modelos estén en otros módulos ya importados
        logging.getLogger("alembic.env").debug("No se encontró backend.models como paquete o módulo.")

# Si tienes modelos en otros módulos, importa aquí explícitamente (ejemplo):
# from backend.user import User  # forzar import si es necesario

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
# ...existing code...