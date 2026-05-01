from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from app.database import get_db
from app import models, schemas
from datetime import datetime

# ════════════════════════════════════════
#              GENEROS
# ════════════════════════════════════════
router_generos = APIRouter(prefix="/generos", tags=["Géneros"])

@router_generos.get("/", response_model=List[schemas.GeneroOut])
def listar_generos(db: Session = Depends(get_db)):
    return db.query(models.Genero).all()

@router_generos.get("/{genero_id}", response_model=schemas.GeneroOut)
def obtener_genero(genero_id: int, db: Session = Depends(get_db)):
    genero = db.query(models.Genero).filter(models.Genero.id == genero_id).first()
    if not genero:
        raise HTTPException(status_code=404, detail="Género no encontrado")
    return genero

@router_generos.post("/", response_model=schemas.GeneroOut, status_code=201)
def crear_genero(data: schemas.GeneroCreate, db: Session = Depends(get_db)):
    genero = models.Genero(**data.model_dump())
    db.add(genero)
    db.commit()
    db.refresh(genero)
    return genero

@router_generos.put("/{genero_id}", response_model=schemas.GeneroOut)
def actualizar_genero(genero_id: int, data: schemas.GeneroUpdate, db: Session = Depends(get_db)):
    genero = db.query(models.Genero).filter(models.Genero.id == genero_id).first()
    if not genero:
        raise HTTPException(status_code=404, detail="Género no encontrado")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(genero, campo, valor)
    db.commit()
    db.refresh(genero)
    return genero

@router_generos.delete("/{genero_id}", status_code=204)
def eliminar_genero(genero_id: int, db: Session = Depends(get_db)):
    genero = db.query(models.Genero).filter(models.Genero.id == genero_id).first()
    if not genero:
        raise HTTPException(status_code=404, detail="Género no encontrado")
    db.delete(genero)
    db.commit()


# ════════════════════════════════════════
#              PELICULAS
# ════════════════════════════════════════
router_peliculas = APIRouter(prefix="/peliculas", tags=["Películas"])

@router_peliculas.get("/", response_model=List[schemas.PeliculaOut])
def listar_peliculas(db: Session = Depends(get_db)):
    return db.query(models.Pelicula).filter(models.Pelicula.activo == True).all()

@router_peliculas.get("/{pelicula_id}", response_model=schemas.PeliculaOut)
def obtener_pelicula(pelicula_id: int, db: Session = Depends(get_db)):
    pelicula = db.query(models.Pelicula).filter(
        models.Pelicula.id == pelicula_id, models.Pelicula.activo == True
    ).first()
    if not pelicula:
        raise HTTPException(status_code=404, detail="Película no encontrada")
    return pelicula

@router_peliculas.post("/", response_model=schemas.PeliculaOut, status_code=201)
def crear_pelicula(data: schemas.PeliculaCreate, db: Session = Depends(get_db)):
    genero_ids = data.genero_ids
    pelicula_data = data.model_dump(exclude={"genero_ids"})
    pelicula = models.Pelicula(**pelicula_data)

    if genero_ids:
        generos = db.query(models.Genero).filter(models.Genero.id.in_(genero_ids)).all()
        if len(generos) != len(genero_ids):
            raise HTTPException(status_code=400, detail="Uno o más géneros no existen")
        pelicula.generos = generos

    db.add(pelicula)
    db.commit()
    db.refresh(pelicula)
    return pelicula

@router_peliculas.put("/{pelicula_id}", response_model=schemas.PeliculaOut)
def actualizar_pelicula(pelicula_id: int, data: schemas.PeliculaUpdate, db: Session = Depends(get_db)):
    pelicula = db.query(models.Pelicula).filter(
        models.Pelicula.id == pelicula_id, models.Pelicula.activo == True
    ).first()
    if not pelicula:
        raise HTTPException(status_code=404, detail="Película no encontrada")

    campos = data.model_dump(exclude_unset=True)
    genero_ids = campos.pop("genero_ids", None)

    for campo, valor in campos.items():
        setattr(pelicula, campo, valor)

    if genero_ids is not None:
        generos = db.query(models.Genero).filter(models.Genero.id.in_(genero_ids)).all()
        pelicula.generos = generos

    db.commit()
    db.refresh(pelicula)
    return pelicula

@router_peliculas.delete("/{pelicula_id}", status_code=204)
def eliminar_pelicula(pelicula_id: int, db: Session = Depends(get_db)):
    """Eliminación lógica: marca activo=False"""
    pelicula = db.query(models.Pelicula).filter(
        models.Pelicula.id == pelicula_id, models.Pelicula.activo == True
    ).first()
    if not pelicula:
        raise HTTPException(status_code=404, detail="Película no encontrada")
    pelicula.activo = False
    db.commit()


# ════════════════════════════════════════
#              SALAS
# ════════════════════════════════════════
router_salas = APIRouter(prefix="/salas", tags=["Salas"])

@router_salas.get("/", response_model=List[schemas.SalaOut])
def listar_salas(db: Session = Depends(get_db)):
    return db.query(models.Sala).filter(models.Sala.activo == True).all()

@router_salas.get("/{sala_id}", response_model=schemas.SalaOut)
def obtener_sala(sala_id: int, db: Session = Depends(get_db)):
    sala = db.query(models.Sala).filter(models.Sala.id == sala_id, models.Sala.activo == True).first()
    if not sala:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    return sala

@router_salas.post("/", response_model=schemas.SalaOut, status_code=201)
def crear_sala(data: schemas.SalaCreate, db: Session = Depends(get_db)):
    sala = models.Sala(**data.model_dump())
    db.add(sala)
    db.commit()
    db.refresh(sala)
    return sala

@router_salas.put("/{sala_id}", response_model=schemas.SalaOut)
def actualizar_sala(sala_id: int, data: schemas.SalaUpdate, db: Session = Depends(get_db)):
    sala = db.query(models.Sala).filter(models.Sala.id == sala_id, models.Sala.activo == True).first()
    if not sala:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(sala, campo, valor)
    db.commit()
    db.refresh(sala)
    return sala

@router_salas.delete("/{sala_id}", status_code=204)
def eliminar_sala(sala_id: int, db: Session = Depends(get_db)):
    """Eliminación lógica"""
    sala = db.query(models.Sala).filter(models.Sala.id == sala_id, models.Sala.activo == True).first()
    if not sala:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    sala.activo = False
    db.commit()


# ════════════════════════════════════════
#              FUNCIONES
# ════════════════════════════════════════
router_funciones = APIRouter(prefix="/funciones", tags=["Funciones"])

@router_funciones.get("/", response_model=List[schemas.FuncionOut])
def listar_funciones(db: Session = Depends(get_db)):
    # Auto-desactivar funciones cuya fecha ya pasó
    ahora = datetime.utcnow()
    vencidas = db.query(models.Funcion).filter(models.Funcion.activo == True, models.Funcion.fecha_hora < ahora).all()
    for f in vencidas:
        f.activo = False
    if vencidas:
        db.commit()
    return db.query(models.Funcion).filter(models.Funcion.activo == True).all()

@router_funciones.get("/{funcion_id}", response_model=schemas.FuncionOut)
def obtener_funcion(funcion_id: int, db: Session = Depends(get_db)):
    funcion = db.query(models.Funcion).filter(
        models.Funcion.id == funcion_id, models.Funcion.activo == True
    ).first()
    if not funcion:
        raise HTTPException(status_code=404, detail="Función no encontrada")
    return funcion

@router_funciones.post("/", response_model=schemas.FuncionOut, status_code=201)
def crear_funcion(data: schemas.FuncionCreate, db: Session = Depends(get_db)):
    # Validar que existan pelicula y sala
    if not db.query(models.Pelicula).filter(models.Pelicula.id == data.pelicula_id).first():
        raise HTTPException(status_code=404, detail="Película no encontrada")
    if not db.query(models.Sala).filter(models.Sala.id == data.sala_id).first():
        raise HTTPException(status_code=404, detail="Sala no encontrada")

    # Validaciones: fecha en el futuro y precio positivo
    if data.fecha_hora <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="La fecha y hora deben ser futuras")
    if data.precio <= 0:
        raise HTTPException(status_code=400, detail="El precio debe ser mayor a 0")

    funcion = models.Funcion(**data.model_dump())
    db.add(funcion)
    db.commit()
    db.refresh(funcion)
    return funcion

@router_funciones.put("/{funcion_id}", response_model=schemas.FuncionOut)
def actualizar_funcion(funcion_id: int, data: schemas.FuncionUpdate, db: Session = Depends(get_db)):
    funcion = db.query(models.Funcion).filter(
        models.Funcion.id == funcion_id, models.Funcion.activo == True
    ).first()
    if not funcion:
        raise HTTPException(status_code=404, detail="Función no encontrada")
    campos = data.model_dump(exclude_unset=True)
    # Validaciones si se actualiza fecha_hora o precio
    if 'fecha_hora' in campos and campos['fecha_hora'] <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="La fecha y hora deben ser futuras")
    if 'precio' in campos and campos['precio'] <= 0:
        raise HTTPException(status_code=400, detail="El precio debe ser mayor a 0")

    for campo, valor in campos.items():
        setattr(funcion, campo, valor)
    db.commit()
    db.refresh(funcion)
    return funcion

@router_funciones.delete("/{funcion_id}", status_code=204)
def eliminar_funcion(funcion_id: int, db: Session = Depends(get_db)):
    """Eliminación lógica"""
    funcion = db.query(models.Funcion).filter(
        models.Funcion.id == funcion_id, models.Funcion.activo == True
    ).first()
    if not funcion:
        raise HTTPException(status_code=404, detail="Función no encontrada")
    # Marcar la función como inactiva
    funcion.activo = False
    # Marcar las reservas activas de esta función como canceladas (eliminación lógica)
    reservas = db.query(models.Reserva).filter(models.Reserva.funcion_id == funcion_id, models.Reserva.activo == True).all()
    for r in reservas:
        r.activo = False
        r.estado = 'cancelada'
    db.commit()


# ════════════════════════════════════════
#              CLIENTES
# ════════════════════════════════════════
router_clientes = APIRouter(prefix="/clientes", tags=["Clientes"])

@router_clientes.get("/", response_model=List[schemas.ClienteOut])
def listar_clientes(db: Session = Depends(get_db)):
    # Excluir clientes que coincidan con un usuario administrador (misma dirección de email)
    admin_emails = select(models.Usuario.email).where(models.Usuario.rol == 'admin', models.Usuario.activo == True)
    return db.query(models.Cliente).filter(models.Cliente.activo == True, ~models.Cliente.email.in_(admin_emails)).all()

@router_clientes.get("/{cliente_id}", response_model=schemas.ClienteOut)
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(
        models.Cliente.id == cliente_id, models.Cliente.activo == True
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router_clientes.post("/", response_model=schemas.ClienteOut, status_code=201)
def crear_cliente(data: schemas.ClienteCreate, db: Session = Depends(get_db)):
    existente = db.query(models.Cliente).filter(models.Cliente.email == data.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un cliente con ese email")
    # Evitar crear un cliente con el email de un administrador
    admin_user = db.query(models.Usuario).filter(models.Usuario.email == data.email, models.Usuario.rol == 'admin', models.Usuario.activo == True).first()
    if admin_user:
        raise HTTPException(status_code=400, detail="No se puede crear un cliente con el email de un administrador")
    cliente = models.Cliente(**data.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

@router_clientes.put("/{cliente_id}", response_model=schemas.ClienteOut)
def actualizar_cliente(cliente_id: int, data: schemas.ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.query(models.Cliente).filter(
        models.Cliente.id == cliente_id, models.Cliente.activo == True
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente

@router_clientes.delete("/{cliente_id}", status_code=204)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    """Eliminación lógica"""
    cliente = db.query(models.Cliente).filter(
        models.Cliente.id == cliente_id, models.Cliente.activo == True
    ).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    cliente.activo = False
    db.commit()


# ════════════════════════════════════════
#              RESERVAS
# ════════════════════════════════════════
router_reservas = APIRouter(prefix="/reservas", tags=["Reservas"])

@router_reservas.get("/", response_model=List[schemas.ReservaOut])
def listar_reservas(db: Session = Depends(get_db)):
    return db.query(models.Reserva).filter(models.Reserva.activo == True).all()

@router_reservas.get("/{reserva_id}", response_model=schemas.ReservaOut)
def obtener_reserva(reserva_id: int, db: Session = Depends(get_db)):
    reserva = db.query(models.Reserva).filter(
        models.Reserva.id == reserva_id, models.Reserva.activo == True
    ).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reserva

@router_reservas.post("/", response_model=schemas.ReservaOut, status_code=201)
def crear_reserva(data: schemas.ReservaCreate, db: Session = Depends(get_db)):
    if not db.query(models.Cliente).filter(models.Cliente.id == data.cliente_id).first():
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if not db.query(models.Funcion).filter(models.Funcion.id == data.funcion_id).first():
        raise HTTPException(status_code=404, detail="Función no encontrada")

    reserva = models.Reserva(**data.model_dump())
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return reserva

@router_reservas.put("/{reserva_id}", response_model=schemas.ReservaOut)
def actualizar_reserva(reserva_id: int, data: schemas.ReservaUpdate, db: Session = Depends(get_db)):
    reserva = db.query(models.Reserva).filter(
        models.Reserva.id == reserva_id, models.Reserva.activo == True
    ).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(reserva, campo, valor)
    db.commit()
    db.refresh(reserva)
    return reserva

@router_reservas.delete("/{reserva_id}", status_code=204)
def eliminar_reserva(reserva_id: int, db: Session = Depends(get_db)):
    """Eliminación lógica: cambia estado a cancelada"""
    reserva = db.query(models.Reserva).filter(
        models.Reserva.id == reserva_id, models.Reserva.activo == True
    ).first()
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    reserva.activo = False
    reserva.estado = "cancelada"
    db.commit()
