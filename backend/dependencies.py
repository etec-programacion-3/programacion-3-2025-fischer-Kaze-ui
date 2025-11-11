# backend/dependencies.py

from fastapi import Depends, HTTPException, status, Header
from typing import Optional


def get_current_user(
    x_user_id: Optional[int] = Header(None),
    x_user_role: Optional[str] = Header(None)
):
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