# backend/api/cart.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

import schemas
import models
from database import get_db
from dependencies import get_current_user

router = APIRouter()

# --- FUNCIÓN AUXILIAR DEL CARRITO ---
def get_or_create_cart(db: Session, user_id: int) -> models.Carrito:
    carrito = db.query(models.Carrito).options(
        joinedload(models.Carrito.items).joinedload(models.ItemCarrito.producto)
    ).filter(models.Carrito.id_usuario == user_id).first()
    
    if not carrito:
        usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == user_id).first()
        if not usuario:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

        carrito = models.Carrito(id_usuario=user_id, items=[]) 
        db.add(carrito)
        db.commit()
        db.refresh(carrito) 
        
        carrito = db.query(models.Carrito).options(
            joinedload(models.Carrito.items).joinedload(models.ItemCarrito.producto)
        ).filter(models.Carrito.id_usuario == user_id).first()
        
    return carrito

# --- ENDPOINTS DE CARRITO ---

@router.get("/cart", response_model=schemas.CarritoResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id_usuario"]
    carrito = get_or_create_cart(db, user_id)
    return carrito

@router.post("/cart/add", response_model=schemas.CarritoResponse)
def add_to_cart(
    item_data: schemas.CarritoAdd,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id_usuario"]
    producto_id = item_data.id_producto
    cantidad_a_agregar = item_data.cantidad
    
    carrito = get_or_create_cart(db, user_id)
    
    producto = db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()
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
        
        nuevo_item = models.ItemCarrito(
            id_carrito=carrito.id_usuario,
            id_producto=producto_id,
            cantidad=cantidad_a_agregar
        )
        db.add(nuevo_item)
        carrito.items.append(nuevo_item) 
    
    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()
    carrito_respuesta = get_or_create_cart(db, user_id)
    return carrito_respuesta

@router.put("/cart/update", response_model=schemas.CarritoResponse)
def update_cart_item(
    item_data: schemas.CarritoUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id_usuario"]
    producto_id = item_data.id_producto
    cantidad_nueva = item_data.cantidad 
    
    carrito = get_or_create_cart(db, user_id)
    
    producto = db.query(models.Producto).filter(models.Producto.id_producto == producto_id).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado.")
    
    if producto.stock < cantidad_nueva:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Stock disponible: {producto.stock}."
        )

    item_existente = db.query(models.ItemCarrito).filter(
        models.ItemCarrito.id_carrito == carrito.id_usuario,
        models.ItemCarrito.id_producto == producto_id
    ).first()
    
    if not item_existente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito.")
        
    item_existente.cantidad = cantidad_nueva
    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()
    carrito_respuesta = get_or_create_cart(db, user_id)
    return carrito_respuesta

@router.delete("/cart/remove/{id_producto}", response_model=schemas.CarritoResponse)
def remove_from_cart(
    id_producto: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id_usuario"]
    carrito = get_or_create_cart(db, user_id)

    item_a_eliminar = db.query(models.ItemCarrito).filter(
        models.ItemCarrito.id_carrito == carrito.id_usuario,
        models.ItemCarrito.id_producto == id_producto
    ).first()
    
    if not item_a_eliminar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado en el carrito.")
        
    db.delete(item_a_eliminar)
    carrito.fecha_actualizacion = datetime.utcnow()
    db.commit()
    carrito_respuesta = get_or_create_cart(db, user_id)
    return carrito_respuesta