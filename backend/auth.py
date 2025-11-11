# backend/auth.py

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# Cargar variables de entorno (para la clave secreta)
load_dotenv()

# --- Configuración de Seguridad ---

# 1. Configuración de Passlib (Hashing de Contraseñas)
# Usamos bcrypt para el hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 2. Configuración de JWT (Tokens)
# Esta es la URL que FastAPI usará para identificar el endpoint de login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Estas variables DEBEN estar en tu archivo .env
SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_debe_ser_larga_y_segura")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if SECRET_KEY == "tu_clave_secreta_debe_ser_larga_y_segura":
    print("ADVERTENCIA: Estás usando la SECRET_KEY por defecto. ¡Cámbiala en tu archivo .env!")


# --- Funciones Auxiliares de Hashing ---

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña plana con su hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera un hash para una contraseña plana."""
    return pwd_context.hash(password)


# --- Funciones Auxiliares de JWT ---

def crear_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un nuevo JSON Web Token (JWT)."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decodificar_token(token: str) -> dict:
    """
    Decodifica un token. Lanza una excepción si es inválido o ha expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        # Si el token expira, JWTError es lanzado
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )