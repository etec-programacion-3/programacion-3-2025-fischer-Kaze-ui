# backend/main.py


from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
import uvicorn


from database import get_db, engine, Base
# --- IMPORTACIONES ACTUALIZADAS (Issue 5) ---
from models import Producto, Usuario, Carrito, ItemCarrito
from pydantic import BaseModel, Field


# Crear las tablas (si no existen) - Alembic es preferido para producción
Base.metadata.create_all(bind=engine)


app = FastAPI(title="E-commerce API", version="1.0.0")


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= SCHEMAS (Pydantic) =============


# --- Schemas de Producto (Issues 3 y 4) ---
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


# ============= SCHEMAS CARRITO (Issue 5) =============


# Schema para mostrar detalles del producto DENTRO del carrito
class ProductoEnCarritoResponse(BaseModel):
    id_producto: int
    nombre_producto: str
    precio: float
    imagen: Optional[str] = None


    class Config:
        from_attributes = True


# Schema para un ítem individual en el carrito (respuesta)
class ItemCarritoResponse(BaseModel):
    id_item_carrito: int
    id_producto: int
    cantidad: int
    producto: ProductoEnCarritoResponse # Objeto anidado con detalles del producto


    class Config:
        from_attributes = True


# Schema para la respuesta completa del carrito
class CarritoResponse(BaseModel):
    id_usuario: int # ID del dueño del carrito
    fecha_actualizacion: Optional[datetime] = None
    items: List[ItemCarritoResponse] = Field(default_factory=list)


    class Config:
        from_attributes = True


# Schema para AÑADIR un producto (POST)
class CarritoAdd(BaseModel):
    id_producto: int
    cantidad: int = Field(default=1, ge=1, description="Cantidad a AÑADIR (se suma a la existente)")


# Schema para ACTUALIZAR un producto (PUT)
class CarritoUpdate(BaseModel):
    id_producto: int
    cantidad: int = Field(..., ge=1, description="Cantidad TOTAL nueva")




# ============= DEPENDENCIAS =============


def get_current_user(x_user_id: Optional[int] = Header(None), x_user_role: Optional[str] = Header(None)):
    """
    (Temporal hasta Issue 9) Obtiene el usuario simulado desde los headers.
    Para la Issue 5, necesitamos el ID del usuario para saber qué carrito gestionar.
    """
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida. Falta el header 'X-User-ID'."
        )
   
    # Simulamos un usuario cliente con ID 2 si no se especifica rol
    role = (x_user_role or "cliente").lower()
   
    return {"id_usuario": x_user_id, "tipo_usuario": role}


def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Verifica que el usuario tenga rol de administrador.
    """
    if current_user.get("tipo_usuario") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de administrador (ADMIN)."
        )
    return current_user


# ============= ENDPOINTS DE PRODUCTOS (Issues 3 y 4) =============


@app.get("/")
def root():
    return {"message": "E-commerce API - Gestión de Productos y Carrito"}


# GET /api/products
@app.get("/api/products", response_model=List[ProductoResponse])
def get_productos(
    page: int = 1, limit: int = 10,
    search: Optional[str] = None,
    category: Optional[str] = None,
    marca: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    db: Session = Depends(get_db)
):
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
   
    skip = (page - 1) * limit
    productos = query.offset(skip).limit(limit).all()
    return productos


# GET /api/products/count
@app.get("/api/products/count")
def get_productos_count(
    search: Optional[str] = None, category: Optional[str] = None,
    marca: Optional[str] = None, precio_min: Optional[float] = None,
    precio_max: Optional[float] = None, db: Session = Depends(get_db)
):
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


# GET /api/products/:id
@app.get("/api/products/{id_producto}", response_model=ProductoResponse)
def get_producto(id_producto: int, db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return producto


# POST /api/products (Admin)
@app.post("/api/products", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
def create_producto(
    producto: ProductoCreate, db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    db_producto = Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto


# PUT /api/products/:id (Admin)
@app.put("/api/products/{id_producto}", response_model=ProductoResponse)
def update_producto(
    id_producto: int, producto: ProductoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    db_producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not db_producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
   
    for key, value in producto.model_dump().items():
        setattr(db_producto, key, value)
   
    db.commit()
    db.refresh(db_producto)
    return db_producto


# DELETE /api/products/:id (Admin)
@app.delete("/api/products/{id_producto}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(
    id_producto: int, db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    db_producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not db_producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
   
    db.delete(db_producto)
    db.commit()
    return None


# =====================================================================
# ENDPOINTS DE CARRITO (Issue 5)
# =====================================================================


def get_or_create_cart(db: Session, user_id: int) -> Carrito:
    """Función auxiliar: Obtiene el carrito del usuario o crea uno nuevo si no existe."""
    # Usamos .options(joinedload(...)) para optimizar y cargar las relaciones
    # (ítems y los productos de esos ítems) en la misma consulta.
    carrito = db.query(Carrito).options(
        joinedload(Carrito.items).joinedload(ItemCarrito.producto)
    ).filter(Carrito.id_usuario == user_id).first()
   
    if not carrito:
        # Verifica que el usuario exista antes de crear un carrito
        usuario = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        if not usuario:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")


        # Crea el carrito nuevo
        carrito = Carrito(id_usuario=user_id, items=[]) # Inicializa items como lista vacía
        db.add(carrito)
        db.commit()
        db.refresh(carrito) # Refresca para obtener el estado de la DB
       
    return carrito


# GET /api/cart - Ver el contenido del carrito
@app.get("/api/cart", response_model=CarritoResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene el contenido completo del carrito del usuario autenticado.
    Si el carrito no existe, lo crea y lo devuelve vacío.
    """
    user_id = current_user["id_usuario"]
    carrito = get_or_create_cart(db, user_id)
    return carrito


