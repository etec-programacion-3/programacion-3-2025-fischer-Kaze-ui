# backend/main.py

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
import uvicorn

from database import get_db, engine, Base
# --- IMPORTACIONES ACTUALIZADAS (Issue 6) ---
from models import Producto, Usuario, Carrito, ItemCarrito, Pedido, ItemPedido
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


# ============= SCHEMAS PEDIDOS (Issue 6) =============

class ItemPedidoResponse(BaseModel):
    """ Muestra un item específico dentro de un pedido """
    id_producto: int
    cantidad: int
    precio_unitario: float
    subtotal: float
    producto: ProductoEnCarritoResponse # Reutilizamos el schema del producto

    class Config:
        from_attributes = True

class PedidoResponse(BaseModel):
    """ Muestra el pedido completo con sus items """
    id_pedido: int
    id_usuario: int
    fecha_pedido: datetime
    total: float
    estado: str
    items: List[ItemPedidoResponse]

    class Config:
        from_attributes = True


# ============= DEPENDENCIAS =============

def get_current_user(x_user_id: Optional[int] = Header(None), x_user_role: Optional[str] = Header(None)):
    """
    (Temporal hasta Issue 9) Obtiene el usuario simulado desde los headers.
    """
    if x_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida. Falta el header 'X-User-ID'."
        )
    
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
    return {"message": "E-commerce API - Gestión de Productos, Carrito y Pedidos"}

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
    # (Lógica de filtros repetida para el conteo)
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
    """
    Función auxiliar: Obtiene el carrito del usuario o crea uno nuevo si no existe.
    CORREGIDO: Asegura que las relaciones (items) se carguen inmediatamente después de la creación.
    """
    carrito = db.query(Carrito).options(
        joinedload(Carrito.items).joinedload(ItemCarrito.producto)
    ).filter(Carrito.id_usuario == user_id).first()
    
    if not carrito:
        usuario = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        if not usuario:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

        carrito = Carrito(id_usuario=user_id, items=[]) 
        db.add(carrito)
        db.commit()
        db.refresh(carrito) 

        # OBLIGATORIO: Recargar el carrito con las relaciones si es nuevo
        carrito = db.query(Carrito).options(
            joinedload(Carrito.items).joinedload(ItemCarrito.producto)
        ).filter(Carrito.id_usuario == user_id).first()
        
    return carrito

# GET /api/cart - Ver el contenido del carrito
@app.get("/api/cart", response_model=CarritoResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
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
    user_id = current_user["id_usuario"]
    producto_id = item_data.id_producto
    cantidad_a_agregar = item_data.cantidad
    
    carrito = get_or_create_cart(db, user_id)
    
    producto = db.query(Producto).filter(Producto.id_producto == producto_id).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    
    item_existente = None
    for item in carrito.items:
        if item.id_producto == producto_id:
            item_existente = item
            break
            
    if item_existente:
        cantidad_nueva_total = item_existente.cantidad + cantidad_a_agregar
        if producto.stock < cantidad_nueva_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Stock disponible: {producto.stock}. (En carrito: {item_existente.cantidad})"
            )
        item_existente.cantidad = cantidad_nueva_total
    else:
        if producto.stock < cantidad_a_agregar:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Stock disponible: {producto.stock}."
            )
        
        nuevo_item = ItemCarrito(
            id_carrito=carrito.id_usuario,
            id_producto=producto_id,
            cantidad=cantidad_a_agregar
        )
        db.add(nuevo_item)
        carrito.items.append(nuevo_item) 
    
    carrito.fecha_actualizacion = datetime.utcnow()
    
    db.commit()
    
    # Usamos get_or_create_cart para recargar la respuesta con joinedload
    carrito_respuesta = get_or_create_cart(db, user_id)
    
    return carrito_respuesta

# PUT /api/cart/update - Actualizar cantidad de un ítem
@app.put("/api/cart/update", response_model=CarritoResponse)
def update_cart_item(
    item_data: CarritoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id_usuario"]
    producto_id = item_data.id_producto
    cantidad_nueva = item_data.cantidad 
    
    carrito = get_or_create_cart(db, user_id)
    
    producto = db.query(Producto).filter(Producto.id_producto == producto_id).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    
    if producto.stock < cantidad_nueva:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Stock disponible: {producto.stock}."
        )

    item_existente = db.query(ItemCarrito).filter(
        ItemCarrito.id_carrito == carrito.id_usuario,
        ItemCarrito.id_producto == producto_id
    ).first()
    
    if not item_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito.")
        
    item_existente.cantidad = cantidad_nueva
    carrito.fecha_actualizacion = datetime.utcnow()
    
    db.commit()
    
    carrito_respuesta = get_or_create_cart(db, user_id)
    return carrito_respuesta

# DELETE /api/cart/remove/:id_producto - Eliminar un ítem del carrito
@app.delete("/api/cart/remove/{id_producto}", response_model=CarritoResponse)
def remove_from_cart(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id_usuario"]
    
    carrito = get_or_create_cart(db, user_id)

    item_a_eliminar = db.query(ItemCarrito).filter(
        ItemCarrito.id_carrito == carrito.id_usuario,
        ItemCarrito.id_producto == id_producto
    ).first()
    
    if not item_a_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito.")
        
    db.delete(item_a_eliminar)
    carrito.fecha_actualizacion = datetime.utcnow()
    
    db.commit()

    carrito_respuesta = get_or_create_cart(db, user_id)
    return carrito_respuesta

# =====================================================================
# ENDPOINTS DE PEDIDOS (Issue 6)
# =====================================================================

@app.post("/api/orders", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea un pedido a partir del carrito del usuario.
    Esto es una transacción: verifica stock, crea el pedido,
    reduce el stock y vacía el carrito.
    """
    user_id = current_user["id_usuario"]
    
    # 1. Obtener el carrito del usuario (con productos cargados)
    carrito = db.query(Carrito).options(
        joinedload(Carrito.items).joinedload(ItemCarrito.producto)
    ).filter(Carrito.id_usuario == user_id).first()

    if not carrito or not carrito.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El carrito está vacío.")

    # Usamos un bloque try/except para manejar la transacción
    try:
        total_pedido = 0
        items_pedido_creados = []
        
        # 3. Verificar stock y calcular total
        for item_carrito in carrito.items:
            producto = item_carrito.producto
            if producto.stock < item_carrito.cantidad:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock insuficiente para {producto.nombre_producto}. Disponible: {producto.stock}"
                )
            
            subtotal = float(producto.precio) * item_carrito.cantidad # Convertir Decimal a float
            total_pedido += subtotal
        
        # 4. Crear el Pedido (Orden)
        nuevo_pedido = Pedido(
            id_usuario=user_id,
            total=total_pedido,
            estado="pendiente", # Estado inicial
            direccion_envio="Dirección de prueba" # (El modelo la requiere no nula)
        )
        db.add(nuevo_pedido)
        db.flush() # Para obtener el id_pedido antes del commit

        # 5. Mover items del carrito a items de pedido y reducir stock
        for item_carrito in carrito.items:
            producto = item_carrito.producto
            
            # A. Reducir el stock
            producto.stock -= item_carrito.cantidad
            
            # B. Crear el ItemPedido
            item_pedido = ItemPedido(
                id_pedido=nuevo_pedido.id_pedido,
                id_producto=item_carrito.id_producto,
                cantidad=item_carrito.cantidad,
                precio_unitario=producto.precio,
                subtotal=float(producto.precio) * item_carrito.cantidad
            )
            items_pedido_creados.append(item_pedido)
            
            # C. Eliminar el item del carrito
            db.delete(item_carrito)

        db.add_all(items_pedido_creados)

        # 6. ¡Commit! Si todo salió bien, guarda todos los cambios.
        db.commit()
        
        # Recargamos el pedido y sus relaciones para la respuesta
        db.refresh(nuevo_pedido)
        
        # Cargamos los items y productos para la respuesta
        pedido_respuesta = db.query(Pedido).options(
            joinedload(Pedido.items).joinedload(ItemPedido.producto)
        ).filter(Pedido.id_pedido == nuevo_pedido.id_pedido).first()
        
        return pedido_respuesta

    except Exception as e:
        # 7. ¡Rollback! Si algo falló (ej: stock), deshace todo.
        db.rollback()
        # Re-lanza la excepción HTTP si la causamos nosotros
        if isinstance(e, HTTPException):
            raise e
        # O lanza un error 500 si fue algo inesperado
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear el pedido: {str(e)}")

@app.get("/api/orders", response_model=List[PedidoResponse])
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """ Obtiene el historial de pedidos del usuario autenticado """
    user_id = current_user["id_usuario"]
    
    pedidos = db.query(Pedido).options(
        joinedload(Pedido.items).joinedload(ItemPedido.producto)
    ).filter(Pedido.id_usuario == user_id).order_by(Pedido.fecha_pedido.desc()).all()
    
    return pedidos

@app.get("/api/orders/{id_pedido}", response_model=PedidoResponse)
def get_order_details(
    id_pedido: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """ Obtiene los detalles de un pedido específico, verificando que pertenezca al usuario """
    user_id = current_user["id_usuario"]
    
    pedido = db.query(Pedido).options(
        joinedload(Pedido.items).joinedload(ItemPedido.producto)
    ).filter(Pedido.id_pedido == id_pedido).first()
    
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado.")
    
    if pedido.id_usuario != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver este pedido.")
        
    return pedido


# ============= EJECUTAR SERVIDOR =============

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)