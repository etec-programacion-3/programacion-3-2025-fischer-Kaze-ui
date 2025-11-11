# backend/routes.py
# Este es ahora el "Router Maestro"

from fastapi import APIRouter

# Importamos los routers individuales desde la nueva carpeta 'api'
from api import products, cart, orders, messages

router = APIRouter()

# Incluimos los routers en el principal, organizados por tags
router.include_router(products.router, prefix="/api", tags=["Productos"])
router.include_router(cart.router, prefix="/api", tags=["Carrito"])
router.include_router(orders.router, prefix="/api", tags=["Pedidos"])
router.include_router(messages.router, prefix="/api", tags=["Mensajería"])

@router.get("/")
def root():
    return {"message": "E-commerce API v2 (Modularizada)"}