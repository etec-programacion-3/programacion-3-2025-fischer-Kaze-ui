# backend/dependencies.py

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Importaciones de nuestros módulos
from database import SessionLocal
import models
import schemas
import auth # <-- Importamos el nuevo archivo auth

# =====================================================================
# DEPENDENCIAS DE BASE DE DATOS
# =====================================================================

def get_db():
    """ Dependencia para obtener la sesión de la base de datos """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =====================================================================
# DEPENDENCIAS DE AUTENTICACIÓN (Issue 9)
# =====================================================================

# Usamos el scheme definido en auth.py
oauth2_scheme = auth.oauth2_scheme

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> models.Usuario:
    """
    Nueva dependencia 'get_current_user'.
    Decodifica el token JWT y obtiene el usuario de la DB.
    """
    
    payload = auth.decodificar_token(token)
    user_id: int = payload.get("user_id")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT inválido: falta ID de usuario",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == user_id).first()
    
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado (token inválido)",
        )
    
    return usuario

# =====================================================================
# DEPENDENCIAS DE AUTORIZACIÓN (Roles)
# =====================================================================

def require_admin(
    current_user: models.Usuario = Depends(get_current_user)
) -> models.Usuario:
    """
    Verifica que el usuario (obtenido del token JWT) tenga el rol 'admin'.
    """
    if current_user.tipo_usuario != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de administrador.",
        )
    return current_user