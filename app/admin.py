from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, hash_password

router_admin = APIRouter(prefix="/admins", tags=["Administradores"])


@router_admin.get("/", response_model=List[schemas.AdminOut])
def listar_admins(db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    if current_user.rol != 'admin':
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return db.query(models.Usuario).filter(models.Usuario.rol == 'admin', models.Usuario.activo == True).all()


@router_admin.get("/{admin_id}", response_model=schemas.AdminOut)
def obtener_admin(admin_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    if current_user.rol != 'admin':
        raise HTTPException(status_code=403, detail="Acceso denegado")
    admin = db.query(models.Usuario).filter(models.Usuario.id == admin_id, models.Usuario.rol == 'admin').first()
    if not admin:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    return admin


@router_admin.post("/", response_model=schemas.AdminOut, status_code=201)
def crear_admin(data: schemas.AdminCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    # Solo administradores pueden crear otros administradores
    if current_user.rol != 'admin':
        raise HTTPException(status_code=403, detail="Acceso denegado")
    existente = db.query(models.Usuario).filter(models.Usuario.email == data.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    usuario = models.Usuario(
        nombre=data.nombre,
        email=data.email,
        password_hash=hash_password(data.password),
        rol='admin',
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router_admin.put("/{admin_id}", response_model=schemas.AdminOut)
def actualizar_admin(admin_id: int, data: schemas.AdminUpdate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    if current_user.rol != 'admin':
        raise HTTPException(status_code=403, detail="Acceso denegado")
    admin = db.query(models.Usuario).filter(models.Usuario.id == admin_id, models.Usuario.rol == 'admin').first()
    if not admin:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    cambios = data.model_dump(exclude_unset=True)
    if 'password' in cambios:
        admin.password_hash = hash_password(cambios.pop('password'))
    if 'email' in cambios:
        # Verificar unicidad
        otro = db.query(models.Usuario).filter(models.Usuario.email == cambios['email'], models.Usuario.id != admin_id).first()
        if otro:
            raise HTTPException(status_code=400, detail="El email ya está en uso")
    for campo, valor in cambios.items():
        setattr(admin, campo, valor)
    db.commit()
    db.refresh(admin)
    return admin


@router_admin.delete("/{admin_id}", status_code=204)
def eliminar_admin(admin_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    if current_user.rol != 'admin':
        raise HTTPException(status_code=403, detail="Acceso denegado")
    admin = db.query(models.Usuario).filter(models.Usuario.id == admin_id, models.Usuario.rol == 'admin').first()
    if not admin:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    # Eliminación lógica
    admin.activo = False
    db.commit()
