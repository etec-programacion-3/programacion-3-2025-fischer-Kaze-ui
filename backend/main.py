# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import Base, engine
from routes import router

# --- CORRECCIÓN ---
# Esta línea entra en conflicto con Alembic y causa el error de "InvalidForeignKey".
# La creación de tablas debe ser manejada ÚNICAMENTE por 'alembic upgrade head'.
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-commerce API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que React (localhost:5173) se conecte
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir todas las rutas
app.include_router(router)

# Ejecutar servidor
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)