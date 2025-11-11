# backend/api/products.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from sqlalchemy import func

import schemas
import models
from database import get_db
# Importamos ambas dependencias
from dependencies import get_current_user, require_admin

router = APIRouter()

# --- FUNCIÓN AUXILIAR DE FILTRO ---
def _apply_product_filters(
    query: "Query", 
    search: Optional[str] = None,
    category: Optional[str] = None,
    marca: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None
):
    """
    Función auxiliar para aplicar filtros de producto comunes a una consulta.
    """
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (models.Producto.nombre_producto.ilike(search_pattern)) |
            (models.Producto.descripcion.ilike(search_pattern))
        )
    if category:
        query = query.filter(models.Producto.categoria == category)
    if marca:
        query = query.filter(models.Producto.marca == marca)
    if precio_min is not None:
        query = query.filter(models.Producto.precio >= precio_min)
    if precio_max is not None:
        query = query.filter(models.Producto.precio <= precio_max)
    return query

# --- ENDPOINTS DE PRODUCTOS ---

@router.get("/products", response_model=List[schemas.ProductoResponse])
def get_productos(
    page: int = Query(1, ge=1), 
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    marca: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Producto)
    query = _apply_product_filters(
        query, search, category, marca, precio_min, precio_max
    )
    skip = (page - 1) * limit
    productos = query.offset(skip).limit(limit).all()
    return productos

@router.get("/products/count", response_model=dict)
def get_productos_count(
    search: Optional[str] = None, 
    category: Optional[str] = None,
    marca: Optional[str] = None, 
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(models.Producto)
    query = _apply_product_filters(
        query, search, category, marca, precio_min, precio_max
    )
    total = query.count()
    return {"total": total}

@router.get("/products/{id_producto}", response_model=schemas.ProductoResponse)
def get_producto(id_producto: int, db: Session = Depends(get_db)):
    producto = db.query(models.Producto).filter(models.Producto.id_producto == id_producto).first()
    if not producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return producto

@router.post("/products", response_model=schemas.ProductoResponse, status_code=status.HTTP_201_CREATED)
def create_producto(
    producto: schemas.ProductoCreate, 
    db: Session = Depends(get_db),
    # --- CORREGIDO (Issue 10) ---
    current_user: models.Usuario = Depends(require_admin)
):
    db_producto = models.Producto(**producto.model_dump())
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

@router.put("/products/{id_producto}", response_model=schemas.ProductoResponse)
def update_producto(
    id_producto: int, 
    producto: schemas.ProductoUpdate,
    db: Session = Depends(get_db),
    # --- CORREGIDO (Issue 10) ---
    current_user: models.Usuario = Depends(require_admin)
):
    db_producto = db.query(models.Producto).filter(models.Producto.id_producto == id_producto).first()
    if not db_producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    
    for key, value in producto.model_dump().items():
        setattr(db_producto, key, value)
    
    db.commit()
    db.refresh(db_producto)
    return db_producto

@router.delete("/products/{id_producto}", status_code=status.HTTP_204_NO_CONTENT)
def delete_producto(
    id_producto: int, 
    db: Session = Depends(get_db),
    # --- CORREGIDO (Issue 10) ---
    current_user: models.Usuario = Depends(require_admin)
):
    db_producto = db.query(models.Producto).filter(models.Producto.id_producto == id_producto).first()
    if not db_producto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    
    db.delete(db_producto)
    db.commit()
    return None