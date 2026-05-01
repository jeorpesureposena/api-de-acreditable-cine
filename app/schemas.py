from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ─────────────── GENERO ───────────────
class GeneroBase(BaseModel):
    nombre: str

class GeneroCreate(GeneroBase):
    pass

class GeneroUpdate(BaseModel):
    nombre: Optional[str] = None

class GeneroOut(GeneroBase):
    id: int
    class Config:
        from_attributes = True


# ─────────────── PELICULA ───────────────
class PeliculaBase(BaseModel):
    titulo: str
    duracion_min: int
    clasificacion: str

class PeliculaCreate(PeliculaBase):
    genero_ids: List[int] = []

class PeliculaUpdate(BaseModel):
    titulo: Optional[str] = None
    duracion_min: Optional[int] = None
    clasificacion: Optional[str] = None
    genero_ids: Optional[List[int]] = None

class PeliculaOut(PeliculaBase):
    id: int
    activo: bool
    generos: List[GeneroOut] = []
    class Config:
        from_attributes = True


# ─────────────── SALA ───────────────
class SalaBase(BaseModel):
    nombre: str
    capacidad: int
    tipo: str

class SalaCreate(SalaBase):
    pass

class SalaUpdate(BaseModel):
    nombre: Optional[str] = None
    capacidad: Optional[int] = None
    tipo: Optional[str] = None

class SalaOut(SalaBase):
    id: int
    activo: bool
    class Config:
        from_attributes = True


# ─────────────── FUNCION ───────────────
class FuncionBase(BaseModel):
    fecha_hora: datetime
    precio: float
    pelicula_id: int
    sala_id: int

class FuncionCreate(FuncionBase):
    pass

class FuncionUpdate(BaseModel):
    fecha_hora: Optional[datetime] = None
    precio: Optional[float] = None
    pelicula_id: Optional[int] = None
    sala_id: Optional[int] = None

class FuncionOut(FuncionBase):
    id: int
    activo: bool
    pelicula: PeliculaOut
    sala: SalaOut
    class Config:
        from_attributes = True


# ─────────────── CLIENTE ───────────────
class ClienteBase(BaseModel):
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None

class ClienteOut(ClienteBase):
    id: int
    activo: bool
    class Config:
        from_attributes = True


# ─────────────── RESERVA ───────────────
class ReservaBase(BaseModel):
    numero_asiento: str
    cliente_id: int
    funcion_id: int

class ReservaCreate(ReservaBase):
    pass

class ReservaUpdate(BaseModel):
    numero_asiento: Optional[str] = None
    estado: Optional[str] = None

class ReservaOut(ReservaBase):
    id: int
    estado: str
    activo: bool
    class Config:
        from_attributes = True


# ─────────────── ADMIN / USUARIOS (solo salida y creación específica) ───────────────
class AdminBase(BaseModel):
    nombre: str
    email: EmailStr

class AdminCreate(AdminBase):
    password: str

class AdminUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    activo: Optional[bool] = None

class AdminOut(AdminBase):
    id: int
    rol: str
    activo: bool
    class Config:
        from_attributes = True
