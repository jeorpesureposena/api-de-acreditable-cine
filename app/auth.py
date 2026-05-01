from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import hashlib
import hmac
import base64
import json
import time

from app.database import get_db
from app import models

router_auth = APIRouter(prefix="/auth", tags=["Autenticación"])

SECRET_KEY = "cine_secret_key_2024"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Utilidades de contraseña ──
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# ── JWT simple (sin librería externa) ──
def create_token(data: dict) -> str:
    payload = {**data, "exp": int(time.time()) + 86400}
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{sig}"

def decode_token(token: str) -> dict:
    try:
        encoded, sig = token.rsplit(".", 1)
        expected = hmac.new(SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=401, detail="Token inválido")
        payload = json.loads(base64.urlsafe_b64decode(encoded.encode()).decode())
        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token expirado")
        return payload
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    user = db.query(models.Usuario).filter(models.Usuario.id == payload.get("id")).first()
    if not user or not user.activo:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user


# ── Schemas ──
class RegisterSchema(BaseModel):
    nombre: str
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: dict


# ── Endpoints ──
@router_auth.post("/registro", status_code=201)
def registro(data: RegisterSchema, db: Session = Depends(get_db), request: Request = None):
    # Si no hay usuarios en la base, permitir crear el primer admin (bootstrap)
    total = db.query(models.Usuario).count()
    if total == 0:
        if db.query(models.Usuario).filter(models.Usuario.email == data.email).first():
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        usuario = models.Usuario(
            nombre=data.nombre,
            email=data.email,
            password_hash=hash_password(data.password),
            rol='admin',
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        return {"mensaje": "Primer administrador creado con éxito", "id": usuario.id}

    # Para crear usuarios posteriormente, requerimos que el solicitante sea admin
    auth = None
    if request:
        auth = request.headers.get('authorization')
    if not auth or not auth.startswith('Bearer '):
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear usuarios")
    token = auth.split(' ', 1)[1]
    payload = decode_token(token)
    user = db.query(models.Usuario).filter(models.Usuario.id == payload.get('id')).first()
    if not user or user.rol != 'admin':
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear usuarios")

    existente = db.query(models.Usuario).filter(models.Usuario.email == data.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    usuario = models.Usuario(
        nombre=data.nombre,
        email=data.email,
        password_hash=hash_password(data.password),
        rol='admin',
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"mensaje": "Usuario registrado con éxito", "id": usuario.id}


@router_auth.post("/login", response_model=LoginResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form.username).first()
    if not usuario or not verify_password(form.password, usuario.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    token = create_token({"id": usuario.id, "email": usuario.email, "rol": usuario.rol})
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {"id": usuario.id, "nombre": usuario.nombre, "email": usuario.email, "rol": usuario.rol}
    }


@router_auth.get("/me")
def me(current_user: models.Usuario = Depends(get_current_user)):
    return {"id": current_user.id, "nombre": current_user.nombre, "email": current_user.email, "rol": current_user.rol}
