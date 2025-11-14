# backend/api/messages.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
from sqlalchemy import case, distinct, func, update

import schemas
import models
from database import get_db
# Importamos la dependencia que devuelve el OBJETO
from dependencies import get_current_user

router = APIRouter()

# --- ENDPOINT NUEVO (Issue 8) ---
@router.get("/notifications/unread-messages", response_model=schemas.NotificacionUnreadResponse)
def get_unread_notification_count(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    user_id = current_user.id_usuario

    count = db.query(func.count(distinct(models.Conversacion.id_usuario_remitente))).filter(
        models.Conversacion.id_usuario_destinatario == user_id,
        models.Conversacion.leido == False
    ).scalar() or 0

    return {"total_conversaciones_no_leidas": int(count)}


# --- ENDPOINTS DE MENSAJERÍA (Issue 7) ---

@router.get("/conversations", response_model=List[schemas.ConversacionResponse])
def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    user_id = current_user.id_usuario
    
    other_user_id = case(
        (models.Conversacion.id_usuario_remitente == user_id, models.Conversacion.id_usuario_destinatario),
        else_=models.Conversacion.id_usuario_remitente
    ).label("other_user_id")

    subquery = db.query(
        models.Conversacion.id_conversacion,
        other_user_id,
        func.row_number().over(
            partition_by=other_user_id,
            order_by=models.Conversacion.fecha_envio.desc()
        ).label('rn')
    ).filter(
        (models.Conversacion.id_usuario_remitente == user_id) |
        (models.Conversacion.id_usuario_destinatario == user_id)
    ).subquery()

    latest_conv_ids = db.query(subquery.c.id_conversacion).filter(subquery.c.rn == 1).all()
    latest_conv_ids = [c_id[0] for c_id in latest_conv_ids]

    if not latest_conv_ids:
        return []

    conversaciones = db.query(models.Conversacion).options(
        joinedload(models.Conversacion.usuario_remitente),
        joinedload(models.Conversacion.usuario_destinatario),
        joinedload(models.Conversacion.mensaje)
    ).filter(
        models.Conversacion.id_conversacion.in_(latest_conv_ids)
    ).order_by(
        models.Conversacion.fecha_envio.desc()
    ).all()
    
    response_list = []
    for conv in conversaciones:
        ultimo_mensaje_schema = None
        if conv.mensaje:
            ultimo_mensaje_schema = schemas.MensajeResponse(
                id_mensaje=conv.mensaje.id_mensaje,
                id_conversacion=conv.id_conversacion,
                id_usuario_remitente=conv.id_usuario_remitente,
                fecha_envio=conv.fecha_envio,
                leido=conv.leido,
                contenido=conv.mensaje.mensaje
            )
        
        mensajes_no_leidos_count = db.query(models.Conversacion).filter(
            (
                (models.Conversacion.id_usuario_remitente == conv.usuario_remitente.id_usuario) &
                (models.Conversacion.id_usuario_destinatario == user_id)
            ) |
            (
                (models.Conversacion.id_usuario_remitente == conv.usuario_destinatario.id_usuario) &
                (models.Conversacion.id_usuario_destinatario == user_id)
            ),
            models.Conversacion.leido == False
        ).count()

        conv_schema = schemas.ConversacionResponse(
            id_conversacion=conv.id_conversacion,
            fecha_envio=conv.fecha_envio,
            usuario_remitente=conv.usuario_remitente,
            usuario_destinatario=conv.usuario_destinatario,
            ultimo_mensaje=ultimo_mensaje_schema,
            mensajes_no_leidos=mensajes_no_leidos_count
        )
        response_list.append(conv_schema)

    return response_list


@router.post("/conversations", response_model=schemas.ConversacionResponse, status_code=status.HTTP_201_CREATED)
def create_or_get_conversation(
    data: schemas.ConversacionCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    remitente_id = current_user.id_usuario
    destinatario_id = data.id_usuario_destinatario

    if remitente_id == destinatario_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No puedes iniciar una conversación contigo mismo.")

    conversacion = db.query(models.Conversacion).options(
        joinedload(models.Conversacion.usuario_remitente),
        joinedload(models.Conversacion.usuario_destinatario)
    ).filter(
        (
            (models.Conversacion.id_usuario_remitente == remitente_id) &
            (models.Conversacion.id_usuario_destinatario == destinatario_id)
        ) |
        (
            (models.Conversacion.id_usuario_remitente == destinatario_id) &
            (models.Conversacion.id_usuario_destinatario == remitente_id)
        )
    ).order_by(models.Conversacion.fecha_envio.desc()).first()

    if conversacion:
        return conversacion

    destinatario = db.query(models.Usuario).filter(models.Usuario.id_usuario == destinatario_id).first()
    if not destinatario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario destinatario no encontrado.")
    
    primer_mensaje = models.Mensaje(
        id_usuario=remitente_id,
        asunto="Nueva Conversación",
        mensaje="Iniciada conversación.",
        estado="leido"
    )
    db.add(primer_mensaje)
    db.flush()

    nueva_conversacion = models.Conversacion(
        id_usuario_remitente=remitente_id,
        id_usuario_destinatario=destinatario_id,
        id_mensaje=primer_mensaje.id_mensaje,
        fecha_envio=primer_mensaje.fecha_mensaje,
        leido=True
    )
    db.add(nueva_conversacion)
    db.commit()
    
    db.refresh(nueva_conversacion)
    conversacion_respuesta = db.query(models.Conversacion).options(
        joinedload(models.Conversacion.usuario_remitente),
        joinedload(models.Conversacion.usuario_destinatario)
    ).filter(models.Conversacion.id_conversacion == nueva_conversacion.id_conversacion).first()

    return conversacion_respuesta


@router.get("/conversations/{conversation_partner_id}/messages", response_model=List[schemas.MensajeResponse])
def get_conversation_messages(
    conversation_partner_id: int,
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=100, description="Mensajes por página"),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    user_id = current_user.id_usuario
    
    conv_ids_to_mark = db.query(models.Conversacion.id_conversacion).filter(
        models.Conversacion.id_usuario_remitente == conversation_partner_id,
        models.Conversacion.id_usuario_destinatario == user_id,
        models.Conversacion.leido == False
    ).all()
    
    conv_ids_list = [c[0] for c in conv_ids_to_mark]

    if conv_ids_list:
        db.execute(
            update(models.Conversacion)
            .where(models.Conversacion.id_conversacion.in_(conv_ids_list))
            .values(leido=True)
        )
        
        mensaje_ids_to_mark = db.query(models.Conversacion.id_mensaje).filter(
             models.Conversacion.id_conversacion.in_(conv_ids_list)
        ).all()
        mensaje_ids_list = [m[0] for m in mensaje_ids_to_mark]
        
        if mensaje_ids_list:
             db.execute(
                update(models.Mensaje)
                .where(models.Mensaje.id_mensaje.in_(mensaje_ids_list))
                .values(estado='leido')
            )
        
        db.commit()

    mensajes_query = db.query(models.Conversacion).options(
        joinedload(models.Conversacion.mensaje)
    ).filter(
        (
            (models.Conversacion.id_usuario_remitente == user_id) &
            (models.Conversacion.id_usuario_destinatario == conversation_partner_id)
        ) |
        (
            (models.Conversacion.id_usuario_remitente == conversation_partner_id) &
            (models.Conversacion.id_usuario_destinatario == user_id)
        )
    ).order_by(models.Conversacion.fecha_envio.desc())

    skip = (page - 1) * limit
    mensajes = mensajes_query.offset(skip).limit(limit).all()
    
    response_list = []
    for conv in mensajes:
        if conv.mensaje:
            msg_schema = schemas.MensajeResponse(
                id_mensaje=conv.mensaje.id_mensaje,
                id_conversacion=conv.id_conversacion,
                id_usuario_remitente=conv.id_usuario_remitente,
                fecha_envio=conv.fecha_envio,
                leido=conv.leido,
                contenido=conv.mensaje.mensaje
            )
            response_list.append(msg_schema)
            
    return response_list


@router.post("/conversations/{id_conversacion}/messages", response_model=schemas.MensajeResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    id_conversacion: int,
    data: schemas.MensajeBase,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    user_id = current_user.id_usuario

    conversacion_base = db.query(models.Conversacion).filter(
        models.Conversacion.id_conversacion == id_conversacion
    ).first()

    if not conversacion_base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada.")
        
    es_participante = (
        conversacion_base.id_usuario_remitente == user_id or 
        conversacion_base.id_usuario_destinatario == user_id
    )
    if not es_participante:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No eres participante de esta conversación.")

    nuevo_mensaje = models.Mensaje(
        id_usuario=user_id,
        asunto=f"Mensaje en Conversación {id_conversacion}",
        mensaje=data.contenido,
        estado='no_leido'
    )
    db.add(nuevo_mensaje)
    db.flush()

    destinatario_id = (
        conversacion_base.id_usuario_destinatario 
        if conversacion_base.id_usuario_remitente == user_id 
        else conversacion_base.id_usuario_remitente
    )

    registro_conversacion = models.Conversacion(
        id_usuario_remitente=user_id,
        id_usuario_destinatario=destinatario_id,
        id_mensaje=nuevo_mensaje.id_mensaje,
        fecha_envio=nuevo_mensaje.fecha_mensaje,
        leido=False
    )
    
    db.add(registro_conversacion)
    
    db.commit()
    db.refresh(nuevo_mensaje)
    db.refresh(registro_conversacion)
    
    mensaje_respuesta = schemas.MensajeResponse(
        id_mensaje=nuevo_mensaje.id_mensaje,
        id_conversacion=registro_conversacion.id_conversacion,
        id_usuario_remitente=user_id,
        fecha_envio=nuevo_mensaje.fecha_mensaje,
        leido=False,
        contenido=nuevo_mensaje.mensaje
    )

    return mensaje_respuesta