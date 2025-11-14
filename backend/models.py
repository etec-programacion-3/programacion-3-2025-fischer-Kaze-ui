# backend/models.py

# --- IMPORTACIÓN MODIFICADA ---
# Se cambió DECIMAL por Float
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Usuario(Base):
    __tablename__ = "usuario"
    
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre_usuario = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=True)
    fecha_registro = Column(DateTime, default=func.now())
    fecha_ultimo_acceso = Column(DateTime, nullable=True)
    estado_cuenta = Column(String(20), default='activo')
    tipo_usuario = Column(String(20), default='cliente')
    
    pedidos = relationship("Pedido", back_populates="usuario")
    mensajes = relationship("Mensaje", back_populates="usuario")
    conversaciones_enviadas = relationship(
        "Conversacion",
        foreign_keys="Conversacion.id_usuario_remitente",
        back_populates="usuario_remitente"
    )
    conversaciones_recibidas = relationship(
        "Conversacion",
        foreign_keys="Conversacion.id_usuario_destinatario",
        back_populates="usuario_destinatario"
    )
    
    # Relación uno a uno (uselist=False) con Carrito
    carrito = relationship("Carrito", back_populates="usuario", uselist=False, cascade="all, delete-orphan")

class Producto(Base):
    __tablename__ = "productos"
    
    id_producto = Column(Integer, primary_key=True, autoincrement=True)
    nombre_producto = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    marca = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)
    
    # --- TIPO DE DATO MODIFICADO ---
    precio = Column(Float, nullable=False)
    
    stock = Column(Integer, default=0)
    imagen = Column(String(255), nullable=True)
    fecha_agregado = Column(DateTime, default=func.now())
    
    items_pedido = relationship("ItemPedido", back_populates="producto")
    items_carrito = relationship("ItemCarrito", back_populates="producto")

class Pedido(Base):
    __tablename__ = "pedidos"
    
    id_pedido = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), nullable=False)
    fecha_pedido = Column(DateTime, default=func.now())
    
    # --- TIPO DE DATO MODIFICADO ---
    total = Column(Float, nullable=False)
    
    estado = Column(String(20), default='pendiente')
    direccion_envio = Column(Text, nullable=False)
    metodo_pago = Column(String(50), nullable=True)
    fecha_entrega = Column(DateTime, nullable=True)
    
    usuario = relationship("Usuario", back_populates="pedidos")
    items = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")

class Mensaje(Base):
    __tablename__ = "mensajes"
    
    id_mensaje = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), nullable=False)
    asunto = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    fecha_mensaje = Column(DateTime, default=func.now())
    estado = Column(String(20), default='no_leido')
    tipo = Column(String(50), nullable=True)
    email_contacto = Column(String(100), nullable=True)
    
    usuario = relationship("Usuario", back_populates="mensajes")
    conversaciones = relationship("Conversacion", back_populates="mensaje")

class ItemPedido(Base):
    __tablename__ = "itemspedido"
    
    id_item = Column(Integer, primary_key=True, autoincrement=True)
    id_pedido = Column(Integer, ForeignKey('pedidos.id_pedido'), nullable=False)
    id_producto = Column(Integer, ForeignKey('productos.id_producto'), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    
    # --- TIPO DE DATO MODIFICADO ---
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    
    pedido = relationship("Pedido", back_populates="items")
    producto = relationship("Producto", back_populates="items_pedido")

class Conversacion(Base):
    __tablename__ = "conversaciones"
    
    id_conversacion = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario_remitente = Column(Integer, ForeignKey('usuario.id_usuario'), nullable=False)
    id_usuario_destinatario = Column(Integer, ForeignKey('usuario.id_usuario'), nullable=False)
    id_mensaje = Column(Integer, ForeignKey('mensajes.id_mensaje'), nullable=False)
    fecha_envio = Column(DateTime, default=func.now())
    leido = Column(Boolean, default=False)
    tipo_participacion = Column(String(20), nullable=True)
    
    usuario_remitente = relationship(
        "Usuario",
        foreign_keys=[id_usuario_remitente],
        back_populates="conversaciones_enviadas"
    )
    usuario_destinatario = relationship(
        "Usuario",
        foreign_keys=[id_usuario_destinatario],
        back_populates="conversaciones_recibidas"
    )
    mensaje = relationship("Mensaje", back_populates="conversaciones")

class Carrito(Base):
    __tablename__ = "carrito"
    
    id_usuario = Column(Integer, ForeignKey('usuario.id_usuario'), primary_key=True)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())

    usuario = relationship("Usuario", back_populates="carrito", uselist=False)
    items = relationship("ItemCarrito", back_populates="carrito", cascade="all, delete-orphan")

class ItemCarrito(Base):
    __tablename__ = "items_carrito"
    
    id_item_carrito = Column(Integer, primary_key=True, autoincrement=True)
    id_carrito = Column(Integer, ForeignKey('carrito.id_usuario'), nullable=False) 
    id_producto = Column(Integer, ForeignKey('productos.id_producto'), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    
    __table_args__ = (
        UniqueConstraint('id_carrito', 'id_producto', name='_carrito_producto_uc'),
    )
    
    carrito = relationship("Carrito", back_populates="items")
    producto = relationship("Producto", back_populates="items_carrito")