# POST /api/cart/add - Agregar producto al carrito
@app.post("/api/cart/add", response_model=CarritoResponse)
def add_to_cart(
    item_data: CarritoAdd,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Agrega un producto al carrito. Si el producto ya existe, incrementa la cantidad.
    Verifica el stock disponible.
    """
    user_id = current_user["id_usuario"]
    producto_id = item_data.id_producto
    cantidad_a_agregar = item_data.cantidad
   
    # 1. Obtener el carrito (y sus ítems cargados)
    carrito = get_or_create_cart(db, user_id)
   
    # 2. Verificar el producto y stock
    producto = db.query(Producto).filter(Producto.id_producto == producto_id).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
   
    # 3. Buscar si el ítem ya está en el carrito
    item_existente = None
    for item in carrito.items:
        if item.id_producto == producto_id:
            item_existente = item
            break
           
    if item_existente:
        # 3a. Si existe, actualizar cantidad y verificar stock
        cantidad_nueva_total = item_existente.cantidad + cantidad_a_agregar
        if producto.stock < cantidad_nueva_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Stock disponible: {producto.stock}. (En carrito: {item_existente.cantidad})"
            )
        item_existente.cantidad = cantidad_nueva_total
    else:
        # 3b. Si no existe, verificar stock y crearlo
        if producto.stock < cantidad_a_agregar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Stock disponible: {producto.stock}."
            )
       
        nuevo_item = ItemCarrito(
            id_carrito=carrito.id_carrito,
            id_producto=producto_id,
            cantidad=cantidad_a_agregar
        )
        db.add(nuevo_item)
        carrito.items.append(nuevo_item)
   
    # Actualiza la fecha del carrito
    carrito.fecha_actualizacion = datetime.utcnow()
   
    db.commit()
    # Refrescamos el carrito completo (con relaciones) para la respuesta
    db.refresh(carrito)
   
    # Volvemos a cargar con las relaciones para la respuesta
    carrito_respuesta = get_or_create_cart(db, user_id)
   
    return carrito_respuesta


# PUT /api/cart/update - Actualizar cantidad de un ítem
@app.put("/api/cart/update", response_model=CarritoResponse)
def update_cart_item(
    item_data: CarritoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza la cantidad TOTAL de un producto en el carrito.
    Verifica el stock.
    """
    user_id = current_user["id_usuario"]
    producto_id = item_data.id_producto
    cantidad_nueva = item_data.cantidad # Esta es la cantidad TOTAL
   
    carrito = get_or_create_cart(db, user_id)
   
    # 1. Verificar producto y stock
    producto = db.query(Producto).filter(Producto.id_producto == producto_id).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
   
    if producto.stock < cantidad_nueva:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Stock disponible: {producto.stock}."
        )


    # 2. Buscar el ítem
    item_existente = db.query(ItemCarrito).filter(
        ItemCarrito.id_carrito == carrito.id_carrito,
        ItemCarrito.id_producto == producto_id
    ).first()
   
    if not item_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito.")
       
    # 3. Actualizar cantidad
    item_existente.cantidad = cantidad_nueva
    carrito.fecha_actualizacion = datetime.utcnow()
   
    db.commit()
   
    # Volvemos a cargar con las relaciones para la respuesta
    carrito_respuesta = get_or_create_cart(db, user_id)
    return carrito_respuesta


# DELETE /api/cart/remove/:id_producto - Eliminar un ítem del carrito
@app.delete("/api/cart/remove/{id_producto}", response_model=CarritoResponse)
def remove_from_cart(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina un producto (un ítem completo) del carrito del usuario.
    """
    user_id = current_user["id_usuario"]
   
    carrito = get_or_create_cart(db, user_id)


    # 1. Buscar el ítem
    item_a_eliminar = db.query(ItemCarrito).filter(
        ItemCarrito.id_carrito == carrito.id_carrito,
        ItemCarrito.id_producto == id_producto
    ).first()
   
    if not item_a_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito.")
       
    # 2. Eliminar el ítem
    db.delete(item_a_eliminar)
    carrito.fecha_actualizacion = datetime.utcnow()
   
    db.commit()


    # Volvemos a cargar con las relaciones para la respuesta
    carrito_respuesta = get_or_create_cart(db, user_id)
    return carrito_respuesta


# ============= EJECUTAR SERVIDOR =============


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

