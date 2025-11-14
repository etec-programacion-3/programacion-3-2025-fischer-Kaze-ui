# backend/auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt  # Usamos bcrypt directamente
from dotenv import load_dotenv

load_dotenv()

# --- Configuración de Seguridad ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# --- Variables de Entorno ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if not SECRET_KEY:
    raise EnvironmentError("Falta la variable de entorno SECRET_KEY en el archivo .env")

# --- Funciones de Hashing (CON BCRYPT DIRECTO) ---

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """Compara una contraseña plana con su hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    """Genera un hash para una contraseña plana."""
    # Truncar a 72 bytes (límite de bcrypt)
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

# --- Funciones de JWT ---

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
    """Decodifica un token. Lanza una excepción si es inválido o ha expirado."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido o expirado: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )