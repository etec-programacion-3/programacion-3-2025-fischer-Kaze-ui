# backend/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import schemas
import models
import auth  # Tu archivo auth.py (el de la raíz de backend/)
from database import get_db

router = APIRouter()

@router.post("/register", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED)
def register_user(
    user_data: schemas.UsuarioCreate, 
    db: Session = Depends(get_db)
):
    """
    Endpoint para registrar un nuevo usuario.
    """
    # 1. Verificar si el email o username ya existen
    existing_user_email = db.query(models.Usuario).filter(models.Usuario.email == user_data.email).first()
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado."
        )
    
    existing_user_name = db.query(models.Usuario).filter(models.Usuario.nombre_usuario == user_data.nombre_usuario).first()
    if existing_user_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe."
        )

    # 2. Hashear la contraseña
    hashed_password = auth.get_password_hash(user_data.password)
    
    # 3. Crear el nuevo usuario
    user_data_dict = user_data.model_dump(exclude={"password"})
    nuevo_usuario = models.Usuario(
        **user_data_dict,
        password_hash=hashed_password
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return nuevo_usuario


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint de Login.
    Recibe un formulario (username y password) y devuelve un Token JWT.
    """
    
    # 1. Buscar al usuario (permitimos login con email o nombre_usuario)
    usuario = db.query(models.Usuario).filter(
        (models.Usuario.nombre_usuario == form_data.username) | 
        (models.Usuario.email == form_data.username)
    ).first()

    # 2. Verificar la contraseña
    if not usuario or not auth.verificar_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. Crear el Token JWT
    token_data = {
        "sub": usuario.nombre_usuario,
        "user_id": usuario.id_usuario 
    }
    access_token = auth.crear_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}