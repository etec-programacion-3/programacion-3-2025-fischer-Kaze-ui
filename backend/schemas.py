# backend/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ============= SCHEMAS DE PRODUCTO =============

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


# ============= SCHEMAS DE CARRITO =============

class ProductoEnCarritoResponse(BaseModel):
    id_producto: int
    nombre_producto: str
    precio: float
    imagen: Optional[str] = None

    class Config:
        from_attributes = True

class ItemCarritoResponse(BaseModel):
    id_item_carrito: int
    id_producto: int
    cantidad: int
    producto: ProductoEnCarritoResponse

    class Config:
        from_attributes = True

class CarritoResponse(BaseModel):
    id_usuario: int
    fecha_actualizacion: Optional[datetime] = None
    items: List[ItemCarritoResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True

class CarritoAdd(BaseModel):
    id_producto: int
    cantidad: int = Field(default=1, ge=1, description="Cantidad a AÑADIR")

class CarritoUpdate(BaseModel):
    id_producto: int
    cantidad: int = Field(..., ge=1, description="Cantidad TOTAL nueva")


# ============= SCHEMAS DE PEDIDOS =============

class ItemPedidoResponse(BaseModel):
    id_producto: int
    cantidad: int
    precio_unitario: float
    subtotal: float
    producto: ProductoEnCarritoResponse

    class Config:
        from_attributes = True

class PedidoResponse(BaseModel):
    id_pedido: int
    id_usuario: int
    fecha_pedido: datetime
    total: float
    estado: str
    items: List[ItemPedidoResponse]

    class Config:
        from_attributes = True

# backend/schemas.py

# ... (Todo tu código anterior de Producto, Carrito y Pedido) ...

# ============= SCHEMAS DE MENSAJERÍA =============

# --- AUXILIAR: Para mostrar quién participa sin exponer contraseñas ---
class ParticipanteResponse(BaseModel):
    id_usuario: int
    nombre_usuario: str
    nombre: str
    apellido: str
    
    class Config:
        from_attributes = True

# --- MENSAJES ---

class MensajeBase(BaseModel):
    # El contenido del mensaje que el usuario escribe y envía
    contenido: str = Field(..., min_length=1)

class MensajeResponse(MensajeBase):
    id_mensaje: int
    id_conversacion: int
    # ID del usuario que envió el mensaje
    id_usuario_remitente: int 
    fecha_envio: datetime
    leido: bool
    
    # Aquí puedes incluir la info del remitente si la necesitas
    # usuario_remitente: ParticipanteResponse 
    
    class Config:
        from_attributes = True

# --- CONVERSACIONES ---

class ConversacionCreate(BaseModel):
    # El ID del usuario con el que se desea iniciar o continuar la conversación.
    id_usuario_destinatario: int

class ConversacionResponse(BaseModel):
    id_conversacion: int
    fecha_envio: datetime
    
    # Incluimos los participantes para saber con quién hablamos
    usuario_remitente: ParticipanteResponse 
    usuario_destinatario: ParticipanteResponse
    
    # Muestra el último mensaje de la conversación
    ultimo_mensaje: Optional[MensajeResponse] = None
    
    # Campo para la Issue 8
    mensajes_no_leidos: int = 0
    
    class Config:
        from_attributes = True