from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn


from database import get_db, engine, Base
from models import Producto, Usuario
from pydantic import BaseModel, Field

# Crear las tablas (si no existen)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-commerce API", version="1.0.0")

# Configurar CORS (para que React pueda conectarse después)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= SCHEMAS (Pydantic) =============

class ProductoBase(BaseModel):
    nombre_producto: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = None
    marca: str = Field(..., min_length=1, max_length=100)
    categoria: str = Field(..., min_length=1, max_length=50)
    precio: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    imagen: Optional[str] = None

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(ProductoBase):
    pass

class ProductoResponse(ProductoBase):
    id_producto: int
    
    class Config:
        from_attributes = True

# ============= DEPENDENCIAS =============

# Simulación básica de autenticación (TEMPORAL)
# En issues futuras implementarás JWT real
def get_current_user(user_type: Optional[str] = None):
    """
    Dependencia temporal para simular roles.
    Parámetros: user_type puede ser "admin" o None (usuario normal)
    """
    def dependency():
        # TEMPORAL: Retorna un usuario simulado
        # En issues futuras esto vendrá del token JWT
        if user_type == "admin":
            return {"tipo_usuario": "admin", "id_usuario": 1}
        return {"tipo_usuario": "cliente", "id_usuario": 2}
    return dependency

def require_admin(current_user: dict = Depends(get_current_user())):
    """Verifica que el usuario sea administrador"""
    if current_user.get("tipo_usuario") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return current_user

# ============= ENDPOINTS =============

@app.get("/")
def root():
    return {"message": "E-commerce API - Gestión de Productos"}

# GET /api/products - Obtener todos los productos (público)
@app.get("/api/products", response_model=List[ProductoResponse])
def get_productos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Obtener lista de productos - Acceso público"""
    productos = db.query(Producto).offset(skip).limit(limit).all()
    return productos

# GET /api/products/:id - Obtener un producto específico (público)
@app.get("/api/products/{id_producto}", response_model=ProductoResponse)
def get_producto(
    id_producto: int,
    db: Session = Depends(get_db)
):
    """Obtener un producto por ID - Acceso público"""
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return producto

# POST /api/products - Crear producto (solo ADMIN)
@app.post("/api/products", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def create_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Crear un nuevo producto - Solo administradores"""
    db_producto = Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

# PUT /api/products/:id - Actualizar producto (solo ADMIN)
@app.put("/api/products/{id_producto}", response_model=ProductoResponse)
def update_producto(
    id_producto: int,
    producto: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Actualizar un producto - Solo administradores"""
    db_producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    for key, value in producto.model_dump().items():
        setattr(db_producto, key, value)
    
    db.commit()
    db.refresh(db_producto)
    return db_producto

# DELETE /api/products/:id - Eliminar producto (solo ADMIN)
@app.delete("/api/products/{id_producto}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Eliminar un producto - Solo administradores"""
    db_producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    db.delete(db_producto)
    db.commit()
    return None

# ============= EJECUTAR SERVIDOR =============

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)