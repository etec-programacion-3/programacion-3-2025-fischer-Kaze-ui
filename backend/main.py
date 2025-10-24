from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn

from database import get_db, engine, Base
from models import Producto, Usuario, Carrito
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
# ============= SCHEMAS CARRITO =============-(EN DUDA, REVISAR SI SE DEBE MOVER A OTRO LADO)

class CarritoAdd(BaseModel):
    id_producto: int
    cantidad: int = Field(default=1, ge=1)

class CarritoUpdate(BaseModel):
    cantidad: int = Field(..., ge=1)

class CarritoItemResponse(BaseModel):
    id_carrito: int
    id_producto: int
    cantidad: int
    producto: ProductoResponse
    
    class Config:
        from_attributes = True

def get_current_user(x_user_role: Optional[str] = Header(None)):
    """
    Obtiene el rol del usuario desde el header X-User-Role.
    
    IMPLEMENTACIÓN DE RESTRICCIÓN POR ROLES:
    - Lee el header HTTP 'X-User-Role' de cada request
    - Si es "admin", retorna un usuario con permisos de administrador
    - Si no existe o es otro valor, retorna un usuario cliente normal
    
    TEMPORAL: En issues futuras esto será reemplazado por JWT tokens.
    """
    if x_user_role == "admin":
        return {"tipo_usuario": "admin", "id_usuario": 1}
    return {"tipo_usuario": "cliente", "id_usuario": 2}

def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Verifica que el usuario tenga rol de administrador.
    
    Esta función se usa como dependencia en endpoints protegidos.
    Si el usuario NO es admin, lanza una excepción HTTP 403 Forbidden.
    """
    if current_user.get("tipo_usuario") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de administrador (ADMIN)."
        )
    return current_user

# ============= ENDPOINTS =============

@app.get("/")
def root():
    return {"message": "E-commerce API - Gestión de Productos"}

# GET /api/products - Obtener productos con paginación, búsqueda y filtros (público)
@app.get("/api/products", response_model=List[ProductoResponse])
def get_productos(
    # Paginación
    page: int = 1,
    limit: int = 10,
    # Búsqueda por texto
    search: Optional[str] = None,
    # Filtros
    category: Optional[str] = None,
    marca: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    # Base de datos
    db: Session = Depends(get_db)
):
    """
    Obtener lista de productos con funcionalidades avanzadas - Acceso público.
    
    PAGINACIÓN:
    - page: número de página (default: 1)
    - limit: productos por página (default: 10)
    
    BÚSQUEDA:
    - search: busca en nombre y descripción del producto
    
    FILTROS:
    - category: filtra por categoría exacta
    - marca: filtra por marca exacta
    - precio_min: precio mínimo
    - precio_max: precio máximo
    
    OPTIMIZACIÓN:
    - Todas las operaciones se hacen EN LA BASE DE DATOS usando SQLAlchemy
    - NO se traen todos los registros a memoria
    - Se usa .filter() para aplicar condiciones SQL
    - Se usa .offset() y .limit() para paginación eficiente
    """
    
    # Iniciar query base
    query = db.query(Producto)
    
    # FILTRADO EN BASE DE DATOS (eficiente)
    # Cada .filter() agrega una cláusula WHERE al SQL
    
    if search:
        # Búsqueda por texto en nombre o descripción
        # ilike = case-insensitive LIKE en SQL
        search_pattern = f"%{search}%"
        query = query.filter(
            (Producto.nombre_producto.ilike(search_pattern)) |
            (Producto.descripcion.ilike(search_pattern))
        )
    
    if category:
        # Filtrar por categoría exacta
        query = query.filter(Producto.categoria == category)
    
    if marca:
        # Filtrar por marca exacta
        query = query.filter(Producto.marca == marca)
    
    if precio_min is not None:
        # Filtrar por precio mínimo
        query = query.filter(Producto.precio >= precio_min)
    
    if precio_max is not None:
        # Filtrar por precio máximo
        query = query.filter(Producto.precio <= precio_max)
    
    # PAGINACIÓN EN BASE DE DATOS (eficiente)
    # Calcular offset basado en la página
    skip = (page - 1) * limit
    
    # Aplicar paginación con LIMIT y OFFSET en SQL
    query = query.offset(skip).limit(limit)
    
    # Ejecutar query y retornar resultados
    # Solo en este punto se ejecuta el SQL y se traen los datos
    productos = query.all()
    
    return productos

# GET /api/products/count - Obtener total de productos (para paginación)
@app.get("/api/products/count")
def get_productos_count(
    search: Optional[str] = None,
    category: Optional[str] = None,
    marca: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """
    Obtener el total de productos que coinciden con los filtros.
    Útil para calcular el total de páginas en el frontend.
    """
    query = db.query(Producto)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Producto.nombre_producto.ilike(search_pattern)) |
            (Producto.descripcion.ilike(search_pattern))
        )
    
    if category:
        query = query.filter(Producto.categoria == category)
    
    if marca:
        query = query.filter(Producto.marca == marca)
    
    if precio_min is not None:
        query = query.filter(Producto.precio >= precio_min)
    
    if precio_max is not None:
        query = query.filter(Producto.precio <= precio_max)
    
    total = query.count()
    
    return {"total": total}

# GET /api/products/:id - Obtener un producto específico (público)
@app.get("/api/products/{id_producto}", response_model=ProductoResponse)
def get_producto(
    id_producto: int,
    db: Session = Depends(get_db)
):
    """Obtener un producto por ID - Acceso público (sin autenticación)"""
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
    """
    Crear un nuevo producto - Solo administradores.
    
    Requiere header: X-User-Role: admin
    """
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
    """
    Actualizar un producto - Solo administradores.
    
    Requiere header: X-User-Role: admin
    """
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
    """
    Eliminar un producto - Solo administradores.
    
    Requiere header: X-User-Role: admin
    """
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