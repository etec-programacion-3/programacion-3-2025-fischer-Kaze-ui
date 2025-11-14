# backend/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# ============= SCHEMAS DE PRODUCTO (Issues 3 y 4) =============

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

# ============= SCHEMAS DE MENSAJERÍA (Issue 7) =============

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
    
    class Config:
        from_attributes = True

# --- CONVERSACIONES ---

class ConversacionCreate(BaseModel):
    # El ID del usuario con el que se desea iniciar o continuar la conversación.
    id_usuario_destinatario: int

class ConversacionResponse(BaseModel):
    id_conversacion: int
    fecha_envio: datetime # <-- CORREGIDO (antes era fecha_actualizacion)
    
    # Incluimos los participantes para saber con quién hablamos
    usuario_remitente: ParticipanteResponse 
    usuario_destinatario: ParticipanteResponse
    
    # Muestra el último mensaje de la conversación
    ultimo_mensaje: Optional[MensajeResponse] = None
    
    # Campo para la Issue 8
    mensajes_no_leidos: int = 0
    
    class Config:
        from_attributes = True

# ============= SCHEMAS NOTIFICACIONES (Issue 8) =============

class NotificacionUnreadResponse(BaseModel):
    # El número total de conversaciones que tienen al menos un mensaje no leído
    total_conversaciones_no_leidas: int

# =====================================================================
# SCHEMAS DE AUTENTICACIÓN (Issue 9)
# =====================================================================

# --- Usuario ---

class UsuarioCreate(BaseModel):
    """ Schema para la creación (registro) de un nuevo usuario """
    nombre_usuario: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, description="La contraseña en texto plano")
    nombre: str = Field(..., max_length=100)
    apellido: str = Field(..., max_length=100)
    telefono: Optional[str] = None

class UsuarioResponse(BaseModel):
    """ Schema para devolver la información pública de un usuario """
    id_usuario: int
    nombre_usuario: str
    email: str
    nombre: str
    apellido: str
    tipo_usuario: str
    
    class Config:
        from_attributes = True

# --- Token (Login) ---

class Token(BaseModel):
    """ Schema para la respuesta del Login (el token JWT) """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """ Schema para el contenido (payload) decodificado del JWT """
    username: Optional[str] = None
    user_id: Optional[int] = None