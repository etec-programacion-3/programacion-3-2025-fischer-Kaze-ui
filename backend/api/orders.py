# backend/api/orders.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

import schemas
import models
from database import get_db
from dependencies import get_current_user

router = APIRouter()

# --- ENDPOINTS DE PEDIDOS ---

@router.post("/orders", response_model=schemas.PedidoResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id_usuario"]
    
    carrito = db.query(models.Carrito).options(
        joinedload(models.Carrito.items).joinedload(models.ItemCarrito.producto)
    ).filter(models.Carrito.id_usuario == user_id).first()

    if not carrito or not carrito.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El carrito está vacío.")

    try:
        total_pedido = 0
        items_pedido_creados = []
        
        for item_carrito in carrito.items:
            producto = item_carrito.producto
            if producto.stock < item_carrito.cantidad:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock insuficiente para {producto.nombre_producto}. Disponible: {producto.stock}"
                )
            subtotal = float(producto.precio) * item_carrito.cantidad
            total_pedido += subtotal
        
        nuevo_pedido = models.Pedido(
            id_usuario=user_id,
            total=total_pedido,
            estado="pendiente",
            direccion_envio="Dirección de prueba"
        )
        db.add(nuevo_pedido)
        db.flush()

        for item_carrito in carrito.items:
            producto = item_carrito.producto
            producto.stock -= item_carrito.cantidad
            
            item_pedido = models.ItemPedido(
                id_pedido=nuevo_pedido.id_pedido,
                id_producto=item_carrito.id_producto,
                cantidad=item_carrito.cantidad,
                precio_unitario=producto.precio,
                subtotal=float(producto.precio) * item_carrito.cantidad
            )
            items_pedido_creados.append(item_pedido)
            db.delete(item_carrito)

        db.add_all(items_pedido_creados)
        db.commit()
        
        db.refresh(nuevo_pedido)
        pedido_respuesta = db.query(models.Pedido).options(
            joinedload(models.Pedido.items).joinedload(models.ItemPedido.producto)
        ).filter(models.Pedido.id_pedido == nuevo_pedido.id_pedido).first()
        
        return pedido_respuesta

    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear el pedido: {str(e)}")

@router.get("/orders", response_model=List[schemas.PedidoResponse])
def get_user_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id_usuario"]
    pedidos = db.query(models.Pedido).options(
        joinedload(models.Pedido.items).joinedload(models.ItemPedido.producto)
    ).filter(models.Pedido.id_usuario == user_id).order_by(models.Pedido.fecha_pedido.desc()).all()
    return pedidos

@router.get("/orders/{id_pedido}", response_model=schemas.PedidoResponse)
def get_order_details(
    id_pedido: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id_usuario"]
    pedido = db.query(models.Pedido).options(
        joinedload(models.Pedido.items).joinedload(models.ItemPedido.producto)
    ).filter(models.Pedido.id_pedido == id_pedido).first()
    
    if not pedido:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado.")
    if pedido.id_usuario != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para ver este pedido.")
    return pedido